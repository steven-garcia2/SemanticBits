from __future__ import print_function

from threading import Thread

from thrift.transport import TSocket
from thrift.protocol import TBinaryProtocol
from AnvelApi import AnvelControlService
from socket import IPPROTO_TCP, TCP_NODELAY
from AnvelApi.ttypes import *
import time
import inputs
from tkinter import *
import threading
import math
import decimal
import tk_tools

#Global Variables
pose=[None]
poseX=[0,0]
poseY=[0,0]
curTerrain=[None]
newTerrain=[None]
poseVel=[None]
vib=[None]
velX=[None]
velY=[None]
vel=[0, 0, 0]
terrain=[None]


def ConnectToANVEL(address='127.0.0.1', port=9094):
    '''Return a connected ANVEL client object.'''
    trans = TSocket.TSocket(address, port)
    proto = TBinaryProtocol.TBinaryProtocol(trans)
    anv = AnvelControlService.Client(proto)
    trans.open()
    trans.handle.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        # disable buffering for congestion control
    return anv

def runAnvel():
    # connect to ANVEL
    anv = ConnectToANVEL('127.0.0.1', 9094)  # default loopback configuration for the server

    # pause the simulation timer in case it's already running
    anv.SetSimulationState(SimulationState.PAUSED)

    # (re)load the environment, removing any previously-created objects
    anv.LoadEnvironment('Exp1.env')

    # set the view of camera
    view = anv.GetObjectDescriptorByTypeAndName('View', 'World View 1 - Ogre3dCam')
    anv.SetProperty(view.objectKey, 'Position', ' -205 -138.08 90 ')

    # create the vehicle
    veh = anv.CreateObject('RG31 Mk5', 'myVeh', 0, Point3(-280, -62, 15), Euler(0, 0, 0), True)
    #NOTE: Default control is human controller so we are good

    # set camera to watch the vehicle
    viewType = 'LookAt'  # camera position is fixed, but it rotates to look at the vehicle
    anv.SendStringCommandParamList('Vehicles.AttachViewToVehicle', [str(view.objectKey), str(veh.objectKey), viewType, 'Orbital'])

    # get initial vehicle positions and velocity
    pose[0] = anv.GetPoseAbs(veh.objectKey)
    poseVel[0]=anv.GetPoseExtendedRel(veh.objectKey)
    velX[0]=poseVel[0].velocity.x
    velY[0]=poseVel[0].velocity.y


    if ((velX[0] < 0.5) and (velX[0] > -0.5) and (velY[0] < 0.5) and (velY[0] > -0.5)):
        vib[0] = 0;
    else:
        vib[0]=1;

    #Calculate overall Velocity
    temp = velX[0]**2 + velY[0]**2
    vel[0] = math.sqrt(temp)
    vel[1] = '%.3f' % (vel[0])
    vel[2] = '%.0f' % (vel[0])

    #check and print terrain data
    checkTer1(pose[0])
    printTer()

    #Loop to step Anvel simulation
    while (1):
        for i in range(1):
            anv.StepSimulation()

        # get vehicle positions and velocity
        pose[0] = anv.GetPoseAbs(veh.objectKey)
        poseX[0]=pose[0].position.x
        poseY[0]=pose[0].position.y
        poseX[1] = '%.3f' % (poseX[0])
        poseY[1] = '%.3f' % (poseY[0])

        poseVel[0] = anv.GetPoseExtendedRel(veh.objectKey)
        velX[0] = poseVel[0].velocity.x
        velY[0] = poseVel[0].velocity.y

        if ((velX[0] < 0.5) and (velX[0] > -0.5) and (velY[0] < 0.5) and (velY[0] > -0.5)):
            vib[0]=0;
        else:
            vib[0]=1;

        # Calculate overall Velocity
        temp = velX[0] ** 2 + velY[0] ** 2
        vel[0] = math.sqrt(temp)
        vel[1] = '%.3f' % (vel[0])

        checkTer2(pose[0])

        #if terrain has changed, print new terrain info
        if (curTerrain[0] != newTerrain[0]):
            curTerrain[0] = newTerrain[0]
            printTer()

#this function checks what terrain vehicle is on based o9n x and y positions
def checkTer1(position1):
    if (pose[0].position.x < -226 and pose[0].position.x > -282 and pose[0].position.y < -54 and pose[0].position.y > -71):
        terrain[0]='Mud'
        curTerrain[0] = 1;
    elif (pose[0].position.x > -226 and pose[0].position.y < -54 and pose[0].position.y > -71):
        terrain[0]='Dirt Road'
        curTerrain[0] = 2;
    else:
        terrain[0]='Grass'
        curTerrain[0] = 3;

