from scipy.stats import linregress

class fix_it:
    def __init__(self, x_values, y_values):
        self.x_values = x_values
        self.y_values = y_values
        self.regress()  # Compute initial regression model

    def regress(self):
        """Computes the regression model based on current x and y values."""
        self.model = linregress(self.x_values, self.y_values)
    
    def add_xy(self, x, y):
        """Adds a new x, y pair and updates the regression model."""
        self.x_values.append(x)
        self.y_values.append(y)
        self.regress()  # Update the regression model
    
    def fix(self, x):
        """Predicts a y value for a given x based on the regression line."""
        return self.model.slope * x + self.model.intercept