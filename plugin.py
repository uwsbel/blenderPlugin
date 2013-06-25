import bpy
import math
import mathutils
import os

#TODO: import selectable number of particles from .dat file
# be able to add materials to it
# export to renderman/rib?
# click and have all the scripts built
# one proxy object per type in a data column
# one script that prepares for cluster
# one script that does one frame for you
# file is: type, posx, posy, posz, quatenion, 3 radii things
# type goes something like 1=sphere, 2=elipsoid, 3=cube... 
# ^^ not any more!

#IDEAL DATA INPUT FORMAT:
# type of object, location, rotation, object specfic params
# ideally type of object ALL OBJECTS of SAME TYPE would be on consecutive lines
# TODO: currently all objects represented by one proxy must have the SAME GEOMETRY
# eg. sphere radius 3, cannot also have spheres of radius 2
#
#OTHER NEEDED/WANTED INFO:
# camera loc, filepath, scaling factor, frame range, data file

#TODO: actually take input from blender for the export (a menu or something) colors and textures

#TODO/CHECKLIST: make file format (pos, rot, geom type, dimensions, group, velocity, pressure
# in bitbucket 
# render the file. in blender(headless?), then using renderman 
# full animation
# fancier stuff (moving camra/lights or fancy materials (shadows, reflection, ambient and global illumination)

bl_info = {
        "name": "Chrono::Render plugin",
        "description": "TODO",
        "author": "Daniel <Daphron> Kaczmarek",
        "version": (0, 2),
        "blender": (2, 67, 1), #TODO: find minimum version
        "location": "TODO",
        "warning": "",
        "wiki_url": "TODO",
        "tracker_url":"TODO",
        "category": "Import-Export"}


class Object:
    def __init__(self, data, index):
        # print("CREATING OBJECT")
        # print("DATA:",data)
        self.kind = data[0]
        self.x = float(data[1])
        self.y = float(data[2])
        self.z = float(data[3])
        self.q0 = float(data[4])
        self.q1 = float(data[5])
        self.q2 = float(data[6])
        self.q3 = float(data[7])
        self.ep = [float(data[x]) for x in range(8,len(data)-1)] #-1 cause of endline char
        self.index = index
        self.color = [0.6, 0.0, 0.6]

        self.quat = mathutils.Quaternion((self.q0, self.q1, self.q2, self.q3))
        #TODO: quaternions inputed in axis,angle or the way above?
        self.euler = self.quat.to_euler()
    
    def __str__(self):
        return "<{:d},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f}>".format(self.kind, self.x, self.y, self.z, self.q0, self.q1, self.q2, self.q3, self.q3, self.ep[1], self.ep[2], self.ep[3])

    def addToBlender(self):
        if self.index % 100 == 0:
            print("index = {}".format(self.index))
        # Cube
        if self.kind == "Cube":
            #ep[0] = length of one side
            bpy.ops.mesh.primitive_cube_add(radius=self.ep[0], location=(self.x, self.y, self.z), rotation=(self.euler.x, self.euler.y, self.euler.z))
        # Cylinder
        elif self.kind == "Cylinder":
            # ep[0] = radius of top, ep[1] = depth
            bpy.ops.mesh.primitive_cylinder_add(radius=self.ep[0], depth=self.ep[1], location=(self.x, self.y, self.z), rotation=(self.euler.x, self.euler.y, self.euler.z))
        # Sphere
        elif self.kind == "Sphere":
            # ep[0] = radius of the sphere
            # uv sphere looks nicer but icosphere might be the better route
            bpy.ops.mesh.primitive_uv_sphere_add(size=self.ep[0], location=(self.x, self.y, self.z), rotation=(self.euler.x, self.euler.y, self.euler.z))
        # Ellipsoid
        elif self.kind == "Ellipsoid":
            #TODO: The elipses are just WRONG.
            #ep[0] is the radius, ep[1] is the length in the direction of rotation
            bpy.ops.mesh.primitive_uv_sphere_add(size=self.ep[0], location=(self.x, self.y, self.z), rotation=(self.euler.x, self.euler.y, self.euler.z))

            #The right way?
            bpy.ops.transform.resize(value=(1,0.5,5))

# 
#             #TODO: this can't even be the right approach... [1,1,1] resizes...
#             matrix = self.quat.to_matrix() #rotation matrix
#             # vec = mathutils.Vector((1,1,self.ep[2]/self.ep[1])) 
#             vec = mathutils.Vector((1,1,1)) 
#             rot = vec * matrix #TODO: right order?
#             bpy.ops.transform.resize(value=rot)
# 
        bpy.context.active_object["index"] = self.index
        bpy.context.active_object.name = "Line " + str(self.index) + " object"
        #object.get("index") to get the value
        #object["index"] doesn't work?

class ProxyObject(Object):
    def __init__(self, data, indicies):
        """ data is a line of the input file, indicies is a list of lines from the file that this obj represents
            whichAttribute is a num which specifies the column of data on the line that decides proxyObjs and attribute
            tells the specifica attribute which this proxyObj is for (sphere, cube...) """
        # print("MAKING PROXY OBJ")

        Object.__init__(self, data, indicies[0])
        self.indicies = indicies
        self.attribute = data[0]
        # print(self.attribute)

    def addToBlender(self):
        # print(self.ep)
        bpy.ops.mesh.primitive_monkey_add(radius=self.ep[0], location=(self.x, self.y, self.z))
        bpy.context.active_object["attribute"] = self.attribute
        bpy.context.active_object.name = "Proxy " + self.attribute


def configInitialScene():
    bpy.ops.object.delete()

