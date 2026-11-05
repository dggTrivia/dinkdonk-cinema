import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import encode_loop as e
from common import ROOT
e.QA=ROOT/'qa6';e.OUT=ROOT/'out6';e.FRAMES=e.QA/'loop_frames';e.ENCODE=e.QA/'encode'
e.main()
