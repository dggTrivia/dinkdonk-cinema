import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pass8b_common import ROOT
source=(ROOT/'calibrate_pass8.py').read_text().replace('roxy_pass8.blend','roxy_pass8b.blend').replace("'qa8'","'qa8b'").replace('from pass8_common import status','from pass8b_common import status')
exec(compile(source,str(ROOT/'calibrate_pass8b.py'),'exec'))
