import json

class Config():
  def __init__(self, location) -> None:
    try:
      with open(location, 'r') as file:
        self.data = json.load(file)
    except FileNotFoundError:
      print("File not found")
    except json.JSONDecodeError:
      print("Invalid file format")
  
  def get_parameter(self, parameter) -> None:
    return self.data[parameter]
