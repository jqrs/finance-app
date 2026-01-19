from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Finance App"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/finance.db"

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    ml_models_dir: Path = base_dir / "app" / "ml" / "models"

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(exist_ok=True)
settings.ml_models_dir.mkdir(parents=True, exist_ok=True)
