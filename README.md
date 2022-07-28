# sverchok_to_svg

An exploration into the extent I can find the patience to interpret nodetree+drawbuttons of Blender Sverchok into an svg. 
nothing is certain, maybe.

## requirements

   ```console
   mathutils ( blender )
   numpy
   sverchok
   lxml
   ```

## usage

1. enable the addon just like any other addon.

2. then in TextEditor or BPY console, execute:

   ```python
   import sverchok_to_svg

   # this outputs the svg in the path of the current .blend ( .svg extension is added )
   sverchok_to_svg.create("NodeTree", SVGName="wollops4")

   # this lets you set the path exactly ( you must add .svg yourself)
   sverchok_to_svg.create("NodeTree", SVGPath="some/full/path/name.svg")

   # this outputs the lxml doc from the function, for further processing.
   from lxml import etree as et
   doc = sverchok_to_svg.create("NodeTree", AsDoc=True)
   print(et.tostring(doc, pretty_print=True).decode())

   ```
3. the file will be created in the same directory as the .blend file containing the current nodetree.

## interesting features of the code

this is a liteweight introduction to the following python modules

```console
- lxml      : for creating svg elements, stylesheet. A remarkable library.
- inspect   : for getting code-text of modules at runtime, this helps getting the code for the node draw_buttons
- dataclass : a convenient way to declare a class
- re        : (regex) for rewriting a string destined for svg path
- importlib : in blender while developing you want to be able to edit the python code and quickly see how it behaves
- numpy     : a little bit of linear algebra for gradients between two colors.

```

## license

no thanks
