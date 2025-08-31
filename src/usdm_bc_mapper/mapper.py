from usdm_model.wrapper import Wrapper
import pandas as pd
from .settings import settings
import json
import uuid
from datetime import date, datetime

from .find_bc import find_biomedical_concept  # noqa

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


async def map_biomedical_concepts(usdm: Wrapper):
    """Map biomedical concepts to USDM wrapper and generate JSON output."""
    biomedical_concept_ids = []
    
    # Process activities to find additional biomedical concepts
    for version in usdm.study.versions:
        print(f"Present biomedical concepts: {len(version.biomedicalConcepts)}")
        
        for study_design in version.studyDesigns:
            print(f"Study design activities: {len(study_design.activities)}")
            
            # Limit to first 5 activities for processing
            for activity in study_design.activities:
                print(f"Mapping activity: {activity.label}")
                
                try:
                    bc_response = await find_biomedical_concept(activity.label)
                    if bc_response and hasattr(bc_response, 'biomedical_concept_id'):
                        biomedical_concept_ids.append(bc_response.biomedical_concept_id)
                        print(f"Found biomedical concept ID: {bc_response.biomedical_concept_id}")
                    else:
                        print(f"No valid response for activity: {activity.label}")
                        
                except Exception as error:
                    if "Max attempts reached" in str(error):
                        print(f"Skipping activity '{activity.label}': Max attempts reached")
                        continue
                    else:
                        print(f"Error processing activity '{activity.label}': {error}")
                        continue

    initial_bc_count = len(usdm.study.versions[0].biomedicalConcepts)
    print(f"Total mapped biomedical concept IDs: {initial_bc_count}")
    
    # Load biomedical concept data
    bmc_data_df = pd.read_csv(settings.data_path)
    bmc_specialization_df = pd.read_csv(settings.dataset_specialization_path)
    filtered_bmc_id_df = bmc_data_df[bmc_data_df.iloc[:, 3].isin(biomedical_concept_ids)]

    # Process each biomedical concept ID
    for concept_id in biomedical_concept_ids:
        specialization_rows = bmc_specialization_df[bmc_specialization_df.iloc[:, 1] == concept_id]
        concept_row = filtered_bmc_id_df[filtered_bmc_id_df.iloc[:, 3] == concept_id]
        properties = []
        
        dec_ids = concept_row.iloc[:, 12]
        dec_id_labels = concept_row.iloc[:, 14]
        dec_id_datatypes = concept_row.iloc[:, 15]
        
        if len(dec_ids) > 0 and not dec_ids.isnull().all():
            for dec_id in dec_ids:
                if pd.isna(dec_id):
                    continue

                property_row_indices = specialization_rows.index[specialization_rows.iloc[:, 9] == dec_id].tolist()
                if property_row_indices:
                    # Get the property name using the row index from specialization_rows (column 8)
                    property_name = specialization_rows.loc[property_row_indices[0], specialization_rows.columns[8]]
                    property_data = specialization_rows.loc[property_row_indices[0], specialization_rows.columns[0]]

                row_indices = dec_ids.index[dec_ids == dec_id].tolist()
                if row_indices:
                    dec_id_label = dec_id_labels.iloc[row_indices[0] - dec_id_labels.index[0]]
                    dec_id_datatype = dec_id_datatypes.iloc[row_indices[0] - dec_id_datatypes.index[0]]
                else:
                    dec_id_label = "Category"
                
                properties.append({
                    "id": uuid.uuid4().hex,
                    "name": property_name,
                    "label": property_name,
                    "isRequired": True,
                    "isEnabled": True,
                    "datatype": dec_id_datatype,
                    "code": {
                        "id": uuid.uuid4().hex,
                        "extensionAttributes": [],
                        "standardCode": {
                            "id": uuid.uuid4().hex,
                            "extensionAttributes": [],
                            "code": dec_id,
                            "codeSystem": "http://www.cdisc.org",
                            "codeSystemVersion": property_data,
                            "decode": dec_id_label,
                            "instanceType": "Code"
                        },
                        "standardCodeAliases": [],
                        "instanceType": "AliasCode"
                    },
                    "notes": "CommentAnnotation",
                    "responseCode": "ResponseCode"
                })

        usdm.study.versions[0].biomedicalConcepts.append({
            "id": f"BiomedicalConcept_{initial_bc_count + 1}",
            "name": concept_row.iloc[0, 1],
            "label": concept_row.iloc[0, 1],
            "synonyms": [],
            "reference": "",
            "code": {
                "id": uuid.uuid4().hex,
                "extensionAttributes": [],
                "standardCode": {
                    "id": uuid.uuid4().hex,
                    "extensionAttributes": [],
                    "code": concept_id,
                    "codeSystem": "http://www.cdisc.org",
                    "codeSystemVersion": concept_row.iloc[0, 0],
                    "decode": concept_row.iloc[0, 1],
                    "instanceType": "Code"
                },
                "standardCodeAliases": [],
                "instanceType": "AliasCode"
            },
            "properties": properties,
            "notes": [],
            "instanceType": "BiomedicalConcept"
        })
        initial_bc_count += 1

    # Save the mapped biomedical concepts to JSON file
    output_file_path = "mapped_biomedical_concept.json"
    with open(output_file_path, "w") as file:
        json.dump(usdm.model_dump(), file, indent=2, cls=DateTimeEncoder)