from abc import ABC, abstractmethod
import requests
import re

class Robot(ABC):
    def __init__(self, ip: str) -> None:
        self.ip = ip
    
    @abstractmethod
    def set_register_value(self, flag: int, payload: float, realflag: int) -> None:
        pass

    @abstractmethod
    def get_registers_values(self, registers: tuple) -> dict:
        pass

class Fanuc(Robot):
    def set_register_value(self, flag: int, payload: float, realflag: int) -> None:
        requests.get(f'http://{self.ip}/karel/ComSet?sValue={payload}&sIndx={flag}&sRealFlag={realflag}&sFc=2')
        
    def get_registers_values(self, registers: tuple) -> dict:
        url = f'http://{self.ip}/MD/NUMREG.VA'
        regs = {"flag": 0, "carton": 0, "variant": 0, "height": 0}
        for line in requests.get(url).text.split('\n'):
            for register in registers:
                if line.strip().startswith(f'[{register}]'):
                    match = re.search(r'=\s*([0-9]+)', line.strip())
                    if match:
                        if register == 1:
                            regs['carton'] = int(match.group(1))
                        elif register == 2:
                            regs['variant'] = int(match.group(1))
                        elif register == 15:
                            regs['flag'] = int(match.group(1))
                        elif register == 17:
                            regs['height'] = int(match.group(1))
        return regs


class RobotController:
    def __init__(self, robot: Robot) -> None:
        self.robot = robot
        self.height: int
        self.flag: int
        
    def get_registers_values(self, registers: tuple) -> dict:
        return self.robot.get_registers_values(registers)
    
    def set_register_value(self, flag: int, payload: float, realflag: int) -> None:
        self.robot.set_register_value(flag, payload, realflag)
