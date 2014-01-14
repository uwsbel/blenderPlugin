import bpy
import math
import mathutils
import os
import yaml
import tarfile
import shutil

#TODO: many particles? IOError io.read()
# check small_test (done correctly) and full_test (running with all particles)

#TODO: all objects have a different radius. Make work.
#TODO: shader selection inside blender?

#TODO: walltime for one frame instead of for the whole big render?

#TODO:
#currently using rough heuristics for ScreenWindow (sun shadows) and light intensity. Improve
#currently using NO user input for ao and color bleeding quality parameters!

#TODO: Why is renderman's window larger than blender's for rendering
#some of the files (the sensor size maybe?)

#TODO: PERFORMANCE:
#   clipping panes
#   spots instead of points if doable#
#   multicore stuff (share shadowmaps, etc)
#    renderman multiple cores (qsub vs -p:16) vs renderman one instance per core
#   a way to remove background images from shadowpass 
#   use DelayedReadArchive instead of ReadArchive for obj and other junk

#Resolution and shading rate affect time and quality of render

#TODO: for server-side, are tarbombs a problem?

#TODO: the fov for simple shots is way off. Why?

#TODO: get intensities right!

#TODO: shadows for moving camera. Done?

#TODO: indicate boundaries of sim particles so you can easily place camera

#TODO: fix the massive if statements passed around. Or just kill the threading?
#could require all objs in same group have contiguous ids?

#urls:
#http://euler.wacc.wisc.edu/~felipegb94/input/data.tar.gz
#http://euler.wacc.wisc.edu/~felipegb94/input/out.tar.gz
bl_info = {
        "name": "Chrono::Render plugin",
        "description": "Allows for easy graphical manipulation of simulated data before rendering with a powerful renderman renderer",
        "author": "Daniel <Daphron> Kaczmarek",
        "version": (0, 9),
        "blender": (2, 67, 1), #TODO: find minimum version
        "location": "File > Import > Import Chrono::Engine",
        "warning": "",
        "wiki_url": "TODO",
        "tracker_url":"TODO",
        "category": "Import-Export"}

DEFAULT_COLOR = (0.4, 0.4, 0.6)

MESH_IMPORT_FUNCTIONS = {"obj": bpy.ops.import_scene.obj,
                        "stl": bpy.ops.import_mesh.stl,
                        "ply": bpy.ops.import_mesh.ply}

fin = ""
objects = ""
proxyObjects = ""
changing_params = False
max_dim = 1
min_dim = 1

class AmbientLightProxy:
    def __init__(self):
        self.material = self.create_material()
        self.obj = None

    def update(self):
        """Grabs stuff like color, texture and stores them"""
        #Color can be diffuse, specular, mirror, and subsurface scattering
        if self.obj.active_material is None:
            self.obj = bpy.context.scene.objects['Ambient Light Proxy']
        self.color = (self.obj.active_material.diffuse_color[0], self.obj.active_material.diffuse_color[1], self.obj.active_material.diffuse_color[2])

    def create_material(self):
        mat = bpy.data.materials.new("Ambient light proxy material")
        mat.diffuse_color = (0,0,0)
        mat.diffuse_shader = 'LAMBERT'
        mat.diffuse_intensity = 1.0
        mat.specular_color = (1.0, 1.0, 1.0)
        mat.specular_shader = 'COOKTORR'
        mat.specular_intensity = 0.5
        mat.alpha = 1.0
        mat.ambient = 1
        return mat

    def addToBlender(self):
        bpy.ops.mesh.primitive_monkey_add(location=(6, 6, 6))
        bpy.context.active_object.name = "Ambient Light Proxy"
        bpy.context.active_object.active_material = self.material
        bpy.context.active_object["index"] = "AMBIENT_PROXY"
        self.obj = bpy.context.active_object
        
