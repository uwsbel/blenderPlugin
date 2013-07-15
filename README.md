**Installing the Plugin and Chrono::Render**
Requirements: blender 2.6x, python3, and pyyaml should all be installed on 
    the machine from which you will be running blender.

Note: this is written assuming you will run blender on a local machine
and then render on euler.

1. Clone the Chrono::Render repo by running 
    hg clone https://daphron@bitbucket.org/daphron/blender-plugin 

    from somewhere on euler.

This contains all the files needed to take the exported data from blender 
and create a nice render from it.

2. Copy the file plugin.py from euler to your local machine's blender
    addons folder by using the following command (execute on local machine)

    scp username@euler.msvc.wisc.edu:/path/to/blender-plugin/plugins/blender/plugin.py
    /path/to/blender/addons/folder/on/your/machine/chronorender_plugin.py

    On linux blender addons go in:
    /home/$user/.config/blender/$version/scripts/addons
    Windows XP:
    C:\Documents and Settings\%username%\Application Data\Blender Foundation\Blender\2.6x\scripts\addons
    Windows7:
    C:\Users\%username%\AppData\Roaming\Blender Foundation\Blender\2.6x\scripts\addons

3. Open up blender.
    Click on File->User Preferences->Addons 
    Then scroll down until you see "Import-Export: Chrono::Render plugin"
    Click the check box on the right side
    Click "Save User Settings" at the bottom of the page
    Congratulations, the plugin is now installed and ready for use

**Basic Use of the Blender Plugin**
The first thing to do is import a data file. To do this, click 
File->Import->Imports a Chrono render file

Then select the file you wish to import data from and click Import ChronoRender

(If the default cube is still there, select it, press "x", and click "Delete")

One of the things you can now do is add color to an object. To do so, select 
    the object and select the material menu on the right hand side. (Symbol is
    a sphere with two dark spots. About 1/3rd down the screen with a bunch of
    other symbols)

Under "Diffuse" there will be a colored bar. Click on it and select your color
    using the color wheel. You can do this for all objects.

In addition to colors, you can select the camera's position, rotation, and focal length
    inside blender. You can move and rotate the camera as normal and press f12
    to get a rough idea of what you will see when you render with renderman.
    
When done, click file->export->Exports chron render file and select where to
    export it to. 

Now you have 2 new files, the output file that you specified, and a file in
    the same directory called custom_camera.rib. 

Somewhere on euler, run:
    /path/to/blender-plugin/scripts/crender.py init

This creates a RENDERMAN directory. Now put you data file, the .yaml file you 
exported from blender, and the custom_camera.rib file inside this directory.

go into the RENDERMAN directory and run:
    /path/to/blender-plugin/scripts/crender.py render -m yourfile.yaml -r aqsis

It will then render your file and place an out.0.tif file in the /job/images folder

If you wish to render multiple frames or make a video, you will need to copy 
    all of the data files and use the "-f startframe endframe" flag.

    /path/to/blender-plugin/scripts/crender.py render -m yourfile.yaml -r aqsis -f 0 99

    will render 100 frames. To make these frames into a movie, just use the 
    cmovie.py script.

    /path/to/blender-plugin/scripts/cmovie.py a/lot/of/junk/RENDERMAN/job/images/out.00.tif movie.mp4

    and all your images will be turned into a video.


**File Format**
Each data file represents one frame of a simulation. Filenames must end in
    _#.dat.
    Ex. mydata_0.dat, mydata_1.dat, mydata_2.dat

Each line will represent one object, and will be of this format:

    Group, Object ID, x_pos, y_pos, z_pos, quat_w, quat_x, quat_y, quat_z,
    object_type, extra_params

Group: An identifier to tell what objects it is related to. When 
applying materials and colors to proxy objects in blender, all members 
of the group will have the same material/color applied to them. The one
exception is the group "individual". Every item in this group will be
visibile in blender and materials will have to be applied to each object
seperately.
    Note: Group names should be completely lowercase. No distinction will
        be made between different cased group names.
    Note: All members of a group MUST have the same object_type and parameters
        for that object (e.g. all spheres have same radius). Locations and 
        rotations may be different.

Object ID: a number that will identify each unique object

x_pos, y_pos, z_pos: x,y,z coorinates of the object


General Notes:
    All values should be separated by commas and there should be no 
    space characters anywhere in the file. Each file should end in .dat 

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
			parameters, the semi-principle axes a, b, and c.
        an object_type of "Cylinder" requires 2 additional params, 
			the radius, and the hight.

EXAMPLE: example.dat
//////////////////////////////////////////////////////////////////////////////
g1,1,0,0,0,0.707,0,-0.707,0,sphere,1.0
g1,2,5,0,0,0.707,0,-0.707,0,sphere,0.5
g2,3,-5,0,0,0.707,0,0,0.707,sphere,0.5
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

**What you can do**
-Apply colors to your objects and have those colors show when you render.

**What this plugin does NOT do (currently)**
-allow you to move, rotate, or size the objects. You can do this in blender but if
    you render with renderman your changes will NOT be applied. (Camera 
    location however, WILL be changed if you move it. ctrl-alt-0 is nice for 
    snapping the camera to your view point)
-allow you to save your changes partway through. You must import the file,
    apply materials and colors, and export it in ONE blender session.
-a full render with blender's "render" button.
