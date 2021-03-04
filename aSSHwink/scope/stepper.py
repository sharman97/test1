import RPi.GPIO as GPIO
from time import sleep
import sys
import numpy as np
import pickle
import os


class Motor :
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)

    CLOCKWISE=1
    ANTICLOCKWISE=-1
    FULL360=2038
    INIT_STATE=[GPIO.HIGH,GPIO.LOW,GPIO.LOW,GPIO.HIGH]
    FOLDERPATH='./scope/_MotorPositions/'

    def __init__(self, name ,channel=[31,33,35,37],maxpos=12000):
        self.name=name
        if not os.path.exists(Motor.FOLDERPATH):
            os.makedirs(Motor.FOLDERPATH)
        try:
            self.load()
        except Exception:
            
            self.state=Motor.INIT_STATE
            self.position=0
        self.state=Motor.INIT_STATE
        self.maxpos=maxpos           
        self.channel=channel
        GPIO.setup(channel, GPIO.OUT)
        self.save()
        
    def move(self, steps=20,direction=CLOCKWISE, delay=2):
        if delay<2:
            print("[WARNING] Motor speed too high, setting it to maximum")
            delay=2
        for i in range(steps):
            if self.position+direction<0 or self.position+direction>self.maxpos:
                print("[WARNING] Motor Stopped Limit Hit")
                return("[WARNING] Motor Stopped Limit Hit")
                break
            self.state=np.roll(self.state,-direction).tolist()
            GPIO.output(self.channel,self.state)
            self.position=self.position+direction
            sleep(delay/1000)            
        self.save()
        return ("Moved "+str(steps)+" Steps"+"Position: "+str(self.position))
            
    def seek(self,pos,delay=2):
        steps=pos-self.position
        self.move(steps=abs(steps), delay=delay, direction=np.sign(steps))

    def reset_min(self):
        self.position = 0
        self.state = Motor.INIT_STATE;
        self.save()

    def reset_max(self):
        self.position = self.maxpos;
        self.state = Motor.INIT_STATE;
        self.save()

    def load(self):
        f = open(Motor.FOLDERPATH+self.name+'.obj', 'rb')
        tmp_dict = pickle.load(f)
        f.close()          

        self.__dict__.update(tmp_dict) 


    def save(self):
        f = open(Motor.FOLDERPATH+self.name+'.obj', 'wb')
        pickle.dump(self.__dict__, f, 2)
        f.close()
