import collections, difflib, json, pathlib, shutil, statistics
ROOT=pathlib.Path(__file__).resolve().parents[2]
rows=[];seen=set()
for line in (ROOT/'cloud/progress-full.log').read_text().splitlines():
    try:r=json.loads(line.removeprefix('CLOUD_PROGRESS '))
    except ValueError:continue
    if r.get('stage')=='render_done' and r['tag'] not in seen:rows.append(r);seen.add(r['tag'])
groups=collections.defaultdict(list)
for r in rows:
    tag=r['tag'];group=next((x for x in ['background','foreground','weather','door'] if tag.startswith(x+'_')),'other');groups[group].append(r)
summary={k:dict(count=len(v),render_sum=sum(x['seconds'] for x in v),render_mean=statistics.mean(x['seconds'] for x in v),total_mean=statistics.mean(x.get('timing',{}).get('total',x['seconds']) for x in v)) for k,v in groups.items()}
m=json.loads((ROOT/'out10/manifest.json').read_text());wet={e['parent'] for e in m['prop_loops'] if e['name'].startswith('wet_')}
summary['brief56']={'foreground_parents':len(m['occluders']),'wet_parents':len(wet),'foreground_captures':len(wet)*25+len(m['occluders'])-len(wet),'background_captures':50,'weather_captures':49,'door_poses':48,'WC_states':2}
(pathlib.Path(__file__).parent/'timing-baseline.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2));print('free GiB',round(shutil.disk_usage(ROOT).free/2**30,2))
a=(ROOT/'cloud/cloud-render.sh.pre57').read_text();b=(ROOT/'cloud/cloud-render.sh').read_text()
diff=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='pre57',tofile='brief57'))
(pathlib.Path(__file__).parent/'helper.diff').write_text(diff)
print(diff)
