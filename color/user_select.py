import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from draw import DrawableLabel
from corrections import corrections  
import cv2# Ensure this import path is correct based on your project structure
import numpy as np
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtCore import QObject, pyqtSignal


class user_select(QWidget):
    finished = pyqtSignal(corrections)  # Define a signal
    def __init__(self, src_path, targ_path, title, composit_img):
        super().__init__()
        self.src_path = src_path
        self.targ_path = targ_path
        self.preview_path = ""  # Initialize with an empty string or a default image path
        self.src_points = []
        self.target_points = []

        self.correct = corrections(src_path, composit_img)
        self.points = 0
        self.new_img = None
        self.title = title
        self.composit_img = composit_img
        self.initUI()

    def set_prev(self):
        files = os.listdir(self.src_path)
        if files:
                first_image_path = os.path.join(self.src_path, files[0])
                src_img = cv2.imread(first_image_path)

                # Apply corrections (ensure your apply method in corrections.py is compatible with this use)
                sn_img = self.correct.apply(src_img)  # This line assumes apply can handle an OpenCV image directly
                self.new_img = sn_img
                # Update preview image
                qtPixmap = self.convertCvImageToQtPixmap(sn_img)
                self.previewImageLabel.setPixmap(qtPixmap)

    def initUI(self):
        self.prev_img = cv2.imread(self.src_path)
        self.setWindowTitle("Image Selection Tool")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)  # Add close button

        # Create a scroll area widget
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)

        # Create a widget to contain all other widgets
        scrollWidget = QWidget()
        scrollArea.setWidget(scrollWidget)

        # Create a layout for the scroll widget
        self.mainLayout = QVBoxLayout(scrollWidget)
        self.mainLayout.setSpacing(20)  # Set spacing between widgets

        # Title label
        titleLabel = QLabel(self.title)
        titleLabel.setAlignment(Qt.AlignCenter)
        titleLabel.setStyleSheet("font-size: 24px; font-weight: bold;")

        # Top layout containing source and target images
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(20)  # Set spacing between widgets

        # Bottom layout containing preview image, sliders, and buttons
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setSpacing(20)  # Set spacing between widgets

        # Initializing DrawableLabels for source, target, and preview images
        self.srcImageLabel = DrawableLabel()
        self.targetImageLabel = DrawableLabel()
        self.previewImageLabel = DrawableLabel()

        # Load the first images from specified paths and calculate aspect ratio
        src_aspect_ratio = self.loadFirstImage(self.src_path, self.srcImageLabel)
        targ_aspect_ratio = self.loadFirstImage(self.targ_path, self.targetImageLabel)
        preview_aspect_ratio = self.loadFirstImage(self.src_path, self.previewImageLabel)

        # Set fixed size for labels based on aspect ratio
        self.srcImageLabel.setFixedSize(1000, int(1000 * src_aspect_ratio))
        self.targetImageLabel.setFixedSize(1000, int(1000 * targ_aspect_ratio))
        self.previewImageLabel.setFixedSize(1000, int(1000 * preview_aspect_ratio))

        # Labels for each image
        self.srcImageTitle = QLabel("IMAGE SOURCE")
        self.targetImageTitle = QLabel("TARGET IMAGE")
        self.previewImageTitle = QLabel("PREVIEW IMAGE")

        # Buttons for adding images and finishing the selection
        self.addSrcImageButton = QPushButton("Select Frame")
        self.addTargetImageButton = QPushButton("Select Frame")
        self.doneButton = QPushButton("Done")
        self.doneButton.setEnabled(False)  # Disabled initially
        self.resetAllButton = QPushButton("Reset All")
        self.nonLinearButton = QPushButton("NL Color Transfer")

        button_width = 100
        self.addSrcImageButton.setMaximumWidth(button_width)
        self.addTargetImageButton.setMaximumWidth(button_width)
        self.doneButton.setMaximumWidth(button_width)
        self.resetAllButton.setMaximumWidth(button_width)
        self.nonLinearButton.setMaximumWidth(button_width * 3)
        
        # Connecting buttons to their actions
        self.addSrcImageButton.clicked.connect(lambda: self.addImage(self.srcImageLabel, self.src_path))
        self.addTargetImageButton.clicked.connect(lambda: self.addImage(self.targetImageLabel, self.targ_path))
        self.doneButton.clicked.connect(self.finish)
        self.resetAllButton.clicked.connect(self.resetAll)
        self.nonLinearButton.clicked.connect(self.set_over)
        # Setting up the top layout
        self.leftLayout = QVBoxLayout()
        self.leftLayout.addWidget(self.srcImageTitle)
        self.leftLayout.addWidget(self.srcImageLabel)
        self.leftLayout.addWidget(self.addSrcImageButton)

        self.rightLayout = QVBoxLayout()
        self.rightLayout.addWidget(self.targetImageTitle)
        self.rightLayout.addWidget(self.targetImageLabel)
        self.rightLayout.addWidget(self.addTargetImageButton)

        self.topLayout.addLayout(self.leftLayout)
        self.topLayout.addLayout(self.rightLayout)

        # Setting up the bottom layout
        self.bottomLayout.addWidget(self.previewImageLabel)
        self.set_prev()


        # Sliders layout
        slidersLayout = QVBoxLayout()

        self.contrastSlider = QSlider(Qt.Vertical)  # Vertical slider
        self.contrastSlider.setMinimum(0)
        self.contrastSlider.setMaximum(100)
        self.contrastSlider.setValue(0)
        self.contrastSlider.setTickPosition(QSlider.TicksLeft)
        self.contrastSlider.setTickInterval(10)
        self.contrastSlider.sliderReleased.connect(lambda: self.set_contrast(self.contrastSlider.value()))

        self.strengthSlider = QSlider(Qt.Vertical)  # Vertical slider
        self.strengthSlider.setMinimum(0)
        self.strengthSlider.setMaximum(100)
        self.strengthSlider.setValue(50)
        self.strengthSlider.setTickPosition(QSlider.TicksLeft)
        self.strengthSlider.setTickInterval(10)
        self.strengthSlider.sliderReleased.connect(lambda: self.set_strength(self.strengthSlider.value()))

        self.contrastLabel = QLabel("Contrast: 0")
        self.strengthLabel = QLabel("Strength: 50")

        slidersLayout.addWidget(self.contrastLabel)
        slidersLayout.addWidget(self.contrastSlider)
        slidersLayout.addWidget(self.strengthLabel)
        slidersLayout.addWidget(self.strengthSlider)

        self.bottomLayout.addLayout(slidersLayout)
        self.bottomLayout.addWidget(self.nonLinearButton)

        # Adding top and bottom layouts to the main layout
        self.mainLayout.addWidget(titleLabel)  # Add title
        self.mainLayout.addLayout(self.topLayout)
        self.mainLayout.addLayout(self.bottomLayout)
        self.mainLayout.addWidget(self.doneButton)
        self.mainLayout.addWidget(self.resetAllButton)

        # Points label
        self.pointsLabel = QLabel("Points: 0")
        self.pointsLabel.setAlignment(Qt.AlignCenter)
        self.mainLayout.addWidget(self.pointsLabel)

        # Set the central widget to the scroll area
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scrollArea)
        

        self.resize(800, 600)

        # Connecting signals from DrawableLabels to slots
        self.srcImageLabel.lineDrawn.connect(self.handleSrcLineColorData)
        self.targetImageLabel.lineDrawn.connect(self.handleTargetLineColorData)
   
        



    def loadFirstImage(self, directory, label):
        files = os.listdir(directory)
        if files:
            first_image_path = os.path.join(directory, files[0])
            pixmap = QPixmap(first_image_path)
            label.setPixmap(pixmap)
            aspect_ratio = pixmap.height() / pixmap.width()
            return aspect_ratio
        return 1.0  # Return a default aspect ratio if no image is found



    def set_over(self):
        # Open a file dialog to select a file
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if file_path:
            # Pass the selected file path to the correct object's set_over method
            self.correct.set_over(file_path)




    def set_strength(self, value):
        self.strengthLabel.setText(f"Strength: {value}")
        # Implement your logic to adjust strength based on the slider value
        print("Strength set to:", value)
        # You might want to call some correction method here
        self.correct.set_PTP_strength(value)
        self.set_prev()


    def set_contrast(self, value):
        self.contrastLabel.setText(f"Contrast: {value}")
        # Implement your logic to adjust contrast based on the slider value
        print("Contrast set to:", value)
        # You might want to call some correction method here
        self.correct.set_contrast(value)
        self.set_prev()
        
    def addImage(self, label, directory):
        filePath, _ = QFileDialog.getOpenFileName(self, "Select an Image", directory, "JPEG Files (*.jpg);;PNG Files (*.png);;All Files (*)")
        if filePath:
            pixmap = QPixmap(filePath).scaled(500, 500, Qt.KeepAspectRatio)
            label.setPixmap(pixmap)
    
    def resetAll(self):
        # Reset or initialize all variables to their defaults
        self.src_points = []
        self.target_points = []
        self.correct = corrections(self.src_path, self.composit_img)
        self.set_prev()
        



    def handleSrcLineColorData(self, avg_color):
        self.src_points.append(avg_color)
        self.checkDoneButtonState()

    def handleTargetLineColorData(self, avg_color):
        self.target_points.append(avg_color)
        self.checkDoneButtonState()


    def convertCvImageToQtPixmap(self, cvImg):
        # Convert the color format from BGR to RGB
        cvImg = cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB)
        height, width, channel = cvImg.shape
        bytesPerLine = 3 * width
        qtImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_RGB888)
        qtPixmap = QPixmap.fromImage(qtImg)
        return qtPixmap



    def replace_image_in_directory(self):
        string_path_img = "prev_" + self.title + ".jpg"
        directory = "media/target"
        cv2_img = self.new_img
        # Iterate over all files in the directory
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            # Check if the file matches the specified string path
            if string_path_img in filepath:
                # Read the existing image
                existing_img = cv2.imread(filepath)
                
                # Check if reading was successful and the shapes match
                if existing_img is not None and existing_img.shape == cv2_img.shape:
                    # Replace the existing image with the new one
                    cv2.imwrite(filepath, cv2_img)
                    print(f"Image replaced in {filepath}")
                    return True  # Return True upon successful replacement
                
        print("Image replacement failed: No matching file found " + string_path_img)
        return False  # Return False if no matching file is found





    def checkDoneButtonState(self):
        if len(self.src_points) == len(self.target_points):
            if (len(self.src_points) > 1) or (self.correct.PTP):
                print("\n " + str(len(self.src_points)))
                print("\n " + str(self.correct.PTP))
                if self.points == 0:
                    self.points = 2
                else:
                    self.points = self.points + 1
                self.doneButton.setEnabled(True)
                self.correct.add_color_points(self.src_points, self.target_points)
                self.src_points = []  # Resetting points lists
                self.target_points = []
                self.pointsLabel.setText(f"Points: {self.points}")  # Update points count
                # Assuming self.src_img is meant to be an image for preview, you'd probably load it or have it updated elsewhere
                # For demonstration, let's assume you want to apply corrections on the first image of src_path again
                self.set_prev()
            else:
                self.doneButton.setEnabled(False)

    def finish(self):
        print("Source Image Color Data:", self.src_points)
        print("Target Image Color Data:", self.target_points)      
        self.close()
        self.finished.emit(self.correct)







if __name__ == '__main__':
    app = QApplication(sys.argv)
    src_path = QFileDialog.getExistingDirectory(None, "Select Source Directory")
    targ_path = QFileDialog.getExistingDirectory(None, "Select Target Directory")
    window = user_select(src_path, targ_path)
    window.show()
    sys.exit(app.exec_())
