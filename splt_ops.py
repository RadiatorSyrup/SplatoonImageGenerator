import re
import bpy
import shutil
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from math import radians, degrees, atan
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
                        "You need choose the armature before")
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
        if context.window_manager.objectselection_props == None:
            self.report({"WARNING"}, "You need choose the armature before")
            return {'CANCELLED'}
        if context.window_manager.game_type == 'noGame':
            self.report({"WARNING"}, "You need choose a game before")
            return {'CANCELLED'}
        
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

        if context.window_manager.game_type == 'splat2' or context.window_manager.game_type == 'splat3':
            bpy.ops.transform.translate(
                value=(0.0, 0.0, 10.0), orient_type='LOCAL')
        elif context.window_manager.game_type == 'acnh':
            bpy.ops.transform.translate(
                value=(0.0, 7.5, 10.0), orient_type='LOCAL')
            height = bpy.context.scene.camera.location.z
            base = bpy.context.scene.camera.location.y
            angle = degrees(atan(height / base)) + 90
            bpy.context.scene.camera.rotation_euler = [radians(angle), 0, 0]
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


class FixFaces(bpy.types.Operator):

    """Fix backfaces on the material CHECK THIS WORKS BEFORE RENDERING"""
    bl_idname = "object.fix_faces"
    bl_label = "Fix faces orientation"

    def execute(self, context):
        # Report "Hello World" to the Info Area

        obj = context.window_manager.objectselection_props

        for child in obj.children:
            child.active_material.show_transparent_back = False

        self.report({'INFO'}, "Fixed material")

        return {'FINISHED'}

class AddHDRI(bpy.types.Operator):
    bl_idname = "object.add_hdri"
    bl_label = "Add HDRI"
    bl_description = "Add the HDRI recommended for the selected game"
    bl_options = {"REGISTER"}

    def execute(self, context):
        scn = context.scene
        if context.window_manager.game_type == 'noGame':
            self.report({"WARNING"}, "You need choose a game before")
            return {'CANCELLED'}
        
        game_type = context.window_manager.game_type
        config_file_path = os.path.join(os.path.dirname(__file__), "games", f"{game_type}.py")
        if not os.path.exists(config_file_path):
            self.report({"WARNING"}, f"The configuration file for {game_type} doesn't exist")
            return {"CANCELLED"}
        
        # Get the environment node tree of the current scene
        node_tree = scn.world.node_tree
        context.scene.render.film_transparent = True
        scn.world.use_nodes = True
        tree_nodes = node_tree.nodes
        # Clear all nodes
        tree_nodes.clear()
        
        # Add Background node
        node_background = tree_nodes.new(type='ShaderNodeBackground')
        node_tree = scn.world.node_tree
        context = bpy.context
        # Import configure_hdri dynamically based on the selected game
        if game_type == 'splat2':
            from .games.splat2 import configure_hdri
        if game_type == 'splat3':
            from .games.splat3 import configure_hdri
        if game_type == 'acnh':
            from .games.acnh import configure_hdri
        if game_type == 'acnl':
            from .games.acnl import configure_hdri
        
        # Call configure_hdri function
        configure_hdri(context, node_tree, tree_nodes, node_background)

        return {'FINISHED'}
        

def configure_hdri_for_game(context):
    configure_common_hdri(context)

class FixLights(bpy.types.Operator):
    bl_idname = "object.fix_lights"
    bl_label = "Fix Lights"
    bl_description = "Delete all lights and add two prefabricated lights for rendering"
    bl_options = {"REGISTER"}

    def execute(self, context):
        scn = context.scene

        if context.window_manager.game_type == 'noGame':
            self.report({"WARNING"}, "You need choose a game before")
            return {'CANCELLED'}
            
        game_type = context.window_manager.game_type
        config_file_path = os.path.join(os.path.dirname(__file__), "games", f"{game_type}.py")
        if not os.path.exists(config_file_path):
            self.report({"WARNING"}, f"The configuration file for {game_type} doesn't exist")
            return {"CANCELLED"}
        
        # Save previous selected objects/collections
        previous_active_collection = bpy.context.view_layer.active_layer_collection
        selected_object = bpy.context.active_object
        
        # Delete all lights
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='LIGHT')
        bpy.ops.object.delete()

        # Create "Basis" collection
        basis_collection = bpy.data.collections.get("Basis")
        if not basis_collection:
            basis_collection = bpy.data.collections.new("Basis")
            bpy.context.scene.collection.children.link(basis_collection)
        
        # Import configure_lights dynamically based on the selected game
        if game_type == 'splat2':
            from .games.splat2 import configure_lights
        if game_type == 'splat3':
            from .games.splat3 import configure_lights
        if game_type == 'acnh':
            from .games.acnh import configure_lights
        if game_type == 'acnl':
            from .games.acnl import configure_lights
        
        # Call configure_lights function
        configure_lights(basis_collection)
        
        # Back to object selected
        if previous_active_collection:
            bpy.context.view_layer.active_layer_collection = previous_active_collection

        if selected_object:
            try:
                selected_object.select_set(True)
                bpy.context.view_layer.objects.active = selected_object
            except ReferenceError:
                pass
        return {"FINISHED"}


