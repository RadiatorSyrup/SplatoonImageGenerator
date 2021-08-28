import re
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from math import radians
from mathutils import Vector
import os
from . ImageProcessor import ImageProcessor


class RotateAndScale(bpy.types.Operator):
    """Rotate the model to correct orientation CHECK THE MODEL STARTS UPSIDE DOWN"""
    bl_idname = "object.rotate_and_scale"
    bl_label = "Rotate and Scale"

    def execute(self, context):
        # Report "Hello World" to the Info Area
        self.report({'INFO'}, "Rotating Object")

        obj = context.window_manager.objectselection_props
        if not obj:
            self.report({'ERROR_INVALID_INPUT'},
                        "Please select the armature of the model above")
            return {'CANCELLED'}
        obj.rotation_euler = [radians(-180), 0, 0]
        obj.scale = [1, 1, 1]
        obj.location = [0, 0, 0]

        return {'FINISHED'}


class PositionModel(bpy.types.Operator):

    """Position the 3d cursor to the centre of the model CHECK THIS WORKS BEFORE RENDERING"""
    bl_idname = "object.position_model"
    bl_label = "Position Cursor"

    def execute(self, context):
        # Report "Hello World" to the Info Area
        # self.report({'INFO'}, "Centred")
        obj = context.window_manager.objectselection_props
        xs = []
        ys = []
        zs = []
        for child in obj.children:
            box = child.bound_box
            print(child.name)
            world_bound = []
            for coord in box:
                world_bound.append(child.matrix_world @ Vector(coord))
            print(world_bound)

            xs += [i[0] for i in world_bound]
            ys += [i[1] for i in world_bound]
            zs += [i[2] for i in world_bound]
        if not xs:
            self.report({'WARNING'}, "Could not find children")
            return {'CANCELLED'}

        deltax = max(xs) - min(xs)
        deltay = max(ys) - min(ys)
        deltaz = max(zs) - min(zs)

        x_pos = min(xs) + deltax/2
        y_pos = min(ys) + deltay/2
        z_pos = min(zs) + deltaz/2

        bpy.context.scene.cursor.location = [x_pos, y_pos, z_pos]

        # obj.location = [x_pos, y_pos, z_pos]
        return {'FINISHED'}


class PositionCamera(bpy.types.Operator):

    """Position camera to frame model CHECK THIS WORKS BEFORE RENDERING"""
    bl_idname = "object.position_camera"
    bl_label = "Position Camera"

    def execute(self, context):
        # Report "Hello World" to the Info Area
        self.report({'INFO'}, "Moving camera")
        context.scene.render.resolution_x = context.window_manager.x_resolution
        context.scene.render.resolution_y = context.window_manager.y_resolution

        obj = context.window_manager.objectselection_props

        bpy.context.scene.camera.rotation_euler = [radians(90), 0, 0]

        bpy.ops.object.select_all(action='DESELECT')

        for child in obj.children:
            child.select_set(True)

        if not bpy.context.selected_objects:
            self.report({'WARNING'}, "Could not find children")
            return {'CANCELLED'}

        # print(largest.name)
        context.region_data.view_perspective = 'CAMERA'
        bpy.context.view_layer.objects.active = obj

        bpy.context.scene.camera.select_set(True)
        bpy.ops.view3d.camera_to_view_selected()

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.camera.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.scene.camera

        bpy.ops.transform.translate(
            value=(0.0, 0.0, 10.0), orient_type='LOCAL')

        return {'FINISHED'}


