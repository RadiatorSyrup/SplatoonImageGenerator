import os
import bpy
from math import radians

def configure_lights(basis_collection):
    # Create first sun
    sun1_data = bpy.data.lights.new(name="Sun_1", type='SUN')
    sun1_object = bpy.data.objects.new(name="Sun_1", object_data=sun1_data)
    basis_collection.objects.link(sun1_object)
    sun1_object.location = (5.0, 5.0, 5.0)
    sun1_object.rotation_euler = (radians(45), 0, 0)
    sun1_data.energy = 10.0
    
def configure_hdri(context, node_tree, tree_nodes, node_background):
    node_environment = tree_nodes.new('ShaderNodeTexEnvironment')
    # Load and assign the image to the node property
    addon_directory = os.path.dirname(__file__)
    hdris_directory = os.path.join(addon_directory, '..', 'HDRIs')
    image_path = os.path.join(hdris_directory, "HDRIHaven_PineAttic.exr")

    node_environment.image = bpy.data.images.load(
        image_path)  # Abs path
    node_environment.location = -300, 0
    
    node_output = tree_nodes.new(type='ShaderNodeOutputWorld')
    node_output.location = 200, 0
    
    # Link nodes
    links = node_tree.links
    link = links.new(
        node_environment.outputs["Color"], node_background.inputs["Color"])
    link = links.new(
        node_background.outputs["Background"], node_output.inputs["Surface"])