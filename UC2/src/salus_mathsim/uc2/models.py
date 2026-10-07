from pathlib import PurePath
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Strict(BaseModel): model_config=ConfigDict(extra="forbid")
class Scene(Strict): approved_devices:int=Field(ge=1); unapproved_devices:int=Field(ge=0); emissions_per_device:int=Field(ge=1)
class Observation(Strict): interfaces:list[Literal["3gpp","wifi","ble"]]; coverage_probability:float=Field(ge=0,le=1); loss_probability:float=Field(ge=0,le=1); association_window_seconds:float=Field(gt=0); queue_capacity:int=Field(ge=1)
class Classification(Strict): accuracy:float=Field(ge=0,le=1); threshold:float=Field(ge=0,le=1)
class Registry(Strict): available:bool; stale:bool
class Policy(Strict): selected_action:Literal["observe","request_review","pause_simulated_event","quarantine_hypothesis"]; available:bool
class Evidence(Strict): enabled:bool; allowed_types:list[str]; allowed_fields:list[str]; retention_seconds:float=Field(ge=0)
class Outputs(Strict):
    directory:str
    @model_validator(mode="after")
    def safe(self):
        p=PurePath(self.directory)
        if p.is_absolute() or ".." in p.parts or p.parts[:3] != ("reports","generated","uc2"): raise ValueError("output must remain under reports/generated/uc2")
        return self
class SimulationConfig(Strict):
    schema_version:Literal["1.0.0"]; scenario_id:str; description:str; seed:int=Field(ge=0); duration_seconds:float=Field(gt=0); scene:Scene; observation:Observation; classification:Classification; registry:Registry; policy:Policy; evidence:Evidence; clock_skew_seconds:float; outputs:Outputs
    @model_validator(mode="after")
    def valid(self):
        if not self.scenario_id.startswith("UC2-"): raise ValueError("scenario_id must start UC2-")
        if len(set(self.observation.interfaces)) != len(self.observation.interfaces): raise ValueError("interfaces must be unique")
        return self
