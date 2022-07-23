import os
import re
import bpy
import sverchok
import numpy as np
from mathutils.geometry import interpolate_bezier as bezlerp
from sverchok.utils.sv_node_utils import recursive_framed_location_finder as absloc
from dataclasses import dataclass

# for prettyprint xml there is only one sane solution:
# from sverchok.utils.pip_utils import install_package
# install_package("lxml")

from lxml import etree as et   

nt = bpy.data.node_groups['NodeTree']
nt_dict = {}
bbox = [[None, None], [None, None]]

@dataclass
class NodeProxy():
    name: str
    label: str
    abs_location: tuple
    width: float
    color: tuple
    inputs: dict
    outputs: dict
    @property
    def x(self): return self.abs_location[0]
    @property
    def y(self): return self.abs_location[1]

def find_children(node):
    return [n.name for n in node.id_data.nodes if n.parent == node]

def absloc_int(n, loc):
    loc = absloc(n, loc)
    return int(loc[0]), int(loc[1])

def convert_rgb(a):
    return f"rgb{tuple(int(i*255) for i in a)}"

def get_component(value, component, func):
    return component if not value else func(value, component)

def as_ints(v):
    return (int(v[0]), int(v[1]))

def clerp(A, B, num):
    def tween(A, B, by):
        return A[0]*(1-by)+B[0]*by, A[1]*(1-by)+B[1]*by, A[2]*(1-by)+B[2]*by
    floats = np.linspace(0.0, 1.0, num).tolist()
    return [tween(A, B, by) for by in floats]

class FrameBBox():
    def __init__(self):
        self.xmin, self.xmax, self.ymin, self.ymax = None, None, None, None

    def add(self, loc, w, h):
        x, y = loc
        #prin(f"{loc, w, h}")
        self.xmin = get_component(self.xmin, x, min)
        self.xmax = get_component(self.xmax, x + w, max)
        self.ymin = get_component(self.ymin, y, min)
        self.ymax = get_component(self.ymax, y + h, max)
        
    def get_box(self, padding=0):
        x = self.xmin - padding
        y = self.ymin - padding
        width = (self.xmax - self.xmin) + (2 * padding) 
        height = (self.ymax - self.ymin) + (2 * padding)
        return x, y, int(width), int(height)

def generate_bbox(x, y):
    bbox[0][0] = get_component(bbox[0][0], x, min)
    bbox[0][1] = get_component(bbox[0][1], x, max)
    bbox[1][0] = get_component(bbox[1][0], y, min)
    bbox[1][1] = get_component(bbox[1][1], y, max)

def gather_socket_data(sockets):
    return {s.name: (s.index, s.color) for s in sockets if not (s.hide or not s.enabled)}
    
for n in nt.nodes:
    if n.bl_idname in {'NodeReroute', 'NodeFrame'}:
        outputs, inputs = {}, {}
        color = n.color if n.bl_idname == "NodeFrame" else [1.0, 0.91764, 0]
    else:
        inputs = gather_socket_data(n.inputs)
        outputs = gather_socket_data(n.outputs)
        color = n.color
    
    x, y = absloc_int(n, n.location[:])
    # not sure wtf is going on with frame nodes but there seems to be an offset incorrectly applied.
    # so for the timebeing, i'm dropping them from the main-frame-bounding-box
    if not n.bl_idname == "NodeFrame":
        generate_bbox(x, y)
    nt_dict[n.name] = NodeProxy(n.name, n.label, (x, y), n.width, color, inputs, outputs)

bw = abs(bbox[0][1] - bbox[0][0])
bh = abs(bbox[1][1] - bbox[1][0])

for n, k in nt_dict.items():
    # k.abs_location = k.abs_location[0] - bbox[0][0], bh - (k.abs_location[1] - bbox[1][0])
    k.abs_location = k.x - bbox[0][0], bh - (k.y - bbox[1][0])


doc = et.Element('svg', width=str(bw*2), height=str(bh*2), version='1.1', xmlns='http://www.w3.org/2000/svg')

css_stylesheet = """
.socket#verts {
    stroke: #222;
}

"""

style_sheet = et.SubElement(doc, "style")
style_sheet.text = css_stylesheet
 
tree = et.SubElement(doc, "g", transform=f"translate({30}, {30})", id="tree")
fdoc = et.SubElement(tree, "g", id="frames", style="stroke-width: 1.0;")
gdoc = et.SubElement(tree, "g", id="node ui")
xdoc = et.SubElement(tree, "g", id="origin", style="stroke-width: 1.0;")
ldoc = et.SubElement(tree, "g", id="link noodles", style="stroke-width: 3.0;")
origin = et.SubElement(xdoc, "path", d=f"M-20,0 L20,0 M0,-20 L0,20", stroke="#333")

