import bpy


class SPLT_PT_Panel_1(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_label = "Basic settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wiki Tools"

    def draw(self, context):
        layout = self.layout
        box1 = layout.box()
        box1.label(text="Game")
        box1.prop(context.window_manager, "game_type", text="")
        box2 = layout.box()
        box2.label(text="Base armature")
        box2.prop(context.window_manager, "objectselection_props", text="")
        box3 = layout.row()
        box3.label(text="Category")
        box3.prop(context.window_manager, "wiki_language", text="")

class SPLT_PT_Panel_2(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_label = "3D model"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wiki Tools"

    def draw(self, context):
        layout = self.layout
        
class SPLT_PT_Panel_2_1(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_parent_id = "SPLT_PT_Panel_2"
    bl_label = "Mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wiki Tools"
    bl_collapsed = False

    def draw(self, context):
        layout = self.layout
        layout.operator("object.rotate_and_scale", icon = "DRIVER_ROTATIONAL_DIFFERENCE")
        layout.operator("object.position_model", icon = "RESTRICT_SELECT_OFF")
        
class SPLT_PT_Panel_2_2(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_parent_id = "SPLT_PT_Panel_2"
    bl_label = "Textures"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wiki Tools"
    bl_collapsed = False

    def draw(self, context):
        layout = self.layout
        layout.operator("object.fix_faces", icon = "MODIFIER_DATA")

class SPLT_PT_Panel_3(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_label = "Camera"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wiki Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.position_camera", icon = "OUTLINER_OB_CAMERA")
        box1 = layout.box()
        box1.label(text="Model rotation")
        box1.prop(context.window_manager, "x_rotations", text="Rotations by lap")
        layout.operator("object.check_rotation", icon = "ORIENTATION_GIMBAL")
        box2 = layout.box()
        box2.label(text="File resolution")
        row2 = box2.row()
        row2.prop(context.window_manager, "x_resolution")
        row2.prop(context.window_manager, "y_resolution")

        
class SPLT_PT_Panel_4(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_label = "Environment"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wiki Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.add_hdri", icon = "MAT_SPHERE_SKY")
        layout.operator("object.fix_lights", icon = "OUTLINER_OB_LIGHT")
        
class SPLT_PT_Panel_5(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_label = "Output"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wiki Tools"

    def draw(self, context):
        layout = self.layout
        box1 = layout.box()
        box1.label(text="Output folder")
        box1.prop(context.window_manager, "output_folder", text="")
        box2 = layout.box()
        box2.label(text="Output format")
        box2.prop(context.window_manager, "output_format", text="")
        layout.operator("object.render_wiki", icon = "IMAGE_DATA")
        
class SPLT_PT_Panel_5_1(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_parent_id = "SPLT_PT_Panel_5"
    bl_label = "Advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wiki Tools"
    bl_collapsed = True

    def draw(self, context):
        layout = self.layout
        row1 = layout.row();
        row1.prop(context.window_manager, "overwrite_files" , text="Overwrite files with number")
        row1.prop(context.window_manager, "number_overwrite", text="")
        layout.prop(context.window_manager, "delete_preview", text="Save preview image")
        layout.prop(context.window_manager, "delete_tmp", text="Save temporary files")

class SPLT_PT_Panel_6(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_label = "Manual"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wiki Tools"
    bl_collapsed = True

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.url_open", text="Manual",
                     icon='HELP', emboss=True).url = "https://splatoonwiki.org/wiki/Inkipedia:3D_Models"

class SPLT_PT_warning_panel(bpy.types.Panel):
    bl_label = "Install Dependencies"
    bl_category = "Wiki Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(self, context):
        return not context.window_manager.dependencies_installed

    def draw(self, context):

        layout = self.layout

        lines = [f"Please install the missing dependencies for the PIL and numpy add-ons.",
                 f"1. Open the preferences (Edit > Preferences > Add-ons).",
                 f"2. Search for the Splatoon add-on.",
                 f"3. Open the details section of the add-on.",
                 f"4. Click on the Install button.",
                 f"   This will download and install the missing Python packages, if Blender has the required",
                 f"   permissions.",
                 f"",
                 f"If you're attempting to run the add-on from the text editor, you won't see the options described",
                 f"above. Please install the add-on properly through the preferences.",
                 f"1. Open the add-on preferences (Edit > Preferences > Add-ons).",
                 f"2. Press the \"Install\" button.",
                 f"3. Search for the add-on file.",
                 f"4. Confirm the selection by pressing the \"Install Add-on\" button in the file blayoutser."]

        for line in lines:
            layout.label(text=line)
