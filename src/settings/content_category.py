from pydantic import BaseModel, field_validator


class ContentCategory(BaseModel):
    id: str
    label: str
    prompt: str
    qbittorrent_category: str
    save_path: str

    @field_validator("id", "label", "prompt", "qbittorrent_category", "save_path")
    @classmethod
    def not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field cannot be empty")
        return value.strip()
