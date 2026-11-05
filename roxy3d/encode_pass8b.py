import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import encode_pass8 as encoder
from pass8b_common import QA,OUT,status
encoder.QA=QA;encoder.OUT=OUT;encoder.status=status
if __name__=='__main__':encoder.main()
