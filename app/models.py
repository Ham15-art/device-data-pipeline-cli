from pydantic import BaseModel

class DeviceResponse(BaseModel):
    status: str
    response_time: float