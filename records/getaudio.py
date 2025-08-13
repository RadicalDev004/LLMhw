from pydantic import BaseModel
from typing import Optional

class GetAudio(BaseModel):
    audio: str