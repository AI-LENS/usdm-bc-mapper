from usdm_model.wrapper import Wrapper

from .find_bc import find_biomedical_concept  # noqa


async def map_biomedical_concepts(usdm: Wrapper):
    for version in usdm.study.versions:
        print("Present biomedical concepts:", len(version.biomedicalConcepts))
        for study_design in version.studyDesigns:
            print("Study design activities:", len(study_design.activities))

    print(study_design.activities[0].model_dump_json(indent=2))
