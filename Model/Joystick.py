import pygame
import math


class Joystick:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.initialize_joystick()

    def initialize_joystick(self):
        if pygame.joystick.get_count() == 0:
            return False
        self.joystick = pygame.joystick.Joystick(0)
        try:
            self.joystick.init()
            return True
        except:
            return False

    def calculate_angle(self):
        if self.joystick is None:
            return None

        x_axis = self.joystick.get_axis(0)
        y_axis = self.joystick.get_axis(1)
        angle = None

        if abs(x_axis) > 0.1 or abs(y_axis) > 0.1:
            angle = math.degrees(math.atan2(-y_axis, x_axis))
            if angle < 0:
                angle += 360
        return angle

    def calculate_strength(self):
        x_axis = self.joystick.get_axis(0)
        y_axis = self.joystick.get_axis(1)

        return math.sqrt(x_axis ** 2 + y_axis ** 2)


    def map_triggers(self, max_increase=0.1):
        if self.joystick is None:
            return None

        right_trigger = (self.joystick.get_axis(5) + 1) / 2
        left_trigger = (self.joystick.get_axis(2) + 1) / 2

        return max((right_trigger - left_trigger) * max_increase, 0.0)

    def process_events(self):
        pygame.event.pump()


