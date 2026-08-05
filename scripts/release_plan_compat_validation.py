# ruff: noqa
"""Compatibility checks retained from the accepted schema-1 release plan."""
from __future__ import annotations
import csv,re
from pathlib import Path
from typing import Any
from .release_plan_model import (ALLOWED_CODE_STATUSES,ALLOWED_DEPTHS,ALLOWED_GROUPS,ALLOWED_STATUSES,COMPETITOR_MATRIX_PATH,COVERAGE_DECISIONS_PATH,COVERAGE_SOURCE_PATH,DECISION_PROFILES_PATH,EXPECTED_MODULE_IDS,EXPECTED_POST_DEMO,EXPECTED_SCENARIOS,LEGAL_MODE_MATRIX_PATH,MODULE_MARKERS,PERSONNEL_AUTHORITY_MATRIX_PATH,PLAN_PATH,REJECTED_CONTRACT_BOILERPLATE,SOURCE_REGISTRY_PATH,split_pipe)
OWNERS={"state":"docs/project/CURRENT_STATE.md","plan":PLAN_PATH,"coverage_source":COVERAGE_SOURCE_PATH,"coverage_decisions":COVERAGE_DECISIONS_PATH}
REFS=[f"REF-OD-{i:03d}" for i in range(1,67)]
COMP=[f"D-{i:02d}" for i in range(1,17)]
REQ_COMP={"D-08":"DEFECT","D-11":"GROUNDING","D-14":"NORMATIVE-EVIDENCE"}
AUTH_MARKERS=("operational right","action_time_evaluation","immutable_snapshot","contractor_seconded_semantics")
def e(file,id,rule,expected,actual): return f"{file}: [{id}] rule={rule}; expected={expected!r}; actual={actual!r}"
def rows(root,path):
 with (root/path).open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f,delimiter=";"))
