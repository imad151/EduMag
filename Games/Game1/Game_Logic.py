import math
import time
import cv2
import numpy as np
from Camera import Camera

class GameLogic:
    def __init__(self):
        self.Camera = Camera()
        self.score = 0
        self.frame, self.pos = self.Camera.get_image_pos()
        self.random = self.RNG(self.pos)

    def start_game(self, duration):
        starting_time = time.time()
        while time.time() < starting_time + duration:
            self.frame, self.pos = self.Camera.get_image_pos()
            if self.is_close():
                self.random = self.RNG(self.pos)
                self.score += 1
            self.overlay_point()

            elapsed_time = time.time() - starting_time
            return self.frame, elapsed_time

    def RNG(self, pos, max_distance=50, borders=50):
        
        phi = np.random.uniform(0, 2 * np.pi)
        r = np.random.uniform(0, max_distance)
            
        x = r * np.cos(phi) + 150
        y = r * np.sin(phi) + 150
                     
        return np.array([int(x), int(y)])

    def is_close(self, error=7):
        return math.sqrt((self.random[0] - self.pos[0]) ** 2 + (self.random[1] - self.pos[1]) ** 2) < error

    def overlay_point(self, radius=3, color=(0, 0, 255), thickness=-1):
        if self.pos is not None:
            cv2.circle(self.frame, (self.random[0], self.random[1]), radius, color, thickness)

