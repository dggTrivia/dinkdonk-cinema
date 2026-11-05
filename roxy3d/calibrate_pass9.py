import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pass9_common import ROOT
source=(ROOT/'calibrate_pass8.py').read_text().replace('roxy_pass8.blend','roxy_pass9.blend').replace("'qa8'","'qa9'").replace('from pass8_common import status','from pass9_common import status')
exec(compile(source,str(ROOT/'calibrate_pass9.py'),'exec'))
