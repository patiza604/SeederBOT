import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App settings
    app_token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    mode: str = Field(default="blackhole", description="Operation mode: radarr or blackhole")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Radarr settings (for primary path)
    radarr_url: str | None = Field(default=None)
    radarr_api_key: str | None = Field(default=None)
    root_folder: str = Field(default="/movies")
    quality_profile_id: int = Field(default=4)

    # Jackett settings (for both paths)
    jackett_url: str | None = Field(default=None)
    jackett_api_key: str | None = Field(default=None)

    # Blackhole settings
    categories: str = Field(default="2000,2010", description="IPTorrents movie categories")
    min_seeders: int = Field(default=20)
    quality_regex: str = Field(default=r"1080p.*WEB-DL|1080p.*BluRay")
    exclude_regex: str = Field(default=r"CAM|TS|TC|WORKPRINT", description="Quality exclusions")
    min_size_gb: float = Field(default=2.5, description="Minimum file size in GB")
    max_size_gb: float = Field(default=6.0, description="Maximum file size in GB")
    autoadd_watch_dir: str = Field(default="/data/torrents/watch")

    def validate_mode_config(self) -> bool:
        if self.mode == "radarr":
            return bool(self.radarr_url and self.radarr_api_key)
        elif self.mode == "blackhole":
            return bool(self.jackett_url and self.jackett_api_key)
        return False


# Global settings instance
settings = Settings()

