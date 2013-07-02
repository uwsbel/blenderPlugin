Format for the data files for the blender plugin.

General Notes:
    All values should be separated by commas and there should be no 
    space characters anywhere in the file. 


Each line will represent one object, and will be of this format:

    Group, Object ID, x_pos, y_pos, z_pos, quat_w, quat_x, quat_y, quat_z,
    object_type, extra_params

Group: An identifier to tell what objects it is related to. When 
applying materials and colors to proxy objects in blender, all members 
of the group will have the same material/color applied to them.
    Note: Group names should be completely lowercase. No distinction will
        be made between different cased group names.

Object ID: a number that will identify each unique object

x_pos, y_pos, z_pos: x,y,z coorinates of the object

quat_w, quat_x, quat_y, quat_z: orientation of the object using quaternions

object_type: A string representing the type of the object
    ex. "sphere", "cube", "ellipsoid"...
    Note: The object_type should always be completely lowercase.

extra_params: Any other parameters needed to define the shape of the 
	object. The number of these parameters will depend on the value of 
	object_type.
    ex. an object_type of "sphere" would require one extra parameter for 
			the radius
        an object_type of "cube" would require one extra parameter for 
			the side length
        an object_type of "ellipsoid" would require 3 additional 
			parameters, the length, width, and height of the ellipsoid
        an object_type of "Cylinder" requires 2 additional params, 
			the radius, and the hight.

EXAMPLE: example.dat
//////////////////////////////////////////////////////////////////////////////
g1,1,0,0,0,90,0,0,sphere,1.0
g1,2,5,0,0,90,0,0,sphere,0.5
g2,3,-5,0,0,0,90,0,cube,0.5
//////////////////////////////////////////////////////////////////////////////

Data files will typically be much longer than this, but this is a perfectly 
valid data file. The first two objects will be of group "g1" spheres located 
at (0,0,0) and (5,0,0) with a radii of 1.0 and 0.5 respectively while a "g2" 
sphere will appear at (-5,0,0) with radius 0.5.   

Possible extensions to the file format:
-density, pressure, velocity for simulations that need them could 
	potentially become part of the extra_params if needed
-Currently object types must be simple primitives, can expand later to 
	cover meshes from .obj and the like
