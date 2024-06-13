import requests
import re
import urllib.request as urllib2

class Robot:
    def __init__(self, ip: str) -> None:
        self.ip = ip


class Fanuc(Robot):
    '''
    Robot interface.
    '''
    def get_register_value(self, register: int) -> int:
        '''
        This method return numeric value of register.
        '''
        url = f'http://{self.ip}/MD/NUMREG.VA'
        for line in requests.get(url).text.split('\n'):
            if line.strip().startswith(f'[{register}]'):
                match = re.search(r'=\s*([0-9]+)', line.strip())
                return match.group(1)
    
    def set_register_value(self, flag: int, payload: int, realflag: int) -> None:
        requests.get(f'http://{self.ip}/karel/ComSet?sValue={payload}&sIndx={flag}&sRealFlag={realflag}&sFc=2')
        
    def get_registers_values(self, registers: tuple) -> dict:
        url = f'http://{self.ip}/MD/NUMREG.VA'
        regs = {"flag": 0, "carton": 0, "variant": 0, "height": 0}
        for line in requests.get(url).text.split('\n'):
            for register in registers:
                if line.strip().startswith(f'[{register}]'):
                    match = re.search(r'=\s*([0-9]+)', line.strip())
                    if register == 1:
                        regs['carton'] = match.group(1)
                    elif register == 2:
                        regs['variant'] = match.group(1)
                    elif register == 15:
                        regs['flag'] = match.group(1)
                    elif register == 17:
                        regs['height'] = match.group(1)
        return regs


class RobotController:
    """
    Controler interface facade.
    """
    def __init__(self, robot: Robot) -> None:
        self.robot = robot
        self.height = None
        
    def get_registers_values(self, registers: tuple) -> dict:
        registers = self.robot.get_registers_values(registers)
        return registers
    
    def set_register_value(self, flag: int, payload: int, realflag: int) -> None:
        self.robot.set_register_value(flag, payload, realflag)
