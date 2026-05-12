from datetime import datetime
from pydantic import BaseModel, Field


class HAProxyLogEntry(BaseModel):
    time_local: datetime
    client_ip: str = Field(..., max_length=45)        # max IPv6 address length
    frontend_name: str = Field(..., max_length=255)
    backend_name: str = Field(..., max_length=255)
    http_request: str = Field(..., max_length=8192)   # 8 KB cap on request line
    status_code: int = Field(..., ge=100, le=599)
    bytes_read: int = Field(..., ge=0)
    time_request: int = Field(..., ge=-1)             # HAProxy uses -1 for N/A
    time_connect: int = Field(..., ge=-1)
    time_response: int = Field(..., ge=-1)
    time_active: int = Field(..., ge=-1)
    termination_state: str = Field(..., max_length=4) # HAProxy 4-char flag field
