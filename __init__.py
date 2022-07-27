bl_info = {
    "name": "Sverchok to svg",
    "author": "zeffii",
    "version": (0, 0, 1),
    "blender": (2, 93, 0),
    "location": "Node Editor",
    "category": "Node",
    "description": "approximate SVG of your sverchok nodetree",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/zeffii/sverchok_to_svg/issues"
}


import importlib

if 'ng2svg_converter_writer' not in locals():
    importlib.import_module('.ng2svg_converter_writer')
else:
    importlib.reload(ng2svg_converter_writer)

create = ng2svg_converter_writer.create

"""
usage:

import sverchok_to_svg
sverchok_to_svg.create("NodeTree", "wollops4")
"""

def register(): pass
def unregister(): pass