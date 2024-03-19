import numpy as np
from scipy.optimize import curve_fit

class fix_it:
    def __init__(self, x_values, y_values):
        self.x_values = np.array(x_values)
        self.y_values = np.array(y_values)
        self.optimize()  # Compute initial optimization model

    def model_function(self, x, a, b):
        """Non-linear function to fit the data."""
        return np.clip(a * x, 0, 255)

    def optimize(self):
        """Fits the non-linear model based on current x and y values."""
        self.params, _ = curve_fit(self.model_function, self.x_values, self.y_values, bounds=(0, np.inf))
    
    def add_xy(self, x, y):
        """Adds new x, y pairs and updates the optimization model."""
        self.x_values = np.append(self.x_values, x)
        self.y_values = np.append(self.y_values, y)
        self.optimize()  # Update the optimization model

    def fix(self, x):
        """Predicts a y value for a given x based on the non-linear model."""
        return self.model_function(x, *self.params)
