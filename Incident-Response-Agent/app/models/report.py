from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


class SpecialistFinding(BaseModel):
    specialist: str
    severity: Severity
    summary: str
    details: str


class IncidentReport(BaseModel):
    timestamp: datetime
    overall_severity: Severity
    title: str
    diagnosis: str
    recommendations: list[str]
    findings: list[SpecialistFinding]
