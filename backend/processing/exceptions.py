class UnsupportedCameraError(Exception):
  def __init__(self, message="Implementation not ready for this camera."):
    self.message = message
    super().__init__(self.message)

class UnsupportedRobotError(Exception):
  def __init__(self, message="Implementation not ready for this robot."):
    self.message = message
    super().__init__(self.message)
