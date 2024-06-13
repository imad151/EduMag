from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5 import uic

from Model.EduMag import EduMag
from Model.Camera import Camera
from Model.Serial_Comm import SerialComm

import sys
import numpy as np


class Game_2(QMainWindow):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi('Games/Game2/Game2_main.ui', self)
        self.Edumag = EduMag()
        self.Camera = Camera()
        self.Serial = SerialComm()

        _ = self.Serial.open('COM3') # Only for Pi. Use virtual ports to run on lappy

        self.add_button.pressed.connect(lambda: self.add_or_remove_row('add'))
        self.remove_button.pressed.connect(lambda: self.add_or_remove_row('remove'))
        self.removeall_button.pressed.connect(lambda: self.add_or_remove_row('remove_all'))


        max = -38.563 * self.B_spinbox.value() + 997.3362
        self.F_spinbox.setMaximum(max)
        self.F_spinbox.setSingleStep(max / 15)

        self.execute_button.pressed.connect(self.execute)

        self.command_list.setColumnCount(4)
        top_row = ['B', 'F', 'Theta', 'Time', 'Repeat']
        self.command_list.setHorizontalHeaderLabels(top_row)

        self.command_list.itemSelectionChanged.connect(self.show_selected_vecfield)
        self.vec_scene = QGraphicsScene()
        self.vec_view.setScene(self.vec_scene)

        self.timer = QTimer()
        self.cam_scene = QGraphicsScene()
        self.cam_view.setScene(self.cam_scene)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.warning_label.setVisible(False)

    def add_or_remove_row(self, action):
        if action == 'add':
            if self.B_spinbox.value() != 0 and self.F_spinbox.value() != 0:
                inputs = [self.B_spinbox.value(), self.F_spinbox.value(), self.theta_spinbox.value(),
                          self.time_spinbox.value()]
                I = self.Edumag.SetFieldForce(inputs[0], inputs[1], inputs[2])
                if not np.all(I == 0):
                    self.draw_field(I)
                    row_count = self.command_list.rowCount()
                    self.command_list.setRowCount(row_count + 1)
                    for column, item in enumerate(inputs):
                        self.command_list.setItem(row_count, column, QTableWidgetItem(str(item)))
                    if self.warning_label.isVisible():
                        self.warning_label.setVisible(False)
                else:
                    self.warning_label.setVisible(True)


        elif action == 'remove':
            selected_items = self.command_list.selectedItems()
            if selected_items:
                for item in selected_items:
                    row = self.command_list.row(item)
                    self.command_list.removeRow(row)
            else:
                pass
        elif action == 'remove_all':
            self.command_list.clearContents()
            self.command_list.setRowCount(0)


    def execute(self):
        rows = self.command_list.rowCount()
        cols = self.command_list.columnCount()
        data = np.zeros((rows, cols), dtype=float)

        for row in range(rows):
            for col in range(cols):
                item = self.command_list.item(row, col)
                if item is not None and item.text() != "":
                    data[row, col] = float(item.text())

        self.iter = iter(data)
        self.process_next_command()

    def show_selected_vecfield(self):
        current_item = self.command_list.currentItem()
        if current_item is not None:
            row_index = self.command_list.row(current_item)
            row_data = []
            for i in range(0, 3):
                row_data.append(self.command_list.item(row_index, i).text())
            data_matrix = np.array([float(val) for val in row_data])
            I = self.Edumag.SetFieldForce(data_matrix[0], data_matrix[1], data_matrix[2])
            self.draw_field(I)

        else:
            self.vec_scene.clear()

    def draw_field(self, I):
        self.vec_scene.clear()
        fig = self.Edumag.plot_vecfield(I)
        fig.canvas.draw()
        width, height = fig.canvas.get_width_height()
        self.vec_scene.clear()
        self.vec_scene.addItem(QGraphicsPixmapItem(
            QPixmap.fromImage(QImage(fig.canvas.buffer_rgba(), width, height, QImage.Format_RGBA8888))))
        self.vec_view.fitInView(self.vec_scene.sceneRect(), Qt.KeepAspectRatio)

    def process_next_command(self):
        try:
            row = next(self.iter)
            param = row[:3]
            delay = row[-1]
            I = self.Edumag.SetFieldForce(param[0], param[1], param[2])
            self.send_currents(I)
            self.draw_field(I)
            if self.stop_button.isDown():
                raise StopIteration
            QTimer.singleShot(int(delay * 1000), self.process_next_command)
        except StopIteration:
            self.Edumag.SetFieldForce(0, 0, 0)
            pass

    def send_currents(self, I):
        self.Serial.send(I)

    def update_frame(self):
        frame, _ = self.Camera.get_image_pos()
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.cam_scene.clear()
        self.cam_scene.addPixmap(pixmap)
        self.cam_view.fitInView(self.cam_scene.sceneRect(), Qt.KeepAspectRatio)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myapp = Game_2()
    myapp.showMaximized()
    app.exec_()


