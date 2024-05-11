from abc import ABC, abstractmethod
from collections.abc import Generator
import cv2
from .exceptions import UnsupportedCameraError

class Camera(ABC):
  @abstractmethod
  def run(self) -> Generator:
    return Generator


class PiCamera(Camera):
  def __init__(self) -> None:
    raise UnsupportedCameraError

  def __del__(self) -> None:
    pass

  def run(self) -> Generator:
    return Generator
  
  def stop(self) -> None:
    self.__del__


class CvCamera(Camera):
  def __init__(self) -> None:
    self.cap = cv2.VideoCapture(0)

  def __del__(self) -> None:
    self.cap.release()

  def run(self) -> Generator:
    while True:
      success, frame = self.cap.read()
      if not success:
          break
      else:
          buffer = cv2.imencode('.jpg', frame)[1]
          yield buffer
  def stop(self) -> None:
    self.__del__


class Basler(Camera):
  def __init__(self) -> None:
    raise UnsupportedCameraError

  def __del__(self) -> None:
    pass

  def run(self) -> Generator:
    return Generator
  
  def stop(self) -> None:
    self.__del__
