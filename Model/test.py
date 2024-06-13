import sys
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsProxyWidget
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class QuiverPlotApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setWindowTitle("Quiver Plot")
        self.view.setGeometry(100, 100, 800, 600)

        # Create a Matplotlib figure
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        # Generate data for quiver plot
        x = np.linspace(-2, 2, 10)
        y = np.linspace(-2, 2, 10)
        X, Y = np.meshgrid(x, y)
        U = np.sin(X)
        V = np.cos(Y)

        # Plot the quiver plot
        self.ax.quiver(X, Y, U, V)

        # Add the Matplotlib canvas to the scene
        self.proxy = self.scene.addWidget(self.canvas)
        self.proxy.setPos(0, 0)
        self.proxy.setZValue(10)

        self.view.show()

        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    app = QuiverPlotApp()
    app.run()
