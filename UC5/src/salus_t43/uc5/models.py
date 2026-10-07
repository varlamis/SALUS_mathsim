from pathlib import PurePath
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
class Strict(BaseModel): model_config=ConfigDict(extra="forbid")
class Device(Strict): essential:bool; backup_monitoring:bool; normal_flows:int=Field(ge=1); normal_bytes:int=Field(gt=0)
class Attack(Strict): enabled:bool; kind:Literal["anomalous_egress","flow_flood","health_fault"]; multiplier:float=Field(gt=0); new_destination:bool
class Channel(Strict): observation_probability:float=Field(ge=0,le=1); loss_probability:float=Field(ge=0,le=1); queue_capacity:int=Field(ge=1)
class Detection(Strict): threshold:float=Field(ge=0,le=1); weights:dict[str,float]
class Policy(Strict): selected_action:Literal["monitor","rate_limit","isolate","human_review"]; authorized:bool; enforcement_available:bool
class Evidence(Strict): enabled:bool; allowed_types:list[str]; allowed_fields:list[str]; sharing_authorized:bool; redaction_enabled:bool; retention_seconds:float=Field(ge=0)
class Outputs(Strict):
 directory:str
 @model_validator(mode="after")
 def safe(self):
  p=PurePath(self.directory)
  if p.is_absolute() or ".." in p.parts or p.parts[:3] != ("reports","generated","uc5"): raise ValueError("unsafe output")
  return self
class SimulationConfig(Strict):
 schema_version:Literal["1.0.0"];scenario_id:str;description:str;seed:int=Field(ge=0);duration_seconds:float=Field(gt=0);device:Device;attack:Attack;channel:Channel;detection:Detection;policy:Policy;evidence:Evidence;clock_skew_seconds:float;outputs:Outputs
 @model_validator(mode="after")
 def valid(self):
  if not self.scenario_id.startswith("UC5-"): raise ValueError("scenario_id must start UC5-")
  if set(self.detection.weights)!={"rate","bytes","destination","health"} or abs(sum(self.detection.weights.values())-1)>1e-9: raise ValueError("invalid weights")
  return self
