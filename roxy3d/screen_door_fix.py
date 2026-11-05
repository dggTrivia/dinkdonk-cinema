"""Draft 15: pose-independent indoor ownership for the three cinema doors."""
import bpy

def is_screen_door(o):
    return str(o.get('door_id','')) in {'1','2','3'} or o.get('anim_id') in {'screen_1','screen_2','screen_3'}

def repair_screen_doors(sc):
    doors=[o for o in sc.objects if is_screen_door(o) and o.type in {'MESH','CURVE','FONT'}]
    added={};restored=[]
    for name in ['D11 cinema interior light receivers','D12 unchanged cinema receivers outside restroom']:
        col=bpy.data.collections.get(name)
        if col:
            added[name]=[]
            for o in doors:
                if o.name not in col.objects:col.objects.link(o);added[name].append(o.name)
    # Restore the leather to the same dry source used by Screens 1 and 3.
    # Keep the existing hardware materials and finishes unchanged.
    for o in doors:
        if str(o.get('door_id',''))!='2' and o.get('anim_id')!='screen_2':continue
        for i,ma in enumerate(o.data.materials):
            if ma and ' | ' in ma.name and 'leather' in ma.name.lower() and ma.name.startswith(('D5 wet ','D10 wet ')):
                original=bpy.data.materials.get(ma.name.split(' | ',1)[1])
                if not original:original=bpy.data.materials.get('D7 oxblood leather upholstery')
                if original:o.data.materials[i]=original;restored.append([o.name,ma.name,original.name])
    return {'doors':len(doors),'added':added,'restored_materials':restored}
