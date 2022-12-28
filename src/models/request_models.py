from pydantic import BaseModel


class CreateShortLinkModel(BaseModel):
    original_link: str
