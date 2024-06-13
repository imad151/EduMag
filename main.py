import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsPixmapItem, QGraphicsScene
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import uic
from PyQt5.QtCore import QTimer, Qt

from Model.Serial_Comm import SerialComm

from Model.EduMag import EduMag
from Model.Joystick import Joystick
from Model.Camera import Camera

from Games.Game1.Game_1 import Game_1
from Games.Game2.Game_2 import Game_2


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.check = 0
        self.initialize_classes()

        # Compute Currents
        self.B_spinbox.valueChanged.connect(self.Compute_Currents)
        self.F_spinbox.valueChanged.connect(self.Compute_Currents)
        self.theta_spinbox.valueChanged.connect(self.Compute_Currents)

        # Serial
        self.SetupSerial()

        # Buttons
        self.connect_angle_buttons()
        self.reset_button.pressed.connect(self.reset_values)

        # Scenes
        self.set_scenes()

        # Timer
        self.connect_timer()

        # Run Games
        self.current_game = None
        self.game_1_instance = None
        self.game_2_instance = None
        self.game1_button.pressed.connect(lambda: self.start_game('1'))
        self.game2_button.pressed.connect(lambda: self.start_game('2'))

    def start_game(self, game):
        if self.current_game:
            self.current_game.close()
            self.current_game = None

        if game == '1':
            self.close()
            self.current_game = Game_1()
            self.current_game.closed.connect(self.close_game)
        elif game == '2':
            self.close()
            self.current_game = Game_2()
            self.current_game.closed.connect(self.close_game)

        self.current_game.showMaximized()

    def close_game(self):
        self.showMaximized()
        self.current_game = None

    def initialize_classes(self):
        self.Edumag = EduMag()
        self.Camera = Camera()
        self.joystick = Joystick()

    def Camera_Enabled(self):
        if self.camera_checkbox.isChecked():
            self.timer.timeout.connect(self.update_frame)
        else:
            try:
                self.timer.timeout.disconnect(self.update_frame)
            except TypeError:
                pass
            self.cam_scene.clear()
            self.camera_status.setText('Camera Disconnected')
            self.camera_status.setStyleSheet("color: Red; font-size: 15px;")

    def connect_timer(self):
        self.timer = QTimer()
        self.timer.start(60)
        self.camera_checkbox.stateChanged.connect(self.Camera_Enabled)
        self.joystick_checkbox.stateChanged.connect(self.Joy_Enabled)

    def update_frame(self):
        frame, _ = self.Camera.get_image_pos()
        if frame is not None:
            self.camera_status.setText('Camera Connected')
            self.camera_status.setStyleSheet("color: Green; font-size: 15px;")
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            self.cam_scene.clear()
            self.cam_scene.addPixmap(pixmap)
            self.cam_view.fitInView(self.cam_scene.sceneRect(), Qt.KeepAspectRatio)
        else:
            self.camera_status.setText('Camera Error')
            self.camera_status.setStyleSheet("color: Red; font-size: 15px;")

    def Joy_Enabled(self):
        if self.joystick_checkbox.isChecked():
            if not self.joystick.initialize_joystick():
                self.joystick_status.setText('Joystick Not Found')
                self.joystick_status.setStyleSheet("color: Red; font-size: 15px;")
            else:
                self.timer.timeout.connect(self.joystick_logic)
                self.joystick_status.setText('Joystick Enabled')
                self.joystick_status.setStyleSheet("color: Green; font-size: 15px;")
        else:
            try:
                self.timer.timeout.disconnect(self.joystick_logic)
            except TypeError:
                pass
            self.joystick_status.setText('Joystick Disabled')
            self.joystick_status.setStyleSheet("color: Red; font-size: 15px;")

    def joystick_logic(self):
        if self.joystick_checkbox.isChecked():
            self.joystick.process_events()
            self.B_spinbox.setValue(self.B_spinbox.value() + self.joystick.map_triggers())
            self.F_spinbox.setValue(0.25 * self.joystick.calculate_strength() * (-38.563 * self.B_spinbox.value() + 997.3362))
            angle = self.joystick.calculate_angle()
            if angle is None:
                self.theta_spinbox.setValue(0)
            else:
                self.theta_spinbox.setValue(angle)


    def Compute_Currents(self):
        max = -38.563 * self.B_spinbox.value() + 997.3362
        self.F_spinbox.setMaximum(max)
        self.F_spinbox.setSingleStep(max / 15)
        I = self.Edumag.SetFieldForce(self.B_spinbox.value(), self.F_spinbox.value(), self.theta_spinbox.value())
        fig = self.Edumag.plot_vecfield(I)
        self.plot_vecfield(fig)
        self.update_current_label(I)

    def plot_vecfield(self, fig):
        if not self.joystick_checkbox.isChecked():
            fig.canvas.draw()
            width, height = fig.canvas.get_width_height()
            self.vec_scene.clear()
            self.vec_scene.addItem(QGraphicsPixmapItem(QPixmap.fromImage(QImage(fig.canvas.buffer_rgba(), width, height, QImage.Format_RGBA8888))))
        else:
            self.vec_view.hide()
            self.label_13.hide()
            self.I1.hide()
            self.I2.hide()
            self.I3.hide()
            self.I4.hide()

    def update_current_label(self, I):
        self.I1.setText(f'{I[0]}')
        self.I2.setText(f'{I[1]}')
        self.I3.setText(f'{I[2]}')
        self.I4.setText(f'{I[3]}')

    def set_scenes(self):
        self.cam_scene = QGraphicsScene()
        self.cam_view.setScene(self.cam_scene)
        self.vec_scene = QGraphicsScene()
        self.vec_view.setScene(self.vec_scene)

    def connect_angle_buttons(self):
        self.angle_buttons = [self.angle_0, self.angle_45, self.angle_90, self.angle_135,
                              self.angle_180, self.angle_225, self.angle_270, self.angle_315]
        for button, value in zip(self.angle_buttons, range(0, 361, 45)):
            button.pressed.connect(lambda val=value: self.button_mapping(val))


    def SetupSerial(self):
        self.serial = SerialComm()
        self.serial_list.addItems(self.serial.list_ports())
        self.serial_checkbox.stateChanged.connect(self.ConnectSerial)

    def ConnectSerial(self):
        if self.serial_checkbox.isChecked():
            print(self.serial.open(self.serial_list.currentText()))
        else:
            self.Serial.close()
            print("Serial Port Disconnected")

    def SendSerial(self, I):
        if self.serial_checkbox.isChecked():
            try:
                self.serial.send(I)
            except:
                print('Error Sending Currents')



    def button_mapping(self, value):
        self.theta_spinbox.setValue(value)

    def reset_values(self):
        self.B_spinbox.setValue(0)
        self.F_spinbox.setValue(0)
        self.theta_spinbox.setValue(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    app.exec_()