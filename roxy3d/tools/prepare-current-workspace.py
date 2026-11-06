"""Snapshot live files before creating an isolated current-art workspace. No rendering."""
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'roxy3d'
WORK = ART / 'current'
if WORK.exists():
    raise SystemExit('Current workspace already exists; refusing to overwrite it.')
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
BACKUP = ROOT.parent / 'dinkdonk-cinema-backups' / stamp
runtime = json.loads(subprocess.check_output(
    ['node', '-e', "console.log(JSON.stringify(require('./package/art').artFiles('.',m=>{throw Error(m)}).files))"],
    cwd=ROOT, text=True))
paths = set(runtime)
paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets').rglob('*') if p.is_file())
for directory in [ROOT, ROOT / 'shared', ROOT / 'package']:
    paths.update(p.relative_to(ROOT).as_posix() for p in directory.iterdir()
                 if p.is_file() and p.suffix in {'.html', '.js', '.json', '.css', '.bat', '.ps1', '.vbs', '.py', '.md'})
# Preserve the historical source chain, not only the final scenes.
paths.update(p.relative_to(ROOT).as_posix() for p in ART.iterdir()
             if p.is_file() and p.suffix in {'.blend', '.py', '.md'})
paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'docs').rglob('*') if p.is_file())
paths.update(p.relative_to(ROOT).as_posix() for p in (ART / 'tools').iterdir() if p.is_file())
lobby = 'roxy3d/cloud/brief57/upload/bundle/out10i/_work/pipeline/scene.blend'
paths.add(lobby)
parent_launcher = ROOT.parent / 'cinema_dgg_lobby.bat'

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

manifest = []
for rel in sorted(paths):
    src = ROOT / rel
    dst = BACKUP / 'project' / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    before = digest(src)
    shutil.copy2(src, dst)
    if digest(dst) != before or digest(src) != before:
        raise RuntimeError(f'Backup verification failed: {rel}')
    manifest.append({'path': rel, 'bytes': src.stat().st_size, 'sha256': before})
shutil.copy2(parent_launcher, BACKUP / parent_launcher.name)
(BACKUP / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(BACKUP / 'README.md').write_text(
    '# Pre-edit backup\n\nEvery project file in manifest.json was copied and SHA-256 verified. '
    'project/ preserves original relative paths, including both live art packs and the selected auditorium assets, '
    'scene code, launchers and original top-level Blender sources/scripts. No .git history or private OBS settings. '
    'Python/aiohttp and Node must be installed separately.\n', encoding='utf-8')
print(f'BACKUP={BACKUP}', flush=True)
print(f'Verified {len(manifest)} files, {sum(x["bytes"] for x in manifest):,} bytes', flush=True)
WORK.mkdir()
sources = WORK / 'sources'
sources.mkdir()
for src, name in [(ART / 'roxy_cinema_draft13.blend', 'auditorium.blend'),
                  (ART / 'roxy_cinema_draft13_dim.blend', 'auditorium-dim.blend'),
                  (ROOT / lobby, 'lobby.blend')]:
    shutil.copy2(src, sources / name)
(WORK / 'baseline.json').write_text(json.dumps({
    'backup': str(BACKUP), 'blender': '5.2.3', 'runtimeDraft': '13',
    'originals': {name: str(src.relative_to(ROOT)) for src, name in [
        (ART / 'roxy_cinema_draft13.blend', 'auditorium.blend'),
        (ART / 'roxy_cinema_draft13_dim.blend', 'auditorium-dim.blend'),
        (ROOT / lobby, 'lobby.blend')]},
    'runtimeFiles': runtime}, indent=2) + '\n', encoding='utf-8')
print(f'WORKSPACE={WORK}', flush=True)
