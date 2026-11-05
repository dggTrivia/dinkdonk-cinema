"""Local shell fixtures only. Never talks to a real pod, or starts a render."""
import json,os,shutil,subprocess,time,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE/'bundle'
TEST=HERE/'watchdog-tests';TEST.mkdir(exist_ok=True)
BASH='C:/Program Files/Git/usr/bin/bash.exe'
def unix(p):
    s=Path(p).resolve().as_posix();return '/'+s[0].lower()+s[2:]
def put(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8',newline='\n');p.chmod(0o755)
def run(script,args,cwd,env=None):
    e=os.environ.copy();e.pop('RUNPOD_POD_ID',None);e.pop('RUNPOD_API_KEY',None)
    if env:e.update(env)
    return subprocess.run([BASH,unix(script),*args],cwd=cwd,env=e,capture_output=True,text=True,timeout=30)
cases=[]
for name,end_offset,start_offset,fallback,stale in [('grace',-10801,-11000,False,False),('hard_cap',-1,-28801,False,False),('hard_cap_running',None,-28801,False,False),('legacy_fallback',-10801,-11000,True,False),('superseded',-10801,-11000,False,True)]:
    d=TEST/name;state=d/'work/watchdog/test';state.mkdir(parents=True,exist_ok=True)
    calls=d/'calls';calls.write_text('');now=int(time.time())
    (state/'start').write_text(str(now+start_offset));(state.parent/'current').write_text('newer' if stale else 'test')
    if end_offset is not None:(state/'end').write_text(str(now+end_offset))
    elif (state/'end').exists():(state/'end').unlink()
    fake=d/'runpodctl';put(fake,'#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "'+unix(calls)+'"\n'+('[[ "$1" == stop ]]\n' if fallback else 'exit 0\n'))
    # Shell PID 1 exists under Git Bash, so the active-run fixture stays active.
    result=run(ROOT/'watchdog.sh',[unix(d),unix(state),'MOCK-POD-NO-NETWORK',unix(fake),'1'],d)
    assert result.returncode==0,(name,result.stdout,result.stderr)
    seen=calls.read_text().splitlines();expected=[] if stale else ['pod stop MOCK-POD-NO-NETWORK']+(['stop pod MOCK-POD-NO-NETWORK'] if fallback else [])
    assert seen==expected,(name,seen)
    if name=='hard_cap_running':assert (d/'FAILED').exists()
    cases.append({'case':name,'passed':True,'fake_cli_calls':seen,'log':result.stdout.strip()})
# Exercise the actual launcher EXIT trap and pipefail with a stub Blender.
# flock is a fixture stub on Windows; real Linux lock semantics are not claimed.
for name,exitcode,bad_hash in [('success',0,False),('failure',7,False),('checksum_failure',0,True)]:
    d=TEST/('launcher_'+name);d.mkdir(exist_ok=True);shutil.copyfile(ROOT/'run.sh',d/'run.sh')
    bins=d/'bin';bins.mkdir(exist_ok=True)
    for cmd,body in {'flock':'exit 0','uname':'if [[ "$1" == -m ]]; then echo x86_64; else echo Linux; fi','nvidia-smi':'echo MOCK-GPU','curl':'exit 99','xz':'exit 0','tar':'exit 99'}.items():put(bins/cmd,'#!/usr/bin/env bash\n'+body+'\n')
    blender=d/'.runtime/blender-5.2.3-linux-x64/blender'
    put(blender,'#!/usr/bin/env bash\nif [[ "$1" == --version ]]; then echo "Blender fixture only"; exit 0; fi\nexit '+str(exitcode)+'\n')
    (d/'fixture').write_text('local fixture')
    digest='0'*64 if bad_hash else hashlib.sha256((d/'fixture').read_bytes()).hexdigest()
    (d/'BUNDLE-SHA256SUMS').write_text(digest+'  fixture\n',newline='\n')
    result=run(d/'run.sh',['smoke'],d,{'PATH':unix(bins)+':/usr/bin:/bin'})
    success=name=='success';assert (result.returncode==0)==success,(name,result.stdout,result.stderr)
    assert (d/('DONE' if success else 'FAILED')).exists(),name
    assert not (d/('FAILED' if success else 'DONE')).exists(),name
    state=next((d/'work/watchdog').glob('*/end'));assert int(state.read_text())>0
    if success:assert 'SUCCESS mode=smoke' in result.stdout
    if name=='failure':assert result.returncode==7
    cases.append({'case':'launcher_'+name,'passed':True,'exit_code':result.returncode,'marker':'DONE' if success else 'FAILED'})
for script in ['run.sh','watchdog.sh']:subprocess.run([BASH,'-n',str(ROOT/script)],check=True)
report={'passed':True,'scope':'Git Bash shell fixtures with fake Blender and fake runpodctl; no network calls, no real pod or render','real_linux_lock_and_detach_tested':False,'cases':cases,'shell_syntax':True}
(ROOT/'watchdog_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
