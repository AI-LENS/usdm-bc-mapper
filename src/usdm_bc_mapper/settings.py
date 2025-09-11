from importlib.resources import files
from pathlib import Path

from pydantic import DirectoryPath, FilePath
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

project_root = Path(files("usdm_bc_mapper"))  # type:ignore


class Settings(BaseSettings):
    llm_api_key: str | None
    llm_model: str = "openai/gpt-5-mini"
    llm_base_url: str = "https://openrouter.ai/api/v1"

    data_path: DirectoryPath = project_root / "data"
    data_search_cols: list[str] = [
        "short_name",
        "bc_categories",
        "synonyms",
        "definition",
    ]
    max_ai_lookup_attempts: int = 7
    system_prompt_file: FilePath = project_root / "data/system_prompt.txt"

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
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )


settings = Settings()  # type: ignore
