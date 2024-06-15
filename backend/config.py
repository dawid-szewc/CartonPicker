from dataclasses import dataclass

@dataclass
class Config:
    host: str = '0.0.0.0'
    robot_ip: str = "192.168.125.100"
    port: int = 8000
    debug: bool = True
    calib_location: str = "/home/pi/camera_interface/calib.p"
    cardboards_location: str = "/home/pi/camera_interface/changes/testing2/data/cardboards.json"
    g_params_location:str = "/home/pi/params.json"
    counter_location: str = "/home/pi/camera_interface/changes/testing2/data/picked.json"
