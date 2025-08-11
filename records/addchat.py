from pydantic import BaseModel
from typing import Optional

class AddChat(BaseModel):
    username: str
    chatname: str