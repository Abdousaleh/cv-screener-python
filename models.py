from typing import List, Optional
from pydantic import BaseModel

class resume(BaseModel):
    name: str
    file_name:str
    email: str
    phone: List[int]
    skills: Optional [List[str]]
    path: Optional[str]