def checkTer2(position1):
    if (pose[0].position.x < -226 and pose[0].position.x > -282 and pose[0].position.y < -54 and pose[0].position.y > -71):
        terrain[0] = 'Mud'
        newTerrain[0] = 1;
    elif (pose[0].position.x > -226 and pose[0].position.y < -54 and pose[0].position.y > -71):
        terrain[0] = 'Dirt Road'
        newTerrain[0] = 2;
    else:
        terrain[0]='Grass'
        newTerrain[0] = 3;


#this function prints the terrain that the vehicle is on
def printTer():
    print('\nPosition = (%.3f m, %.3f m). \nVelocity is %.3f m/s in X and %.3f m/s in Y.' % (poseX[0], poseY[0], velX[0], velY[0]))
    print('Overall Velocity is %.3f.' % (vel[0]))
    if (curTerrain[0]==1):
        print("Position is in mud.");
    elif (curTerrain[0]==2):
        print("Position is on dirt road.");
    else:
        print("Position is in grass.");


def vibrate(gamepad=None):
    while (1):
        if not gamepad:
            gamepad = inputs.devices.gamepads[0]

        #Calculate sleep time. The slower the speed, the greater the pause in vibrations. At fast speeds vibration is constant (sleep time =0)
        if (vel[0] < 2):
            sleepTime = 1.2
        else:
            sleepTime = (3 / (vel[0]))
            if (sleepTime < .3):
                sleepTime=0

        if (vib[0] == 0):
            gamepad.set_vibration(0, 0, 0)
            #print("Velocity is nearly 0. Not vibrating.")
        elif ((curTerrain[0] == 1) and (vib[0] != 0) ):
            # terrain is mud vibration
            gamepad.set_vibration(1, 1, 75)
            time.sleep(sleepTime)
        elif ((curTerrain[0] == 2) and (vib[0] != 0) ):
            # terrain is dirt road vibration
            gamepad.set_vibration(1, 0, 10)
            time.sleep(sleepTime)
        elif ((curTerrain[0] == 3) and (vib[0] != 0) ):
            # terrain is grass vibration
            gamepad.set_vibration(0, 1, 10)
            time.sleep(sleepTime)

def tkinter_user_window():
    root = Tk()
    root.title('Vehicle Information')


    var = StringVar()
    var2 = StringVar()

    max_speed = 20
    global terrain
    speed_gauge = tk_tools.Gauge(root,
                                 max_value=max_speed,
                                 label='Speed',
                                 unit=' m/s',
                                 bg='grey')
    speed_gauge.grid(row=0, column=0, sticky='news')

    def update_gauge():
        global vel
        # update the gauges according to their value
        speed_gauge.set_value(vel[1])

        root.after(50, update_gauge)


    var.set("Gathering terrain data")

    def check():
        if (curTerrain[0] == 1):
            var.set("Terrain is: Mud")
            root.after(50, check)
        elif (curTerrain[0] == 2):
            var.set("Terrain is: Dirt Road")
            root.after(50, check)
        elif (curTerrain[0] == 3):
            var.set("Terrain is: Grass")
            root.after(50, check)
        else:
            var.set("Gathering terrain data")
            root.after(50, check)

    var2.set("Gathering Vehicle Position data")
    def getPose():
        var2.set("Vehicle position is (" + str(poseX[1]) + "m, " + str(poseY[1]) + "m).")
        root.after(50, getPose)

    lbl = Label(root, textvariable=var, anchor=NW, justify=CENTER, bg="grey", fg="white")
    lbl.grid(row=1, column=0, sticky='news')

    lbl = Label(root, textvariable=var2, anchor=NW, justify=CENTER, bg="grey", fg="white")
    lbl.grid(row=2, column=0, sticky='news')


    #    root.after(500, getOverallVel)
    root.after(50, check)
    root.after(50, getPose)
    root.after(50, update_gauge)
    root.mainloop()



def main():
    anvel_thread = threading.Thread(target=runAnvel)
    vibrate_thread = threading.Thread(target=vibrate)
    gui_thread = threading.Thread(target=tkinter_user_window)

    anvel_thread.start()
    vibrate_thread.start()
    gui_thread.start()


if __name__ == "__main__":
    main()
