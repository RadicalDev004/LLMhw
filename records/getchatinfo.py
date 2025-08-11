from pydantic import BaseModel
from typing import Optional

class GetChatInfo(BaseModel):
    id: int