class Object:
    def __init__(self, data, currdir):
        # print("DATA:",data)
        self.group = data[0]
        self.index = int(data[1]) #The objects unique ID/index number
        #XYZ locations
        self.x = float(data[2])
        self.y = float(data[3])
        self.z = float(data[4])

        self.quat = mathutils.Quaternion((float(data[5]), float(data[6]), float(data[7]), float(data[8])))
        # self.euler_zyx = self.quat.to_euler('ZYX')
        self.euler = tuple(a for a in self.quat.to_euler())

        self.obj_type = data[9].lower()

        #Extra parameters (specific to each object type)
        # test = []
        # for x in range(10,len(data)):
        #     if data[x] is not '\n':
        #         test.append(float(data[x]))
        # self.ep = [float(data[x]) for x in range(10,len(data)) if data[x] is not '\n'] 
        self.ep = []
        for x in range(10,len(data)):
            if data[x] is not '\n':
                try:
                    self.ep.append(float(data[x]))
                except ValueError:
                    self.ep.append(data[x].strip("\n"))

        self.color = DEFAULT_COLOR
        self.currdir = currdir
        self.material = self.create_material()

    def create_material(self):
        mat = bpy.data.materials.new("Object {}'s material".format(self.index))
        mat.diffuse_color = self.color
        mat.diffuse_shader = 'LAMBERT'
        mat.diffuse_intensity = 1.0
        mat.specular_color = (1.0, 1.0, 1.0)
        mat.specular_shader = 'COOKTORR'
        mat.specular_intensity = 0.5
        mat.alpha = 1.0
        mat.ambient = 1
        return mat

    def addToBlender(self):
        # if self.index % 100 == 0:
            # print("index = {}".format(self.index))
        # Cube
        if self.obj_type == "cube":
            #ep[0] = length of one side
            bpy.ops.mesh.primitive_cube_add(radius=self.ep[0], location=(self.x, self.y, self.z), rotation=self.euler)
        #Box
        elif self.obj_type == "box":
            bpy.ops.mesh.primitive_cube_add(radius=1.0, location=(self.x, self.y, self.z))
            bpy.ops.transform.resize(value=(self.ep[0], self.ep[1], self.ep[2]))
            bpy.context.object.rotation_euler = mathutils.Euler(self.euler)
        # Cylinder
        elif self.obj_type == "cylinder":
            # ep[0] = radius of top, 2*ep[1] = depth
            bpy.ops.mesh.primitive_cylinder_add(radius=self.ep[0], depth=2*self.ep[1], location=(self.x, self.y, self.z), rotation=self.euler)
        # Sphere
        elif self.obj_type == "sphere":
            # ep[0] = radius of the sphere
            # uv sphere looks nicer but icosphere might be the better route
            bpy.ops.mesh.primitive_uv_sphere_add(size=self.ep[0], location=(self.x, self.y, self.z), rotation=self.euler)
        # Ellipsoid
        elif self.obj_type == "ellipsoid":
            #ep[0] is the radius, ep[1] is the length in the direction of rotation
            bpy.ops.mesh.primitive_uv_sphere_add(size=1.0, location=(self.x, self.y, self.z))
            #The right way?
            bpy.ops.transform.resize(value=(self.ep[0],self.ep[1],self.ep[2]))
            bpy.context.object.rotation_euler = mathutils.Euler(self.euler)

        #Cone
        elif self.obj_type == "cone":
            # self.ep[0] = radius of cone bottom, self.ep[1] = half_height of cone
            bpy.ops.mesh.primitive_cone_add(radius1=self.ep[0], depth=2*self.ep[1], location=(self.x, self.y, self.z), rotation=self.euler)
        #Torus
        elif self.obj_type == "torus":
            bpy.ops.mesh.primitive_torus_add(rotation=self.euler, location=(self.x, self.y, self.z), major_radius=self.ep[0], minor_radius=self.ep[1])
        #External Mesh
        elif self.obj_type in MESH_IMPORT_FUNCTIONS:
            filename = os.path.join(self.currdir, "meshes", self.ep[0])
            MESH_IMPORT_FUNCTIONS[self.obj_type](filepath=filename, use_split_groups=False, use_split_objects=False)
            # bpy.ops.object.join()
            for o in bpy.context.selected_objects:
                o.location = [self.x, self.y, self.z]
                # Now rotate and move to match what renderman render looks like
                o.rotation_euler = mathutils.Euler(self.euler)
                # o.rotation_euler = self.euler_zyx
                # o.rotation_euler.rotate(mathutils.Euler((math.pi, 0, 0)))
                # o.rotation_quaternion = self.quat.rotate(mathutils.Euler((180, 0, 0)))
                bpy.context.scene.objects.active = o 
        else:
            print("Object type {} is not currently supported as a primitive in the blender plugin")
 
        bpy.context.active_object.rotation_mode = 'ZYX'
        bpy.context.active_object["index"] = self.index
        bpy.context.active_object.name = "Obj # {}".format(self.index)
        bpy.context.active_object.active_material = self.material
        self.obj = bpy.context.active_object
        #object.get("index") to get the value
        #object["index"] doesn't work?

        #TODO: it is taking the obj2 as active_object and then relabling it here. Fixed?

    def update(self):
        """Grabs stuff like color, texture and stores them"""
        try:
            self.obj = bpy.context.scene.objects['Obj # {}'.format(self.index)]
            self.color = (self.obj.active_material.diffuse_color[0], self.obj.active_material.diffuse_color[1], self.obj.active_material.diffuse_color[2])
            self.mat = self.obj.active_material
        except Exception as e:
            print(e.strerror)
            print("EXCEPTION! Dropping to pdb shell")
            import pdb; pdb.set_trace()

