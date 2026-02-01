import os

from pydantic import BaseModel  # type: ignore


class Settings(BaseModel):  # type: ignore
    VERSION: str = "1.0.0"
    DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"
    CONTRACTS_VERSION: str = (
        "1.0.0"  # Pinned manually for now, should read from package
    )

    # Validation Limits
    MAX_BODY_SIZE_BYTES: int = 256 * 1024  # 256KB


SETTINGS = Settings()
