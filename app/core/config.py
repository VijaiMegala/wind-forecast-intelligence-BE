from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    elexon_base_url: str = os.getenv(
        "ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1"
    )
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("ALLOW_ORIGIN", "http://localhost:3000").split(",")
        if origin.strip()
    )


settings = Settings()