class ProxyObject(Object):
    def __init__(self, data, currdir, indicies):
        """ data is a line of the input file, indicies is a list of lines 
        from the file that this obj represents whichAttribute is a num which 
        specifies the column of data on the line that decides proxyObjs and 
        group tells the specifica group which this proxyObj is for 
        (sphere, cube...) """
        # print("MAKING PROXY OBJ")

        Object.__init__(self, data, currdir)
        self.indicies = indicies
        # print(self.group)
        self.color = DEFAULT_COLOR
        self.material.name = "Group {}'s material".format(self.group)

    def same_params(self, data):

        other_ep = []
        for x in range(10,len(data)):
            if data[x] is not '\n':
                try:
                    other_ep.append(float(data[x]))
                except ValueError:
                    other_ep.append(data[x].strip("\n"))

        return other_ep == self.ep

    def addToBlender(self):
        # print(self.ep)
        bpy.ops.mesh.primitive_monkey_add(radius=self.ep[0], location=(self.x, self.y, self.z))
        bpy.context.active_object["group"] = self.group
        bpy.context.active_object["index"] = "PROXY"
        bpy.context.active_object.name = "Proxy " + self.group
        bpy.context.active_object.active_material = self.material
        self.obj = bpy.context.active_object

    def update(self):
        try:
            self.obj = bpy.context.scene.objects['Proxy {}'.format(self.group)]
            self.color = (self.obj.active_material.diffuse_color[0], self.obj.active_material.diffuse_color[1], self.obj.active_material.diffuse_color[2])
            self.mat = self.obj.active_material
        except:
            print("EXCEPTION! Dropping to pdb shell")
            import pdb; pdb.set_trace()

    # def update(self):
    #     """Grabs stuff like color, texture and stores them"""
    #     #Color can be diffuse, specular, mirror, and subsurface scattering
    #     if self.obj.active_material is not None:
    #         self.color = (self.obj.active_material.diffuse_color[0], self.obj.active_material.diffuse_color[1], self.obj.active_material.diffuse_color[2])
    #         self.mat = self.obj.active_material

def configInitialScene(fin_frame):
    # bpy.ops.object.delete()
    bpy.data.scenes["Scene"].frame_end = fin_frame
    bpy.data.scenes["Scene"].frame_start = 0
    bpy.data.scenes["Scene"].frame_current = bpy.data.scenes["Scene"].frame_start

class ImportChronoRender(bpy.types.Operator):
    """Import ChronoRender"""
    bl_idname = "import.import_chrono_render"
    bl_label = "Import ChronoRender"
    filename = bpy.props.StringProperty(subtype='FILE_PATH')
    directory = bpy.props.StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def process_max_dimensions(self, data):
        global max_dim
        global min_dim
        max_length = 0
        if data[9] in MESH_IMPORT_FUNCTIONS:
            pass
            #TODO: this could screw up some shadows. Fix. (because now sun shadows out of box)
        else:
            max_length = max(float(data[x]) for x in range(10,len(data)) if data[x] is not '\n') 
        for coord in (data[2:5]):
            if float(coord) + max_length > max_dim:
                max_dim = float(coord) + max_length
            if float(coord) - max_length < min_dim:
                min_dim = float(coord) - max_length

    def import_mesh(self, data):
        global extra_geometry_indicies

        mesh_filename = os.path.join(self.directory, "meshes", data[10].strip("\n"))
        MESH_IMPORT_FUNCTIONS["obj"](filepath=mesh_filename)
        extra_geometry_indicies.append(int(data[1]))

        for o in bpy.context.selected_objects:
            o.location = [float(data[2]), float(data[3]), float(data[4])]

        quat = mathutils.Quaternion((float(data[5]), float(data[6]), float(data[7]), float(data[8])))
        euler = tuple(a for a in quat.to_euler())

        for o in bpy.context.selected_objects:
            o.rotation_euler =  mathutils.Euler(euler)

    def execute(self, context):
        global fin_name
        global objects
        global proxyObjects
        global changing_params
        global ambient_proxy
        global extra_geometry_indicies
        global fin_dir
        # filename = "/home/xeno/repos/blender-plugin/plugins/blender/blender_input_test.dat"
        # individualObjectsIndicies = [1,2,3,4, 5, 6] #LINE NUMBERS

        objects = []
        proxyObjects = []
        extra_geometry_indicies = []

        fin_name = self.filename
        fin_frame = 10
        try:
            fin_frame = self.filename.replace(".dat", "")
            fin_frame = fin_frame.replace("data_", "")
            fin_frame = int(fin_frame)
        except:
            print("Failed to automatically get the framerange from the file. You will likely need to set it manually.")
        
        filepath = os.path.join(self.directory, self.filename)
        fin_dir = self.directory

        fin = open(filepath, "r")

        for i, line in enumerate(fin):
            index = line.split(",")[1]
            # if line.split(",")[9].lower() == "extrageometry":
                # extra_geometry_indicies.append(line.split(",")[1])
            # if line.split(",")[9].lower() in MESH_IMPORT_FUNCTIONS:
                # self.import_mesh(line.split(","))
            # else:
            self.process_max_dimensions(line.split(","))
            if line.split(",")[0].lower() == "individual":
                objects.append(Object(line.split(","), self.directory))
                print("Object {}".format(index))

            else:
                data = line.split(",")
                proxyExists = False
                for obj in proxyObjects:
                    if obj.group == data[0]:
                        obj.indicies.append(index)
                        if not changing_params and not obj.same_params(data):
                            changing_params = True

                        proxyExists = True
                if not proxyExists:
                    print("New Proxy obj num {}".format(index))
                    proxyObjects.append(ProxyObject(data, self.directory, [index]))

        configInitialScene(fin_frame)

        for obj in objects:
            obj.addToBlender()
        for obj in proxyObjects:
            obj.addToBlender()

        ambient_proxy = AmbientLightProxy()
        ambient_proxy.addToBlender()
        print("objects added")
        return {'FINISHED'}

