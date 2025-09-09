import logging
from dataclasses import dataclass

from cyclopts import App, Parameter
from pydantic import FilePath
from pydantic_settings import YamlConfigSettingsSource
from usdm_model.wrapper import Wrapper

from .cdisc_bc_search import CdiscBcIndex
from .find_bc import find_biomedical_concept
from .mapper import map_biomedical_concepts
from .settings import Settings, settings


@Parameter(name="*")
@dataclass
class CommonArgs:
    config: FilePath | None = None
    show_logs: bool = False

    def __post_init__(self):
        if self.show_logs:
            logging.basicConfig(level=logging.DEBUG)
            logging.getLogger("openai").setLevel(logging.CRITICAL + 1)
            logging.getLogger("httpcore").setLevel(logging.CRITICAL + 1)
            logging.getLogger("httpx").setLevel(logging.CRITICAL + 1)
            logging.getLogger("bm25s").setLevel(logging.CRITICAL + 1)
        if self.config:
            yaml_config = YamlConfigSettingsSource(Settings, yaml_file=self.config)
            new_settings = Settings.model_validate(yaml_config())
            settings.__init__(**new_settings.model_dump())


cli = App()


@cli.command(name="usdm")
async def usdm_bc_mapper(
    usdm_path: FilePath, output: str | None = None, *, _: CommonArgs | None = None
):
    """Map biomedical concepts in a USDM (Unified Study Data Model) file.

    Args:
        usdm_path (FilePath): The path to the USDM file to process.
    """
    print("Processing file: ", usdm_path.absolute().as_posix())

    usdm = Wrapper.model_validate_json(usdm_path.read_text(encoding="utf-8"))
    print("Study Name: ", usdm.study.name)

    await map_biomedical_concepts(usdm, output_file_name=output)


@cli.command
async def find_bc_cdisc(concept: str, *, _: CommonArgs | None = None):
    """Find a matching biomedical concept in the CDISC library using LLM.

    Args:
        concept (str): The biomedical concept to find a match for.
    """
    result = await find_biomedical_concept(concept=concept)
    print("Search result:\n", result.model_dump_json(indent=2))


@cli.command
async def search_bc_cdisc(concept: str, k: int = 10, *, _: CommonArgs | None = None):
    """Search for biomedical concepts in the CDISC library using a local index.

    Args:
        concept (str): The biomedical concept to search for.
        k (int, optional): The number of search results to return. Defaults to 10.
    """
    bc_index = CdiscBcIndex()
    result = bc_index.search(concept, k=k, return_formatted_string=True)
    print("Search result:\n", result)
