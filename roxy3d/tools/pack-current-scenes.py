"""Run in background Blender. Pack only isolated working copies; never render."""
import bpy
import json
import os
from pathlib import Path

WORK = Path(__file__).resolve().parents[1] / 'current'
reports = []
for name in ['auditorium.blend', 'auditorium-dim.blend', 'lobby.blend']:
    source = WORK / 'sources' / name
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    missing = []
    for image in bpy.data.images:
        if image.source not in {'GENERATED', 'VIEWER'} and not image.packed_file and image.filepath:
            path = bpy.path.abspath(image.filepath, library=image.library)
            if not os.path.isfile(path):
                missing.append({'type': 'image', 'name': image.name, 'path': path})
    for font in bpy.data.fonts:
        if font.filepath not in {'', '<builtin>'} and not font.packed_file:
            path = bpy.path.abspath(font.filepath, library=font.library)
            if not os.path.isfile(path):
                missing.append({'type': 'font', 'name': font.name, 'path': path})
    libraries = [bpy.path.abspath(lib.filepath) for lib in bpy.data.libraries]
    # Appended data is embedded. Blender also reports its old source filename as
    # a weak reference; that is provenance, not a linked-library dependency.
    weak = {bpy.path.abspath(block.library_weak_reference.filepath)
            for block in bpy.data.all_ids if block.library_weak_reference}
    external = list(bpy.utils.blend_paths(absolute=True, packed=False))
    report = {'file': name, 'objects': len(bpy.data.objects), 'camera': bpy.context.scene.camera.name if bpy.context.scene.camera else None,
              'missing': missing, 'linkedLibraries': libraries, 'externalPathsBefore': external}
    if not missing and not libraries:
        bpy.ops.file.pack_all()
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(source), compress=True)
        bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
        remaining = [p for p in bpy.utils.blend_paths(absolute=True, packed=False) if p and p != '<builtin>']
        report['externalPathsAfter'] = sorted(set(remaining) - weak)
        report['embeddedAssetProvenance'] = sorted(weak)
        report['selfContained'] = not report['externalPathsAfter']
    else:
        report['selfContained'] = False
    reports.append(report)
(WORK / 'dependency-report.json').write_text(json.dumps(reports, indent=2) + '\n', encoding='utf-8')
print(json.dumps([{k: r[k] for k in ['file', 'objects', 'missing', 'linkedLibraries', 'selfContained']} for r in reports], indent=2))
