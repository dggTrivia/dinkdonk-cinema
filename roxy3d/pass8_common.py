"""Pass-8 stage journal and fixed workspace paths; no live output mutations."""
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa8';OUT=ROOT/'out8';LIVE=ROOT/'out7'
def status(stage):
    QA.mkdir(exist_ok=True)
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: '+stage+'\n')
    print('PASS8_STAGE',stage,flush=True)

def gpu(sc):
    import bpy
    prefs=bpy.context.preferences.addons['cycles'].preferences
    for backend in ['OPTIX','CUDA']:
        try:
            prefs.compute_device_type=backend;prefs.get_devices()
            available=[d for d in prefs.devices if d.type==backend]
            if available:
                for d in prefs.devices:d.use=d.type==backend
                sc.cycles.device='GPU';print('PASS8_DEVICE',backend,[d.name for d in available],flush=True);return
        except Exception:pass
    sc.cycles.device='CPU';print('PASS8_DEVICE CPU fallback',flush=True)