def validate_release_plan_compatibility(plan:dict[str,Any],root:Path)->list[str]:
 x=[]
 for k,v in {"schema":2,"version":"1.0","release":"DEMO-RELEASE","baseline_status":"ACCEPTED"}.items():
  if plan.get(k)!=v:x.append(e(PLAN_PATH,k,f"release-{k}",v,plan.get(k)))
 if plan.get("owners")!=OWNERS:x.append(e(PLAN_PATH,"owners","canonical-release-plan-owners",OWNERS,plan.get("owners")))
 for k,v in (("statuses",ALLOWED_STATUSES),("depths",ALLOWED_DEPTHS),("code_statuses",ALLOWED_CODE_STATUSES)):
  if plan.get(k)!=list(v):x.append(e(PLAN_PATH,k,f"{k}-vocabulary",list(v),plan.get(k)))
 modules=plan.get("modules",[]); ids=[m.get("id") for m in modules if isinstance(m,dict)]; by={m["id"]:m for m in modules if isinstance(m,dict) and isinstance(m.get("id"),str)}
 if ids!=list(EXPECTED_MODULE_IDS):x.append(e(PLAN_PATH,"modules","exact-demo-module-catalog",list(EXPECTED_MODULE_IDS),ids))
 if len(ids)!=len(set(ids)):x.append(e(PLAN_PATH,"modules","module-id-uniqueness","unique",ids))
 orders=[m.get("order") for m in modules if isinstance(m,dict)]
 if sorted(o for o in orders if isinstance(o,int))!=list(range(1,28)):x.append(e(PLAN_PATH,"modules","module-catalog-orders",list(range(1,28)),orders))
 if len(orders)!=len(set(orders)):x.append(e(PLAN_PATH,"modules","module-order-uniqueness","unique",orders))
 agg={"capability":[],"acceptance":[],"work_item":[]}; detail={"cap":set(),"acc":set(),"work":set()}; protected=plan.get("reconciliation",{}).get("accepted_slices",{})
 for mid,m in by.items():
  for k,v in (("status",ALLOWED_STATUSES),("depth",ALLOWED_DEPTHS),("code",ALLOWED_CODE_STATUSES),("group",ALLOWED_GROUPS)):
   if m.get(k) not in v:x.append(e(PLAN_PATH,mid,f"module-{k}-vocabulary",list(v),m.get(k)))
  for k in agg:
   value=m.get(k)
   if not isinstance(value,str) or not value:x.append(e(PLAN_PATH,mid,f"module-{k}-required","non-empty unique identifier",value))
   else:agg[k].append(value)
  if not split_pipe(m.get("sources")):x.append(e(PLAN_PATH,mid,"module-sources-required","one or more source IDs",m.get("sources")))
  path=str(m.get("contract","")); p=root/path
  if not p.is_file():x.append(e(path,mid,"module-contract-exists","file","missing"));continue
  text=p.read_text(encoding="utf-8")
  if f"`{mid}`" not in text:x.append(e(path,mid,"module-contract-id-marker",f"`{mid}`","missing"))
  for marker in MODULE_MARKERS:
   if marker not in text:x.append(e(path,mid,"module-contract-marker",marker,"missing"))
  for bad in REJECTED_CONTRACT_BOILERPLATE:
   if bad in text:x.append(e(path,mid,"rejected-generic-boilerplate","absent",bad))
  caps=set(re.findall(r"\bCAP-[A-Z0-9-]+\b",text));accs=set(re.findall(r"\bAC-[A-Z0-9-]+\b",text));works=set(re.findall(r"\b(?:[A-Z][A-Z0-9]*-)+\d{3}\b",text));detail["cap"]|=caps;detail["acc"]|=accs;detail["work"]|=works
  expected=set(protected.get(mid,[]));actual=set(split_pipe(m.get("accepted")))
  if actual!=expected:x.append(e(PLAN_PATH,mid,"protected-accepted-slices",sorted(expected),sorted(actual)))
  for cap in expected:
   if cap not in caps:x.append(e(path,mid,"accepted-slice-evidence-marker",cap,"missing"))
  if "Текущий planning status принадлежит только" in text:
   section=text.split("## CURRENT CODE STATUS / CAPABILITIES",1)[-1].split("\n## ",1)[0]; match=re.search(r"`(?P<code>IMPLEMENTED-[A-Z]+|FOUNDATION-ONLY|PRESENTATION-ONLY|PLANNED-ONLY|ABSENT|VERIFY)`; release `(?P<status>[A-Z_]+)`",section);actual_projection=None if match is None else (match.group("code"),match.group("status"));expected_projection=(m.get("code"),m.get("status"))
   if actual_projection!=expected_projection:x.append(e(path,mid,"module-current-status-projection",expected_projection,actual_projection))
 for k,v in agg.items():
  if len(v)!=len(set(v)):x.append(e(PLAN_PATH,k,f"module-{k}-uniqueness","unique",v))
 order=plan.get("dependency_order",[])
 if len(order)!=27 or set(order)!=set(EXPECTED_MODULE_IDS) or len(order)!=len(set(order)):x.append(e(PLAN_PATH,"dependency_order","dependency-order-membership",list(EXPECTED_MODULE_IDS),order))
 else:
  pos={mid:i for i,mid in enumerate(order)}
  for mid,m in by.items():
   for dep in m.get("deps",[]):
    if dep not in pos:x.append(e(PLAN_PATH,mid,"module-dependency-reference","existing module",dep))
    elif pos[dep]>=pos[mid]:x.append(e(PLAN_PATH,mid,"dependency-topology",f"{dep} before {mid}",order))
 if plan.get("post_demo")!=list(EXPECTED_POST_DEMO):x.append(e(PLAN_PATH,"post_demo","post-demo-contour-set",list(EXPECTED_POST_DEMO),plan.get("post_demo")))
 if plan.get("scenarios")!=list(EXPECTED_SCENARIOS):x.append(e(PLAN_PATH,"scenarios","presentation-scenario-set",list(EXPECTED_SCENARIOS),plan.get("scenarios")))
 try:coverage=rows(root,COVERAGE_SOURCE_PATH);decisions=rows(root,COVERAGE_DECISIONS_PATH);profiles=rows(root,DECISION_PROFILES_PATH);registry=rows(root,SOURCE_REGISTRY_PATH)
 except OSError as exc:return x+[e(PLAN_PATH,"coverage","coverage-inputs-readable","readable CSV inputs",str(exc))]
 for data,path,rule in ((coverage,COVERAGE_SOURCE_PATH,"coverage-exact-66-rows"),(decisions,COVERAGE_DECISIONS_PATH,"coverage-decisions-exact-66-rows")):
  actual=[r.get("reference_id") for r in data]
  if actual!=REFS:x.append(e(path,"reference_id",rule,REFS,actual))
 profile_by={r.get("profile_id"):r for r in profiles}
 if len(profile_by)!=len(profiles):x.append(e(DECISION_PROFILES_PATH,"profiles","decision-profile-uniqueness","unique profile_id",[r.get("profile_id") for r in profiles]))
 for r in decisions:
  if r.get("profile_id") not in profile_by:x.append(e(COVERAGE_DECISIONS_PATH,r.get("reference_id"),"decision-profile-reference","existing profile_id",r.get("profile_id")))
 aggregate_work={m.get("work_item") for m in modules if isinstance(m,dict)}
 for pid,p in profile_by.items():
  for mid in split_pipe(p.get("module_ids")):
   if mid not in by:x.append(e(DECISION_PROFILES_PATH,pid,"profile-module-reference","accepted module ID",mid))
  for cap in split_pipe(p.get("capability_ids")):
   if cap not in detail["cap"]:x.append(e(DECISION_PROFILES_PATH,pid,"profile-capability-reference","capability marker",cap))
  for acc in split_pipe(p.get("acceptance_ids")):
   if acc not in detail["acc"]:x.append(e(DECISION_PROFILES_PATH,pid,"profile-acceptance-reference","acceptance marker",acc))
  for work in split_pipe(p.get("planned_work_items")):
   if work not in detail["work"] and work not in aggregate_work:x.append(e(DECISION_PROFILES_PATH,pid,"profile-work-item-reference","known work item",work))
  if p.get("proven_legal_mode")!="VERIFY":x.append(e(DECISION_PROFILES_PATH,pid,"decision-profile-proven-legal-mode","VERIFY",p.get("proven_legal_mode")))
 decision_by_ref={r.get("reference_id"):r for r in decisions};p59=profile_by.get(decision_by_ref.get("REF-OD-059",{}).get("profile_id"),{});actual59=(set(split_pipe(p59.get("module_ids"))),set(split_pipe(p59.get("product_target_modes"))));expected59=({"PERMIT-WORK-JOURNAL","ORDER-WORK-JOURNAL"},{"ELECTRONIC_ORIGINAL_TARGET","PAPER_MIRROR"})
 if actual59!=expected59:x.append(e(DECISION_PROFILES_PATH,"REF-OD-059","ref-od-059-split",expected59,actual59))
 p63=profile_by.get(decision_by_ref.get("REF-OD-063",{}).get("profile_id"),{})
 if p63.get("post_demo_contour")!="KEYS":x.append(e(DECISION_PROFILES_PATH,"REF-OD-063","ref-od-063-keys-boundary","KEYS",p63.get("post_demo_contour")))
 known={r.get("source_id") for r in registry}|set(REFS)
 for mid,m in by.items():
  for sid in split_pipe(m.get("sources")):
   if sid not in known:x.append(e(PLAN_PATH,mid,"module-source-reference","SOURCE_REGISTRY.csv or REF-OD-001..066",sid))
 try:comp=rows(root,COMPETITOR_MATRIX_PATH)
 except OSError as exc:comp=[];x.append(e(COMPETITOR_MATRIX_PATH,"matrix","competitor-matrix-readable","readable CSV",str(exc)))
 actual_comp=[r.get("decision_id") for r in comp]
 if actual_comp!=COMP:x.append(e(COMPETITOR_MATRIX_PATH,"decision_id","competitor-decision-catalog",COMP,actual_comp))
 for r in comp:
  did=r.get("decision_id");mids=split_pipe(r.get("module_ids"))
  for mid in mids:
   if mid not in by:x.append(e(COMPETITOR_MATRIX_PATH,did,"competitor-module-reference","accepted module ID",mid))
  for cap in split_pipe(r.get("capability_ids")):
   if cap not in detail["cap"]:x.append(e(COMPETITOR_MATRIX_PATH,did,"competitor-capability-reference","capability marker",cap))
  if did in REQ_COMP and REQ_COMP[did] not in mids:x.append(e(COMPETITOR_MATRIX_PATH,did,"competitor-required-mapping",REQ_COMP[did],mids))
 try:legal=rows(root,LEGAL_MODE_MATRIX_PATH)
 except OSError as exc:legal=[];x.append(e(LEGAL_MODE_MATRIX_PATH,"matrix","legal-mode-matrix-readable","readable CSV",str(exc)))
 invalid=[r for r in legal if r.get("proven_legal_mode")!="VERIFY"]
 if invalid:x.append(e(LEGAL_MODE_MATRIX_PATH,"proven_legal_mode","legal-mode-remains-verify","VERIFY for every row",invalid))
 try:auth=(root/PERSONNEL_AUTHORITY_MATRIX_PATH).read_text(encoding="utf-8")
 except OSError as exc:auth="";x.append(e(PERSONNEL_AUTHORITY_MATRIX_PATH,"matrix","personnel-authority-matrix-readable","readable CSV",str(exc)))
 for marker in AUTH_MARKERS:
  if marker not in auth:x.append(e(PERSONNEL_AUTHORITY_MATRIX_PATH,marker,"personnel-authority-evidence-marker",marker,"missing"))
 return x
