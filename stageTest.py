import numpy as np
import syncmrt.hardware.stage as stage
import os
cwd = os.getcwd()

motorList = cwd+'/resources/motorList.csv'

s = stage(motorList)
s.load('DynMRT')

tx = 5
ty = -5
tz = 7
x = np.deg2rad(0)
y = np.deg2rad(2)
z = np.deg2rad(90)

rx = np.array([[1,0,0,0],[0,np.cos(x),-np.sin(x),0],[0,np.sin(x),np.cos(x),0],[0,0,0,1]])
ry = np.array([[np.cos(y),0,-np.sin(y),0],[0,1,0,0],[np.sin(y),0,np.cos(y),0],[0,0,0,1]])
rz = np.array([[np.cos(z),-np.sin(z),0,0],[np.sin(z),np.cos(z),0,0],[0,0,1,0],[0,0,0,1]])
t = np.array([[1,0,0,tx],[0,1,0,ty],[0,0,1,tz],[0,0,0,1]])

G = t@rz@ry@rx
variables = np.array([tx,ty,tz,np.rad2deg(x),np.rad2deg(y),np.rad2deg(z)])

s.calculateMotion(G,variables)