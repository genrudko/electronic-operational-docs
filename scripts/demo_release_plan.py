from __future__ import annotations
import csv,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'docs/project/DEMO_RELEASE_PLAN.yaml'
EXPECTED={'PLATFORM','UX','NORMATIVE-EVIDENCE','MASTER-DATA','PERSONNEL-AUTHORITY','WORKPLACE-DOCS','SCHEMES-DOCUMENTS','OPJ','SHIFT','APPLICATION','OPERATIONAL-ORDERS','DEFECT','GROUNDING','SWITCHING-DOCUMENTS','WORK-PERMIT','PERMIT-WORK-JOURNAL','ORDER-WORK-JOURNAL','CURRENT-OPERATION-WORKS','EQUIPMENT-INSPECTIONS','EQUIPMENT-COMMISSIONING','RZA-TM','BREAKER-INTERRUPTIONS','BATTERY-INSPECTION','EMERGENCY-READINESS','CROSS-DOC','DASHBOARD-REPORTING','DEMO-DATA'}
RS={'NOT_STARTED','READY','IN_PROGRESS','BLOCKED','AT_REVIEW','ACCEPTED','DEFERRED','EXCLUDED'}
DS={'DEMO-FUNCTIONAL','DEMO-BOUNDED','DEMO-HYBRID','DEMO-PAPER-MIRROR','DEMO-REFERENCE','POST-DEMO-INDUSTRIAL','VERIFY','EXCLUDED'}
CS={'IMPLEMENTED-ACCEPTED','IMPLEMENTED-PARTIAL','FOUNDATION-ONLY','PRESENTATION-ONLY','PLANNED-ONLY','ABSENT','VERIFY'}
EXPECTED_CODE={'PLATFORM':'IMPLEMENTED-PARTIAL','UX':'IMPLEMENTED-PARTIAL','NORMATIVE-EVIDENCE':'IMPLEMENTED-PARTIAL','MASTER-DATA':'IMPLEMENTED-PARTIAL','PERSONNEL-AUTHORITY':'ABSENT','WORKPLACE-DOCS':'IMPLEMENTED-PARTIAL','SCHEMES-DOCUMENTS':'FOUNDATION-ONLY','OPJ':'IMPLEMENTED-PARTIAL','SHIFT':'IMPLEMENTED-PARTIAL','APPLICATION':'ABSENT','OPERATIONAL-ORDERS':'ABSENT','DEFECT':'IMPLEMENTED-ACCEPTED','GROUNDING':'ABSENT','SWITCHING-DOCUMENTS':'ABSENT','WORK-PERMIT':'ABSENT','PERMIT-WORK-JOURNAL':'ABSENT','ORDER-WORK-JOURNAL':'ABSENT','CURRENT-OPERATION-WORKS':'ABSENT','EQUIPMENT-INSPECTIONS':'ABSENT','EQUIPMENT-COMMISSIONING':'ABSENT','RZA-TM':'ABSENT','BREAKER-INTERRUPTIONS':'ABSENT','BATTERY-INSPECTION':'ABSENT','EMERGENCY-READINESS':'ABSENT','CROSS-DOC':'FOUNDATION-ONLY','DASHBOARD-REPORTING':'PRESENTATION-ONLY','DEMO-DATA':'PRESENTATION-ONLY'}
MARKERS=['## MODULE ID','## НАЗНАЧЕНИЕ','## КРИТИЧЕСКИЕ СЦЕНАРИИ','## PRIMARY FACTS / DERIVED VIEWS','## РОЛИ И ПОЛНОМОЧИЯ','## ДОКУМЕНТЫ И LEGAL MODE','## СВЯЗИ','## SOURCE IDS / BENCHMARK','## DEMO / POST-DEMO','## CURRENT CODE STATUS / CAPABILITIES','## DEPENDENCIES / UX CONTRACT','## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS']

def load(): return json.loads(PLAN.read_text(encoding='utf-8'))
def split(value): return [x for x in (value or '').split('|') if x]
def csv_rows(path):
 with path.open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f,delimiter=';'))
