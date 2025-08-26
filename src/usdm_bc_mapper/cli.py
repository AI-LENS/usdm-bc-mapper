import logging

from cyclopts import App
from pydantic import FilePath
from pydantic_settings import YamlConfigSettingsSource

from usdm_bc_mapper.settings import Settings, settings

cli = App()


@cli.default
async def usdm_bc_mapper(
    usdm_path: FilePath, *, config: FilePath | None = None, show_logs: bool = False
):
    print("Processing file: ", usdm_path.absolute().as_posix())

    if show_logs:
        logging.basicConfig(level=logging.DEBUG)

    if config:
        yaml_config = YamlConfigSettingsSource(Settings, yaml_file=config)
        new_settings = Settings.model_validate(yaml_config())
        settings.__init__(**new_settings.model_dump())
