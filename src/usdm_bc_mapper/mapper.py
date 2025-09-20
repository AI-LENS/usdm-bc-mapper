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

            for activity in tqdm(study_design.activities[:5]):
                logger.info(f"=== PROCESSING ACTIVITY: {activity.name} ({activity.label}) ===")

                try:
                    # STEP 1: Search for biomedical concept
                    logger.info(f"STEP 1: Searching for biomedical concept for activity '{activity.name}'")
                    bc_response = await find_biomedical_concept(
                        activity.name + "\n" + (activity.label or "")
                    )
                    
                    if bc_response and bc_response.type == "FinalAnswer":
                        activities[activity.name] = bc_response.vlm_group_id
                        logger.info(f"STEP 1: ✅ SUCCESS - Found vlm_group_id: {bc_response.vlm_group_id}")
                    else:
                        logger.warning(f"STEP 1: ❌ FAILED - No valid biomedical concept found for activity '{activity.name}'")
                        logger.warning(f"STEP 1: Reason - Response type: {bc_response.type if bc_response else 'None'}")
                        continue

                except Exception as error:
                    if "Max attempts reached" in str(error):
                        logger.warning(f"STEP 1: ❌ FAILED - Max LLM attempts reached for activity '{activity.name}'")
                        continue
                    else:
                        logger.error(f"STEP 1: ❌ ERROR - Exception in activity '{activity.name}': {error}")
                        continue

    logger.info(f"Total mapped biomedical concept IDs: {len(activities)}")

    vlm_df = build_data()

    # Find next sequential biomedical concept number
    existing_bc_ids = [bc.id for bc in usdm.study.versions[0].biomedicalConcepts if bc.id.startswith("BiomedicalConcept_")]
    next_bc_number = max([int(id.split("_")[1]) for id in existing_bc_ids], default=0) + 1

    # Process each biomedical concept ID
    logger.info(f"\n=== STEP 2: CHECKING FOR EXISTING BIOMEDICAL CONCEPTS ===")
    for activity_name, vlm_group_id in activities.items():
        logger.info(f"\n--- Processing activity '{activity_name}' ---")
        
        # Get the CDISC bc_id for this vlm_group_id
        logger.info(f"STEP 2A: Getting bc_id for vlm_group_id: {vlm_group_id}")
        vlm_row = vlm_df.filter(pl.col("vlm_group_id") == vlm_group_id).row(0, named=True)
        bc_id = vlm_row["bc_id"]  # This is the unique CDISC bc_id (starts with "C...")
        logger.info(f"STEP 2A: ✅ Found bc_id: {bc_id}")
        
        # Check if this bc_id already exists in any biomedical concept
        logger.info(f"STEP 2B: Checking if bc_id '{bc_id}' already exists in USDM...")
        existing_bc = None
        for bc in usdm.study.versions[0].biomedicalConcepts:
            if bc.code and hasattr(bc.code, 'standardCode') and bc.code.standardCode.code == bc_id:
                existing_bc = bc
                break
        
        if existing_bc:
            # Skip - biomedical concept with this bc_id already exists
            logger.info(f"STEP 2B: ❌ SKIP - bc_id '{bc_id}' already exists as '{existing_bc.id}'")
            logger.info(f"STEP 2B: Reason - Avoiding duplicate biomedical concept")
            continue
        else:
            logger.info(f"STEP 2B: ✅ bc_id '{bc_id}' not found in existing biomedical concepts")
        
        # STEP 3: Create new biomedical concept with sequential ID
        logger.info(f"\nSTEP 3: Creating new biomedical concept for activity '{activity_name}'")
        target_bc_id = f"BiomedicalConcept_{next_bc_number}"
        logger.info(f"STEP 3A: Assigned new sequential ID: {target_bc_id}")
        next_bc_number += 1
        
        try:
            logger.info(f"STEP 3B: Gathering biomedical concept data...")
            synonyms = bc_df.filter(pl.col("bc_id") == bc_id).select("synonyms").unique().collect().item().split(";")
            link = f"https://api.library.cdisc.org/api/cosmos/v2/mdr/specializations/sdtm/datasetspecializations/{vlm_group_id}"
            logger.info(f"STEP 3B: ✅ Found {len(synonyms)} synonyms and reference link")
            
            logger.info(f"STEP 3C: Creating biomedical concept structure...")
            code = Code(
                id=str(uuid4()),
                code=bc_id,
                codeSystem="http://www.cdisc.org",
                codeSystemVersion=vlm_row["package_date"],
                decode=vlm_row["short_name_bc"],
                instanceType="Code",
            )
            alias_code = AliasCode(
                id=str(uuid4()), standardCode=code, instanceType="AliasCode"
            )
            new_target = BiomedicalConcept(
                id=target_bc_id,
                name=vlm_row["short_name"],
                label=vlm_row["short_name"],
                synonyms=synonyms,
                reference=link,
                code=alias_code,
                instanceType="BiomedicalConcept",
            )
            logger.info(f"STEP 3C: ✅ Created biomedical concept '{target_bc_id}' with bc_id '{bc_id}'")
        except Exception as e:
            logger.error(f"STEP 3: ❌ ERROR - Failed to create biomedical concept: {e}")
            continue

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

        # STEP 3D: Create properties and add new biomedical concept to study
        try:
            logger.info(f"STEP 3D: Adding properties to biomedical concept...")
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
            logger.info(f"STEP 3D: ✅ Added biomedical concept '{target_bc_id}' to USDM study")
            
            # STEP 3E: Link the activity to the new biomedical concept
            logger.info(f"STEP 3E: Linking activity '{activity_name}' to biomedical concept '{target_bc_id}'...")
            linked = False
            for activity in usdm.study.versions[0].studyDesigns[0].activities:
                if activity.name == activity_name:
                    activity.biomedicalConceptIds.append(target_bc_id)
                    linked = True
                    break
            
            if linked:
                logger.info(f"STEP 3E: ✅ Successfully linked activity '{activity_name}' to '{target_bc_id}'")
            else:
                logger.warning(f"STEP 3E: ❌ FAILED - Could not find activity '{activity_name}' to link")
                
        except Exception as e:
            logger.error(f"STEP 3D/3E: ❌ ERROR - Failed to add properties or link activity: {e}")
            continue

    # Save the mapped biomedical concepts to JSON file
    output_file_path = output_file_name or "mapped_biomedical_concept.json"
    with open(output_file_path, "w") as file:
        json.dump(usdm.model_dump(), file, indent=2, cls=DateTimeEncoder)