def validate(plan):
 errors=[]
 if plan.get('version')!='1.0-candidate' or plan.get('release')!='DEMO-RELEASE' or plan.get('baseline_status')!='AT_REVIEW': errors.append('release identity/version/status invalid')
 if plan.get('accepted_main')!='50d96842e8700540832210990993e64fc2e3636d': errors.append('accepted main baseline invalid')
 if set(plan.get('statuses',[]))!=RS or set(plan.get('depths',[]))!=DS or set(plan.get('code_statuses',[]))!=CS: errors.append('status vocabularies invalid')
 owners=plan.get('owners',{})
 expected_owners={'state':'docs/project/CURRENT_STATE.md','plan':'docs/project/DEMO_RELEASE_PLAN.yaml','coverage_source':'docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_COVERAGE.csv','coverage_decisions':'docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISIONS.csv'}
 if owners!=expected_owners: errors.append('canonical owners invalid')
 modules=plan.get('modules',[]); ids=[m.get('id') for m in modules]
 if len(modules)!=27 or set(ids)!=EXPECTED or len(ids)!=len(set(ids)): errors.append('module set/count/uniqueness invalid')
 by={m['id']:m for m in modules}; aggregate_caps=[]; aggregate_acc=[]; aggregate_work=[]; detailed_caps=set(); detailed_acc=set(); detailed_work=set()
 for m in modules:
  mid=m['id']
  if m.get('order') not in range(1,28): errors.append(f'{mid}: catalog order invalid')
  if m.get('status') not in RS or m.get('depth') not in DS or m.get('code') not in CS: errors.append(f'{mid}: status/depth/code invalid')
  if m.get('code')!=EXPECTED_CODE[mid]: errors.append(f'{mid}: current code status diverges from Stage 1')
  for dep in m.get('deps',[]):
   if dep not in EXPECTED: errors.append(f'{mid}: unknown dependency {dep}')
  for key,store in [('capability',aggregate_caps),('acceptance',aggregate_acc),('work_item',aggregate_work)]:
   value=m.get(key)
   if not value: errors.append(f'{mid}: {key} required')
   else: store.append(value)
  if not m.get('sources'): errors.append(f'{mid}: sources required')
  contract=ROOT/m.get('contract','')
  if not contract.is_file(): errors.append(f'{mid}: missing contract'); continue
  text=contract.read_text(encoding='utf-8')
  if f'`{mid}`' not in text: errors.append(f'{mid}: contract ID missing')
  for marker in MARKERS:
   if marker not in text: errors.append(f'{mid}: missing contract marker {marker}')
  if 'Создать или выбрать первичный факт, проверить полномочие' in text: errors.append(f'{mid}: rejected boilerplate')
  detailed_caps.update(re.findall(r'\bCAP-[A-Z0-9-]+\b',text))
  detailed_acc.update(re.findall(r'\bAC-[A-Z0-9-]+\b',text))
  detailed_work.update(re.findall(r'\b(?:[A-Z][A-Z0-9]*-)+\d{3}\b',text))
 if len({m.get('order') for m in modules})!=27: errors.append('catalog orders not unique')
 for values,label in [(aggregate_caps,'aggregate capability'),(aggregate_acc,'aggregate acceptance'),(aggregate_work,'aggregate work item')]:
  if len(values)!=len(set(values)): errors.append(f'duplicate {label}')
 defect=by.get('DEFECT',{})
 if defect.get('status')!='ACCEPTED' or defect.get('code')!='IMPLEMENTED-ACCEPTED': errors.append('accepted DEFECT slice reset')
 dep_order=plan.get('dependency_order',[])
 if len(dep_order)!=27 or set(dep_order)!=EXPECTED or len(dep_order)!=len(set(dep_order)): errors.append('dependency order must contain every module once')
 else:
  pos={mid:i for i,mid in enumerate(dep_order)}
  for mid,m in by.items():
   for dep in m.get('deps',[]):
    if pos[dep]>=pos[mid]: errors.append(f'dependency order violation {dep}->{mid}')
 queue=plan.get('implementation_queue',[])
 if [x.get('order') for x in queue]!=list(range(1,len(queue)+1)): errors.append('implementation queue order invalid')
 if not queue or queue[0].get('work_item')!='UX-THEME-001': errors.append('first work item must be UX-THEME-001')
 if any(x.get('work_item')=='DEFECT-001' for x in queue): errors.append('accepted DEFECT-001 reopened')
 if any(x.get('module_id') not in EXPECTED for x in queue): errors.append('queue unknown module')
 if len(plan.get('post_demo',[]))!=7 or len(set(plan.get('post_demo',[])))!=7 or 'KEYS' not in plan.get('post_demo',[]): errors.append('post-demo contours invalid')
 if len(plan.get('scenarios',[]))!=9: errors.append('presentation scenario count invalid')
 source=csv_rows(ROOT/owners['coverage_source']); assignments=csv_rows(ROOT/owners['coverage_decisions']); profiles=csv_rows(ROOT/'docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISION_PROFILES.csv')
 refs=[f'REF-OD-{i:03d}' for i in range(1,67)]
 if [r['reference_id'] for r in source]!=refs: errors.append('reference source is not exact ordered 66 rows')
 if [r['reference_id'] for r in assignments]!=refs: errors.append('reference decisions are not exact ordered 66 rows')
 profile_by={r['profile_id']:r for r in profiles}
 if len(profile_by)!=len(profiles): errors.append('duplicate decision profile')
 for row in assignments:
  if row['profile_id'] not in profile_by: errors.append(f"{row['reference_id']}: unknown profile")
 for pid,p in profile_by.items():
  for mid in split(p['module_ids']):
   if mid not in EXPECTED: errors.append(f'{pid}: unknown module {mid}')
  for cid in split(p['capability_ids']):
   if cid not in detailed_caps: errors.append(f'{pid}: unknown capability {cid}')
  for aid in split(p['acceptance_ids']):
   if aid not in detailed_acc: errors.append(f'{pid}: unknown acceptance {aid}')
  for wid in split(p['planned_work_items']):
   if wid not in detailed_work and wid not in aggregate_work: errors.append(f'{pid}: unknown work item {wid}')
  if p['proven_legal_mode']!='VERIFY': errors.append(f'{pid}: proven legal mode must remain VERIFY')
 p59=profile_by.get(next(r['profile_id'] for r in assignments if r['reference_id']=='REF-OD-059'),{})
 if set(split(p59.get('module_ids')))!={'PERMIT-WORK-JOURNAL','ORDER-WORK-JOURNAL'} or set(split(p59.get('product_target_modes')))!={'ELECTRONIC_ORIGINAL_TARGET','PAPER_MIRROR'}: errors.append('REF-OD-059 split invalid')
 p63=profile_by.get(next(r['profile_id'] for r in assignments if r['reference_id']=='REF-OD-063'),{})
 if p63.get('post_demo_contour')!='KEYS': errors.append('REF-OD-063 KEYS boundary missing')
 source_registry=csv_rows(ROOT/'docs/evidence/SOURCE_REGISTRY.csv'); known={r['source_id'] for r in source_registry}; refset=set(refs)
 for m in modules:
  for sid in split(m.get('sources')):
   if sid not in known and sid not in refset: errors.append(f"{m['id']}: unknown source {sid}")
 comp=csv_rows(ROOT/'docs/evidence/COMPETITOR_CAPABILITY_MATRIX.csv')
 if [r['decision_id'] for r in comp]!=[f'D-{i:02d}' for i in range(1,17)]: errors.append('competitor decisions must be D-01..D-16')
 required={'D-08':'DEFECT','D-11':'GROUNDING','D-14':'NORMATIVE-EVIDENCE'}
 for row in comp:
  for mid in split(row['module_ids']):
   if mid not in EXPECTED: errors.append(f"{row['decision_id']}: unknown module")
  for cid in split(row['capability_ids']):
   if cid not in detailed_caps: errors.append(f"{row['decision_id']}: unknown capability {cid}")
  if row['decision_id'] in required and required[row['decision_id']] not in split(row['module_ids']): errors.append(f"{row['decision_id']}: wrong mapping")
 legal=csv_rows(ROOT/'docs/evidence/DOCUMENT_LEGAL_MODE_MATRIX.csv')
 if any(r['proven_legal_mode']!='VERIFY' for r in legal): errors.append('legal matrix confuses product boundary and proven mode')
 auth=(ROOT/'docs/evidence/PERSONNEL_AUTHORITY_MATRIX.csv').read_text(encoding='utf-8')
 for marker in ['operational right','action_time_evaluation','immutable_snapshot','contractor_seconded_semantics']:
  if marker not in auth: errors.append(f'authority matrix missing {marker}')
 module_map=(ROOT/'docs/product/MODULE_MAP.md').read_text(encoding='utf-8'); checklist=(ROOT/'docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md').read_text(encoding='utf-8'); sequence=(ROOT/'docs/product/IMPLEMENTATION_SEQUENCE.md').read_text(encoding='utf-8')
 for m in modules:
  for value in [m['id'],m['depth'],m['status'],m['code'],m['work_item']]:
   if value not in module_map: errors.append(f"{m['id']}: module map drift for {value}")
  for value in [m['id'],m['capability'],m['acceptance'],m['depth'],m['status'],m['code'],m['work_item']]:
   if value not in checklist: errors.append(f"{m['id']}: checklist drift for {value}")
 for mid in dep_order:
  if f'`{mid}`' not in sequence: errors.append(f'sequence missing {mid}')
 for item in queue:
  if item['work_item'] not in sequence: errors.append(f"sequence missing {item['work_item']}")
 state=(ROOT/'docs/project/CURRENT_STATE.md').read_text(encoding='utf-8'); handoff=(ROOT/'docs/project/CURRENT_HANDOFF.md').read_text(encoding='utf-8')
 if 'main / 50d96842e8700540832210990993e64fc2e3636d' not in state or 'PROJECT-BASELINE-001' not in state: errors.append('CURRENT_STATE owner invalid')
 if re.search(r'\b[0-9a-f]{40}\b',handoff) or 'active work item:' in handoff.lower(): errors.append('CURRENT_HANDOFF duplicates volatile state')
 return errors
