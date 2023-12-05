from pydantic import BaseModel
from typing import Dict, Union

class RequestItem(BaseModel):
    action: str
    data: Dict[str, Union[int, str]]
    failures: Dict[str, str]