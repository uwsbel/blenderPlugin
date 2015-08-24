**Installing the Plugin and Chrono::Render**

*For a more comprehinsive understanding of the plugin, read the 
blender-plugin-tutorial.odt file. It tells how to install the plugin, and goes 
through a in-depth tutorial of all of the features available*

Requirements: blender 2.67+, python3, and pyyaml should all be installed on 
    the machine from which you will be running blender.
    
Note: this is written assuming you will run blender on a local machine
and then render on on an external machine.

1. Clone the Chrono::Render repo by running 
    git clone https://github.com/uwsbel/ChronoRender

    from somewhere on the machine you wish to render on.

This contains all the files needed to take the exported data from blender 
and create a nice render from it.

2. Clone this repo onto your local machine
3. Copy the file plugin.py from the repo to your local machine's blender
    addons folder by using the following command (execute on local machine)

    scp username@euler.msvc.wisc.edu:/path/to/blender-plugin/plugins/blender/plugin.py
    /path/to/blender/addons/folder/on/your/machine/chronorender_plugin.py

    On linux blender addons go in:
    /home/$user/.config/blender/$version/scripts/addons
    Windows XP:
    C:\Documents and Settings\%username%\Application Data\Blender Foundation\Blender\2.6x\scripts\addons
    Windows7:
    C:\Users\%username%\AppData\Roaming\Blender Foundation\Blender\2.6x\scripts\addons

4. Open up blender.
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
    export it to and name the file out.yaml
 
You will now have two files, out.tar.gz and data.tar.gz. In order to run your render on the cluster, upload the two tar.gz files to the rendering cluster and simply
run

    /path/to/chrono/render/scripts/crender_auto.py -r prman -o /path/to/out.tar.gz -d /path/to/data.tar.gz
    
Parameters for this script can be gotten with --help or -h

This will extract and begin your render. Upon completion your images will be located in out/RENDERMAN/job/images
 
If you wish to re-render you can either delete the created directory and run the script again or follow the instructions
below (more complicated and should be avoided).

*Instructions for rendering AFTER files have all been propperly extracted follow:*

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
        right by default). The little camera will toggle it invisible for 
        rendering. 

**File Format**
See FileFormat.txt

**What you can do**
-Apply colors to your objects and have those colors show when you render.
-Position the camera and lighting
-Move the camera using keyframing
-A variety of lighting effects, including shadows, ambient occlusion, and 
    color bleeding
-Selectively choose which objects to render

**What this plugin does NOT do (currently)**

-allow you to move, rotate, or size the objects. You can do this in blender but if
    you render with renderman your changes will NOT be applied. (Camera 
    location however, WILL be changed if you move it. ctrl-alt-0 is nice for 
    snapping the camera to your view point)
    
-allow you to save your changes partway through. You must import the file,
    apply materials and colors, and export it in ONE blender session.
    
-a full render with blender's "render" button.
