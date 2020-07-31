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
#Of course, make sure that each sensor has data (is post processed) in your PreonLab scene


import preonpy
import numpy
import glob
#import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D

#Load file. If several are available, only the first one will be loaded !
File = glob.glob('*.prscene')
s = preonpy.Scene(File[0])

#Find names of heat flux sensors in the scene
HeatFluxSensors = []
for obj_name in s.object_names:
        obj = s.find_object(obj_name)
        if obj.type == "Heat flux sensor":
            HeatFluxSensors.append(obj)
            print(obj_name + " is Heat flux sensor")

#HeatFluxSensor = HeatFluxSensors[0]
for HeatFluxSensor in HeatFluxSensors :
    
    #Make sure a sensor plane is connected
    sensor_plane_connected_bool = 0
    if len(HeatFluxSensor.get_connected_objects("SensorPlaneTemperature", False)) != 0 :
        sensor_plane_connected_bool = 1
    else :
        print(HeatFluxSensor.name + " is not linked to a sensor plane ! This is necessary to get global HTC. This sensor will be ignored")
    
    #Make sure a keyframing is done
    keyframe_is_done_bool = 0
    if len(HeatFluxSensor.get_keyframes("behavior")) != 0 : 
        keyframe_is_done_bool = 1
    else :
        print(HeatFluxSensor.name + " is not keyframed ! This sensor will be ignored")  

    if (sensor_plane_connected_bool and keyframe_is_done_bool) :    
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
        SensorActiveFrames = Frames[Activity==1]
        if len(SensorActiveFrames) == 0 :
            print(HeatFluxSensor.name + " Is never active and will be ignored !")   
        else : 
            SensorActiveBeginEnd = [preonpy.to_seconds(frame = SensorActiveFrames[0], scene=s, view = False), preonpy.to_seconds(frame = SensorActiveFrames[-1], scene=s, view = False)]
            print(HeatFluxSensor.name + " activity frames are " + str(SensorActiveFrames))

            #Find positions 
            s.load_frame(0)
            with Solid.particle_buffers() as buffers:
                position_buffer = numpy.array(buffers["Position"], copy=False)
            Surface_Area_buffer = numpy.array(HeatFluxSensor.sensor_buffers(True)["SurfaceArea"], copy=False)
            x = position_buffer[:,0]
            y = position_buffer[:,1]
            z = position_buffer[:,2]
            Surface_Area = Surface_Area_buffer
            #Close buffers
            del buffers
            del position_buffer
            del Surface_Area_buffer
        
            #Initialize Vals
            Size_Of_Vals = len(x)
            HeatFlux = numpy.zeros(Size_Of_Vals)
            HTC = numpy.zeros(Size_Of_Vals)
            Surface_Area = numpy.zeros(Size_Of_Vals)
                       
            print("Let's parse " + HeatFluxSensor.name + " data!")
            for frame in SensorActiveFrames:
                
                print("Parsing frame " + str(frame) + "in a list of " + str(len(SensorActiveFrames)) + " frames")
                #Set current frame    
                s.load_frame(frame)
        
                #Find values in buffer
                HeatFlux_buffer = numpy.array(HeatFluxSensor.sensor_buffers(True)["HeatFlux"], copy=False)
                HTC_buffer = numpy.array(HeatFluxSensor.sensor_buffers(True)["HeatTransferCoefficient"], copy=False)
                
                #Do an average without loading all frames
                HeatFlux = HeatFlux+(HeatFlux_buffer/len(SensorActiveFrames))
                HTC = HTC + (HTC_buffer/len(SensorActiveFrames))
                #Close buffers
                del HeatFlux_buffer
                del HTC_buffer
                
            #Get ref temp with right shape
            ref_temp = numpy.ones(Size_Of_Vals)*SensorPlane.get_statistic_avg("mean temp.", SensorActiveBeginEnd[0], SensorActiveBeginEnd[1])
        
            #Write file
            print("Writing " + HeatFluxSensor.name + " data!")
            NAMES = numpy.array(['X','Y','Z','REF_TEMP','CONV_HTC','HEAT_FLUX'])
            result = numpy.vstack((NAMES,numpy.transpose(numpy.array([x,y,z,ref_temp,HTC,HeatFlux]))))
            numpy.savetxt((HeatFluxSensor.name + "_AVG.csv"), result, delimiter="," , fmt="%s")
            print("Done writing " + HeatFluxSensor.name + " data!")

print("Done!)")
#Show mean heat flux◘
#fig = plt.figure()
#ax = fig.add_subplot(111, projection='3d')
#pnt3d = ax.scatter3D(x, y, z, c=HTC, s=0.05)
#cbar=plt.colorbar(pnt3d)
#plt.show()
