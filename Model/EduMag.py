import numpy as np
from numpy import sin, cos, round
from numpy.linalg import pinv
import pandas as pd
import matplotlib.pyplot as plt




class EduMag:
    def __init__(self):
        self.Vfield_data = pd.read_excel('Model/VecField_Data.xlsx')
        self.fig, self.ax = plt.subplots()

    def SetFieldForce(self, B, F, theta):
        Theta = theta / 180.0 * 3.14        

        B = B / 1000
        F = F / 1000
        
        if B == 0 or F == 0:
            I = np.array([0, 0, 0, 0])
            return I
        
        Unit = np.array([cos(Theta), sin(Theta)])


        Breq = round(Unit * B, 3)
        Freq = round(Unit * F, 3)

        B_vec = np.array([[-0.00340, -0.00030, 0.00340, 0.00030], [-0.00030, 0.00340, 0.00030, -0.00340]])
        Grad_X = np.array([[-0.23960, 0.16450, -0.23960, 0.16450], [-0.00620, 0.00680, -0.00620, 0.00680]])
        Grad_Y = np.array([[-0.00680, 0.00620, -0.00680, 0.00620], [0.16450, -0.23960, 0.16450, -0.23960]])

        Sol = np.vstack((B_vec, Unit.dot(Grad_X), Unit.dot(Grad_Y)))
        inv = pinv(Sol)
        I = round(pinv(Sol).dot(np.hstack((Breq, Freq))), 3)
        if np.prod (np.abs(I) < 4):
            print("Safe")
        else:
            print("Unsafe")
            I = np.array([0, 0, 0, 0])
        return I

    def plot_vecfield(self, I):
        X = self.Vfield_data['X'].values
        Y = self.Vfield_data['Y'].values
        BiX = self.Vfield_data[['B1X', 'B2X', 'B3X', 'B4X']].values
        BiY = self.Vfield_data[['B1Y', 'B2Y', 'B3Y', 'B4Y']].values

        I = I[:, np.newaxis]

        BXnet = np.sum(BiX * I.T, axis=1)
        BYnet = np.sum(BiY * I.T, axis=1)
        Bnet = np.sqrt(BXnet ** 2 + BYnet ** 2)

        # Clear the axes
        self.ax.cla()

        # Plot the quiver
        quiver = self.ax.quiver(X, Y, BXnet * 1000.0, BYnet * 1000.0, Bnet * 1000.0, cmap='jet')

        # Create or update the colorbar
        if not hasattr(self, 'colorbar'):
            self.colorbar = self.fig.colorbar(quiver, ax=self.ax, label='Bnet')
        else:
            self.colorbar.update_normal(quiver)

        # Set labels and title
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_title('Quiver Plot of Bx and By')
        self.ax.grid()

        return self.fig
