import sys

from PyQt5 import uic
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene
import numpy as np

from Model.EduMag import EduMag
from Model.Joystick import Joystick
from Model.Camera import Camera
from Model.Serial_Comm import SerialComm


class Game_3(QMainWindow):
    closed = pyqtSignal()
    def __init__(self):
        super().__init__()
        uic.loadUi('Games/Game3/Game3ui.ui', self)

        self.Initialize_Classes()

        self.CamScene = QGraphicsScene()
        self.CameraView.setScene(self.CamScene)

        self.timer = QTimer()
        self.timer.start(30)
        self.timer.timeout.connect(self.update_frame())


    def Initalize_Classes(self):
        self.EduMag = EduMag()
        self.Joystick = Joystick()
        self.Camera = Camera()
        self.Serial = SerialComm()

    def update_frame(self):
        frame, pos = self.Camera.get_image_pos()
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            self.CamScene.clear()
            self.CamScene.addPixmap(pixmap)
            self.CameraView.fitInView(self.CamScene.sceneRect(), Qt.KeepAspectRatio)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    myapp = Game_3()
    myapp.showMaximized()
    sys.exit(app.exec_())