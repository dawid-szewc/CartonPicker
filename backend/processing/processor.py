import pickle
import numpy as np
import cv2
import json
import math
import itertools
from .robot import RobotController, Robot
from .carton import Carton, Hole

class Counter:
    def __init__(self, counter_location: str) -> None:
        self.counter_location = counter_location
        
    def get(self, param: str) -> int:
        with open(self.counter_location, 'r') as file:
            value = json.load(file)
        return int(value[param])
    
    def increment(self, param: str) -> None:
        with open(self.counter_location, 'r+') as file:
            data = json.load(file)
            data[param] += 1
            file.seek(0)
            json.dump(data, file)

class Processor:
    def __init__(self,
                 calib_location: str,
                 cardboards_location: str,
                 g_params_location: str,
                 counter_location: str,
                 robot_obj: Robot) -> None:
        self.counter = Counter(counter_location)
        self.exposure = None
        self.robot = RobotController(robot_obj)
        self.hole = Hole(min_area=0,
                         max_area=0,
                         min_radius=0,
                         max_radius=0)
        self.carton = Carton(area_min=0,
                             area_max=0,
                             epsilon_min=0,
                             epsilon_max=0,
                             ratio_min=0,
                             ratio_max=0,
                             width=0,
                             program=0,
                             variant=0,
                             description="")
        
        with open(calib_location, "rb") as file:
            self.undistort_matrix = pickle.load(file)
        with open(cardboards_location) as file:
            self.carton_program = json.load(file)
        with open(g_params_location) as file:
            self.g_params = json.load(file)
    
    def carton_width(self) -> None:
        self.carton.width = self.carton_program['cardboards'][f'{self.carton.program}']['variants'][f'{self.carton.variant}']['width']

    def cartio_ratio(self) -> None:
        ratio = self.carton_program['cardboards'][f'{self.carton.program}']['variants'][f'{self.carton.variant}']['ratio']
        self.carton.ratio_min = ratio - 0.4 # Offset value
        self.carton.ratio_max = ratio + 0.4 # Offset value

    def run(self, img, camera) -> np.ndarray:
        #print("Flaga robota pocztek run:", self.robot.flag)   
        # Temporary solution
        draw_cross = False
        
        # Undistort image
        gray = self.undistort(img)

        # Prepare carton info
        self.caron_parameters()
        self.carton_width()
        self.cartio_ratio()
        
        # set camera parameters
        camera.set_exposure(self.exposure)
        camera.set_gain(10)
        
        # Draw black border around workspace
        self.draw_border_frame(gray, (0, 0, 0))
        blank = np.zeros((gray.shape[0], gray.shape[1]), dtype=np.uint8)
        erode = self.erode_image(gray)
        
        if draw_cross:
            self.draw_center_cross(gray)
        
        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        angles, centers = self.get_holes(gray, erode)

        self.draw_text(gray, (255, 255, 255), [f"range: {self.carton.description}", f"cardboard: {self.carton.program}", f"variant: {self.carton.variant}", f"counter: {self.counter.get('total')}"])

        # Return frame if not found 4 holes
        if len(centers) < 4: 
            return gray
        
        # Squares with similar angles
        m = self.matches(angles, 5)
        self.draw_cardboard_rect(m, centers, blank)
        self.check_valid_rect(gray, blank)
        
        return gray
        
    def undistort(self, img) -> np.ndarray:
        gray = cv2.undistort(img, self.undistort_matrix['mtx'], self.undistort_matrix['dist'], None, self.undistort_matrix['ncmtx'])
        x, y, w, h = self.undistort_matrix['roi']
        return gray[y:y+h, x:x+w]
    
    def get_robot_parameters(self) -> dict:
        return self.robot.get_registers_values((15, 1, 2, 17))
    
    def caron_parameters(self) -> None:
        robot_registers = self.get_robot_parameters()
        self.robot.height = int(robot_registers['height'])
        self.carton.program = int(robot_registers['carton'])
        self.carton.variant = int(robot_registers['variant'])
        self.robot.flag = int(robot_registers['flag'])

        height_ranges = self.carton_program['height_ranges']
        for data in height_ranges:
            if self.robot.height > height_ranges[data]['range_height_min'] and self.robot.height < height_ranges[data]['range_height_max']:
                self.hole.min_area = height_ranges[data]["hole_area_min"]
                self.hole.max_area = height_ranges[data]["hole_area_max"]
                self.hole.min_radius = height_ranges[data]["hole_radius_min"]
                self.hole.max_radius = height_ranges[data]["hole_radius_max"]
                self.carton.area_min = height_ranges[data]["carton_area_min"]
                self.carton.area_max = height_ranges[data]["carton_area_max"]
                self.carton.epsilon_min = height_ranges[data]["epsilon_min"]
                self.carton.epsilon_max = height_ranges[data]["epsilon_max"]
                self.exposure = height_ranges[data]["exposure"]
                self.carton.description = height_ranges[data]["description"]
                break
    
    def draw_border_frame(self, img, color) -> None:
        shape = img.shape
        coords = [((0, 150), (shape[1], 0)), ((0, 0),(50, shape[0])), ((shape[1], 0), (shape[1] - 50, shape[0])), ((0, shape[0] - 100), (shape[1], shape[0]))]
        
        for loc in coords:
            cv2.rectangle(img, loc[0], loc[1], color, thickness=-1)
    
    def erode_image(self, img) -> np.ndarray:
        blur = cv2.blur(img,(int(self.g_params["threshold"]["blur"]), int(self.g_params["threshold"]["blur"])))
        treshold = cv2.adaptiveThreshold(blur, 125, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, int(self.g_params["threshold"]["density1"]), int(self.g_params["threshold"]["density2"]))
        kernel = np.ones((int(self.g_params["threshold"]["kernel"]), int(self.g_params["threshold"]["kernel"])), np.uint8)
        dilate = cv2.dilate(treshold, kernel, iterations=int(self.g_params["threshold"]["dilate"]))
        erode = cv2.erode(dilate, kernel, iterations=int(self.g_params["threshold"]["erode"]))
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
        y_position = 35
        x_position = 20
        
        for text in texts:
            cv2.putText(img, text, (x_position, y_position), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
            y_position += 20

            
    def get_holes(self, gray, erode):
        contours, _ = cv2.findContours(erode, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
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
            w = math.sqrt((box[2][0] - box[3][0]) * (box[2][0] - box[3][0]) + (box[3][1] - box[2][1]) * (box[3][1] - box[2][1]))
            h = math.sqrt((box[3][0] - box[0][0]) * (box[3][0] - box[0][0]) + (box[3][1] - box[0][1]) * (box[3][1] - box[0][1]))

            # Box angle correction
            if w < h:
                rect = (rect[0], sorted(rect[1]), abs(rect[2] - 90))

            # Filtering area
            if area > self.hole.min_area and area < self.hole.max_area:
                
                # Filtering radius
                if radius > self.hole.min_radius and radius < self.hole.max_radius:
                    try:
                        ratio = rect[1][1] / rect[1][0]
                    except ZeroDivisionError:
                        continue

                    # Ratio of two sides of a rectangle
                    if ratio > 2 and ratio < 6:
                        
                        if rect[2] >= 0 and rect[2] <= 30:
                            angles.append(abs(round(rect[2], 3)))
                            centers.append(center)
                            cv2.drawContours(gray, [box], 0, (255, 0, 0), 2)
                            M = cv2.moments(contour)
                            cX = int(M["m10"] / M["m00"]) # X Center of each hole
                            cY = int(M["m01"] / M["m00"]) # Y Center of each hole
                            cv2.circle(gray, (cX, cY), 3, (0, 255, 0), -1)
        
        return angles, centers
    
    def draw_cardboard_rect(self, m, centers, blank):
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
                            if (ratio > self.carton.ratio_min and ratio < self.carton.ratio_max):
                                area = rect[1][0] * rect[1][1]

                                if area > self.carton.area_min and area < self.carton.area_max:
                                    epsilon = 0.1 * cv2.arcLength(cnt, True)

                                    if epsilon > self.carton.epsilon_min and epsilon < self.carton.epsilon_max:
                                        cv2.drawContours(blank, [cnt], 0, (255, 255, 255), 2)
                                        break
                                    
    def check_valid_rect(self, gray, blank):
        # Image center
        y = int(gray.shape[0] / 2)
        x = int(gray.shape[1] / 2)

        # Finding contour on blank image with prepared contour
        contours, _ = cv2.findContours(blank, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            angle = round(rect[2], 5)
            
            # Carton central point
            c_point = int(rect[0][0]), int(rect[0][1])
            cv2.circle(gray, (c_point), 2, (0, 255, 0), 3)

            # Assigning the longest and the shortest line from pytaghoras formula
            w = math.sqrt((box[2][0] - box[3][0]) * (box[2][0] - box[3][0]) + (box[3][1] - box[2][1]) * (box[3][1] - box[2][1]))
            h = math.sqrt((box[3][0] - box[0][0]) * (box[3][0] - box[0][0]) + (box[3][1] - box[0][1]) * (box[3][1] - box[0][1]))

            # Angle correction with dynamic pixel to mm converter
            if w > h:
                mm = 1 / (w / self.carton.width)
                angle = round((angle + 90) * -1, 5)

            else:
                mm = 1 / (h / self.carton.width)
                angle = angle * -1

            # Sometimes camera while found carton on the image can send incorrect angle to the numeric register, this is correction, dont mind it, it weird but it should be there
            if angle == -90 or angle == 90:
                angle = 0

            # Draw lines to visualization center of the carton
            cv2.line(gray, (x, y), (c_point[0], y), (0, 255, 0), 2)
            cv2.line(gray, (c_point[0], y), (c_point[0], c_point[1]), (0, 0, 255), 2)

            # Position calculation
            X = round((y - c_point[1]) * mm, 5) * -1.0
            Y = round((c_point[0] - x) * mm, 5)


            self.draw_border_frame(gray, (0, 255, 0))
            self.draw_text(gray, (0, 0, 0), ["Position found", f"range: {self.carton.description}", f"cardboard: {self.carton.program}", f"variant: {self.carton.variant}", f"counter: {self.counter.get('total')}"])
            
            if self.robot.flag == 1:
                self.robot.set_register_value(flag=11, payload=float(X), realflag=2) # Send X
                self.robot.set_register_value(flag=12, payload=float(Y), realflag=2) # Send Y
                self.robot.set_register_value(flag=14, payload=float(angle), realflag=2) # Send angle
                self.robot.set_register_value(flag=15, payload=2, realflag=-1) # Send flag
                print("Flaga robota if self.robot.flag == 1: ", self.robot.flag)   
                self.counter.increment('total')
                return
