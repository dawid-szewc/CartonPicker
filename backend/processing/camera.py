from pypylon import pylon
import pickle
import numpy as np
import cv2
from threading import Lock
import json
import math
import itertools
from .robot import RobotController, Robot


class Camera:
    def __init__(self) -> None:
        self.camera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    def grab_frame(self):
        grabResult = self.camera.RetrieveResult(
            5000, pylon.TimeoutHandling_ThrowException
        )
        if grabResult.GrabSucceeded():
            image = self.converter.Convert(grabResult)
            img = image.GetArray()
            grabResult.Release()
            return img
        return None

    def stop_grabbing(self):
        self.camera.StopGrabbing()

    def set_exposure(self, exposure):
        self.camera.ExposureTime.SetValue(exposure)

    def set_gain(self, gain):
        self.camera.Gain.SetValue(gain)


class ImageProcessor:
    def __init__(self, calib_location, robot: Robot) -> None:
        self.robot_controller = RobotController(robot)
        with open(calib_location, "rb") as file:
            self.undistort_matrix = pickle.load(file)
        with open("/home/pi/camera_interface/sample.json") as file:
            self.carton_program = json.load(file)
        with open("/home/pi/params.json") as file:
            self.g_params = json.load(file)

    def run(self, img, camera) -> np.ndarray:
        # camera logic implementation
        gray = self.__undistort(img)
        robot_registers = self.get_robot_parameters()
        robot_height = int(robot_registers["height"])
        if robot_height == 0:
            robot_height = 4000
        carton = int(robot_registers["carton"])
        variant = int(robot_registers["variant"])
        flag = int(robot_registers["flag"])

        for x in self.carton_program[f"{carton}"][f"{variant}"]:
            if robot_height >= x["z_min"] and robot_height <= x["z_max"]:
                preset = x["preset"]
                min_area = x["min_area"]
                max_area = x["max_area"]
                min_radius = x["min_radius"]
                max_radius = x["max_radius"]
                area2_min = x["area2_min"]
                area2_max = x["area2_max"]
                epsilon_min = x["epsilon_min"]
                epsilon_max = x["epsilon_max"]
                exposure = x["exposure"]
                carton_ratio_min = x["carton_ratio_min"]
                carton_ratio_max = x["carton_ratio_max"]
                carton_width = x["carton_width"]
                break

        camera.set_exposure(exposure)
        camera.set_gain(10)

        self.draw_border_frame(gray, (0, 0, 0))
        blank = np.zeros((gray.shape[0], gray.shape[1]), dtype=np.uint8)
        erode = self.erode_image(gray)
        self.draw_center_cross(gray)

        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        angles, centers = self.get_holes(
            gray, erode, min_area, max_area, min_radius, max_radius
        )

        self.draw_text(
            gray,
            (255, 255, 255),
            [f"{preset}", f"Current program: {carton}, producent: {variant}"],
        )

        if len(centers) < 4:  # If algorithm not found 4 holes, return frame
            return gray

        # Squares with similar angles
        m = self.matches(angles, 5)
        self.draw_cardboard_rect(
            m,
            centers,
            carton_ratio_min,
            carton_ratio_max,
            area2_min,
            area2_max,
            epsilon_min,
            epsilon_max,
            blank,
        )
        self.check_valid_rect(carton_width, preset, carton, variant, flag, gray, blank)

        return gray

    def __undistort(self, img) -> np.ndarray:
        gray = cv2.undistort(
            img,
            self.undistort_matrix["mtx"],
            self.undistort_matrix["dist"],
            None,
            self.undistort_matrix["ncmtx"],
        )
        x, y, w, h = self.undistort_matrix["roi"]
        return gray[y : y + h, x : x + w]

    def get_robot_parameters(self) -> dict:
        return self.robot_controller.get_registers_values((15, 1, 2, 17))

    def draw_border_frame(self, img, color) -> None:
        shape = img.shape
        coords = [
            ((0, 150), (shape[1], 0)),
            ((0, 0), (50, shape[0])),
            ((shape[1], 0), (shape[1] - 50, shape[0])),
            ((0, shape[0] - 100), (shape[1], shape[0])),
        ]

        for loc in coords:
            cv2.rectangle(img, loc[0], loc[1], color, thickness=-1)

    def erode_image(self, img) -> np.ndarray:
        blur = cv2.blur(
            img,
            (
                int(self.g_params["threshold"]["blur"]),
                int(self.g_params["threshold"]["blur"]),
            ),
        )
        treshold = cv2.adaptiveThreshold(
            blur,
            125,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            int(self.g_params["threshold"]["density1"]),
            int(self.g_params["threshold"]["density2"]),
        )
        kernel = np.ones(
            (
                int(self.g_params["threshold"]["kernel"]),
                int(self.g_params["threshold"]["kernel"]),
            ),
            np.uint8,
        )
        dilate = cv2.dilate(
            treshold, kernel, iterations=int(self.g_params["threshold"]["dilate"])
        )
        erode = cv2.erode(
            dilate, kernel, iterations=int(self.g_params["threshold"]["erode"])
        )
        return erode

    def draw_center_cross(self, img) -> None:
        w = img.shape[1]
        h = img.shape[0]
        cv2.line(img, (int(w / 2), 0), (int(w / 2), h), (255, 255, 255), 1)
        cv2.line(img, (0, int(h / 2)), (w, int(h / 2)), (255, 255, 255), 1)

    def matches(self, val, pre):
        val = np.array(val)
        out = []

        for i in val:
            condition = np.logical_and(val >= i - pre, val <= i + pre)
            if np.count_nonzero(condition) >= 4:
                out = np.where(condition)
        return out

    def draw_text(self, img, color, texts: list) -> None:
        y_position = 15
        x_position = 20

        for text in texts:
            cv2.putText(
                img,
                text,
                (x_position, y_position),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )
            y_position += 15

    def get_holes(self, gray, erode, min_area, max_area, min_radius, max_radius):
        contours, hier = cv2.findContours(erode, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        angles = []
        centers = []

        for contour in contours:
            rect = cv2.minAreaRect(contour)
            box = np.int0(cv2.boxPoints(rect))
            area = rect[1][0] * rect[1][1]
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            rect = (rect[0], sorted(rect[1]), abs(rect[2]))

            # Calculating width and height of each boxes using pythagoras formula
            w = math.sqrt(
                (box[2][0] - box[3][0]) * (box[2][0] - box[3][0])
                + (box[3][1] - box[2][1]) * (box[3][1] - box[2][1])
            )
            h = math.sqrt(
                (box[3][0] - box[0][0]) * (box[3][0] - box[0][0])
                + (box[3][1] - box[0][1]) * (box[3][1] - box[0][1])
            )

            # Box angle correction
            if w < h:
                rect = (rect[0], sorted(rect[1]), abs(rect[2] - 90))

            # Filtering area
            if area > min_area and area < max_area:
                # Filtering radius
                if radius > min_radius and radius < max_radius:
                    try:
                        ratio = rect[1][1] / rect[1][0]
                    except ZeroDivisionError:
                        continue

                    # Ratio of two sides of a rectangle
                    if ratio > 2 and ratio < 6:
                        if rect[2] >= 0 and rect[2] <= 30:
                            angles.append(abs(round(rect[2], 3)))
                            centers.append(center)
                            cv2.drawContours(gray, [box], 0, (255, 0, 0), 1)
                            M = cv2.moments(contour)
                            cX = int(M["m10"] / M["m00"])  # X Center of each hole
                            cY = int(M["m01"] / M["m00"])  # Y Center of each hole
                            cv2.circle(gray, (cX, cY), 3, (0, 255, 0), -1)

        return angles, centers

    def draw_cardboard_rect(
        self,
        m,
        centers,
        carton_ratio_min,
        carton_ratio_max,
        area_min,
        area_max,
        epsilon_min,
        epsilon_max,
        blank,
    ):
        # Squares coordinates with similar angles
        if m:
            if len(m[0]) >= 4:
                box_b = [[centers[x][0], centers[x][1]] for x in m[0]]

                # Permutation all similar points for check correct arrangement of points
                for i in itertools.permutations(box_b, 4):
                    cnt = np.array(i).astype(np.int32)
                    hull = cv2.convexHull(cnt, returnPoints=False)
                    defect = cv2.convexityDefects(cnt, hull)

                    # Rejection of twisted rectangles
                    if type(defect) == type(None):
                        rect = cv2.minAreaRect(cnt)
                        rect = (rect[0], sorted(rect[1]), rect[2])
                        box = cv2.boxPoints(rect)
                        box = np.int0(box)

                        # Rejection all rectangles which are not looking like valid rectangle
                        if abs(cv2.contourArea(cnt) - cv2.contourArea(box)) < 3000:
                            try:
                                ratio = rect[1][1] / rect[1][0]
                            except ZeroDivisionError:
                                ratio = 0

                            # Ratio of two two sides in rectangle
                            if ratio > carton_ratio_min and ratio < carton_ratio_max:
                                area = rect[1][0] * rect[1][1]

                                if area > area_min and area < area_max:
                                    epsilon = 0.1 * cv2.arcLength(cnt, True)

                                    if epsilon > epsilon_min and epsilon < epsilon_max:
                                        cv2.drawContours(
                                            blank, [cnt], 0, (255, 255, 255), 2
                                        )
                                        break

    def check_valid_rect(
        self, carton_width, preset, carton, variant, flag, gray, blank
    ):
        # Image center
        y = int(gray.shape[0] / 2)
        x = int(gray.shape[1] / 2)

        # Finding contour on blank image with prepared contour
        contours, hier = cv2.findContours(blank, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            cnt = contours[0]
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            area2 = rect[1][0] * rect[1][1]
            angle = round(rect[2], 5)

            # Carton central point
            c_point = int(rect[0][0]), int(rect[0][1])
            cv2.circle(gray, (c_point), 2, (0, 255, 0), 3)

            # Assigning the longest and the shortest line from pytaghoras formula
            w = math.sqrt(
                (box[2][0] - box[3][0]) * (box[2][0] - box[3][0])
                + (box[3][1] - box[2][1]) * (box[3][1] - box[2][1])
            )
            h = math.sqrt(
                (box[3][0] - box[0][0]) * (box[3][0] - box[0][0])
                + (box[3][1] - box[0][1]) * (box[3][1] - box[0][1])
            )

            # Angle correction with dynamic pixel to mm converter
            if w > h:
                mm = 1 / (w / carton_width)
                angle = round((angle + 90) * -1, 5)

            if h > w:
                mm = 1 / (h / carton_width)
                angle = angle * -1

            # Sometimes camera while found carton on the image can send incorrect angle to the numeric register, this is correction, dont mind it, it weird but it should be there
            if angle == -90 or angle == 90:
                angle = 0

            # Draw lines to visualization center of the carton
            cv2.line(gray, (x, y), (c_point[0], y), (0, 255, 0), 1)
            cv2.line(gray, (c_point[0], y), (c_point[0], c_point[1]), (0, 0, 255), 1)

            # Position calculation
            od_x = round((c_point[0] - x) * mm, 5)
            od_y = round((y - c_point[1]) * mm, 5)

            # Conversion for the robot X is -Y
            X = od_y * -1.0
            Y = od_x

            self.draw_border_frame(gray, (0, 255, 0))
            self.draw_text(
                gray,
                (0, 0, 0),
                [
                    f"Position found",
                    f"Carton angle: {angle}",
                    f"Z: {X} mm",
                    f"Y: {Y} mm",
                    f"{preset}",
                    f"Current program: {carton}, producent: {variant}",
                ],
            )

            if flag == 1:
                self.robot_controller.set_register_value(
                    flag=11, payload=X, realflag=2
                )  # Send X
                self.robot_controller.set_register_value(
                    flag=12, payload=Y, realflag=2
                )  # Send Y
                self.robot_controller.set_register_value(
                    flag=14, payload=angle, realflag=2
                )  # Send angle
                self.robot_controller.set_register_value(
                    flag=15, payload=2, realflag=-1
                )  # Send flag


class VideoStreamer:
    def __init__(self, camera: Camera, processor: ImageProcessor, lock: Lock) -> None:
        self.camera = camera
        self.processor = processor
        self.frame = None
        self.lock = lock

    def start(self):
        while self.camera.camera.IsGrabbing():
            img = self.camera.grab_frame()
            if img is not None:
                processed_frame = self.processor.run(img, self.camera)
                with self.lock:
                    self.frame = processed_frame

    def get_frame(self):
        with self.lock:
            return self.frame
