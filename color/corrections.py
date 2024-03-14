from user_select import user_select
from fix_it import fix_it
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

class corrections:
    def __init__(self, source_image_path, target_image_path):
        self.source_image_path = source_image_path
        self.target_image_path = target_image_path
        self.src_points = []  # To store source points after averaging
        self.target_points = []  # To store target points after averaging
        self.red_model = None
        self.green_model = None
        self.blue_model = None
        self.create_models()  # Initialize models upon creation

    def ask_user_continue(self):
        response = input("Do you want to select more points? (y/n): ").strip().lower()
        return response == 'y'

    def create_models(self):
        app = QApplication(sys.argv)
        color_selector = user_select(self.source_image_path, self.target_image_path)
        color_selector.show()  # Show the user_select widget
        app.exec_()  # Run the application event loop to interact with the widget
        self.src_points, self.target_points = color_selector.get_points()
        if self.src_points and self.target_points:  # Ensure we have collected points
            src_reds, src_greens, src_blues = zip(*self.src_points)
            target_reds, target_greens, target_blues = zip(*self.target_points)

            self.red_model = fix_it(list(src_reds), list(target_reds))
            self.green_model = fix_it(list(src_greens), list(target_greens))
            self.blue_model = fix_it(list(src_blues), list(target_blues))

    def correct_color(self, rgb, strength=100):
        """
        Takes an RGB color array and a strength parameter (0-100) to adjust it based on the regression models created.
        The strength parameter determines how much the color is adjusted towards the regression model prediction.
        Returns the corrected color as (r, g, b).
        """
        if len(rgb) != 3:
            print("Invalid RGB array. It must have three elements.")
            return None
        
        # Ensure strength is within bounds
        strength = max(0, min(100, strength))
        r, g, b = rgb  # Unpack the RGB values from the array
        
        if self.red_model and self.green_model and self.blue_model:
            corrected_r = self.red_model.fix(r)
            corrected_g = self.green_model.fix(g)
            corrected_b = self.blue_model.fix(b)

            # Calculate the adjusted color based on the strength parameter
            adjusted_r = r + (corrected_r - r) * (strength / 100.0)
            adjusted_g = g + (corrected_g - g) * (strength / 100.0)
            adjusted_b = b + (corrected_b - b) * (strength / 100.0)

            return (adjusted_r, adjusted_g, adjusted_b)
        else:
            print("Regression models not initialized.")
            return rgb
