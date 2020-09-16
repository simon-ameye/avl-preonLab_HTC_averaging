# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 10:03:32 2020

@author:
Simon Ameye
AVL AST FRANCE
Technical Sales/Application support engineer
simon.ameye@avl.com
"""

#Make sure HF sensors activity is on for the last rotation and inactive outside
#Make sure the HF sensors are linked with MeasuredScalarValue with a reference sensor plane
#Also make sure that current_dir and scene_name are filled bellow
#Of course, make sure that each sensor has data (is post processed) in your PreonLab scene


import preonpy
import numpy
import glob

#current_dir = "//frchtwd311130/c$/Data/PREONLAB/VALEO_electrical_system/2020_preonlab_benchmark/02_E-motor_Simulation/Simulation/M24/MAGNA3_WEEK25_to_export"
#scene_name = "ValeoE-motor_rename.prscene"

#current_dir = "//frchtwd311130/c$/Data/PREONLAB/VALEO_electrical_system/2020_preonlab_benchmark/02_E-motor_Simulation/Simulation/M24/MAGNA3_WEEK25_to_export"
#scene_name = "ValeoE-motor_rename.prscene"
header = "SPATIAL\n1.0\tscale_xyz\n0.0\ttrans_x\n0.0\ttrans_y\n0.0\ttrans_z\nx\trot_axis\n0.0\trot_angle\n"

def addheader(filename):
    #Add the CONVERGE style header
    f = open(filename,'r+')
    lines = f.readlines() # read old content
    f.seek(0) # go back to the beginning of the file
    f.write(header) # write new content at the beginning
    for line in lines: # write old content after new
        f.write(line)
    f.close()
    
def sensor_plane_is_connected(HeatFluxSensor):
    #Make sure a sensor plane is connected
    if len(HeatFluxSensor.get_connected_objects("SensorPlaneTemperature", False)) != 0 :
        return 1
    else :
        print(HeatFluxSensor.name + " is not linked to a sensor plane ! This is necessary to get global HTC. This sensor will be ignored")
        return 0
    
def keyframe_is_done(HeatFluxSensor):
    #Make sure a keyframing is done
    if len(HeatFluxSensor.get_keyframes("behavior")) != 0 : 
        return 1
    else :
        print(HeatFluxSensor.name + " is not keyframed ! This sensor will be ignored")
        return 0
    
def find_heat_flux_sensors(s):
    #Find names of heat flux sensors in the scene
    HeatFluxSensors = []
    for obj_name in s.object_names:
        obj = s.find_object(obj_name)
        if obj.type == "Heat flux sensor":
            HeatFluxSensors.append(obj)
            print(obj_name + " is Heat flux sensor")
            return HeatFluxSensors
        
def average_heat_flux(s, SensorActiveFrames, HeatFluxSensor, Size_Of_Vals):
    #Initialize Vals
    HeatFlux = numpy.zeros(Size_Of_Vals)
    HTC = numpy.zeros(Size_Of_Vals)
    for frame in SensorActiveFrames:
        print("Parsing frame " + str(frame) + "in a list of " + str(len(SensorActiveFrames)) + " frames")
        #Set current frame    
        s.load_frame(frame)
        #Find values in buffer
        HeatFlux_buffer = numpy.array(HeatFluxSensor.sensor_buffers(True)["HeatFlux"], copy=True)
        HTC_buffer = numpy.array(HeatFluxSensor.sensor_buffers(True)["HeatTransferCoefficient"], copy=True)
                
        #Do an average without loading all frames
        HeatFlux = HeatFlux+(HeatFlux_buffer/len(SensorActiveFrames))
        HTC = HTC + (HTC_buffer/len(SensorActiveFrames))
    return numpy.array([HTC, HeatFlux]).T

def keys_to_frames(s, keys_frames, keys_val):
    #This will convert KeyFrames into a list of frames where sensor is active
    Frames = numpy.arange(preonpy.to_frame(s.get_statistic_max("Time"), scene=s)+1)
    Activity = numpy.zeros(len(Frames))
    Activity[0] = keys_val[0]
    for i in Frames[1:]:
        for j in range(len(keys_val)):
            if i==keys_frames[j]:
                Activity[i] = keys_val[j]
            else:
                Activity[i] = Activity[i-1]
    return Frames[Activity==1]

#Load file. If several are available, only the first one will be loaded !
File = glob.glob('*.prscene')[0]
#s = preonpy.Scene(current_dir + "/" + scene_name)
s = preonpy.Scene(File)

HeatFluxSensors = find_heat_flux_sensors(s)
for HeatFluxSensor in HeatFluxSensors :
    if (sensor_plane_is_connected(HeatFluxSensor) and keyframe_is_done(HeatFluxSensor)) :    
        #Find solids objects connected to heat flux sensors (only the first one is considered !)
        Solid = HeatFluxSensor.get_connected_objects("TriangleMesh", False)[0]
        print(HeatFluxSensor.name + " gets its mesh from " + Solid.name)
    
        #Find temperature reference sensor plane, if any (only the first one is considered !)
        SensorPlane = HeatFluxSensor.get_connected_objects("SensorPlaneTemperature", False)[0]
        print(HeatFluxSensor.name + " gets its reference temperature from " + SensorPlane.name)
    
        #Find Heat Flux sensor activity frames
        keys = HeatFluxSensor.get_keyframes("behavior")
        keys_times = [key[0] for key in keys] 
        keys_frames = [preonpy.to_frame(key_time, scene=s) for key_time in keys_times]
        keys_val = [1 if i=='active' else 0 for i in [key[1] for key in keys]]
        

        SensorActiveFrames = keys_to_frames(s, keys_frames, keys_val)
        if len(SensorActiveFrames) == 0 :
            print(HeatFluxSensor.name + " Is never active and will be ignored !")   
        else : 
            SensorActiveBeginEnd = [preonpy.to_seconds(frame = SensorActiveFrames[0], scene=s, view = False), preonpy.to_seconds(frame = SensorActiveFrames[-1], scene=s, view = False)]
            print(HeatFluxSensor.name + " activity frames are " + str(SensorActiveFrames))

            #Find positions 
            s.load_frame(0)
            #with Solid.particle_buffers() as buffers:
            xyz             = numpy.array(HeatFluxSensor.sensor_buffers(True)["Position"], copy=True)
            Surface_Area    = numpy.array(HeatFluxSensor.sensor_buffers(True)["SurfaceArea"], copy=True)

            print("Let's parse " + HeatFluxSensor.name + " data!")
            Size_Of_Vals = len(xyz[:,0])
            HTCHeatFlux = average_heat_flux(s, SensorActiveFrames, HeatFluxSensor, Size_Of_Vals)
                
            #Get ref temp with right shape
            ref_temp = numpy.array([numpy.ones(Size_Of_Vals)*SensorPlane.get_statistic_avg("mean temp.", SensorActiveBeginEnd[0], SensorActiveBeginEnd[1])]).T
        
            #Write file
            print("Writing " + HeatFluxSensor.name + " data!")
            NAMES = numpy.array(['x','y','z','REF_TEMP','CONV_HTC','HEAT_FLUX'])
            result = numpy.vstack((NAMES,numpy.concatenate([xyz, ref_temp, HTCHeatFlux], axis = 1)))
#            filename = current_dir + "/" + HeatFluxSensor.name + "_AVG.csv"
            filename = HeatFluxSensor.name + "_AVG.csv"
            numpy.savetxt(filename, result, delimiter="," , fmt="%s")
            print("Done writing " + HeatFluxSensor.name + " data!")
            addheader(filename)
print("Done!)")
#Show mean heat flux
#fig = plt.figure()
#ax = fig.add_subplot(111, projection='3d')
#pnt3d = ax.scatter3D(x, y, z, c=HTC, s=0.05)
#cbar=plt.colorbar(pnt3d)
#plt.show()
