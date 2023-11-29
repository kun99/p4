from pydantic import BaseModel
from typing import Dict

class RequestItem(BaseModel):
    action: str
    data: Dict[str, str]
    failures: Dict[str, str]