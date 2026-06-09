from pydantic import BaseModel, HttpUrl, field_validator


class Stremio(BaseModel):
    admin_base_url: HttpUrl
    admin_scan_token: str

    @field_validator("admin_scan_token")
    @classmethod
    def strip_token(cls, value: str) -> str:
        return (value or "").strip()
