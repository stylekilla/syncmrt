import numpy as np
import syncmrt.hardware.stage as stage
import os
cwd = os.getcwd()

motorList = cwd+'/resources/motorList.csv'

s = stage(motorList)
s.load('DynMRT')

np.set_printoptions(formatter={'float': lambda x: "{0:0.2f}".format(x)})

# Left Points: [[ -0.57354312  26.35644294  26.81580788]
#  [-35.83045567 -30.31917351  25.71836707]
#  [ 63.87910219 -33.96387602 -32.07190331]]
# Left Ctd: [  9.1583678  -12.6422022    6.82075721]
# Right Points: [[-13.49948167  37.01392239  35.33400712]
#  [-48.36751869 -23.1485434   35.65805283]
#  [ 53.19313396 -24.33244429 -24.45276326]]
# Right Ctd: [ -2.8912888   -3.48902176  15.5130989 ]
# Patient Isoc: [-0.94397577 -0.06557865  1.02160867]
# Machine Isoc: [ 0.  0.  0.]


tx = 1.76
ty = -0.04
tz = 0.12
x = np.deg2rad(0)
y = np.deg2rad(0)
z = np.deg2rad(0)

rx = np.array([[1,0,0,0],[0,np.cos(x),-np.sin(x),0],[0,np.sin(x),np.cos(x),0],[0,0,0,1]])
ry = np.array([[np.cos(y),0,-np.sin(y),0],[0,1,0,0],[np.sin(y),0,np.cos(y),0],[0,0,0,1]])
rz = np.array([[np.cos(z),-np.sin(z),0,0],[np.sin(z),np.cos(z),0,0],[0,0,1,0],[0,0,0,1]])
t = np.array([[1,0,0,tx],[0,1,0,ty],[0,0,1,tz],[0,0,0,1]])

G = t@rz@ry@rx
variables = np.array([tx,ty,tz,np.rad2deg(x),np.rad2deg(y),np.rad2deg(z)])

s.calculateMotion(G,variables)
s.applyMotion()