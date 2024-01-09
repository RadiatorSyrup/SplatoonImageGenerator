import bpy
import subprocess
import sys
from collections import namedtuple
from bpy.props import (
    PointerProperty,
    StringProperty,
    BoolProperty,
    IntProperty
)

from . splt_panel import SPLT_PT_Panel, SPLT_PT_warning_panel
from . splt_ops import *
from bpy.app.handlers import persistent

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "SplatoonImageGenerator",
    "author": "Radiator Syrup",
    "description": "An addon to automate the rendering of Splatoon weapon models into 2d images",
    "blender": (2, 80, 0),
    "version": (1, 1, 0),
    "location": "",
    "warning": "",
    "category": "Generic"
}

Dependency = namedtuple("Dependency", ["module", "package", "name"])

# Declare all modules that this add-on depends on. The package and (global) name can be set to None,
# if they are equal to the module name. See import_module and ensure_and_import_module for the
# explanation of the arguments.
dependencies = (Dependency(module="PIL", package="Pillow", name=None),
                Dependency(module="numpy", package=None, name=None))


def install_pip():
    """
    Installs pip if not already present. Please note that ensurepip.bootstrap() also calls pip, which adds the
    environment variable PIP_REQ_TRACKER. After ensurepip.bootstrap() finishes execution, the directory doesn't exist
    anymore. However, when subprocess is used to call pip, in order to install a package, the environment variables
    still contain PIP_REQ_TRACKER with the now nonexistent path. This is a problem since pip checks if PIP_REQ_TRACKER
    is set and if it is, attempts to use it as temp directory. This would result in an error because the
    directory can't be found. Therefore, PIP_REQ_TRACKER needs to be removed from environment variables.
    :return:
    """

    try:
        # Check if pip is already installed
        subprocess.run([sys.executable, "-m",
                       "pip", "--version"], check=True)
    except subprocess.CalledProcessError:
        import os
        import ensurepip

        ensurepip.bootstrap()
        os.environ.pop("PIP_REQ_TRACKER", None)


def import_module(module_name, global_name=None):
    """
    Import a module.
    :param module_name: Module to import.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: ImportError and ModuleNotFoundError
    """
    import importlib

    if global_name is None:
        global_name = module_name

    # Attempt to import the module and assign it to globals dictionary. This allow to access the module under
    # the given name, just like the regular import would.
    globals()[global_name] = importlib.import_module(module_name)


def install_and_import_module(module_name, package_name=None, global_name=None):
    """
    Installs the package through pip and attempts to import the installed module.
    :param module_name: Module to import.
    :param package_name: (Optional) Name of the package that needs to be installed. If None it is assumed to be equal
       to the module_name.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: subprocess.CalledProcessError and ImportError
    """
    import importlib

    if package_name is None:
        package_name = module_name

    if global_name is None:
        global_name = module_name

    # Try to install the package. This may fail with subprocess.CalledProcessError
    subprocess.run([sys.executable, "-m", "pip",
                   "install", package_name], check=True)

    # The installation succeeded, attempt to import the module again
    import_module(module_name, global_name)


class SPLT_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "splatoon.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = ("Downloads and installs the required python packages for this add-on. "
                      "Internet connection is required. Blender may have to be started with "
                      "elevated permissions in order to install the package")
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(self, context):
        # Deactivate when dependencies have been installed
        return not context.window_manager.dependencies_installed

    def execute(self, context):
        print(sys.executable)
        try:
            install_pip()
            for dependency in dependencies:
                install_and_import_module(module_name=dependency.module,
                                          package_name=dependency.package,
                                          global_name=dependency.name)
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        context.window_manager.dependencies_installed = True

        # Register the panels, operators, etc. since dependencies are installed
        for cls in classes:
            bpy.utils.register_class(cls)

        return {"FINISHED"}


class SPLT_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.operator(
            SPLT_OT_install_dependencies.bl_idname, icon="CONSOLE")


preference_classes = (SPLT_PT_warning_panel,
                      SPLT_OT_install_dependencies,
                      SPLT_preferences)
classes = (RotateAndScale, PositionCamera,
           PositionModel, FixMaterial, FixLights, RenderWiki, CheckRotateModel, SPLT_PT_Panel)

dependencies_installed = False


def set_x_resolution(self, context):
    if not self:
        self = context.window_manager
    context.scene.render.resolution_x = self.x_resolution


def set_y_resolution(self, context):
    if not self:
        self = context.window_manager
    context.scene.render.resolution_y = self.y_resolution


@persistent
def load_handler(dummy):
    # set_x_resolution(None, bpy.context)
    # set_y_resolution(None, bpy.context)
    pass


def register():
    global dependencies_installed
    dependencies_installed = False

    for cls in preference_classes:
        bpy.utils.register_class(cls)

    try:
        for dependency in dependencies:
            import_module(module_name=dependency.module,
                          global_name=dependency.name)
        dependencies_installed = True
    except ModuleNotFoundError as e:
        print(e)
        # Don't register other panels, operators etc.
        pass

    if(dependencies_installed):
        for cls in classes:
            bpy.utils.register_class(cls)

    # bpy.utils.register_class(SPLT_PT_Panel)

    mode_options = [
        ("JPEG", "JPEG", '', 'JPEG', 0),
        ("PNG", "PNG", '', 'PNG', 1),

    ]

    bpy.types.WindowManager.output_format = bpy.props.EnumProperty(
        items=mode_options,
        description="File Format",
        default=1,
        name="Output Format"
    )

    bpy.types.WindowManager.objectselection_props = PointerProperty(
        name="Base armature",
        type=bpy.types.Object
    )
    bpy.types.WindowManager.x_rotations = IntProperty(
        name="X Rotations",
        default=36
    )
    bpy.types.WindowManager.y_rotations = IntProperty(
        name="Y Rotations",
        default=1
    )
    bpy.types.WindowManager.x_resolution = IntProperty(
        name="X Resolution",
        default=296,
        update=set_x_resolution
    )
    bpy.types.WindowManager.y_resolution = IntProperty(
        name="Y Resolution",
        default=228,
        update=set_y_resolution
    )
    bpy.types.WindowManager.delete_tmp = BoolProperty(
        name="Don't keep temporary files",
        default=True
    )
    bpy.types.WindowManager.delete_preview = BoolProperty(
        name="Don't create preview image",
        default=True
    )
    bpy.types.WindowManager.output_folder = StringProperty(
        name="Output Folder",
        description="Path to Directory",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )

    bpy.types.WindowManager.dependencies_installed = BoolProperty(
        name="Dependencies installed",
        default=dependencies_installed

    )

    bpy.app.handlers.load_post.append(load_handler)


def unregister():
    try:
        for cls in preference_classes:
            bpy.utils.unregister_class(cls)

        if dependencies_installed:
            for cls in classes:
                bpy.utils.unregister_class(cls)
    except RuntimeError:
        pass

    del bpy.types.WindowManager.objectselection_props
    del bpy.types.WindowManager.x_rotations
    del bpy.types.WindowManager.y_rotations
    del bpy.types.WindowManager.output_folder
    del bpy.types.WindowManager.x_resolution
    del bpy.types.WindowManager.y_resolution
    del bpy.types.WindowManager.dependencies_installed
    bpy.app.handlers.load_post.remove(load_handler)
