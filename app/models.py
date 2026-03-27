from pydantic import BaseModel
from typing import Optional, Dict, Any


class DeviceResponse(BaseModel):
    device_id: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    api_latency: float
    queue_time: float
    end_to_end_latency: float
