#!/usr/bin/env python3
"""Decode AVIF skill/perk-tree structures and imported-baseline graph deltas."""
from __future__ import annotations
import base64,csv,json,struct,collections,math
from pathlib import Path

ROOT=Path('/mnt/data/simonrim-balancer/data/snapshots/2026-09-23')
SCHEMA='UESP TES5/SSE AVIF perk-section layout (cached 2026-07-01)'
CATEGORIES={0:'None',1:'Combat',2:'Magic',3:'Stealth'}
AVSK_FIELDS=['skill_use_mult','skill_use_offset','skill_improve_mult','skill_improve_offset']

def read_csv(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write_csv(path,rows,fields=None):
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open('w',encoding='utf-8',newline='') as f:
        if not fields:return
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def u32(b):return struct.unpack('<I',b)[0]
def i32(b):return struct.unpack('<i',b)[0]
def f32(b):return struct.unpack('<f',b)[0]
def text(b):return b.split(b'\x00',1)[0].decode('utf-8','replace')
def canonicalize(fid,plugin,masters):
    if not fid:return ''
    slot=(fid>>24)&0xff;obj=fid&0xffffff
    if slot<len(masters):origin=masters[slot]
    elif slot==len(masters):origin=plugin
    else:return ''
    return f'{origin}:{obj:06X}'

def parse_record(r, masters, resolved):
    subs=[(s['type'],base64.b64decode(s['data_base64'])) for s in r['subrecords']]
    pre_cnam=[];avsk=None;abbr='';nodes=[];cur=None;after_avsk=False
    for typ,data in subs:
        if typ=='ANAM':abbr=text(data)
        elif typ=='CNAM' and not after_avsk:pre_cnam.append(u32(data))
        elif typ=='AVSK':
            if len(data)!=16:raise ValueError(f'AVSK size {len(data)}')
            avsk=struct.unpack('<4f',data);after_avsk=True
        elif after_avsk:
            if typ=='PNAM':
                if cur is not None:nodes.append(cur)
                cur={'perk_form_id_raw':u32(data),'connections':[]}
            elif cur is not None:
                if typ=='FNAM':cur['flag_raw']=u32(data)
                elif typ=='XNAM':cur['x_raw_unsigned']=u32(data);cur['x_grid']=i32(data)
                elif typ=='YNAM':cur['y_raw_unsigned']=u32(data);cur['y_grid']=i32(data)
                elif typ=='HNAM':cur['horizontal_pos']=f32(data)
                elif typ=='VNAM':cur['vertical_pos']=f32(data)
                elif typ=='SNAM':cur['skill_form_id_raw']=u32(data)
                elif typ=='CNAM':cur['connections'].append(u32(data))
                elif typ=='INAM':cur['index_id']=u32(data)
    if cur is not None:nodes.append(cur)
    if avsk is None:raise ValueError('missing AVSK')
    rr=resolved.get((r['plugin'],r['form_id_hex']),{})
    row={'mod':r['mod'],'version':r['version'],'plugin':r['plugin'],'form_id_hex':r['form_id_hex'],'canonical_key':rr.get('canonical_key',''),'record_role':rr.get('record_role',''),'baseline_kind':rr.get('baseline_kind',''),'baseline_plugin':rr.get('baseline_plugin',''),'edid':r.get('edid') or '','name':r.get('full') or r.get('name') or '','description':r.get('description') or r.get('desc') or '','abbreviation':abbr,'record_level_cnam_count':len(pre_cnam),'skill_category_id':pre_cnam[0] if pre_cnam else '', 'skill_category_name':CATEGORIES.get(pre_cnam[0],f'Unknown({pre_cnam[0]})') if pre_cnam else '' ,'schema_source':SCHEMA,'evidence_stage':'decoded','rule_status':'not_a_rule'}
    row.update(dict(zip(AVSK_FIELDS,avsk)))
    return row,nodes

def visible_perk(plugin,key,plugins,perks_by_occ,perks_by_key):
    if not key:return None
    if (plugin,key) in perks_by_occ:return perks_by_occ[(plugin,key)]
    for m in reversed(plugins[plugin]):
        if (m,key) in perks_by_occ:return perks_by_occ[(m,key)]
    arr=perks_by_key.get(key,[])
    return arr[-1] if arr else None

def graph_metrics(nodes):
    byidx={n['index_id']:n for n in nodes if 'index_id' in n}
    indeg=collections.Counter();outdeg={n['index_id']:len(n['connections']) for n in nodes if 'index_id' in n};missing=[]
    for n in nodes:
        for d in n.get('connections',[]):
            if d in byidx:indeg[d]+=1
            else:missing.append((n.get('index_id'),d))
    root=next((n for n in nodes if n.get('perk_form_id_raw')==0),None)
    rootid=root.get('index_id') if root else None
    reachable=set();depth={}
    if rootid is not None:
        q=collections.deque([(rootid,0)])
        while q:
            x,d=q.popleft()
            if x in reachable:continue
            reachable.add(x);depth[x]=d
            for y in byidx.get(x,{}).get('connections',[]):
                if y in byidx and y not in reachable:q.append((y,d+1))
    state={};cyclic=False
    def dfs(x):
        nonlocal cyclic
        state[x]=1
        for y in byidx.get(x,{}).get('connections',[]):
            if y not in byidx:continue
            if state.get(y)==1:cyclic=True;continue
            if state.get(y,0)==0:dfs(y)
        state[x]=2
    for x in byidx:
        if state.get(x,0)==0:dfs(x)
    nonroot=[n for n in nodes if n.get('perk_form_id_raw')!=0]
    geom=[n for n in nonroot if 'x_grid' in n and 'y_grid' in n]
    return {'node_count':len(nodes),'perk_node_count':len(nonroot),'edge_count':sum(len(n.get('connections',[])) for n in nodes),'root_index_id':rootid if rootid is not None else '', 'root_out_degree':len(root.get('connections',[])) if root else 0,'branch_node_count':sum(1 for n in nonroot if outdeg.get(n.get('index_id'),0)>1),'merge_node_count':sum(1 for n in nonroot if indeg.get(n.get('index_id'),0)>1),'leaf_node_count':sum(1 for n in nonroot if outdeg.get(n.get('index_id'),0)==0),'max_shortest_depth':max(depth.values()) if depth else '', 'unreachable_node_count':len(set(byidx)-reachable) if rootid is not None else len(byidx),'missing_edge_target_count':len(missing),'has_cycle':cyclic,'x_grid_min':min((n['x_grid'] for n in geom),default=''),'x_grid_max':max((n['x_grid'] for n in geom),default=''),'y_grid_min':min((n['y_grid'] for n in geom),default=''),'y_grid_max':max((n['y_grid'] for n in geom),default='')}

def graph_sets(skill_row,nodes):
    byidx={n['index_id']:n for n in nodes}
    def ident(n):return 'ROOT' if n.get('root_placeholder') else (n.get('perk_canonical_key') or f"RAW:{n.get('perk_form_id_hex','')}")
    node_set={ident(n) for n in nodes if not n.get('root_placeholder')}
    edges=set()
    for n in nodes:
        src=ident(n)
        for d in n.get('connections',[]):
            dest=byidx.get(d)
            edges.add((src,ident(dest) if dest else f'INDEX:{d}'))
    positions={ident(n):(n.get('x_grid'),n.get('y_grid'),round(float(n.get('horizontal_pos',0)),7),round(float(n.get('vertical_pos',0)),7)) for n in nodes if not n.get('root_placeholder')}
    return node_set,edges,positions

def main():
    plugins={r['plugin']:[x for x in r['masters'].split(';') if x] for r in read_csv(ROOT/'plugins.csv')}
    resolved={(r['plugin'],r['form_id_hex']):r for r in read_csv(ROOT/'resolved_forms.csv') if r['record_type']=='AVIF'}
    perks=read_csv(ROOT/'perks_full.csv');perks_by_occ={(r['plugin'],r['canonical_key']):r for r in perks};perks_by_key=collections.defaultdict(list)
    for r in perks:perks_by_key[r['canonical_key']].append(r)
    skills=[];allnodes=[];alledges=[];failures=[];nodes_by_occ={}
    for line in (ROOT/'records_full.jsonl').open(encoding='utf-8'):
        r=json.loads(line)
        if r.get('record_type')!='AVIF':continue
        try:
            skill,nodes=parse_record(r,plugins[r['plugin']],resolved)
            for n in nodes:
                n['root_placeholder']=n.get('perk_form_id_raw',0)==0
                n['perk_form_id_hex']=f"{n.get('perk_form_id_raw',0):08X}" if n.get('perk_form_id_raw') else ''
                n['perk_canonical_key']=canonicalize(n.get('perk_form_id_raw',0),r['plugin'],plugins[r['plugin']]) if n.get('perk_form_id_raw') else ''
                pr=visible_perk(r['plugin'],n['perk_canonical_key'],plugins,perks_by_occ,perks_by_key)
                n['perk_source_plugin']=pr.get('plugin','') if pr else ''
                n['perk_edid']=pr.get('edid','') if pr else ''
                n['perk_name']=pr.get('name','') if pr else ''
                n['skill_form_id_hex']=f"{n.get('skill_form_id_raw',0):08X}" if n.get('skill_form_id_raw') else ''
                n['skill_canonical_key']=canonicalize(n.get('skill_form_id_raw',0),r['plugin'],plugins[r['plugin']]) if n.get('skill_form_id_raw') else ''
                n['plugin']=r['plugin'];n['skill_avif_canonical_key']=skill['canonical_key'];n['skill_edid']=skill['edid'];n['mod']=r['mod'];n['version']=r['version']
            byidx={n['index_id']:n for n in nodes}
            for n in nodes:
                n['outgoing_index_ids']=';'.join(map(str,n.get('connections',[])))
                n['outgoing_perk_keys']=';'.join(('ROOT' if byidx.get(d,{}).get('root_placeholder') else byidx.get(d,{}).get('perk_canonical_key',f'INDEX:{d}')) for d in n.get('connections',[]))
            incoming=collections.defaultdict(list)
            for n in nodes:
                for d in n.get('connections',[]):incoming[d].append(n['index_id'])
            for n in nodes:n['incoming_index_ids']=';'.join(map(str,sorted(incoming.get(n['index_id'],[]))))
            metrics=graph_metrics(nodes);skill.update(metrics)
            skills.append(skill);nodes_by_occ[(r['plugin'],skill['canonical_key'])]=nodes
            for n in nodes:
                row={k:v for k,v in n.items() if k!='connections'};allnodes.append(row)
                for d in n.get('connections',[]):
                    dest=byidx.get(d)
                    alledges.append({'mod':r['mod'],'version':r['version'],'plugin':r['plugin'],'skill_avif_canonical_key':skill['canonical_key'],'skill_edid':skill['edid'],'source_index_id':n['index_id'],'source_perk_canonical_key':'ROOT' if n['root_placeholder'] else n['perk_canonical_key'],'source_perk_edid':'ROOT' if n['root_placeholder'] else n['perk_edid'],'destination_index_id':d,'destination_exists':bool(dest),'destination_perk_canonical_key':('ROOT' if dest and dest['root_placeholder'] else (dest['perk_canonical_key'] if dest else '')),'destination_perk_edid':('ROOT' if dest and dest['root_placeholder'] else (dest['perk_edid'] if dest else '')),'evidence_stage':'decoded','rule_status':'not_a_rule'})
        except Exception as e:failures.append({'plugin':r.get('plugin'),'form_id_hex':r.get('form_id_hex'),'edid':r.get('edid'),'error':str(e)})
    write_csv(ROOT/'actor_values_full.csv',skills)
    write_csv(ROOT/'perk_tree_nodes.csv',allnodes)
    write_csv(ROOT/'perk_tree_edges.csv',alledges)
    profile_fields=['mod','version','plugin','canonical_key','record_role','baseline_kind','baseline_plugin','edid','name','skill_category_id','skill_category_name']+AVSK_FIELDS+['node_count','perk_node_count','edge_count','root_out_degree','branch_node_count','merge_node_count','leaf_node_count','max_shortest_depth','unreachable_node_count','missing_edge_target_count','has_cycle','x_grid_min','x_grid_max','y_grid_min','y_grid_max','evidence_stage','rule_status']
    write_csv(ROOT/'perk_tree_profiles.csv',skills,profile_fields)
    deltas=[]
    skill_by_occ={(r['plugin'],r['canonical_key']):r for r in skills}
    for cur in skills:
        if cur['baseline_kind']!='imported_master' or not cur['baseline_plugin']:continue
        base=skill_by_occ.get((cur['baseline_plugin'],cur['canonical_key']))
        if not base:continue
        bn=nodes_by_occ[(base['plugin'],base['canonical_key'])];cn=nodes_by_occ[(cur['plugin'],cur['canonical_key'])]
        bnodes,bedges,bpos=graph_sets(base,bn);cnodes,cedges,cpos=graph_sets(cur,cn)
        shared=bnodes&cnodes;pos_changed=[k for k in sorted(shared) if bpos.get(k)!=cpos.get(k)]
        avsk_changes=[f for f in AVSK_FIELDS if float(base[f])!=float(cur[f])]
        deltas.append({'plugin':cur['plugin'],'baseline_plugin':base['plugin'],'canonical_key':cur['canonical_key'],'edid':cur['edid'],'category_changed':cur['skill_category_id']!=base['skill_category_id'],'avsk_fields_changed':';'.join(avsk_changes),'added_nodes_count':len(cnodes-bnodes),'added_nodes':';'.join(sorted(cnodes-bnodes)),'removed_nodes_count':len(bnodes-cnodes),'removed_nodes':';'.join(sorted(bnodes-cnodes)),'added_edges_count':len(cedges-bedges),'added_edges':';'.join(f'{a}->{b}' for a,b in sorted(cedges-bedges)),'removed_edges_count':len(bedges-cedges),'removed_edges':';'.join(f'{a}->{b}' for a,b in sorted(bedges-cedges)),'position_changed_nodes_count':len(pos_changed),'position_changed_nodes':';'.join(pos_changed),'baseline_perk_nodes':base['perk_node_count'],'current_perk_nodes':cur['perk_node_count'],'baseline_edges':base['edge_count'],'current_edges':cur['edge_count'],'evidence_stage':'decoded_delta','rule_status':'not_a_rule'})
    write_csv(ROOT/'perk_tree_deltas.csv',deltas)
    summary={'avif_records_found':len(skills)+len(failures),'avif_records_decoded':len(skills),'decode_failures':len(failures),'perk_tree_nodes':len(allnodes),'perk_tree_edges':len(alledges),'root_placeholder_nodes':sum(1 for n in allnodes if n['root_placeholder']),'graphs_with_cycles':sum(1 for r in skills if r['has_cycle']),'graphs_with_unreachable_nodes':sum(1 for r in skills if int(r['unreachable_node_count'])>0),'missing_edge_targets':sum(int(r['missing_edge_target_count']) for r in skills),'exact_imported_baselines':sum(1 for r in skills if r['baseline_kind']=='imported_master'),'external_baselines':sum(1 for r in skills if r['baseline_kind']=='external_master_not_imported'),'imported_baseline_graph_deltas':len(deltas),'delta_records_with_added_nodes':sum(1 for r in deltas if int(r['added_nodes_count'])>0),'delta_records_with_removed_nodes':sum(1 for r in deltas if int(r['removed_nodes_count'])>0),'delta_records_with_edge_changes':sum(1 for r in deltas if int(r['added_edges_count'])+int(r['removed_edges_count'])>0),'approved_rules':0,'note':'AVIF graph layout does not itself define perk prerequisites; PERK CTDA remains authoritative for requirements.'}
    (ROOT/'actor_value_decoder_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    if failures:print('FAILURES',json.dumps(failures,indent=2))

if __name__=='__main__':main()
