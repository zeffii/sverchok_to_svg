import os
import re
import math
import bpy
import sverchok
from sverchok.utils.sv_node_utils import recursive_framed_location_finder as absloc
from dataclasses import dataclass

# for prettyprint xml there is only one sane solution:
# from sverchok.utils.pip_utils import install_package
# install_package("lxml")

from lxml import etree as et   

@dataclass
class NodeProxy():
    name: str
    label: str
    abs_location: tuple
    width: float
    inputs: dict
    outputs: dict


nt = bpy.data.node_groups['NodeTree']
nt_dict = {}
bbox = [[None, None], [None, None]]
def generate_bbox(x, y):
    bbox[0][0] = x if not bbox[0][0] else min(bbox[0][0], x)
    bbox[0][1] = x if not bbox[0][1] else max(bbox[0][1], x)
    bbox[1][0] = y if not bbox[1][0] else min(bbox[1][0], y)
    bbox[1][1] = y if not bbox[1][1] else max(bbox[1][1], y)

for n in nt.nodes:
    if n.bl_idname in {'NodeReroute', 'NodeFrame'}:
        outputs, inputs = {}, {}
    else:
        inputs = {s.name: (s.index, s.color) for s in n.inputs if not (s.hide or not s.enabled)} 
        outputs = {s.name: (s.index, s.color) for s in n.outputs if not (s.hide or not s.enabled)}
    
    x, y = absloc(n, n.location)
    generate_bbox(x, y)
    nt_dict[n.name] = NodeProxy(n.name, n.label, (int(x), int(y)), n.width, inputs, outputs)

bw = abs(bbox[0][1] - bbox[0][0]) + 20
bh = abs(bbox[1][1] - bbox[1][0]) + 20
print(bw, bh)

for n, k in nt_dict.items():
    k.abs_location = k.abs_location[0], bh - k.abs_location[1]


doc = et.Element('svg', width=str(bw*2), height=str(bh*2), version='1.1', xmlns='http://www.w3.org/2000/svg')
gdoc = et.SubElement(doc, "g", transform=f"translate({430}, {0})")
ldoc = et.SubElement(doc, "g", transform=f"translate({430}, {0})", style="stroke-width: 3.0;")

for k, v in nt_dict.items():
    g = et.SubElement(gdoc, "g", transform=f"translate{v.abs_location}")
    node_height = (max(len(v.inputs), len(v.outputs)) * 15)
    m = et.SubElement(g, "rect", width=str(v.width), height=f"{node_height-5}", fill='rgb(74, 177, 231)')
    t = et.SubElement(g, "text", fill="#333", y="-2", x="3")
    t.text = v.name

    sog = et.SubElement(g, "g", width="400", height="200")
    for idx, (socket_name, socket) in enumerate(v.inputs.items()):
        rgb = f"rgb{tuple(int(i*255) for i in socket[1][:3])}"
        ypos = f"{idx*15}"
        et.SubElement(sog, "circle", r="5", cy=ypos, fill=rgb, id=f"index_{idx}")
    for idx, (socket_name, socket) in enumerate(v.outputs.items()):
        rgb = f"rgb{tuple(int(i*255) for i in socket[1][:3])}"
        ypos = f"{idx*15}"
        et.SubElement(sog, "circle", r="5", cx=str(v.width), cy=ypos, fill=rgb, id=f"index_{idx}")    

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
    #absloc(n1, n1.location), absloc(n2, n2.location)

    # y1 and y2 should be offset depending on the visible socket indices. using info from s1 and s2
    y1_offset = calculate_offset(n1, s1, n1.outputs)
    y2_offset = calculate_offset(n2, s2, n2.inputs)

    xdist = min((x2 - x1), 40)
    ctrl_1 = int(x1) + n1.width + xdist,              int(y1) + y1_offset
    knot_1 = int(x1) + n1.width + socket_distance,    int(y1) + y1_offset
    knot_2 = int(x2) - socket_distance,               int(y2) + y2_offset
    ctrl_2 = int(x2) - xdist,                         int(y2) + y2_offset

    dpath = re.sub("\(|\)", "", f"M{knot_1} C{ctrl_1} {ctrl_2} {knot_2}")
    path = et.SubElement(ldoc, "path", d=dpath, stroke="#333", fill="transparent") 


svg_filename = "wooooop"
svg_path = os.path.join(bpy.path.abspath('//'), svg_filename + '.svg')
with open(svg_path, 'w') as f:
    f.write('\n\n')
    f.write(f"<!--{bbox}-->\n")
    f.write(et.tostring(doc, pretty_print=True).decode())
