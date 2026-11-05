"""Cycles surface-position AOV, used to split long sprites for DOM depth sorting."""
import bpy
import numpy as np
from pathlib import Path

def configure(scene,directory):
    aov=scene.view_layers[0].aovs.add();aov.name='FloorUV';aov.type='COLOR'
    for mat in bpy.data.materials:
        if not mat.node_tree:continue
        nodes=mat.node_tree.nodes
        geo=nodes.new('ShaderNodeNewGeometry')
        vec=nodes.new('ShaderNodeVectorMath');vec.operation='MULTIPLY'
        vec.inputs[1].default_value=(1,-1,1)
        out=nodes.new('ShaderNodeOutputAOV');out.aov_name='FloorUV'
        mat.node_tree.links.new(geo.outputs['Position'],vec.inputs[0])
        mat.node_tree.links.new(vec.outputs['Vector'],out.inputs['Color'])
    tree=bpy.data.node_groups.new('Roxy beauty and surface position','CompositorNodeTree')
    tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    scene.compositing_node_group=tree
    output=tree.nodes.new('NodeGroupOutput')
    layer=tree.nodes.new('CompositorNodeRLayers');layer.scene=scene
    tree.links.new(layer.outputs['Image'],output.inputs['Image'])
    file=tree.nodes.new('CompositorNodeOutputFile')
    file.format.media_type='IMAGE'
    file.format.file_format='OPEN_EXR';file.format.color_mode='RGBA';file.format.color_depth='32'
    file.format.exr_codec='ZIP'
    file.directory=str(directory)
    file.file_name='position'
    file.file_output_items.new('RGBA','FloorUV')
    tree.links.new(layer.outputs['FloorUV'],file.inputs['FloorUV'])
    return file

def export_array(path,target):
    im=bpy.data.images.load(str(path),check_existing=False)
    w,h=im.size
    buf=np.empty(w*h*4,np.float32);im.pixels.foreach_get(buf)
    data=buf.reshape(h,w,4)[::-1].copy()
    # AOV RGB is associated with its coverage alpha. Undo that before binning.
    uv=np.divide(data[:,:,:2],data[:,:,3:4],out=np.zeros_like(data[:,:,:2]),where=data[:,:,3:4]>1e-7)
    np.savez_compressed(target,uv=uv)
    bpy.data.images.remove(im)
    return data
