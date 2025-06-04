from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from pydantic.v1 import BaseModel as LCBaseModel, Field as LCField, constr
##R from langchain.pydantic_v1 import BaseModel as LCBaseModel, Field as LCField, constr
class Incident(BaseModel):
    incident_id: str
    summary: str
    description: str
    service_ci_name: str
    priority: int
    created_at: str
    status: str
    assigned_to: str
    affected_users: Optional[List[str]] = []
    
class HistoricalIncident(Incident):
    is_major_incident: bool
    resolution_time: float  # in hours
    reassignment_count: int

class ServiceCI(BaseModel):
    ci_id: str
    name: str
    type: str
    criticality: int  # 1-5 scale, 5 being most critical
    dependencies: List[str]
    users: List[str]
    
class User(BaseModel):
    user_id: str
    name: str
    department: str
    is_vip: bool
    
class ChangeRecord(BaseModel):
    change_id: str
    summary: str
    ci_id: str
    implemented_at: str
    risk_score: float  # 0-1 scale
    
class ServiceHealth(BaseModel):
    ci_id: str
    timestamp: str
    health_score: float  # 0-100 scale
    
class ReassignmentRecord(BaseModel):
    incident_id: str
    timestamp: str
    from_group: str
    to_group: str

class MIDetectionResult(BaseModel):
    is_major_incident: bool
    confidence: float
    predictor_scores: Dict[str, float]
    weighted_score: float
    llm_reasoning: str
    recommendation: str
    summary_reasoning: str  # New: one-line reasoning summary
    details: Dict[str, Dict]  # New: detailed predictor information
    
class MIReasoningOutput(LCBaseModel):
    summary_reasoning: str = LCField(description="A one-line summary of the reasoning behind the major incident decision")
    full_reasoning: str = LCField(description="The complete reasoning process formatted as bullet points for each predictor")
    decision: bool = LCField(description="The final decision on whether this is a major incident (True) or not (False)")
    @classmethod
    def model_json_schema(cls) -> dict:
        return cls.schema()
#---
#class MIDetectionResult(BaseModel):
#    is_major_incident: bool
#    details: Dict[str, Dict]  # New: detailed predictor information
    
#class MIReasoningOutput(LCBaseModel):
#    summary_reasoning: str = LCField(description="A one-line summary of the reasoning behind the major incident decision")
#    full_reasoning: str = LCField(description="The complete reasoning process formatted as bullet points for each predictor")
#    decision: bool = LCField(description="The final decision on whether this is a major incident (True) or not (False)")
     