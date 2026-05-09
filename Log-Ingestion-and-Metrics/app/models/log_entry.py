from datetime import datetime
from pydantic import BaseModel


class HAProxyLogEntry(BaseModel):
    time_local: datetime
    client_ip: str
    frontend_name: str
    backend_name: str
    http_request: str
    status_code: int
    bytes_read: int
    time_request: int  # ms waiting for full request
    time_connect: int  # ms to establish backend connection
    time_response: int  # ms waiting for backend response header
    time_active: int   # ms total active time
    termination_state: str
