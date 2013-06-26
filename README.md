The current revision of the script can render a full scene with the default 
positions for blender's lights and camera. In order to do this, run this command
in the directory in which you want the first frame.

blender -P ~/repos/blender-plugin/plugins/blender/plugin.py -o rendered -F JPEG -x 1 -f 1

Tested on blender 2.67 (sub 1) and likely requires at least a 2.6 version of blender.
