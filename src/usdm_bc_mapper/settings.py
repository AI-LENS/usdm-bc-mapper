import os
from importlib.resources import files
from pathlib import Path

from pydantic import FilePath
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

print("settings -- working directory:", os.getcwd())


class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"

    data_path: FilePath = (
        Path(str(files("usdm_bc_mapper"))) / "data/cdisc_biomedical_concepts_latest.csv"
    )
    data_search_cols: list[str] = [
        "short_name",
        "bc_categories",
        "synonyms",
        "definition",
    ]
    max_ai_lookup_attempts: int = 7
    system_prompt_file: FilePath = (
        Path(str(files("usdm_bc_mapper"))) / "data/system_prompt.txt"
    )

    model_config = SettingsConfigDict(
        yaml_file="config.yaml", yaml_file_encoding="utf-8"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()  # type: ignore
