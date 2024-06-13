import sys
import time
from PyQt5 import uic
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene
import numpy as np

from Model.EduMag import EduMag
from Model.Joystick import Joystick
from Model.Camera import Camera
from Model.Serial_Comm import SerialComm


class Game_1(QMainWindow):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()

        uic.loadUi('Games/Game1/game1.ui', self)

        self.initialize_classes()
        self.connect_angle_buttons()
        self.timer = QTimer()
        self.setup_timer()

        _ = self.Serial.open('/dev/tty/USB0') # Only for Pi. Use virtual ports to run on lappy

        self.start_button.stateChanged.connect(self.start_game)


        # Currents
        self.B_spinbox.valueChanged.connect(self.Compute_Currents)
        self.F_spinbox.valueChanged.connect(self.Compute_Currents)
        self.theta_spinbox.valueChanged.connect(self.Compute_Currents)

        # Joystick
        self.timer.timeout.connect(self.Joy_Enabled)

        # Camera
        self.CamScene = QGraphicsScene()
        self.game1_cam.setScene(self.CamScene)
        self.Camera_Checkbox.stateChanged.connect(self.setup_timer)

        # Close

    def initialize_classes(self):
        self.Edumag = EduMag()
        self.Camera = Camera()
        self.joystick = Joystick()
        self.Serial = SerialComm()

    def setup_timer(self):
        self.timer.start(30)
        if self.Camera_Checkbox.isChecked():
            self.timer.timeout.connect(self.update_frame)


    def start_game(self):
        if self.start_button.isChecked():
            self.game_duration = self.time_spinbox.value()
            self.start_time = time.time()
            self.target_point = np.array([150, 150])
            self.score_spinbox.setValue(0)
        else:
            self.time_spinbox.setValue(60)
            self.B_spinbox.setValue(0)
            self.F_spinbox.setValue(0)

    def RNG(self, max_distance=40):

        phi = np.random.uniform(0, 2 * np.pi)
        r = np.random.uniform(0, max_distance)

        x = r * np.cos(phi) + 150
        y = r * np.sin(phi) + 150

        return np.array([int(x), int(y)])

    def update_frame(self):
        if self.start_button.isChecked() and time.time() - self.start_time <= self.game_duration:
            elapsed_time = time.time() - self.start_time
            self.time_spinbox.setValue(int(self.game_duration - elapsed_time))

            frame, pos = self.Camera.get_image_pos()
            frame = self.Camera.overlay_point(frame, self.target_point)

            self.display_frame(frame)

            if np.linalg.norm(pos - self.target_point) <= 5:
                self.target_point = self.RNG()
                self.score_spinbox.setValue(self.score_spinbox.value() + 1)

        else:
            self.start_button.setCheckState(False)
            frame, _ = self.Camera.get_image_pos()
            self.display_frame(frame)


    def display_frame(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.CamScene.clear()
        self.CamScene.addPixmap(pixmap)
        self.game1_cam.fitInView(self.CamScene.sceneRect(), Qt.KeepAspectRatio)

    def Joy_Enabled(self):
        if self.joystick_checkbox.isChecked():
            if not self.joystick.initialize_joystick():
                return
            self.B_spinbox.setValue(self.B_spinbox.value() + self.joystick.map_triggers())
            self.F_spinbox.setValue(0.25 * self.joystick.calculate_strength() * (-38.563 * self.B_spinbox.value() + 997.3362))
            angle = self.joystick.calculate_angle()
            if angle is not None:
                self.theta_spinbox.setValue(angle)

    def Compute_Currents(self):
        max_current = -38.563 * self.B_spinbox.value() + 997.3362
        self.F_spinbox.setMaximum(max_current)
        self.F_spinbox.setSingleStep(max_current / 15)
        I = self.Edumag.SetFieldForce(self.B_spinbox.value(), self.F_spinbox.value(), self.theta_spinbox.value())
        self.send_currents(I)

    def send_currents(self, I):
        try:
            self.Serial.send(I)
        except:
            pass

    def connect_angle_buttons(self):
        self.angle_buttons = [self.angle_0, self.angle_45, self.angle_90, self.angle_135,
                              self.angle_180, self.angle_225, self.angle_270, self.angle_315]
        for button, value in zip(self.angle_buttons, range(0, 361, 45)):
            button.pressed.connect(lambda val=value: self.button_mapping(val))

    def button_mapping(self, value):
        self.theta_spinbox.setValue(value)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Game_1()
    window.setWindowTitle("Whack a Mole")
    window.showMaximized()
    sys.exit(app.exec_())
