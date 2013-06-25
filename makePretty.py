#TODO: make file format (pos, rot, geom type, dimensions, group, velocity, pressure
# in bitbucket 
# render the file. in blender(headless?), then using renderman 
# full animation
# fancier stuff (moving camra/lights or fancy materials (shadows, reflection, ambient and global illumination)
fin = open("blender_input_test.dat.orig", "r")
fo = open("blender_input_test.dat", "w")
a1 = []
a2 = []
a3 = []
a4 = []
for i, line in enumerate(fin):
    sp = line.split(",")
    idd = sp[0]
    print(idd)
    print(line)
    # fo.write(str(i) + "," + line)
    if idd == "1":
        a1.append("Cube" + line[1:])
    elif idd == "2":
        a2.append("Sphere," + ",".join(sp[1:-3]) + ",\n")
    elif idd == "3":
        a3.append("Sphere," + ",".join(sp[1:-3]) + ",\n")
    elif idd == "4":
        a4.append("Ellipsoid," + ",".join(sp[1:-2]) + ",\n")

print(a1)
fo.writelines(a1)
fo.writelines(a2)
fo.writelines(a3)
fo.writelines(a4)

fin.close()
fo.close()
