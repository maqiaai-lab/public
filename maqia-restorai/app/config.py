from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    replicate_api_token: str = ""

    storage_dir: Path = Path("./storage")
    max_edge: int = 2048
    codeformer_fidelity: float = 0.75          # default (adults)
    codeformer_skip_age: int = 4               # infants/toddlers: skip entirely
    codeformer_child_fidelity: float = 0.90    # ages 4-12: very identity-leaning
    codeformer_teen_fidelity: float = 0.82     # ages 13-17
    # Guard: if CodeFormer drops face identity below this vs the pre-restore
    # face, it distorted the person — revert to the un-restored face. This is
    # the robust protection (age estimation is unreliable on degraded photos).
    codeformer_min_identity: float = 0.75
    identity_threshold: float = 0.55
    review_threshold: float = 0.68

    # Colorization: "deoldify" (natural, conservative — default) or "ddcolor"
    # (vivid but prone to implausible hues on plain regions).
    colorizer: str = "deoldify"
    deoldify_model: str = "Artistic"   # "Artistic" (warmer skin) or "Stable" (muted)
    deoldify_render_factor: int = 35

    # Digitization (phone capture of a physical photo)
    digitize_enabled: bool = True
    digitize_auto_detect: bool = True
    digitize_min_confidence: float = 0.65
    digitize_crop_margin: int = 3
    digitize_demoire: bool = False
    digitize_strategy: str = "single_shot"  # "single_shot" | "multi_shot"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
