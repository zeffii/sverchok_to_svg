# sverchok_to_svg

An exploration into the extent I can find the patience to interpret nodetree+drawbuttons of Blender Sverchok into an svg. 
nothing is certain, maybe.

## usage

1. enable the addon just like any other addon.

2. then in TextEditor or BPY console, execute:
   ```python
   import sverchok_to_svg
   sverchok_to_svg.create("NodeTree", "some_svg_name")  # extension is added automatically
   ```
3. the file will be created in the same directory as the .blend file containing the current nodetree.

## license

no thanks
