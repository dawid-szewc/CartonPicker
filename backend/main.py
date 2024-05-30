from flask import Flask, Response, stream_with_context
from flask_cors import CORS
import threading, argparse
import cv2
from processing.camera import Camera, ImageProcessor, VideoStreamer
from processing.robot import Fanuc

lock = threading.Lock()
grayFrame = None

app = Flask(__name__)
CORS(app)

# Global instances
camera = Camera()
robot = Fanuc(ip="192.168.125.100")
processor = ImageProcessor(
    calib_location="/home/pi/camera_interface/calib.p", robot=robot
)
video_streamer = VideoStreamer(camera, processor, lock)


def stream_frames():
    while True:
        frame = video_streamer.get_frame()
        if frame is None:
            continue
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + bytearray(encodedImage) + b"\r\n"
        )


@app.route("/feed_gray")
def feed_gray():
    return Response(
        stream_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def main(runlevel):
    streamer_thread = threading.Thread(target=video_streamer.start)
    streamer_thread.daemon = True
    streamer_thread.start()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-i", "--ip", type=str, required=True, help="ip address of the device"
    )
    ap.add_argument(
        "-o",
        "--port",
        type=int,
        required=True,
        help="ephemeral port number of the server (1024 to 65535)",
    )
    ap.add_argument("-r", "--runlevel", type=int, default=1, help="runlevel")
    args = vars(ap.parse_args())

    main(args["runlevel"])
    app.run(
        host=args["ip"],
        port=args["port"],
        debug=True,
        threaded=True,
        use_reloader=False,
    )
    camera.stop_grabbing()
