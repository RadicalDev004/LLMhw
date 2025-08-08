from pydantic import BaseModel
from typing import Optional

class GetChat(BaseModel):
    username: str