def add_importChronoRenderButton(self, context):
    self.layout.operator(
            ImportChronoRender.bl_idname,
            text=ImportChronoRender.__doc__,
            icon='PLUGIN')

class ExportChronoRender(bpy.types.Operator):
    """Exports to Chrono::Render"""
    bl_idname = "export.export_chrono_render"
    bl_label = "Export Chrono::Render"
    filename = bpy.props.StringProperty(subtype='FILE_PATH')
    directory = bpy.props.StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        self.context = context
        return {'RUNNING_MODAL'}

    def construct_condition(self, indicies):
        """docstring for construct_condition"""
        #Very simple way
        rtnd = "id == "
        if len(indicies) <= 0:
            raise Exception("No indicies in this proxy object")
        for i in indicies:
            rtnd += str(i) + " or id == "
        rtnd = rtnd[:-10] # -10 to remove the trailing "or id =="

        # Group by ranges

        return rtnd

    def export_mesh(self, context, fout, obj):
        #TODO: don't use just one file for the whole animation. One per frame. (per obj also?)
        for face in obj.obj.data.polygons:
            pgonstr = "Polygon "
            vertices = '"P" ['
            for v in face.vertices:
                vert = obj.obj.data.vertices[v].co
                vertices += "  {} {} {}".format(vert.x, vert.y, vert.z)

            vertices += ']\n'
            pgonstr += vertices

            # fout.write('AttributeBegin\n')
            # fout.write('Surface "matte"\n')
            # fout.write('Color [{} {} {}]\n'.format(obj.color[0], obj.color[1], obj.color[2]))
            #TODO: get rotations to work with any blender rotation scheme
            # fout.write('Rotate {} 0 0 1\n'.format(math.degrees(obj.rotation_euler[2])))
            # fout.write('Rotate {} 0 1 0\n'.format(math.degrees(obj.rotation_euler[1])))
            # fout.write('Rotate {} 1 0 0\n'.format(math.degrees(obj.rotation_euler[0])))
            # fout.write('Translate {} {} {}\n'.format(obj.location[0], obj.location[2], -obj.location[1]))
            fout.write(pgonstr)
            # fout.write('AttributeEnd\n')

    def write_object(self, objects, is_proxy=False):
        global changing_params
        renderobject = []
        for obj in objects:
            obj.update()
            name = obj.group

            #Start writing
            color = "{} {} {}".format(obj.color[0], obj.color[1], obj.color[2])

            data = dict()
            data["name"] = str(name)

            if is_proxy:
                data["condition"] = self.construct_condition(obj.indicies)

            else:
                data["condition"] = "id == {}".format(obj.index)
                # maxIndex = obj.index
                # minIndex = obj.index
                # data["condition"] = "id >= {} and id <= {}".format(minIndex, maxIndex)

            data["color"] = color
            if obj.obj_type in MESH_IMPORT_FUNCTIONS:
                data["geometry"] = [{"type" : "archive"}]
            else:
                data["geometry"] = [{"type" : obj.obj_type}]
            data["shader"] = [{"name" : "matte.sl"}] #TODO: not hardcoded
            data["geometry"][0]["changingprams"] = changing_params
            
            if obj.obj_type.lower() == "sphere":
                data["geometry"][0]["radius"] = obj.ep[0]
            elif obj.obj_type.lower() == "cube":
                data["geometry"][0]["side"] = obj.ep[0]
            elif obj.obj_type.lower() == "cone":
                data["geometry"][0]["radius"] = obj.ep[0]
                data["geometry"][0]["height"] = obj.ep[1]
            elif obj.obj_type.lower() == "cylinder":
                data["geometry"][0]["radius"] = obj.ep[0]
                data["geometry"][0]["height"] = obj.ep[1]
            elif obj.obj_type.lower() == "ellipsoid":
                data["geometry"][0]["a"] = obj.ep[0]
                data["geometry"][0]["b"] = obj.ep[1]
                data["geometry"][0]["c"] = obj.ep[2]
            elif obj.obj_type.lower() == "torus":
                data["geometry"][0]["rmajor"] = obj.ep[0]
                data["geometry"][0]["rminor"] = obj.ep[1]
            elif obj.obj_type.lower() == "box":
                data["geometry"][0]["xlength"] = obj.ep[0]
                data["geometry"][0]["ylength"] = obj.ep[1]
                data["geometry"][0]["zlength"] = obj.ep[2]
            elif obj.obj_type.lower() in MESH_IMPORT_FUNCTIONS:
                extra_rib_filename = "extra_geo_{}".format(obj.index) + ".rib"
                data["geometry"][0]["filename"] = extra_rib_filename
                renderman_dir = os.path.join(self.directory, "RENDERMAN")
                if not os.path.exists(renderman_dir):
                    os.makedirs(renderman_dir)
                ribarchives_dir = os.path.join(renderman_dir, "ribarchives")
                if not os.path.exists(ribarchives_dir):
                    os.makedirs(ribarchives_dir)
                fout_fullpath = os.path.join(ribarchives_dir,  extra_rib_filename)
                fout = open(fout_fullpath, "w")
                self.export_mesh(self.context, fout, obj)
                fout.close()
            else:
                print("Geometry type {} not supported by blender export at this time".format(obj.obj_type))

            if not obj.obj.hide_render:
                renderobject.append(data)

        return renderobject

    def write_extra_geometry(self, context, obj):
        global extra_geometry_indicies
        renderobject = []
        data = dict()
        # data["color"] = "{} {} {}".format(obj.color[0], obj.color[1], obj.color[2])
        data["geometry"] = [{"type" : "archive"}]
        # data["shader"] = [{"type" : "matte.sl"}]
        data["geometry"][0]["filename"] = "extrageometry.rib"
        data["name"] = "extrageometry"
        id_str = ""
        for i in extra_geometry_indicies:
            id_str += "id == {} or ".format(i)
        id_str = id_str[:-4]
        data["condition"] = id_str

        renderobject.append(data)
        return renderobject

    def camera_to_renderman(self, context, obj):
        camera_matrix = obj.matrix_world
        camera = obj
        camera_loc = obj.location
        camera_euler = obj.rotation_euler

        fov = None
        try:
            cam_fov = math.degrees(obj.data.angle)
            fov = 360.0*math.atan(16.0/camera.data.lens)/math.pi 
        except AttributeError:
            if hasattr(obj.data, "spot_size"):
                fov = math.degrees(obj.data.spot_size)
            else:
                pass

        out = ''

        if hasattr(obj.data, "type"):
            if obj.data.type == 'SUN':
                out += ('Projection "orthographic"\n')
            else:
                out += ('Projection "perspective" "fov" [{}]\n'.format(fov))
        else:
            out += ('Projection "perspective" "fov" [{}]\n'.format(fov))
            
        out += ("Scale 1 1 -1\n")
        out += ("Rotate {} 1 0 0\n".format(-math.degrees(camera_euler[0])))
        out += ("Rotate {} 0 1 0\n".format(-math.degrees(camera_euler[1])))
        out += ("Rotate {} 0 0 1\n".format(-math.degrees(camera_euler[2])))
        out += ("Translate {} {} {}\n".format(-camera_matrix[0][3],
                                                    -camera_matrix[1][3],
                                                    -camera_matrix[2][3]))
        return out
    
    def write_shadowspot(self, context, renderpasses, light_file, obj, end_x, end_y, end_z, delta_angle, index):
        name = "shadow_" + obj.data.name 
        name = name.replace(".", "_")
        correct_name = obj.data.name.replace(".", "_")
        shadowmap_name = name + ".rib"
        shadowmap_file_path = os.path.join(self.fout_dir, shadowmap_name)
        shadowmap_file = open(shadowmap_file_path, 'w')
        shadowmap_file.write(self.camera_to_renderman(context, obj))

        light_string = 'LightSource "shadowspot" {} "intensity" {}  "coneangle" {} "conedeltaangle" {} "lightcolor" [{} {} {}] "from" [{} {} {}] "to" [{} {} {}] "shadowname" ["{}"]\n'.format(index, obj.data.energy*30, obj.data.spot_size/2.0, delta_angle, obj.data.color[0], obj.data.color[1], obj.data.color[2], obj.location.x, obj.location.y, obj.location.z, end_x+obj.location.x, end_y+obj.location.y, end_z+obj.location.z, name+".shd")
        light_file.write(light_string)

        #TODO: heuristic for resolution of pass
        shadowpass = {
                    "name": "shadowpass" + str(index),
                    "type": "shadow",
                    "settings" : {
                        "resolution" : "512 512 1",
                        "shadingrate" : 1.0,
                        "pixelsamples" : "1 1",
                        "shadowfilepath" : "shadow_" + correct_name+ ".rib",
                        "display" : {"output" : "shadow_" + correct_name + ".z",
                                    "outtype" : "zfile",
                                    "mode" : "z"}}}
        renderpasses.append(shadowpass)

    def write_sun(self, context, renderpasses, light_file, obj, end_x, end_y, end_z, index):
        global max_dim
        global min_dim
        name = "shadow_" + obj.data.name 
        name = name.replace(".", "_")
        correct_name = obj.data.name.replace(".", "_")
        shadowmap_name = name + ".rib"
        shadowmap_file_path = os.path.join(self.fout_dir, shadowmap_name)
        shadowmap_file = open(shadowmap_file_path, 'w')
        shadowmap_file.write(self.camera_to_renderman(context, obj))
        shadowmap_file.write('ScreenWindow {} {} {} {}'.format(min_dim, max_dim, min_dim, max_dim))

        light_string = 'LightSource "shadowdistant" {} "intensity" {} "lightcolor" [{} {} {}] "from" [{} {} {}] "to" [{} {} {}] "shadowname" ["{}"]\n'.format(index, obj.data.energy, obj.data.color[0], obj.data.color[1], obj.data.color[2], 0, 0, 0, end_x, end_y, end_z, name+".shd")
        light_file.write(light_string)

        shadowpass = {
                    "name": "shadowpass" + str(index),
                    "type": "shadow",
                    "settings" : {
                        "resolution" : "512 512 1",
                        "shadingrate" : 1.0,
                        "pixelsamples" : "1 1",
                        "shadowfilepath" : "shadow_" + correct_name + ".rib",
                        "display" : {"output" : "shadow_" + correct_name + ".z",
                                    "outtype" : "zfile",
                                    "mode" : "z"}}}
        renderpasses.append(shadowpass)

    def write_shadowpoint(self, context, renderpasses, light_file, obj, index):
        light_string = 'LightSource "shadowpoint" {} "intensity" {} "lightcolor" [{} {} {}] "from" [{} {} {}]'.format(index, obj.data.energy*20.0, obj.data.color[0], obj.data.color[1], obj.data.color[2], obj.location.x, obj.location.y, obj.location.z)

        name = "shadow_" + obj.data.name 
        name = name.replace(".", "_")
        correct_name = obj.data.name.replace(".", "_")
        shadowmap_name_base = name + ".rib"

        rotations = {'px': 'Rotate -90.0 0.0 1.0 0.0',
                    'py': 'Rotate 90.0 1.0 0.0 0.0',
                    'pz': 'Rotate 0.0 0.0 1.0 0.0',
                    'nx': 'Rotate 90.0 0.0 1.0 0.0',
                    'ny': 'Rotate -90.0 1.0 0.0 0.0',
                    'nz': 'Rotate 180 0.0 1.0 0.0'}
        for end in ('px', 'py', 'pz', 'nx', 'ny', 'nz'):
            shadowmap_name = end + shadowmap_name_base
            shadowmap_file_path = os.path.join(self.fout_dir, shadowmap_name)
            shadowmap_file = open(shadowmap_file_path, 'w')

            light_string += ' "sf{}" ["{}"]'.format(end, end + "shadow_" + correct_name + ".shd")
            
            shadowmap_file.write('Projection "perspective" "fov" [95.0]\n')
            # shadowmap_file.write("Scale 1 1 -1\n")
            shadowmap_file.write(rotations[end] + "\n")
            shadowmap_file.write('Translate {} {} {}\n'.format(-obj.location.x, -obj.location.y, -obj.location.z))

            shadowpass = {
                        "name": "shadowpass" + str(index) + "_" + end,
                        "type": "shadow",
                        "settings" : {
                            "resolution" : "512 512 1",
                            "shadingrate" : 1.0,
                            "pixelsamples" : "1 1",
                            "shadowfilepath" : shadowmap_name,
                            "display" : {"output" : end + "shadow_" + correct_name + ".z",
                                        "outtype" : "zfile",
                                        "mode" : "z"}}}

            renderpasses.append(shadowpass)


        light_string += '\n'
        light_file.write(light_string)

    def write_ambient_occlusion(self, context, renderpasses, shader):
        resolution = "{} {}".format(bpy.data.scenes["Scene"].render.resolution_x,
                                bpy.data.scenes["Scene"].render.resolution_y)
        shadowpass = {
                "name": "ambientpass",
                "type": "ao",
                "settings": {
                    "resolution": resolution,
                    "bounces": bpy.context.scene.world.light_settings.indirect_bounces,
                    "display": {"output" : "out.tif"}},
                "shader": {
                    "name": shader,
                    "samples": 256}} #TODO: some nice way of setting samples

        renderpasses.append(shadowpass)

    def execute(self, context):
        #TODO: get objects and proxyobject properties from blender
        # into the yaml file
        global fin_name
        global objects
        global proxyObjects
        global ambient_proxy
        global fin_dir

        renderpasses = [] 

        self.fout_dir = os.path.join(self.directory, "RENDERMAN")

        if not os.path.exists(self.fout_dir):
            os.makedirs(self.fout_dir)

        filepath = os.path.join(self.fout_dir, self.filename)
        fout = open(filepath, "w")
        print("Export beginning")

        ##############
        #Camera stuff#
        ##############
        current_frame = bpy.context.scene.frame_current
        fmax = bpy.data.scenes["Scene"].frame_end
        fmin = 0
        camera_moved = False
        last_camera_output = None
        for frame in range(fmin, fmax+1):
            bpy.context.scene.frame_set(frame)
            cam_file_name = "custom_camera_{}.rib".format(frame)
            cam_file_path = os.path.join(self.fout_dir, cam_file_name)
            cam_file = open(cam_file_path, 'w')

            camera_output = self.camera_to_renderman(context, bpy.data.objects['Camera'])
            if last_camera_output == None:
                last_camera_output = camera_output
            if camera_output != last_camera_output:
                camrea_moved = True

            cam_file.write(camera_output)
            #TODO: only write the file if camera hasn't moved at all (would have to fix the one camera or indididual camera frames thing)

            cam_file.close()

            if not camera_moved and frame == fmax:
                cam_file_name = "custom_camera.rib"
                cam_file_path = os.path.join(self.fout_dir, cam_file_name)
                cam_file = open(cam_file_path, 'w')
                cam_file.write(camera_output)
                cam_file.close()


        moving_camera = {"moving_camera" : camera_moved}
        cam_file_name = "custom_camera.rib"
        bpy.context.scene.frame_current = current_frame
        #############
        #Light stuff#
        #############
        light_file_name = "custom_lighting.rib"
        light_file_path = os.path.join(self.fout_dir, light_file_name)
        light_file = open(light_file_path, 'w')

        for i, obj in enumerate(bpy.context.scene.objects):
            if obj.type == 'LAMP' and obj.hide_render == False:
                light_string = None
                
                e = obj.rotation_euler
                M = e.to_matrix()
                v = mathutils.Vector((0,0,-1)) #default direction of light
                # v.rotate(e)
                # end_x, end_y, end_z = v
                end_x, end_y, end_z = M*v

                # x20 for point and spot intensity as a rough heuristic to get them looking the same in blender and renderman(matte shader)
                if obj.data.type == 'SUN':
                    # intensity = obj.data.energy*
                    if obj.data.shadow_method == 'NOSHADOW':
                        light_string = 'LightSource "distantlight" {} "intensity" {} "lightcolor" [{} {} {}] "from" [{} {} {}] "to" [{} {} {}]\n'.format(i, obj.data.energy, obj.data.color[0], obj.data.color[1], obj.data.color[2], 0, 0, 0, end_x, end_y, end_z)
                    else:
                        self.write_sun(context, renderpasses, light_file, obj, end_x, end_y, end_z, i)

                elif obj.data.type == 'POINT':
                    if obj.data.shadow_method == 'NOSHADOW':
                        light_string = 'LightSource "pointlight" {} "intensity" {} "lightcolor" [{} {} {}] "from" [{} {} {}]\n'.format(i, obj.data.energy*20, obj.data.color[0], obj.data.color[1], obj.data.color[2], obj.location.x, obj.location.y, obj.location.z)
                    else:
                        self.write_shadowpoint(context, renderpasses, light_file, obj, i)

                elif obj.data.type == 'SPOT':
                    delta_angle = obj.data.spot_size/2 * obj.data.spot_blend
                    if obj.data.shadow_method == 'NOSHADOW':
                        light_string = 'LightSource "spotlight" {} "intensity" {}  "coneangle" {} "conedeltaangle" {} "lightcolor" [{} {} {}] "from" [{} {} {}] "to" [{} {} {}]\n'.format(i, obj.data.energy*20, obj.data.spot_size/2.0, delta_angle, obj.data.color[0], obj.data.color[1], obj.data.color[2], obj.location.x, obj.location.y, obj.location.z, end_x+obj.location.x, end_y+obj.location.y, end_z+obj.location.z)
                    else:
                        self.write_shadowspot(context, renderpasses, light_file, obj, end_x, end_y, end_z, delta_angle, i)

                if light_string != None:
                    light_file.write(light_string)

        ambient_proxy.update()
        light_string = 'LightSource "ambientlight" {} "intensity" {} "lightcolor" [{} {} {}]\n'.format(i, ambient_proxy.obj.active_material.ambient, bpy.data.worlds["World"].ambient_color[0], bpy.data.worlds["World"].ambient_color[1], bpy.data.worlds["World"].ambient_color[2])
        light_file.write(light_string)
        light_file.close()

        #Ambient Occlusion/Color Bleeding
        if bpy.context.scene.world.light_settings.use_indirect_light:
            self.write_ambient_occlusion(context, renderpasses, "colorbleedinglight.sl")
        elif bpy.context.scene.world.light_settings.use_ambient_occlusion:
            self.write_ambient_occlusion(context, renderpasses, "occlusionlight.sl")

        ##########
        #The Rest#
        ##########

        renderobject = self.write_object(objects, is_proxy = False)
        renderobject += self.write_object(proxyObjects, is_proxy = True)

        #Imported meshes
        fout_extrageo = open(os.path.join(self.fout_dir, "extrageometry.rib"), "w")
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.name != "Ambient Light Proxy":
                if not 'index' in obj:
                    self.export_mesh(context, fout_extrageo, obj)
                    renderobject += self.write_extra_geometry(context, obj)

        fout_extrageo.close()

        data_name = "./data/" + "_".join(fin_name.split("_")[:-1]) + "_*.dat"

        resolution = "{} {}".format(bpy.data.scenes["Scene"].render.resolution_x, 
                               bpy.data.scenes["Scene"].render.resolution_y)

        defaultpass = {
                    "name": "defaultpass",
                    "settings" : {
                        "resolution" : resolution,
                        "display" : {"output" : "out.tif"}}}
        if not bpy.context.scene.world.light_settings.use_ambient_occlusion and not bpy.context.scene.world.light_settings.use_indirect_light:
            renderpasses.append(defaultpass)

        data = {"chronorender" : {
                    "rendersettings" : {"searchpaths" : "./"},
                    "camera" : [{"filename" : cam_file_name}, moving_camera],
                    "lighting" : [{"filename" : "custom_lighting.rib"}],
                    # "scene" : [{"filename" : "default_scene.rib"}],
                    "renderpass" : renderpasses ,
                    "simulation" : {
                        "data" : {
                            "datasource" : [{
                                "type" : "csv",
                                "name" : "defaultdata",
                                "resource" : data_name,
                                "fields" : [
                                    #TODO: ugly hack for ignores
                                    ["group", "string"],
                                    ["id", "integer"],
                                    ["pos_x", "float"],
                                    ["pos_y", "float"],
                                    ["pos_z", "float"],
                                    ["quat_w", "float"],
                                    ["quat_x", "float"],
                                    ["quat_y", "float"],
                                    ["quat_z", "float"],
                                    ["ignore", "string"], #object type
                                    ["ep1", "string"], #extra params
                                    ["ep2", "string"], #need to modify if more than 4 extra params
                                    ["ep3", "string"],
                                    ["ep4", "string"],
                                    ]}]},
                            "renderobject" : renderobject}}}
                            # [{
                            #     "name" : "particle",
                            #     "condition" : "id >= 0",
                            #     "color" : color,
                            #     "geometry" : [{
                            #         "radius" : 0.888,
                            #         "type" : "sphere"}]}]}}}}

        yaml.safe_dump(data, fout)

        self.move_ribs(self.fout_dir)

        print("Export complete! (yes really)")
        print("Compression beginning")
        self.compress(fin_name, fin_dir, self.filename, self.fout_dir)
        print("Compression finished")
        return {'FINISHED'}

    def move_ribs(self, fout_dir):
        """Moves all rib files to the ribarchive directory"""
        ribarchives = os.path.join(fout_dir, "ribarchives")
        if not os.path.isdir(ribarchives):
            os.mkdir(ribarchives)
        init_dir = os.getcwd()

        os.chdir(fout_dir)
        for f in os.listdir("."):
            if f.endswith(".rib"):
                dest = os.path.join(ribarchives, os.path.basename(f))
                shutil.copy(f, dest)

        os.chdir(init_dir)

    def compress(self, fin_name, fin_dir, fout_name, fout_dir, force_data=False):
        #TODO: allow user to select force_data
        #requires a SEPARATE data directory to work
        #TODO: put all extra .rib files in the ribarchives dir so they can be used
        data_zipped_path = os.path.join(self.directory, "data.tar.gz")
        metadata_zipped_path = os.path.join(self.directory, fout_name.split(".")[0] + ".tar.gz")
        if not os.path.exists(data_zipped_path) or force_data == True:
            with tarfile.open(data_zipped_path, "w:gz") as tar:
                tar.add(fin_dir, arcname="job/data")
        with tarfile.open(metadata_zipped_path, "w:gz") as tar2:
            tar2.add(fout_dir, arcname="")

def add_exportChronoRenderButton(self, context):
    self.layout.operator(
            ExportChronoRender.bl_idname,
            text=ExportChronoRender.__doc__,
            icon='PLUGIN')

def register():
    print("Registering")
    bpy.utils.register_class(ImportChronoRender)
    # bpy.types.INFO_MT_file.append(add_object_button)
    bpy.types.INFO_MT_file_import.append(add_importChronoRenderButton)

    bpy.utils.register_class(ExportChronoRender)
    bpy.types.INFO_MT_file_export.append(add_exportChronoRenderButton)

def unregister():
    print("Unregistering")
    bpy.utils.unregister_class(ImportChronoRender)
    bpy.types.unregister_class(ExportChronoRender)

if __name__ == "__main__":
    register()

