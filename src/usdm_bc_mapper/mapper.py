import json
import logging
from datetime import date, datetime
from uuid import uuid4

import polars as pl
from tqdm import tqdm
from usdm_model.alias_code import AliasCode
from usdm_model.biomedical_concept import BiomedicalConcept
from usdm_model.biomedical_concept_property import BiomedicalConceptProperty
from usdm_model.code import Code
from usdm_model.response_code import ResponseCode
from usdm_model.wrapper import Wrapper

from .cdisc_bc_search import build_data
from .find_bc import find_biomedical_concept
from .settings import settings

logger = logging.getLogger(__name__)

data_spec_df = pl.scan_csv(
    str(settings.data_path / "cdisc_sdtm_dataset_specializations_latest.csv")
)
bc_df = pl.scan_csv(str(settings.data_path / "cdisc_biomedical_concepts_latest.csv"))


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


async def map_biomedical_concepts(usdm: Wrapper, output_file_name: str | None = None):
    """Map biomedical concepts to USDM wrapper and generate JSON output."""
    activities: dict[str, str] = {}

    # Process activities to find additional biomedical concepts
    for version in usdm.study.versions:
        logger.info(f"Present biomedical concepts: {len(version.biomedicalConcepts)}")

        for study_design in version.studyDesigns:
            logger.info(f"Study design activities: {len(study_design.activities)}")

            # Limit to first 5 activities for processing
            for activity in tqdm(study_design.activities):
                logger.info(f"Mapping activity: {activity.label}")

                try:
                    bc_response = await find_biomedical_concept(
                        activity.name + "\n" + (activity.label or "")
                    )
                    if bc_response and bc_response.type == "FinalAnswer":
                        activities[activity.name] = bc_response.vlm_group_id
                        logger.info(
                            f"Found biomedical concept ID: {bc_response.vlm_group_id}"
                        )
                    else:
                        logger.warning(
                            f"No valid response for activity: {activity.label}"
                        )

                except Exception as error:
                    if "Max attempts reached" in str(error):
                        logger.warning(
                            f"Skipping activity '{activity.label}': Max attempts reached"
                        )
                        continue
                    else:
                        logger.error(
                            f"Error processing activity '{activity.label}': {error}"
                        )
                        continue

    logger.info(f"Total mapped biomedical concept IDs: {len(activities)}")

    vlm_df = build_data()

    # Process each biomedical concept ID
    for activity_name, vlm_group_id in activities.items():
        link = f"https://api.library.cdisc.org/api/cosmos/v2/mdr/specializations/sdtm/datasetspecializations/{vlm_group_id}"

        vlm_row = vlm_df.filter(pl.col("vlm_group_id") == vlm_group_id).row(
            0, named=True
        )

        bc_id = vlm_row["bc_id"]
        synonyms = (
            bc_df.filter(pl.col("bc_id") == bc_id)
            .select("synonyms")
            .unique()
            .collect()
            .item()
            .split(";")
        )

        code = Code(
            id=str(uuid4()),
            code=vlm_row["bc_id"],
            codeSystem="http://www.cdisc.org",
            codeSystemVersion=vlm_row["package_date"],
            decode=vlm_row["short_name_bc"],
            instanceType="Code",
        )
        alias_code = AliasCode(
            id=str(uuid4()), standardCode=code, instanceType="AliasCode"
        )
        new_target = BiomedicalConcept(
            id=str(uuid4()),
            name=vlm_row["short_name"],
            label=vlm_row["short_name"],
            synonyms=synonyms,
            reference=link,
            code=alias_code,
            instanceType="BiomedicalConcept",
        )

        df = pl.scan_csv(
            str(settings.data_path / "Thesaurus.txt"),
            separator="\t",
            has_header=False,
            quote_char=None,
            new_columns=[
                "code",
                "concept IRI",
                "parents",
                "synonyms",
                "definition",
                "display name",
                "concept status",
                "semantic type",
                "concept in subset",
            ],
        )

        def dec_decode2(code: str):
            return (
                df.filter(pl.col("code") == code)
                .select("synonyms")
                .collect()
                .item()
                .split("|")[0]
            )

        cdisc_data_path = settings.data_path / "cdisc_terminology"
        datasets = []
        for file in cdisc_data_path.glob("*.txt"):
            tmp_df = pl.scan_csv(file, separator="\t", quote_char=None)
            package = file.stem.split(" ")[0]
            logging.info(f"Loading codelists for {package}")
            tmp_df = tmp_df.with_columns(pl.lit(package).alias("package"))
            tmp_df = tmp_df.with_columns(pl.lit("2025-03-28").alias("package_date"))
            datasets.append(tmp_df)

        # Concatenate all datasets
        codelist_df: pl.LazyFrame = pl.concat(datasets)

        for variable in vlm_df.rows(named=True):
            if not (dec := variable.get("dec_id")):
                continue
            bc_code = Code(
                id=str(uuid4()),
                code=dec,
                codeSystem="http://www.cdisc.org",
                codeSystemVersion=variable["package_date"],
                decode=dec_decode2(dec),
                instanceType="Code",
            )
            bc_alias_code = AliasCode(
                id=str(uuid4()), standardCode=bc_code, instanceType="AliasCode"
            )
            new_property = BiomedicalConceptProperty(
                id=str(uuid4()),
                name=variable["sdtm_variable"],
                label=variable["sdtm_variable"],
                isRequired=variable.get("mandatory_variable", "N") == "Y",
                isEnabled=True,
                responseCodes=[],
                datatype=variable["data_type"] or "",
                code=bc_alias_code,
                instanceType="BiomedicalConceptProperty",
            )
            if (value_list := variable["value_list"]) is None:
                continue
            if (codelist := variable["codelist"]) is None:
                continue
            response_df = (
                codelist_df.filter(
                    (pl.col("Codelist Code") == codelist)
                    & pl.col("CDISC Submission Value").is_in(value_list.split(";"))
                )
                .select(
                    "Code",
                    "CDISC Submission Value",
                    "NCI Preferred Term",
                    "package_date",
                )
                .unique()
                .collect()
            )
            for response in response_df.rows(named=True):
                new_response_code = ResponseCode(
                    id=str(uuid4()),
                    name=f"RC_{response['Code']}",
                    isEnabled=True,
                    code=Code(
                        id=str(uuid4()),
                        code=response["Code"],
                        codeSystem="http://www.cdisc.org",
                        codeSystemVersion=response["package_date"],
                        decode=response["NCI Preferred Term"],
                        instanceType="Code",
                    ),
                    instanceType="ResponseCode",
                )
                new_property.responseCodes.append(new_response_code)
            new_target.properties.append(new_property)

        topic_code = alias_code.model_copy(deep=True)
        topic_code.id = str(uuid4())
        topic_code.standardCode.id = str(uuid4())
        topic_property = BiomedicalConceptProperty(
            id=str(uuid4()),
            name=vlm_row["short_name"],
            label=vlm_row["short_name"],
            code=topic_code,
            isRequired=True,
            isEnabled=True,
            datatype=vlm_row["data_type"] or "String",
            responseCodes=[],
            instanceType="BiomedicalConceptProperty",
        )

        new_target.properties.append(topic_property)
        usdm.study.versions[0].biomedicalConcepts.append(new_target)
        for activity in usdm.study.versions[0].studyDesigns[0].activities:
            if activity.name == activity_name:
                activity.biomedicalConceptIds.append(new_target.id)

    # Save the mapped biomedical concepts to JSON file
    output_file_path = output_file_name or "mapped_biomedical_concept.json"
    with open(output_file_path, "w") as file:
        json.dump(usdm.model_dump(), file, indent=2, cls=DateTimeEncoder)
