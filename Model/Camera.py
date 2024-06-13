import cv2
import numpy as np
import threading
import queue

class Camera:
    _instance = None
    _lock = threading.Lock()
    _current_instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(Camera, cls).__new__(cls)
                    cls._instance.init_camera(*args, **kwargs)
                    cls._current_instance = cls._instance
                else:
                    cls._current_instance.stop()
                    cls._instance = super(Camera, cls).__new__(cls)
                    cls._instance.init_camera(*args, **kwargs)
                    cls._current_instance = cls._instance
        return cls._instance

    def init_camera(self, index=0):
        self.camera = None
        self.index = index
        self.frame_queue = queue.Queue(maxsize=1)
        self.init_successful = False
        self.Pc = None
        self.stopped = False

        # Start the thread to initialize the camera and read frames
        self.thread = threading.Thread(target=self.initialize_camera)
        self.thread.start()
        self.thread.join()

        # Start the thread to read frames continuously
        self.read_thread = threading.Thread(target=self.read_frames, daemon=True)
        self.read_thread.start()

    def initialize_camera(self):
        self.camera = cv2.VideoCapture(self.index)
        if self.camera.isOpened():
            self.init_successful = True
        else:
            print("Error: Unable to open camera")

    def read_frames(self):
        while not self.stopped:
            if self.camera:
                ret, frame = self.camera.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Ensure the queue always has the latest frame
                    if not self.frame_queue.full():
                        self.frame_queue.put(frame)
                    else:
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put(frame)
                        except queue.Empty:
                            pass

    def crop_image(self, frame):
        if frame is None:
            print("Error: Image not provided.")
            return None
        return frame[100:400, 170:470]

    def rotate_image(self, frame):
        if frame is None:
            print("Error: Image not provided.")
            return None
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    def GetPosition(self, frame):
        if frame is not None:
            Image = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            ret, BinaryImage = cv2.threshold(Image, 110, 255, cv2.THRESH_BINARY_INV)
            kernel = np.ones((3, 3), np.uint8)
            dilate = cv2.dilate(BinaryImage, kernel, iterations=1)
            contours, _ = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    self.Pc = np.array([cx, cy])
                    return self.Pc
        return None

    def overlay_point(self, frame, random, radius=2, color=(255, 0, 0), thickness=-1):
        cv2.circle(frame, (random[0], random[1]), radius, color, thickness)
        return frame

    def get_image_pos(self):
        try:
            frame = self.frame_queue.get(timeout=1)  # Timeout to avoid blocking indefinitely
            if frame is not None:
                cropped_frame = self.crop_image(frame)
                rotated_frame = self.rotate_image(cropped_frame)
                pos = self.GetPosition(rotated_frame)
                return rotated_frame, pos
        except queue.Empty:
            return None, None

    def stop(self):
        self.stopped = True
        if self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()
