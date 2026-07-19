from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    replicate_api_token: str = ""

    storage_dir: Path = Path("./storage")
    max_edge: int = 2048
    codeformer_fidelity: float = 0.75
    identity_threshold: float = 0.55
    review_threshold: float = 0.68

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
