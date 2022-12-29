from models.base_json_model import BaseOrjsonModel


class CreateShortLinkModel(BaseOrjsonModel):
    original_link: str
