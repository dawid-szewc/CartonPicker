from abc import ABC, abstractmethod
from .exceptions import UnsupportedRobotError

class Robot(ABC):
  @abstractmethod
  def set_register(self) -> None:
    pass

  @abstractmethod
  def get_register(self) -> None:
    pass


class Fanuc(Robot):
  def __init__(self, ip_address: str, port: int) -> None:
    self.ip_address = ip_address
    self.port = port

  def set_register(self) -> None:
    pass

  def get_register(self) -> None:
    pass


class Kuka(Robot):
  def __init__(self) -> None:
    raise UnsupportedRobotError

  def set_register(self) -> None:
    pass

  def get_register(self) -> None:
    pass


class ABB(Robot):
  def __init__(self) -> None:
    raise UnsupportedRobotError

  def set_register(self) -> None:
    pass

  def get_register(self) -> None:
    pass
