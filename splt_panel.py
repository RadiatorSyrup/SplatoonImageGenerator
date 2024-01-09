import bpy


class SPLT_PT_Panel(bpy.types.Panel):
    # bl_idname = "splatoonpanel"
    bl_label = "Splatoon Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Splatoon Tools"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Basic Settings")
        box.prop(context.window_manager, "objectselection_props")

        box.operator("object.rotate_and_scale")
        box.operator("object.position_model")
        box.operator("object.position_camera")
        box.operator("object.check_rotation")
        box.operator("object.fix_material")
        box.operator("object.fix_lights")

        layout.separator()

        box = layout.box()
        box.label(text="Advanced Settings")

        box.prop(context.window_manager, "x_rotations")

        row = box.row()
        row.prop(context.window_manager, "x_resolution")
        row.prop(context.window_manager, "y_resolution")
        box.prop(context.window_manager, "output_format")

        layout.separator()
        box = layout.box()
        box.prop(context.window_manager, "output_folder")
        box.prop(context.window_manager, "delete_tmp", text="Don't keep temporary files")
        box.prop(context.window_manager, "delete_preview", text="Don't create preview image")
        box.operator("object.render_wiki")
        layout.separator()

        box = layout.box()

        box.operator("wm.url_open", text="Manual",
                     icon='HELP', emboss=True).url = "https://splatoonwiki.org/wiki/Inkipedia:3D_Models"


class SPLT_PT_warning_panel(bpy.types.Panel):
    bl_label = "Install Dependencies"
    bl_category = "Splatoon Tools"
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
                 f"4. Confirm the selection by pressing the \"Install Add-on\" button in the file browser."]

        for line in lines:
            layout.label(text=line)
