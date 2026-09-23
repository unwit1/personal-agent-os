#!/usr/bin/env python3
from __future__ import annotations
import csv, json, re
from pathlib import Path
from collections import Counter, defaultdict

ROOT=Path('/mnt/data/simonrim-balancer/data/snapshots/2026-09-23')
OUT=ROOT/'rule_candidates.csv'
SUMMARY=ROOT/'rule_candidate_summary.json'

FIELDS=[
'candidate_id','domain','source_kind','candidate_type','scope_mod','scope_plugins','module_roles',
'proposition','sample_count','evidence_ids','evidence_basis','baseline_status','counterexample_status',
'counterexample_count','contamination_flags','confidence_score','confidence_label','status','approved_rule','review_notes'
]

def read_csv(name):
    with (ROOT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def write_csv(path, rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore');w.writeheader();w.writerows(rows)

def role_map():
    return {r['plugin']:r['module_role'] for r in read_csv('module_semantics.csv')}

def mod_map():
    return {r['plugin']:r['mod'] for r in read_csv('module_semantics.csv')}

def norm_plugins(s):
    if not s:return []
    return [x.strip() for x in s.split(';') if x.strip()]

def confidence(sample, source_kind, roles, baseline_status, explicit=False):
    score=0
    if explicit: score+=45
    if source_kind=='observed_pattern':
        if sample>=20:score+=35
        elif sample>=10:score+=30
        elif sample>=5:score+=24
        elif sample>=3:score+=18
    if roles and all(r in {'main','standalone_main'} for r in roles):score+=18
    elif any(r in {'reversion','compatibility_patch'} for r in roles):score-=22
    elif any(r in {'feature_addon','integration_addon'} for r in roles):score-=8
    if baseline_status=='exact_imported':score+=12
    elif baseline_status=='external_missing':score-=8
    score=max(0,min(100,score))
    label='high' if score>=75 else 'medium' if score>=50 else 'low'
    return score,label

def baseline_for_plugins(plugins):
    if any(p in {'BladeAndBlunt.esp','Adamant.esp','MysticismMagic.esp'} for p in plugins):
        return 'mixed_or_external_missing'
    return 'exact_imported_or_local'

def main():
    roles=role_map(); mods=mod_map(); candidates=[]; cid=1
    observed=read_csv('observed_patterns.csv')
    delivery=read_csv('delivery_observed_patterns.csv')
    for r in delivery:
        observed.append({
            'domain':r['domain'],'plugin':r.get('plugin_scope',''),'pattern_key':r['pattern_key'],
            'sample_count':r['sample_count'],'observed_range':'','observed_median':'',
            'confidence_basis':r['confidence_basis'],'status':r['status'],'approved_rule':r['approved_rule']
        })
    alt_counts=Counter()
    for r in observed:
        ps=tuple(norm_plugins(r.get('plugin','')))
        alt_counts[(r['domain'],ps)] += 1
    for r in observed:
        sample=int(float(r.get('sample_count') or 0))
        if sample<3: continue
        plugins=norm_plugins(r.get('plugin',''))
        rs=[roles.get(p,'unknown') for p in plugins]
        ms=sorted({mods.get(p,'') for p in plugins if mods.get(p,'')})
        contam=[]
        if any(x in {'reversion','compatibility_patch'} for x in rs):contam.append('reversion_or_compatibility_module')
        if any(x in {'feature_addon','integration_addon'} for x in rs):contam.append('optional_or_integration_addon')
        baseline='mixed_or_external_missing' if any(p in {'BladeAndBlunt.esp','Adamant.esp','MysticismMagic.esp'} for p in plugins) else 'exact_imported_or_local'
        score,label=confidence(sample,'observed_pattern',rs,baseline)
        proposition=(f"Within {', '.join(plugins) or 'the observed plugin scope'}, the {r['domain']} implementation repeatedly uses: {r['pattern_key']}")
        if r.get('observed_median'): proposition += f"; observed center: {r['observed_median']}"
        candidates.append({
            'candidate_id':f'RC-{cid:04d}','domain':r['domain'],'source_kind':'observed_pattern',
            'candidate_type':'repeated_implementation_profile','scope_mod':';'.join(ms),'scope_plugins':';'.join(plugins),
            'module_roles':';'.join(rs),'proposition':proposition,'sample_count':sample,
            'evidence_ids':f"observed_patterns:{r['domain']}:{r['pattern_key']}",
            'evidence_basis':r.get('confidence_basis',''),'baseline_status':baseline,
            'counterexample_status':'alternative_profiles_present' if alt_counts[(r['domain'],tuple(plugins))]>1 else 'no_alternative_profile_in_current_grouping',
            'counterexample_count':max(0,alt_counts[(r['domain'],tuple(plugins))]-1),
            'contamination_flags':';'.join(contam),'confidence_score':score,'confidence_label':label,
            'status':'review_required','approved_rule':'False',
            'review_notes':'Do not promote without scope review, exception review, and author-intent/baseline corroboration.'
        });cid+=1
    explicit=read_csv('explicit_design_evidence.csv')
    trivial=re.compile(r'^(This is the main file|This installs|This option installs)',re.I)
    for r in explicit:
        claim=(r.get('claim') or '').strip()
        if not claim or trivial.search(claim):continue
        role=r.get('module_role') or 'unknown'; contam=[]
        if role in {'reversion','compatibility_patch'}:contam.append('reversion_or_compatibility_module')
        if role in {'feature_addon','integration_addon'}:contam.append('optional_or_integration_addon')
        score,label=confidence(1,'explicit_author_evidence',[role],'external_missing',explicit=True)
        candidates.append({
            'candidate_id':f'RC-{cid:04d}','domain':'author_explicit_design','source_kind':'fomod_description',
            'candidate_type':'explicit_author_claim','scope_mod':r['mod'],'scope_plugins':'',
            'module_roles':role,'proposition':claim,'sample_count':1,'evidence_ids':r['evidence_id'],
            'evidence_basis':'author_supplied_installer_description','baseline_status':'not_required_for_claim_text',
            'counterexample_status':'not_yet_checked','counterexample_count':'',
            'contamination_flags':';'.join(contam),'confidence_score':score,'confidence_label':label,
            'status':'review_required','approved_rule':'False',
            'review_notes':'Author statement is strong intent evidence, but implementation corroboration and scope interpretation are still required.'
        });cid+=1
    write_csv(OUT,candidates)
    summary={
        'candidate_count':len(candidates),
        'by_source_kind':dict(Counter(r['source_kind'] for r in candidates)),
        'by_domain':dict(Counter(r['domain'] for r in candidates)),
        'by_confidence':dict(Counter(r['confidence_label'] for r in candidates)),
        'with_contamination_flags':sum(bool(r['contamination_flags']) for r in candidates),
        'review_required':sum(r['status']=='review_required' for r in candidates),
        'approved_rules':0,
        'guardrail':'Candidates are hypotheses/review units, not canonical design rules.'
    }
    SUMMARY.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
