from datetime import datetime

class Logger():
  def __init__(self, location: str) -> None:
    self.location = location
    try:
        self.file = open(self.location, 'a+')
    except Exception as e:
        print(e)
  
  def info(self, message: str) -> None:
    self._log(f'INFO: {message}')
  
  def debug(self, message: str) -> None:
    self._log(f'DEBUG: {message}')

  def warning(self, message: str) -> None:
    self._log(f'WARNING: {message}')

  def error(self, message: str) -> None:
    self._log(f'ERROR: {message}')

  def _get_current_time(self) -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  def _log(self, message: str) -> None:
    result = f'{self._get_current_time()} - {message}'
    try:
        self.file.write(result + '\n')
    except Exception as e:
      print(f'{e}')
