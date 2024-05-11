from collections.abc import Generator
from typing import Tuple, Optional
import numpy as np
from .logger import Logger
from .robot import Fanuc, ABB, Kuka
from .camera import PiCamera, CvCamera, Basler

class Processing:
  def __init__(self, robot: Tuple[str, str, int], camera_type: str, logger: Optional[Logger] = None, **kwargs) -> None:
    self.logger = logger
    robot_type, ip_address, port = robot
    robot_map = {
      "Fanuc": Fanuc,
      "ABB": ABB,
      "Kuka": Kuka
    }
    camera_map = {
      "PiCamera": PiCamera,
      "CvCamera": CvCamera,
      "Basler": Basler
    }
    robot_class = robot_map.get(robot_type)
    if robot_class is None:
        raise ValueError("Unknown robot type")
    camera_class = camera_map.get(camera_type)
    if camera_class is None:
        raise ValueError("Unknown camera type")

    robot_kwargs = kwargs.get('robot_kwargs', {})
    robot_kwargs.update({"ip_address": ip_address, "port": port})

    self.robot = robot_class(**robot_kwargs)
    self.camera = camera_class(**kwargs.get('camera_kwargs', {}))
  
  def __del__(self):
    try:
      self.camera.stop()
    except Exception as e:
      if self.logger:
        self.logger.error(f"Camera can't be stoped:{e}")

  def processing(self) -> Generator:
    for frame in self.camera.run():
      frame = self.process_frame(frame).tobytes()
      yield (b'--frame\r\n'
             b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
  
  def process_frame(self, frame) -> np.ndarray:
    return frame


class ProcessingFacade:
  '''
  Facade for managing the image processing and robot data.
  '''
  def __init__(self, robot: Tuple[str, str, int], camera_type: str,
               logger: Optional[Logger] = None, **kwargs) -> None:
    '''
    Initializes the ProcessingFacade with the specified robot and camera types.

    Args:
        robot_type (str): The type of robot to use ("Fanuc", "ABB", "Kuka").
        camera_type (str): The type of camera to use ("PiCamera", "CvCamera", "Basler").
        logger (Logger): optional parameter if you want log events.
        **kwargs: Additional keyword arguments for robot and camera initialization.
    '''
    self.logger = logger
    self.processing = Processing(robot, camera_type, **kwargs)

  def start_processing(self) -> Generator:
    '''
    Return processed generator
    '''
    self.logger.info("Start processing")
    for frame in self.processing.processing():
      yield frame
