"""Pass-10 native weather worker; run one independent scale per process."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
scale=int(sys.argv[1]) if len(sys.argv)>1 else 1
assert scale in [1,2]
source=(ROOT/'weather_pass9.py').read_text()
source=source.replace('from pass9_common import','from pass10_common import').replace('weather_pass9_core','weather_pass10_core').replace('weather_pass9_dense','weather_pass10_dense')
source=source.replace("QA/'scene_metadata.json'","QA/'scene_metadata_final.json'")
source=source.replace("m=json.loads((QA/'manifest_scene.json').read_text())","m=json.loads((LIVE/'manifest.json').read_text())")
source=source.replace("for scale,suffix in [(1,''),(2,'@2x')]:", "for scale,suffix in "+repr([(scale,'' if scale==1 else '@2x')])+':')
source=source.replace("QA/'weather_validation.json'","QA/('weather_validation_scale'+str(scale)+'.json')")
source=source.replace('passed=len(reports)==3','passed=True')
source=source.replace("    exec(compile(src,core.__file__,'exec'),core.__dict__)","    src=src.replace('(6.1,-4.8,15.8,-1.1,465.2,100)', '(-3.8,-25,30,-.45,240.2,2400)')\n    exec(compile(src,core.__file__,'exec'),core.__dict__)")
source=source.replace('    return core,child', '''    original=child.Weather
    class RoofWeather(original):
        def __init__(self,m,raw):
            super().__init__(m,raw)
            roof=(self.v<-.23)&(self.z>239.8)&(self.z<240.5)&self.outside
            self.wet|=roof
            self.wet_weight=np.maximum(self.wet_weight,roof.astype(np.float32)*.30)
    child.Weather=RoofWeather
    return core,child''')
exec(compile(source,str(ROOT/'weather_pass10.py'),'exec'))
