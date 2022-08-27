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
    # previously i had just  `.ng2svg_converter_writer` in the import module on the next line.
    # but for some reason i started getting an error
    # TypeError: the 'package' argument is required to perform a relative import for ..
    importlib.import_module('sverchok_to_svg.ng2svg_converter_writer')
else:
    importlib.reload(ng2svg_converter_writer)

create = ng2svg_converter_writer.create

"""
usage:

import sverchok_to_svg

# this outputs the svg in the path of the current .blend ( .svg extension is added )
sverchok_to_svg.create("NodeTree", SVGName="wollops4")

# this lets you set the path exactly ( you must add .svg yourself)
sverchok_to_svg.create("NodeTree", SVGPath="some/full/path/name.svg")

# this outputs the lxml doc from the function, for further processing.
from lxml import etree as et
doc = sverchok_to_svg.create("NodeTree", AsDoc=True)
print(et.tostring(doc, pretty_print=True).decode())

"""

def register(): pass
def unregister(): pass