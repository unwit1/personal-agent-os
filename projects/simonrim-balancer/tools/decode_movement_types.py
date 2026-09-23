#!/usr/bin/env python3
"""Decode Skyrim/SSE MOVT records for Simonrim Balancer."""
from __future__ import annotations
import base64,csv,json,math,struct
from pathlib import Path
from collections import Counter,defaultdict

ROOT=Path('data/snapshots/2026-09-23')
SCHEMA='UESP TES5/SSE MOVT SPED/INAM layout (cached 2026-07-02)'
SPED_FIELDS=['left_walk','left_run','right_walk','right_run','forward_walk','forward_run','back_walk','back_run','rotate_in_place_walk','rotate_in_place_run','rotate_while_moving_run']
INAM_FIELDS=['directional_threshold','movement_speed_threshold','rotation_speed_threshold']

def read_csv(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def write_csv(path,rows,fields=None):
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open('w',encoding='utf-8',newline='') as f:
        if not fields:return
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def submap(record):return {s['type']:base64.b64decode(s['data_base64']) for s in record['subrecords']}
def ratio(a,b):return a/b if b not in (0,None) else None
def sentinel(v):return (not math.isfinite(v)) or abs(v)>1e30

def main():
    resolved={(r['plugin'],r['form_id_hex']):r for r in read_csv(ROOT/'resolved_forms.csv') if r['record_type']=='MOVT'}
    rows=[];failures=[];sizes=Counter()
    for line in (ROOT/'records_full.jsonl').open(encoding='utf-8'):
        r=json.loads(line)
        if r.get('record_type')!='MOVT':continue
        try:
            sm=submap(r)
            if len(sm.get('SPED',b'')) not in (40,44):raise ValueError('unexpected SPED size')
            sped=list(struct.unpack('<'+'f'*(len(sm['SPED'])//4),sm['SPED']))
            if len(sped)==10:sped.append(None)
            inam=list(struct.unpack('<3f',sm['INAM'])) if 'INAM' in sm else [None,None,None]
            rr=resolved.get((r['plugin'],r['form_id_hex']),{})
            out={'mod':r['mod'],'version':r['version'],'plugin':r['plugin'],'form_id_hex':r['form_id_hex'],'canonical_key':rr.get('canonical_key',''),'record_role':rr.get('record_role',''),'baseline_kind':rr.get('baseline_kind',''),'edid':r.get('edid') or '','schema_source':SCHEMA,'evidence_stage':'decoded','rule_status':'not_a_rule'}
            out.update(dict(zip(SPED_FIELDS,sped)));out.update(dict(zip(INAM_FIELDS,inam)))
            for k,v in zip(INAM_FIELDS,inam):out[k+'_is_sentinel']=sentinel(v) if v is not None else ''
            out['forward_run_walk_ratio']=ratio(out['forward_run'],out['forward_walk']);out['back_run_walk_ratio']=ratio(out['back_run'],out['back_walk'])
            out['rotate_walk_deg']=math.degrees(out['rotate_in_place_walk']);out['rotate_run_deg']=math.degrees(out['rotate_in_place_run']);out['rotate_moving_run_deg']=math.degrees(out['rotate_while_moving_run']) if out['rotate_while_moving_run'] is not None else None
            out['profile_key']='|'.join(f'{float(out[k]):.6f}' for k in SPED_FIELDS)
            rows.append(out);sizes[f'SPED:{len(sm["SPED"])}']+=1;sizes[f'INAM:{len(sm["INAM"])}' if 'INAM' in sm else 'INAM:absent']+=1
        except Exception as e:failures.append({'plugin':r.get('plugin'),'form_id_hex':r.get('form_id_hex'),'edid':r.get('edid'),'error':str(e)})
    write_csv(ROOT/'movement_types_full.csv',rows)
    groups=defaultdict(list)
    for r in rows:groups[r['profile_key']].append(r)
    bas=[]
    for i,(_,rs) in enumerate(sorted(groups.items(),key=lambda kv:(-len(kv[1]),kv[1][0]['edid'])),1):
        r=rs[0];out={'profile_id':f'MOVT-P{i:02d}','plugin':r['plugin'],'sample_count':len(rs),'member_edids':';'.join(sorted(x['edid'] for x in rs)),'all_thresholds_sentinel':all(x['directional_threshold_is_sentinel'] and x['movement_speed_threshold_is_sentinel'] and x['rotation_speed_threshold_is_sentinel'] for x in rs),'evidence_stage':'observed_pattern','rule_status':'not_a_rule'}
        for k in SPED_FIELDS+['forward_run_walk_ratio','back_run_walk_ratio','rotate_walk_deg','rotate_run_deg','rotate_moving_run_deg']:out[k]=r[k]
        bas.append(out)
    write_csv(ROOT/'movement_numeric_baselines.csv',bas)
    obs=[]
    for r in bas:
        if r['sample_count']>=3:obs.append({'domain':'movement_numeric','plugin':r['plugin'],'pattern_key':f"Exact MOVT profile {r['profile_id']} | {r['member_edids']}",'sample_count':r['sample_count'],'observed_range':f"forward walk/run {r['forward_walk']}/{r['forward_run']}; back {r['back_walk']}/{r['back_run']}; rotate-run-deg {r['rotate_run_deg']:.3f}",'observed_median':f"forward run/walk ratio={r['forward_run_walk_ratio']:.6g}",'confidence_basis':'exact_repeated_profile','status':'observed_pattern','approved_rule':False})
    if rows and all(r['directional_threshold_is_sentinel'] and r['movement_speed_threshold_is_sentinel'] and r['rotation_speed_threshold_is_sentinel'] for r in rows):obs.append({'domain':'movement_thresholds','plugin':'BladeAndBlunt.esp','pattern_key':'All supplied MOVT INAM thresholds use FLT_MAX sentinel','sample_count':len(rows),'observed_range':'directional/movement/rotation threshold = FLT_MAX sentinel in every record','observed_median':'sentinel','confidence_basis':'complete_domain_observation','status':'observed_pattern','approved_rule':False})
    write_csv(ROOT/'movement_observed_patterns.csv',obs,['domain','plugin','pattern_key','sample_count','observed_range','observed_median','confidence_basis','status','approved_rule'])
    summary={'movement_type_records_found':len(rows)+len(failures),'movement_type_records_decoded':len(rows),'decode_failures':len(failures),'field_sizes':dict(sizes),'exact_numeric_profile_groups':len(bas),'observed_patterns':len(obs),'repeated_profiles_min_sample_3':sum(1 for r in bas if r['sample_count']>=3),'all_inam_thresholds_sentinel':bool(rows) and all(r['directional_threshold_is_sentinel'] and r['movement_speed_threshold_is_sentinel'] and r['rotation_speed_threshold_is_sentinel'] for r in rows),'exact_imported_baselines':sum(1 for r in rows if r['baseline_kind']=='imported_master'),'external_baselines':sum(1 for r in rows if r['baseline_kind']=='external_master_not_imported'),'approved_rules':0}
    (ROOT/'movement_decoder_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    if failures:print(json.dumps(failures,indent=2))

if __name__=='__main__':main()
