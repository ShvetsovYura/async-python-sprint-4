from models.base_json_model import BaseOrjsonModel


class CreatedLinkModel(BaseOrjsonModel):
    url_id: str
    link: str
