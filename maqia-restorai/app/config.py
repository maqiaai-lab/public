from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    replicate_api_token: str = ""

    storage_dir: Path = Path("./storage")
    max_edge: int = 2048
    codeformer_fidelity: float = 0.75
    identity_threshold: float = 0.55
    review_threshold: float = 0.68

    # Digitization (phone capture of a physical photo)
    digitize_enabled: bool = True
    digitize_auto_detect: bool = True
    digitize_min_confidence: float = 0.65
    digitize_crop_margin: int = 3
    digitize_demoire: bool = False
    digitize_strategy: str = "single_shot"  # "single_shot" | "multi_shot"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
