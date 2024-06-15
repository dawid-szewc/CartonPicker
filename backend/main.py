from flask import Flask, Response, request
from flask_cors import CORS
import threading 
import cv2
from processing.camera import Camera, VideoStreamer
from processing.robot import Fanuc
from processing.processor import Processor
from config import Config

setup = Config()
camera = Camera()

lock = threading.Lock()
grayFrame = None

app = Flask(__name__)
CORS(app)
        
processor = Processor(calib_location=setup.calib_location,
                      cardboards_location=setup.cardboards_location,
                      g_params_location=setup.g_params_location,
                      counter_location=setup.counter_location,
                      robot_obj=Fanuc(ip=setup.robot_ip))

video_streamer = VideoStreamer(camera, processor, lock)

def stream_frames():
    while True:
        frame = video_streamer.get_frame()
        if frame is None:
            continue
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')


@app.route("/feed_gray")
def feed_gray():
    return Response(stream_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


def main():
    streamer_thread = threading.Thread(target=video_streamer.start)
    streamer_thread.daemon = True
    streamer_thread.start()


if __name__ == '__main__':
    main()
    app.run(host=setup.host, port=setup.port, debug=setup.debug, threaded=True, use_reloader=False)
    camera.stop_grabbing()
