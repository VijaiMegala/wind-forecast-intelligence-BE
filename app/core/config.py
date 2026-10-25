from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    elexon_base_url: str = os.getenv(
        "ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1"
    )


settings = Settings()
