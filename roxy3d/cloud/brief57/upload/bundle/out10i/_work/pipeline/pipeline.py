"""Portable entry point; smoke never enters production full()."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))

def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if args==['smoke']:
        from smoke27 import smoke
        smoke()
    elif args==['full']:
        from production import full
        full()
    elif args==['validate-only']:
        from production import validate_only
        validate_only()
    elif args==['preflight']:
        from validation import preflight
        preflight()
    else:raise SystemExit('Usage: blender -b --python pipeline.py -- smoke|full|validate-only|preflight')

if __name__=='__main__':main()
