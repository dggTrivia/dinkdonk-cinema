"""Use the proven VP9 encoder with all writable paths redirected to pass 4."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import encode_loop as enc
from common import ROOT
enc.QA=ROOT/'qa4';enc.OUT=ROOT/'out4';enc.FRAMES=enc.QA/'loop_frames';enc.ENCODE=enc.QA/'encode'
if __name__=='__main__':enc.main()
