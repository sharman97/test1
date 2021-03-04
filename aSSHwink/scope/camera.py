import imutils
import cv2
import time
from imutils.video.pivideostream import PiVideoStream
from picamera.array import PiRGBArray
from picamera import PiCamera
import threading 

class ScopeStream():
    streaming=False
    still_cap = False
    stillfilename=None

    def __init__(self,name='nameless',func=None,quality=50,set_fps=80,resolution=(320,240)):
        self.name=name
        if func == None:
            self.func= self.do_nothing
        else:
            self.func=func
        self.quality=quality
        self.set_fps=set_fps

        self.resolution=resolution
        self.initStream()
        ScopeStream.stream.camera.shutter_speed = 2000
    
    def initStream(self):
        if not ScopeStream.streaming:
            ScopeStream.stream=PiVideoStream(resolution=self.resolution).start()
            time.sleep(2)
            ScopeStream.streaming=True
            print("[INFO] Stream Started")
        else:
            print("[INFO] Already Streaming")
    
    def do_nothing(self,img):
        return img
    
    def start_stream_object(self):
        while True:
            frame=self.stream.read()
            img=self.func(frame)
            self.img=img
            ret, jpeg = cv2.imencode('.jpg', img)
            img=jpeg.tobytes()
            time.sleep((1/self.set_fps)  -0.0047)
            if ScopeStream.still_cap==True:
                self.snap()
                ScopeStream.still_cap=False
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n\r\n')
    
    
    #def process(self):
        
          
    def wait(self):
        self.thread.join()
        
    def capture_still(self,filename=None):
        if filename is not None:
            ScopeStream.stillfilename=filename
        else:
            ScopeStream.stillfilename= 'snap_'+str(int(time.time()))+'.jpg'
        print("Still Capture")
        ScopeStream.still_cap=True

        
    def snap(self):
        ScopeStream.stream.stop()
        print("[[INFO]] Stream Stopped")
        ScopeStream.streaming = False
        time.sleep(0.5)
        ScopeStream.stream.camera.close()
        time.sleep(0.5)
        camera=PiCamera(resolution=(2592,1944))
        camera.shutter_speed = 3000
        time.sleep(0.5)
        print("[[INFO]] Saving High Res to "+'./scope/static/scope/snapshots/'+ScopeStream.stillfilename)
        camera.capture('./scope/static/scope/snapshots/'+ScopeStream.stillfilename, use_video_port=False)
        camera.close()
        
        self.initStream()
        
