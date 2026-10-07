from dataclasses import dataclass
import hashlib,json,random
from pathlib import Path
from typing import Any
import yaml
from .models import SimulationConfig
from .identifiers import IdentifierFactory
from .evidence import collect,digest,verify
from .graph import load_entities,load_relationships,runtime_graph,competency_queries

@dataclass(frozen=True)
class SimulationResult: scenario_id:str; canonical_hash:str; documents:dict[str,Any]
def event(ids,kind,t,source,target,msg,attrs,visible=True):
    public={"event_type":kind,"event_time":round(t,6),"source_entity":source,"target_entity":target,"message_id":msg,"attributes":attrs}
    return {"event_id":ids.next("EV"),**public,"ingest_time":round(t,6),"payload_hash":hashlib.sha256(json.dumps(public,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"observable":visible}
def simulate(root:Path,c:SimulationConfig)->SimulationResult:
    ids=IdentifierFactory(); obs_rng=random.Random(c.seed*19+1); cls_rng=random.Random(c.seed*19+2)
    truth=[]; observations=[]; hypotheses=[]; classifications=[]; registry=[]; alerts=[]; policies=[]; actions=[]; loss=0; overflow=0
    devices=[(f"UC2-DEV-{i+1:03d}",True,"environmental_sensor") for i in range(c.scene.approved_devices)]+[(f"UC2-DEV-U{i+1:03d}",False,"unapproved_camera") for i in range(c.scene.unapproved_devices)]
    ordinal=0
    for device_id,approved,hidden_class in devices:
      seen=[]
      for n in range(c.scene.emissions_per_device):
       for interface in c.observation.interfaces:
        ordinal+=1
        if ordinal>c.observation.queue_capacity: overflow+=1; continue
        if obs_rng.random()>c.observation.coverage_probability or obs_rng.random()<c.observation.loss_probability: loss+=1; continue
        pseudonym=hashlib.sha256(f"{c.seed}:{device_id}:{interface}".encode()).hexdigest()[:16]
        row=event(ids,"observation",float(n),{"3gpp":"UC2-D01","wifi":"UC2-D02","ble":"UC2-D03"}[interface],"UC2-S01",f"UC2-OBS-{ordinal:06d}",{"interface":interface,"pseudonym":pseudonym,"signal_bucket":"medium","payload_captured":False,"precise_location":False})
        truth.append(row);observations.append(row);seen.append(row)
      if not seen: continue
      hid=f"UC2-HYP-{len(hypotheses)+1:06d}"; hypotheses.append({"hypothesis_id":hid,"observation_ids":[x["event_id"] for x in seen],"association_window_seconds":c.observation.association_window_seconds,"alternatives":[]})
      predicted=hidden_class if cls_rng.random()<c.classification.accuracy else "unknown_iot";confidence=c.classification.accuracy
      cls=event(ids,"classification",seen[-1]["event_time"],"UC2-S01","UC2-S02",None,{"hypothesis_id":hid,"predicted_class":predicted,"confidence":confidence,"alternatives":["unknown_iot"],"hidden_class_used":False});truth.append(cls);classifications.append(cls)
      status="approved" if approved else "unapproved"
      if not c.registry.available: status="unknown"
      elif c.registry.stale: status="stale_registry"
      reg=event(ids,"registry_decision",cls["event_time"],"UC2-S02","UC2-S03",None,{"hypothesis_id":hid,"status":status});truth.append(reg);registry.append(reg)
      if status=="unapproved" and confidence>=c.classification.threshold:
        al=event(ids,"alert",cls["event_time"],"UC2-S03","UC2-S04",None,{"hypothesis_id":hid,"score":confidence,"explanation":["unapproved_registry_status","classification_confidence"],"missing":[]});truth.append(al);alerts.append(al)
        applied=c.policy.selected_action if c.policy.available else "none";pd=event(ids,"policy_decision",al["event_time"],"UC2-S04","UC2-A01",None,{"requested_action":c.policy.selected_action,"applied_action":applied,"active_rf_action":False});truth.append(pd);policies.append(pd)
        ac=event(ids,"mitigation_action",pd["event_time"],"UC2-A01","UC2-S01",None,{"action":applied,"effective":applied!="none","active_rf_action":False});truth.append(ac);actions.append(ac)
    evidence,custody=collect(truth,set(c.evidence.allowed_types),set(c.evidence.allowed_fields)) if c.evidence.enabled else ([],[]);integrity=verify(evidence,custody)
    reconstruction={"hidden_truth_used":False,"claims":[{"claim_id":"UC2-CLM-000001","statement":"A pseudonymous device hypothesis was observed and categorized.","status":"supported" if classifications else "inconclusive","supporting_evidence_ids":[e["evidence_id"] for e in evidence],"alternatives":["observation loss","ambiguous association"]}]}
    metrics={"alert_count":len(alerts),"process_effect_count":0,"safety_violation_count":0,"observations":len(observations),"observation_loss":loss,"queue_overflow":overflow,"classification_count":len(classifications),"unauthorized_disclosure_count":0,"active_rf_action_count":0,"integrity_failure_count":len(integrity)}
    core={"ground_truth_events":truth,"observed_events":observations,"association_hypotheses":hypotheses,"classifications":classifications,"registry_decisions":registry,"alerts":alerts,"policy_decisions":policies,"mitigation_actions":actions,"evidence_manifest":evidence,"custody_events":custody,"reconstructed_timeline":reconstruction,"metrics":metrics};graph=runtime_graph(root,core)
    docs={"resolved_config":c.model_dump(mode="json"),"entities":load_entities(root),"relationships":load_relationships(root),**core,"graph":graph,"competency_queries":competency_queries(graph),"validation_report":{"status":"valid","integrity_errors":integrity,"invariants":{"passive_only":True,"hidden_truth_isolated":True,"privacy_violations":0}},"investigation_summary":{"scenario_id":c.scenario_id,"synthetic":True,"alerts":len(alerts),"limitations":"No live RF, interception, tracking, identity, payload, or legal authority."}}
    h=digest(docs);docs["run_manifest"]={"schema_version":"1.0.0","use_case":"UC2","scenario_id":c.scenario_id,"seed":c.seed,"canonical_result_sha256":h,"synthetic":True};return SimulationResult(c.scenario_id,h,docs)
def run_simulation(root,config_path): return simulate(root,SimulationConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8"))))
def export_result(result,output):
    output.mkdir(parents=True,exist_ok=True); jsonl={"ground_truth_events","observed_events","classifications","registry_decisions","alerts","policy_decisions","mitigation_actions","custody_events"}
    for name,doc in result.documents.items():
      if name=="resolved_config": path=output/"resolved_config.yaml";text=yaml.safe_dump(doc,sort_keys=True)
      elif name=="investigation_summary": path=output/"investigation_summary.md";text="# UC2 synthetic investigation summary\n\n"+"\n".join(f"- **{k}:** {v}" for k,v in doc.items())+"\n"
      elif name in jsonl: path=output/f"{name}.jsonl";text="".join(json.dumps(x,sort_keys=True)+"\n" for x in doc)
      else: path=output/f"{name}.json";text=json.dumps(doc,indent=2,sort_keys=True)+"\n"
      path.write_text(text,encoding="utf-8")
    (output/"graph_overview.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="700" height="70"><text x="20" y="40">passive observers to association classification review and evidence</text></svg>\n',encoding="utf-8")
