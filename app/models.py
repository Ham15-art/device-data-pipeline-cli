from pydantic import BaseModel
from typing import Optional, Dict, Any

class DeviceResponse(BaseModel):
    device_id: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    duration: float