from pypylon import pylon
from threading import Lock
from .processor import Processor

class Camera:
    def __init__(self) -> None:
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    
    def grab_frame(self):
        grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        if grabResult.GrabSucceeded():
            image = self.converter.Convert(grabResult)
            img = image.GetArray()
            grabResult.Release()
            return img
        return None
    
    def stop_grabbing(self):
        self.camera.StopGrabbing()

    def set_exposure(self, exposure):
        self.camera.ExposureTime.SetValue(exposure)
    
    def set_gain(self, gain):
        self.camera.Gain.SetValue(gain)
        
                
class VideoStreamer:
    def __init__(self, camera: Camera, processor: Processor, lock: Lock) -> None:
        self.camera = camera
        self.processor = processor
        self.frame = None
        self.lock = lock
    
    def start(self):
        while self.camera.camera.IsGrabbing():
            img = self.camera.grab_frame()
            if img is not None:
                with self.lock:
                    self.frame = self.processor.run(img, self.camera)
    
    def get_frame(self):
        with self.lock:
            return self.frame