def export(fin, filename, objects, proxyObjects):
    print("Exporting!")
    fout = open(filename, "w")
    writeFilename = "blender_test.rib"
    writePath = "/home/dankaczma/chronoman2/test/output/"
    dataFilename = "blender_test.dat"
    dataPath = "/home/dankaczma/chronoman2/test/input/data/blender/"
    padding = "2"
    scalingFactor = "0.01"
    resolution = "320 240"
    # cameraPos = "-0 1 -10"
    cameraPos = "{} {} {}".format(bpy.data.objects['Camera'].location[0], bpy.data.objects['Camera'].location[1],bpy.data.objects['Camera'].location[2])
    cameraRot = "{} {} {}".format(bpy.data.objects['Camera'].rotation_euler[0], bpy.data.objects['Camera'].rotation_euler[0], bpy.data.objects['Camera'].rotation_euler[0])
    surface = "plastic" #TODO: get all params through input and surface through blender!

    #The boring initial setup stuff
    fout.write("%WRITE_FILENAME={}\n".format(writeFilename)) 
    fout.write("%WRITE_PATH={}\n".format(writePath))
    fout.write("%DATA_FILENAME={}\n".format(dataFilename))
    fout.write("%DATA_PATH={}\n".format(dataPath))
    #TODO:quat xyzw or wxyz?)
    fout.write("%DATA_FORMAT=ID,POS_X,POS_Y,POS_Z,QUAT_W,QUAT_X,QUAT_Y,QUAT_Z,ignore,ignore,ignore\n")
    fout.write("%DELIM=,\n")
    fout.write("%QUALITY=production\n")
    fout.write("%PADDING={}\n".format(padding))
    fout.write("%SCALING_FACTOR={}\n".format(scalingFactor))
    fout.write("%RESOLUTION=\"{}\"\n".format(resolution))
    fout.write("%PADDING={}\n".format(padding))
    fout.write("%CAMERA_POS=\"{}\"\n".format(cameraPos))
    fout.write("%CAMERA_ROT=\"{}\"\n".format(cameraRot))
    fout.write("%INJECTIONRIB_SEARCHPATH=./:/home/dankaczma/chronoman2/test/input/injection_ribs:/home/dankaczma/chronoman2/share/injection_ribs/:/home/dankaczma/chronoman2/share/injection_ribs/cameras:/home/dankaczma/chronoman2/share/injection_ribs/lighting:/home/dankaczma/chronoman2/share/injection_ribs/passes:/home/dankaczma/chronoman2/share/injection_ribs/scenes:/home/dankaczma/chronoman2/share/injection_ribs/examples\n")
    
    #Now the proxy objects
    for proxy in proxyObjects:
        fout.write("\nObjectBegin\n")
        fout.write("%Name={}\n".format(proxy.attribute))
        fout.write("%Range=\"{} {}\"\n".format(min(proxy.indicies), max(proxy.indicies)))
        #TODO:quat xyzw or wxyz?
        fout.write("%DATA_FORMAT=ID,POS_X,POS_Y,POS_Z,QUAT_W,QUAT_X,QUAT_Y,QUAT_Z,ignore,ignore,ignore\n")

        extraParams = proxy.attribute
        for e in proxy.ep:
            extraParams += " " + str(e)

        fout.write("%Geometry = {}\n".format(extraParams))
        fout.write("%color = \"{} {} {}\"\n".format(proxy.color[0], proxy.color[1], proxy.color[2]))
        fout.write("Surface \"{}\"\n".format(surface))
        fout.write("ObjectEnd\n")

# class OBJECT_PT_pingpong(bpy.types.Panel):
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "TOOLS"
#     bl_context = "object"
#     bl_label = "Ping Pong"
# 
#     display = 0
# 
#     def draw_header(self, context):
#         layout = self.layout
#         layout.label(text="HEADER", icon="PHYSICS")
# 
#     def draw(self, context):
#         layout = self.layout
#         row = layout.row()
#         split = row.split(percentage=0.5)
#         colL = split.column()
#         colR = split.column()
# 
#         if self.display == 0:
#             colL.operator("pipo", text="Ping")
#         else:
#             colR.operator("pipo", text="Pong")
# 
# 
# class OBJECT_OT_pingpong(bpy.types.Operator):
#     bl_label = "PingPong operator"
#     bl_idname = "pipo"
#     bl_description = "Move the ball"
# 
#     def invoke(self, context, event):
#         import bpy
# 
#         self.report("INFO", "Moving the ball")
#         bpy.types.OBJECT_PT_pingpong.display = 1 - by.types.OBJECT_PT_pingpong.display
#         return {"FINISHED"}
# 

def main():
    # print(os.getcwd())
    filename = "/home/xeno/repos/blender-plugin/plugins/blender/blender_input_test.dat"
    export_filename = "/home/xeno/repos/blender-plugin/plugins/blender/blender_output_test.md"
    individualObjectsIndicies = range(1,7900, 100) 

    objects = []
    proxyObjects = []

    fin = open(filename, "r")

    for i, line in enumerate(fin):
        if i+1 in individualObjectsIndicies:
            objects.append(Object(line.split(","), i+1))
            if i % 100 == 0:
                print("Object {}".format(i))

        else:
            data = line.split(",")
            proxyExists = False
            for obj in proxyObjects:
                if obj.attribute == data[0]:
                    obj.indicies.append(i+1)
                    proxyExists = True
            if not proxyExists:
                print("New Proxy line num {}".format(i))
                proxyObjects.append(ProxyObject(data, [i+1]))
        

    configInitialScene()
    print("Here")

    
    for obj in objects:
        obj.addToBlender()
    for obj in proxyObjects:
        obj.addToBlender()

    print("objects added")
        

    export(fin, export_filename, objects, proxyObjects)

    #TODO: run only when export button hit!
    fin.close()


if __name__ == "__main__":
    # bpy.utils.register_module(__name__)
    main()
