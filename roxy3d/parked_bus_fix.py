"""Ownership of the four Draft 6 plates attached to the inspection-only bus."""
PLATE_PREFIXES=('D6 bus DGG 05 number plate','D6 bus plate DGG 05')

def is_parked_bus_plate(ob):
    return ob.name.startswith(PLATE_PREFIXES)

def tag_parked_bus_plate(ob):
    ob['draft5_bus']=True
    ob['layer']='draft5_parked_bus'

def repair_parked_bus_plates(scene, *, remove=False):
    import bpy
    names=[]
    for ob in list(scene.objects):
        if not is_parked_bus_plate(ob):
            continue
        names.append(ob.name)
        if remove:
            bpy.data.objects.remove(ob,do_unlink=True)
        else:
            tag_parked_bus_plate(ob)
    return sorted(names)