class CheckRotateModel(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "object.check_rotation"
    bl_label = "Check Object Rotation"

    limits: bpy.props.IntProperty(default=0)  # not 'limits ='
    _timer = None
    original_rotation = [0, 0, 0]

    def modal(self, context, event):
        x_rot = context.window_manager.x_rotations
        y_rot = context.window_manager.y_rotations
        total_steps = x_rot * (2*y_rot + 2)
        if event.type in {'RIGHTMOUSE', 'ESC'} or self.limits > total_steps:
            self.limits = 0
            self.cancel(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            subject = context.window_manager.objectselection_props
            bpy.ops.object.select_all(action='DESELECT')
            subject.select_set(True)
            bpy.context.view_layer.objects.active = subject

            rotation_steps = context.window_manager.x_rotations

            rotation_angle = 360

            centre = bpy.context.scene.cursor.location
            rot = [15, -15, -15, 15]
            y_rotation = rot[self.limits % 4]

            if not (self.limits % 4):
                bpy.ops.transform.rotate(
                    value=-1 * radians(rotation_angle/rotation_steps), center_override=centre, orient_type='GLOBAL')

            bpy.ops.transform.rotate(value=radians(
                y_rotation), orient_axis='Y', orient_type='LOCAL', center_override=centre)

            self.limits += 1
        return {'PASS_THROUGH'}

    def execute(self, context):

        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step=0.1, window=context.window)
        obj = context.window_manager.objectselection_props
        if self.limits == 0:
            self.original_rotation = obj.rotation_euler.copy()
            self.original_location = obj.location.copy()
        print(self.original_rotation)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        obj = context.window_manager.objectselection_props
        wm = context.window_manager
        print(self.original_rotation)
        obj.rotation_euler = self.original_rotation.copy()
        obj.location = self.original_location.copy()
        wm.event_timer_remove(self._timer)


class FixMaterial(bpy.types.Operator):

    """Fix backfaces on the material CHECK THIS WORKS BEFORE RENDERING"""
    bl_idname = "object.fix_material"
    bl_label = "Fix Object Material"

    def execute(self, context):
        # Report "Hello World" to the Info Area

        obj = context.window_manager.objectselection_props

        for child in obj.children:
            child.active_material.show_transparent_back = False

        self.report({'INFO'}, "Fixed material")

        return {'FINISHED'}


class AddHRDI(bpy.types.Operator):
    bl_idname = "object.addhdri"
    bl_label = "Set HDRI"
    bl_description = "Add a HDRI for rendering"
    bl_options = {"REGISTER"}

    def execute(self, context):
        scn = context.scene

        # Get the environment node tree of the current scene
        node_tree = scn.world.node_tree
        context.scene.render.film_transparent = True
        scn.world.use_nodes = True
        tree_nodes = node_tree.nodes

        # Clear all nodes
        tree_nodes.clear()

        # Add Background node
        node_background = tree_nodes.new(type='ShaderNodeBackground')

        # Add Environment Texture node
        node_environment = tree_nodes.new('ShaderNodeTexEnvironment')
        if not bpy.data.images.get("skate_park_4k.exr"):
            # Load and assign the image to the node property
            image_path = os.path.dirname(os.path.realpath(__file__))
            image_path = os.path.join(image_path, "skate_park_4k.exr")

            node_environment.image = bpy.data.images.load(
                image_path)  # Abs path
        else:
            node_environment.image = bpy.data.images.get("skate_park_4k.exr")
        node_environment.location = -300, 0

        # Add Output node
        node_output = tree_nodes.new(type='ShaderNodeOutputWorld')
        node_output.location = 200, 0

        # Link all nodes
        links = node_tree.links
        link = links.new(
            node_environment.outputs["Color"], node_background.inputs["Color"])
        link = links.new(
            node_background.outputs["Background"], node_output.inputs["Surface"])
        return {"FINISHED"}


class RenderWiki(bpy.types.Operator):

    """Render weapon to a format accepted by the Wiki"""
    bl_idname = "object.render_wiki"
    bl_label = "Render to Wiki Image"
    bl_options = {'REGISTER'}

    def execute(self, context):

        context.scene.render.resolution_x = context.window_manager.x_resolution
        context.scene.render.resolution_y = context.window_manager.y_resolution
        directory = context.window_manager.output_folder
        if not directory:
            self.report({'ERROR_INVALID_INPUT'},
                        'Please select an output folder')
            return {'CANCELLED'}
        directory = bpy.path.abspath(directory)
        subject = context.window_manager.objectselection_props
        bpy.ops.object.select_all(action='DESELECT')
        subject.select_set(True)
        bpy.context.view_layer.objects.active = subject

        rotation_steps = context.window_manager.x_rotations

        # TODO customise rotation angle, vertical steps
        rotation_angle = 360

        original_rotation = subject.rotation_euler
        centre = bpy.context.scene.cursor.location
        output_file_pattern_string = 'render%d%d.jpg'
        if not os.path.exists(os.path.join(directory, "tmp")):
            os.mkdir(os.path.join(directory, "tmp"))
        for f in os.listdir(os.path.join(directory, "tmp")):
            os.remove(os.path.join(os.path.join(directory, "tmp"), f))
        for step in range(0, rotation_steps):

            bpy.ops.transform.rotate(
                value=-1 * radians(rotation_angle/rotation_steps), center_override=centre, orient_type='GLOBAL')
            rot = [15, -15, -15]
            for i in range(3):
                bpy.ops.transform.rotate(value=radians(
                    rot[i]), orient_axis='Y', orient_type='LOCAL', center_override=centre)

                bpy.context.scene.render.filepath = os.path.join(
                    os.path.join(directory, "tmp"), (output_file_pattern_string % (step, i)))
                bpy.ops.render.render(write_still=True)
            bpy.ops.transform.rotate(
                value=radians(15), orient_axis='Y', orient_type='LOCAL', center_override=centre)
        subject.rotation_euler = original_rotation
        bpy.context.scene.render.filepath = os.path.join(
            os.path.join(directory), "final.png")
        bpy.ops.render.render(write_still=True)
        files = os.listdir(os.path.join(directory, 'tmp'))
        files.sort(key=lambda f: int(re.sub('\D', '', f)))

        p = ImageProcessor(rotation_steps, 1)
        for i, filename in enumerate(files):
            print(filename)
            p.blend(os.path.join(directory, 'tmp', filename))

        file_format = str(context.window_manager.output_format)
        p.stitch_and_upload(directory, file_format)
        return {'FINISHED'}


# class AddEmission(bpy.types.Operator, ImportHelper):

#     bl_idname = "object.addemission"
#     bl_label = "Add Emission Shader"

#     filter_glob: StringProperty(
#         default='*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp',
#         options={'HIDDEN'}
#     )

#     some_boolean: BoolProperty(
#         name='Do a thing',
#         description='Do a thing with the file you\'ve selected',
#         default=True,
#     )

#     def execute(self, context):
#         """Do something with the selected file(s)."""

#         filename, extension = os.path.splitext(self.filepath)

#         print('Selected file:', self.filepath)
#         print('File name:', filename)
#         print('File extension:', extension)
#         print('Some Boolean:', self.some_boolean)

#         obj = context.window_manager.objectselection_props
#         # Get the environment node tree of the current scene
#         node_tree = obj.active_material.node_tree
#         tree_nodes = node_tree.nodes

#         # Add Background node
#         node_emission = tree_nodes.new(type='ShaderNodeTexImage')

#         # Add Environment Texture node
#         node_mixRGB = tree_nodes.new('ShaderNodeMixRGB')
#         # if not bpy.data.images.get("skate_park_4k.exr"):
#         # Load and assign the image to the node property

#         node_emission.image = bpy.data.images.load(
#             self.filepath)  # Abs path
#         # else:
#         #     node_environment.image = bpy.data.images.get("skate_park_4k.exr")
#         node_emission.location = -300, 0
#         node_mixRGB.location = -200, 0
#         for node in tree_nodes:
#             print(node.name)
#             print(node.idname)

#         links = node_tree.links
#         link = links.new(
#             node_emission.outputs["Color"], node_mixRGB.inputs["Fac"])
#         return {'FINISHED'}

#         # Link all nodes

#         link = links.new(
#             node_mixRGB.outputs["Color"], node_output.inputs["Surface"])
#         return {"FINISHED"}
