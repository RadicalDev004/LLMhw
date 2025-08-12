from pydantic import BaseModel
from typing import Optional

class AddMsg(BaseModel):
    id: int
    content: str
    image: bool
    sound: bool