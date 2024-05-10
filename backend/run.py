from config.config import Config
from processing.logger import Logger
from processing.processor import ProcessingFacade

from flask import Flask, Response

app = Flask(__name__)

logger = Logger('output.log')
config = Config('config/config.json')
vision = ProcessingFacade(robot=('Fanuc', '1.1.1.1', 5000), camera_type='CvCamera', logger=logger)

def gen_frames():
  for frame in vision.start_processing():
    yield frame

@app.route('/feed')
def video_feed():
  return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
  app.run(debug=True, host=config.get_parameter("host"), port=config.get_parameter("port"))