class RenderWiki(bpy.types.Operator):
    bl_idname = "object.render_wiki"
    bl_label = "Render to Wiki Image"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if not context.window_manager.objectselection_props:
            self.report({'ERROR_INVALID_INPUT'},
                        'You need to specify the armature')
            return {'CANCELLED'}

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
        output_file_pattern_string = 'render%d%d.png'
        
        file_format="PNG"
        
        tmp_folder_base = os.path.join(directory, "tmp")
        preview_file_base = os.path.join(directory, "preview")
        output_file_base = os.path.join(directory, "rendered")
        rendered_file_base = os.path.join(directory, "renderedoffsets")
        counter = 1
        if not context.window_manager.overwrite_files:
            while True:
                tmp_folder = f"{tmp_folder_base}{counter}"
                preview_file = f"{preview_file_base}{counter}.png"
                output_file = f"{output_file_base}{counter}.{file_format.lower()}"
                rendered_file = f"{rendered_file_base}{counter}.txt"
                
                if not os.path.exists(tmp_folder) and not os.path.exists(preview_file) and not os.path.exists(output_file) and not os.path.exists(rendered_file):
                    break
                else:
                    counter += 1
        else:
            counter = context.window_manager.number_overwrite
            tmp_folder = f"{tmp_folder_base}{counter}"
            preview_file = f"{preview_file_base}{counter}.png"
            output_file = f"{output_file_base}{counter}.{file_format.lower()}"
            rendered_file = f"{rendered_file_base}{counter}.txt"
            
            if os.path.exists(tmp_folder):
                shutil.rmtree(tmp_folder)
            if os.path.exists(preview_file):
                os.remove(preview_file)
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(rendered_file):
                os.remove(rendered_file)
        
        final_counter = counter
        os.mkdir(tmp_folder)

        for step in range(0, rotation_steps):
            bpy.ops.transform.rotate(
                value=-1 * radians(rotation_angle/rotation_steps), center_override=centre, orient_type='GLOBAL')
            rot = [15, -15, -15]
            for i in range(3):
                bpy.ops.transform.rotate(value=radians(
                    rot[i]), orient_axis='Y', orient_type='LOCAL', center_override=centre)

                bpy.context.scene.render.filepath = os.path.join(
                    tmp_folder, (output_file_pattern_string % (step, i)))
                bpy.ops.render.render(write_still=True)

            bpy.ops.transform.rotate(
                value=radians(15), orient_axis='Y', orient_type='LOCAL', center_override=centre)

        subject.rotation_euler = original_rotation
        bpy.context.scene.render.filepath = preview_file
        bpy.ops.render.render(write_still=True)
        files = os.listdir(tmp_folder)
        files.sort(key=lambda f: int(re.sub('\D', '', f)))

        p = ImageProcessor(rotation_steps, 1, final_counter, context)
        for i, filename in enumerate(files):
            print(filename)
            p.blend(os.path.join(tmp_folder, filename))

        file_format = str(context.window_manager.output_format)
        p.stitch_and_upload(directory, file_format)

        if not context.window_manager.delete_tmp:
            if os.path.exists(tmp_folder):
                shutil.rmtree(tmp_folder)

        if not context.window_manager.delete_preview:
            if os.path.exists(preview_file):
                os.remove(preview_file)

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
#         # if not bpy.data.images.get("HDRIHaven_Parking.hdr"):
#         # Load and assign the image to the node property

#         node_emission.image = bpy.data.images.load(
#             self.filepath)  # Abs path
#         # else:
#         #     node_environment.image = bpy.data.images.get("HDRIHaven_Parking.hdr")
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
