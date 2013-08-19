**Installing the Plugin and Chrono::Render**
Requirements: blender 2.6x, python3, and pyyaml should all be installed on 
    the machine from which you will be running blender.

The Short Way (requires access to euler):
1. Copy the stable version of the blender plugin from euler at
    /home/groups/sbel/rendering/chrono-render/plugins/blender
    put this file in the the proper place on your machine.

    On linux blender addons go in:
    /home/$user/.config/blender/$version/scripts/addons
    Windows XP:
    C:\Documents and Settings\%username%\Application Data\Blender Foundation\Blender\2.6x\scripts\addons
    Windows7:
    C:\Users\%username%\AppData\Roaming\Blender Foundation\Blender\2.6x\scripts\addons

2. Enable the blender plugin by opening blender and going to File -> User
        Preferences -> Addons and clicking the checkbox next to Import-Export:
        Chrono::Render plugin. Hit Save User Settings at the bottom and you
        are done!

The Long Way:
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

This creates a RENDERMAN directory. Now put the .yaml file you 
exported from blender, and the custom_camera.rib file inside this directory.
Put all of your data files inside the RENDERMAN/job/data directory


go into the RENDERMAN directory and run:
    /path/to/blender-plugin/scripts/crender.py update
    /path/to/blender-plugin/scripts/crender.py render -m yourfile.yaml -r aqsis

It will then render your file and place an out.0.tif file in the /job/images folder

If you wish to render multiple frames or make a video, you will need to copy 
    all of the data files and use the "-f startframe endframe" flag.

    /path/to/blender-plugin/scripts/crender.py render -m yourfile.yaml -r aqsis -f 0 99

    will render 100 frames. To make these frames into a movie, just use the 
    cmovie.py script.

    /path/to/blender-plugin/scripts/cmovie.py a/lot/of/junk/RENDERMAN/job/images/out.00.tif movie.mp4

    and all your images will be turned into a video.

**Submitting to the cluster for rendering**
The procedure for submitting a job to the cluster for rendering is almost exactly
the same as for rendering locally. Compare:

    For a local render:
        /path/to/crender.py render -m yourfile.yaml -r aqsis -f 0 99

    For a distributed render:
        /path/to/crender.py submit -m yourfile.yaml -r aqsis -f 0 99
    
    Of course, there are more options for # nodes etc. To see these, just
    call crender.py submit -h.

    A possibly out of date list:

    optional arguments:
      -h, --help            show this help message and exit
      -m METADATA, --metadata METADATA
                            the data file that contains the render job info
      -r RENDERER, --renderer RENDERER
                            which renderer to use, dumps to stdout by default
      -f FRAMERANGE FRAMERANGE, --framerange FRAMERANGE FRAMERANGE
                            render the specified framerange; by default renders
                            frame 0
      -c NAME, --name NAME  the name of the job you are submitting. What it is
                            (c)alled
      -n NODES, --nodes NODES
                            the number of nodes
      -p PPN, --ppn PPN     the number of cores per node
      -w WALLTIME, --walltime WALLTIME
                            limit on how long the job can run HH:MM:SS
      -q QUEUE, --queue QUEUE
                            which queue to submit the job to

    Note: 
        When using aqsis as the renderer, it will automatically submit a seperate
        job for each node. Do NOT bother giving aqsis renders multiple nodes or
        ppn as it is unable to use them.

        
**Lighting**
The most basic way to light a scene is to use the "Ambient Light Proxy" object.
    This object allows you to set the intensity of the ambient light by going 
    to the materials tab (the little checkered sphere mid way down the right 
    sidebar) and adjusting the "Ambient" parameter. In order to adjust the 
    color, you must go to the World tab (a blueish circle to the left of the 
    materials tab) and adjust the "Ambient Color" parameter. 

    Note: the effects of the intensity that you specified will NOT be visible
    in blender as blender uses individual intensities for each object. This
    does not happen in renderman, so a proxy object is required to set the 
    intensity.

The other way to light a scene is to use blender's built in lights. In the
    default scene there is already one point light. To edit the parameters
    for this light, go to the little tab that has a little x with a dot in the 
    center. This is the lighting tab. Here you may change the type of light
    (note that only point, sun, and spot are allowed for renderman), the color,
    and the energy (a max of 1 for sun should be used). Finally, if using the 
    "spot" light, the angle of the beam can be adjusted using the "Size"
    parameter under "Spot Shape".

Other things to be aware of:
    Once you start adding shaders, you WILL need to adjust the intensities and
        colors of your lights.
    Turning off the shadows in blender turns off the shadows in renderman. They
        are ON by default so make sure you want it that way!
    Do NOT delete objects you have imported! The export will fail if you do. If
        you want to see around them, you can toggle them invisible by cliking
        on the little eye next to the object you wish to turn invisible (upper
        right by default). THe little camera will toggle it invisible for 
        rendering. 
    In blender, the sun will light the same no matter where you place it, but
        in order to get correct shadows efficently with renderman, there are a
        few restrictions. If you ignore these restrictions your shadows WILL be 
        messed up. The sun should just outside of the scene, and the ray coming
        out from it should pass roughly through the origin.
    Enabling Ambient Occlusion is done by checking the box under the world tab.
        While there are sliders for settings, these will NOT affect the renderman
        render at this time because sane renderman defaults are beyond blender's
        capability. You DO need to check that box though!


**File Format**
See FileFormat.txt

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