# Step 1: draw Nodes, Names and Sockets
node_heights = {}
for k, v in nt_dict.items():
    node = nt.nodes.get(v.name) 
    bl_idname = node.bl_idname
    if bl_idname == "NodeFrame": continue

    g = et.SubElement(gdoc, "g", transform=f"translate{v.abs_location}", id=f"NODE:{node.name}")
    
    if bl_idname == "NodeReroute":
        m = et.SubElement(g, "circle", r="10", cx=str(v.width/2), fill=convert_rgb(v.color[:3]))
        continue
    else:
        node_height = (max(len(v.inputs), len(v.outputs)) * 15)
        node_heights[node.name] = node_height
        m = et.SubElement(g, "rect", width=str(v.width), y="-9", height=f"{node_height+1}", fill=convert_rgb(v.color[:3]))
        t = et.SubElement(g, "text", fill="#333", y="-12", x="7", **{"font-size":"11"})
        t.text = v.name
    
    sog = et.SubElement(g, "g", width="400", height="200")
    for idx, (socket_name, socket) in enumerate(v.inputs.items()):
        et.SubElement(sog, "circle", r="5", cy=f"{idx*15}", fill=convert_rgb(socket[1][:3]), id=f"index_{idx}")
        t = et.SubElement(sog, "text", fill="#fff", y=f"{(idx*15)+3}", x="7", **{"font-size":"10"})
        t.text = socket_name

    for idx, (socket_name, socket) in enumerate(v.outputs.items()):
        et.SubElement(sog, "circle", r="5", cx=str(v.width), cy=f"{idx*15}", fill=convert_rgb(socket[1][:3]), id=f"index_{idx}")    
        t = et.SubElement(sog, "text", fill="#fff", y=f"{(idx*15)+3}", x=str(v.width-6), **{"text-anchor": "end", "font-size":"10"})
        t.text = socket_name

# Step 2: draw nodeframes on lower layer, using node dimensions generated in step 1
for k, v in nt_dict.items():
    node = nt.nodes.get(v.name) 
    if not node.bl_idname == "NodeFrame": continue

    # calculate bounding frame
    box = FrameBBox()
    children = find_children(node)
    if children:
        for name in children:
            child_node = nt_dict[name] 
            box.add(child_node.abs_location, child_node.width, node_heights[name])
        _x, _y, _w, _h = box.get_box(padding=20)
    else:
        _x, _y, _w, _h = v.x, v.y, node.width, node.height
    params = dict(x=str(_x), y=str(_y-8), width=str(_w), height=str(_h)) | {"id": v.name, "class": "FRAME"}
    m = et.SubElement(fdoc, "rect", fill=convert_rgb(v.color[:3]), style="opacity: 0.3;", **params)

# prin("------")

calculated_offsets = {}
def calculate_offset(node, socket, sockets=None):
    if socket.bl_idname == "NodeReroute": return 0
    if socket in calculated_offsets:
        return calculated_offsets[socket]

    vis_idx = 0
    for idx, s in enumerate(sockets):
        if s.hide or not s.enabled:
            continue
        if s.is_linked and socket == s:
            offset = vis_idx * 15
            break
        vis_idx += 1
    
    return offset


socket_distance = 5
for link in nt.links:
    n1, s1, n2, s2 = link.from_node, link.from_socket, link.to_node, link.to_socket
    (x1, y1), (x2, y2) = nt_dict[n1.name].abs_location, nt_dict[n2.name].abs_location

    # y1 and y2 should be offset depending on the visible socket indices. using info from s1 and s2
    y1_offset = calculate_offset(n1, s1, n1.outputs)
    y2_offset = calculate_offset(n2, s2, n2.inputs)

    xdist = min((x2 - x1), 40)
    ctrl_1 = int(x1 + n1.width + xdist),              int(y1) + y1_offset
    knot_1 = int(x1 + n1.width + socket_distance),    int(y1) + y1_offset
    knot_2 = int(x2) - socket_distance,               int(y2) + y2_offset
    ctrl_2 = int(x2) - xdist,                         int(y2) + y2_offset

    dstroke = "#333"
    dpath = re.sub("\(|\)", "", f"M{knot_1} C{ctrl_1} {ctrl_2} {knot_2}")
    
    mode = "transition"
    if (s1.bl_idname == s2.bl_idname) or (n2.bl_idname == "NodeReroute"):
        dstroke = convert_rgb(s1.color[:3])
        mode = "take from destination"
    elif n1.bl_idname == "NodeReroute":
        if n1.inputs[0].is_linked:
            dstroke = convert_rgb(s2.color[:3])
            mode = "take from destination"

    if mode == "take from destination":
        path = et.SubElement(ldoc, "path", d=dpath, stroke=dstroke, fill="transparent") 
    else:
        # draw the bezier manually using 15 segments and transition their color
        arc_verts = bezlerp(knot_1, ctrl_1, ctrl_2, knot_2, 15)
        
        if not n1.inputs[0].is_linked:
            start_color = [1.0, 0.91764, 0]
        else:
            start_color = s1.color[:]    
            
        gradient = clerp(start_color, s2.color[:], len(arc_verts)-1)
        bezier = et.SubElement(ldoc, "g", fill="transparent", **{"class": "gradient_bezier"})
        for idx in range(len(arc_verts)-1):
            idx2 = idx+1
            v1, v2 = arc_verts[idx], arc_verts[idx2]
            v1, v2 = as_ints(v1), as_ints(v2)
            dpath = re.sub("\(|\)", "", f"M{v1[:]} L{v2[:]}")
            stroke_color = convert_rgb(gradient[idx])
            et.SubElement(bezier, "path", d=dpath, stroke=stroke_color) 

svg_filename = "wooooop"
svg_path = os.path.join(bpy.path.abspath('//'), svg_filename + '.svg')
with open(svg_path, 'w') as f:
    f.write(f"<!--{bbox}-->\n")
    f.write(et.tostring(doc, pretty_print=True).decode())
