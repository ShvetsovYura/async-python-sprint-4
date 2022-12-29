from pydantic import BaseModel


class CreatedLinkModel(BaseModel):
    url_id: str
    link: str
