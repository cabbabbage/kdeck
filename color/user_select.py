import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from draw import DrawableLabel  # Ensure this import path is correct based on your project structure

class user_select(QWidget):
    def __init__(self, src_path, targ_path):
        super().__init__()
        self.src_path = src_path
        self.targ_path = targ_path
        self.src_points = []
        self.target_points = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Image Selection Tool")
        self.mainLayout = QHBoxLayout()
        self.leftLayout = QVBoxLayout()
        self.rightLayout = QVBoxLayout()

        # Initializing DrawableLabels
        self.srcImageLabel = DrawableLabel()
        self.targetImageLabel = DrawableLabel()
        self.srcImageLabel.setFixedSize(1000, 1000)
        self.targetImageLabel.setFixedSize(1000, 1000)

        # Buttons for adding images and finishing the selection
        self.addSrcImageButton = QPushButton("Add Image")
        self.addTargetImageButton = QPushButton("Add Image")
        self.doneButton = QPushButton("Done")
        self.doneButton.setEnabled(False)  # Disabled initially

        # Connecting buttons to their actions
        self.addSrcImageButton.clicked.connect(lambda: self.addImage(self.srcImageLabel, self.src_path))
        self.addTargetImageButton.clicked.connect(lambda: self.addImage(self.targetImageLabel, self.targ_path))
        self.doneButton.clicked.connect(self.finish)

        # Setting up the layout
        self.leftLayout.addWidget(self.srcImageLabel)
        self.leftLayout.addWidget(self.addSrcImageButton)
        self.rightLayout.addWidget(self.targetImageLabel)
        self.rightLayout.addWidget(self.addTargetImageButton)
        self.mainLayout.addLayout(self.leftLayout)
        self.mainLayout.addLayout(self.rightLayout)
        self.mainLayout.addWidget(self.doneButton)
        self.setLayout(self.mainLayout)

        # Load the first images from specified paths
        self.loadFirstImage(self.src_path, self.srcImageLabel)
        self.loadFirstImage(self.targ_path, self.targetImageLabel)

        # Connecting signals from DrawableLabels to slots
        self.srcImageLabel.lineDrawn.connect(self.handleSrcLineColorData)
        self.targetImageLabel.lineDrawn.connect(self.handleTargetLineColorData)

    def addImage(self, label, directory):
        filePath, _ = QFileDialog.getOpenFileName(self, "Select an Image", directory, "JPEG Files (*.jpg);;PNG Files (*.png);;All Files (*)")
        if filePath:
            pixmap = QPixmap(filePath).scaled(500, 500, Qt.KeepAspectRatio)
            label.setPixmap(pixmap)

    def loadFirstImage(self, directory, label):
        files = os.listdir(directory)
        if files:
            first_image_path = os.path.join(directory, files[0])
            pixmap = QPixmap(first_image_path).scaled(500, 500, Qt.KeepAspectRatio)
            label.setPixmap(pixmap)

    def handleSrcLineColorData(self, avg_color):
        self.src_points.append(avg_color)
        self.checkDoneButtonState()

    def handleTargetLineColorData(self, avg_color):
        self.target_points.append(avg_color)
        self.checkDoneButtonState()

    def checkDoneButtonState(self):
        if len(self.src_points) == len(self.target_points) and len(self.src_points) > 1:
            self.doneButton.setEnabled(True)
        else:
            self.doneButton.setEnabled(False)

    def finish(self):
        print("Source Image Color Data:", self.src_points)
        print("Target Image Color Data:", self.target_points)
        self.close()
    def get_points(self):
        print(self.src_points)
        print(self.src_points)
        return self.src_points, self.target_points

if __name__ == '__main__':
    app = QApplication(sys.argv)
    src_path = QFileDialog.getExistingDirectory(None, "Select Source Directory")
    targ_path = QFileDialog.getExistingDirectory(None, "Select Target Directory")
    window = user_select(src_path, targ_path)
    window.show()
    sys.exit(app.exec_())
