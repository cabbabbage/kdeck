from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout, QProgressBar
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
import sys
import os
import shutil
import glob
import cv2
from user_select import user_select  # Import the user_select class
from corrections import corrections  # Import the corrections class
import numpy as np


class SetupWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Setup")
        self.setupUI()
        self.corrections = []
        self.user_select_list = []
        self.composite_img = None
        self.targets = []

    def setupUI(self):
        self.mainLayout = QVBoxLayout()

        self.selectVideoButton = QPushButton("Select Your Video")
        self.selectVideoButton.clicked.connect(self.selectVideo)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        self.shotCountLabel = QLabel("Shots Identified: 0")

        self.beginButton = QPushButton("Begin")
        self.beginButton.clicked.connect(self.beginSetup)
        self.beginButton.setEnabled(False)

        self.mainLayout.addWidget(self.selectVideoButton)
        self.mainLayout.addWidget(self.progressBar)
        self.mainLayout.addWidget(self.shotCountLabel)
        self.mainLayout.addWidget(self.beginButton)

        self.setLayout(self.mainLayout)

    def selectVideo(self):
        # Open a file dialog to select a video file or folder
        self.path, _ = QFileDialog.getOpenFileName(self, "Select Video or Folder", "", "Video Files (*.mp4);;All Files (*)")
        if self.path:
            self.selectedPath = self.path
            self.beginButton.setEnabled(True)

    def beginSetup(self):
        self.beginButton.setEnabled(False)
        self.progressBar.setValue(0)
        self.shotCountLabel.setText("Shots Identified: 0")

        # Start the setup process
        QTimer.singleShot(0, self.setupEnvironment)

    def setupEnvironment(self):
        def analyze_video_and_save_shots(filename, file_names, threshold=40000):
            cap = cv2.VideoCapture(filename)
            if not cap.isOpened():
                print("Error: Could not open video file.")
                return

            previous_frame = None
            new_shot = False
            shot_num = 0
            media_dir = "media"

            while True:
                ret, current_frame = cap.read()
                if not ret:
                    break

                gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

                if previous_frame is not None:
                    diff = cv2.norm(gray_frame, previous_frame, cv2.NORM_L2)
                    if diff > threshold:
                        new_shot = True

                previous_frame = gray_frame.copy()

                if new_shot or shot_num == 0:
                    shot_num += 1
                    shot_dir = os.path.join(media_dir, f"shot_{shot_num}")
                    os.makedirs(shot_dir, exist_ok=True)
                    frame_num = 0
                    new_shot = False
                    file_names.append(os.path.abspath(shot_dir))

                frame_num += 1
                frame_path = os.path.join(shot_dir, f"frame_{frame_num}.jpg")
                cv2.imwrite(frame_path, current_frame)

            cap.release()

        def clear_or_create_dir(path):
            if os.path.exists(path):
                shutil.rmtree(path)
            os.makedirs(path)

        def save_frames_from_video(video_path, output_folder, skip_frames=1):
            clear_or_create_dir(output_folder)
            cap = cv2.VideoCapture(video_path)
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % skip_frames == 0:
                    frame_path = os.path.join(output_folder, f"frame_{frame_count:04d}.jpg")
                    cv2.imwrite(frame_path, frame)

                frame_count += 1

            cap.release()

        def create_target():
            media_dir = "media"
            target_dir = os.path.join(media_dir, "target")
            clear_or_create_dir(target_dir)
            shot_dirs = [d for d in os.listdir(media_dir) if os.path.isdir(os.path.join(media_dir, d)) and d.startswith("shot_")]
            median_photos = []

            for shot_dir in shot_dirs:
                shot_path = os.path.join(media_dir, shot_dir)
                photos = sorted([os.path.join(shot_path, f) for f in os.listdir(shot_path) if f.endswith(('.jpg', '.jpeg', '.png'))])
                if photos:
                    median_photo = photos[len(photos) // 2]
                    median_photos.append(median_photo)
                    shutil.copy(median_photo, os.path.join(target_dir, f"prev_Shot_{shot_dirs.index(shot_dir) + 1}.jpg"))
                    self.targets.append(median_photo)

            return os.path.abspath(target_dir)

        def select_and_process_source():
            path = self.path
            file_names = []

            if path:
                if os.path.isdir(path):
                    video_paths = glob.glob(os.path.join(path, "*.mp4"))
                    for index, video_path in enumerate(video_paths):
                        shot_folder = os.path.join("media", f"Shot_{index + 1}")
                        save_frames_from_video(video_path, shot_folder)
                        file_names.append(os.path.abspath(shot_folder))
                elif path.lower().endswith('.mp4'):
                    analyze_video_and_save_shots(path, file_names)
                    
            return file_names

        def setup_environment():
            clear_or_create_dir("media")
            
            source_folders = select_and_process_source()
            target = create_target()
            clear_or_create_dir("final")
            clear_or_create_dir("out_frames")
            return target, source_folders

        self.target, self.sourceFolders = setup_environment()

        # Initialize only one user_select instance at a time
        self.processNextUserSelect()

    def mse(self, image1, image2):
        """Compute Mean Squared Error (MSE) between two images."""
        err = np.sum((image1.astype("float") - image2.astype("float")) ** 2)
        err /= float(image1.shape[0] * image1.shape[1])
        return err

    def order_images(self, targets):
        """
        Reorders an array of images based on color similarity.

        Args:
        targets: List of numpy arrays representing images or file paths.

        Returns:
        ordered_targets: List of numpy arrays representing reordered images.
        """
        # Convert file paths to images if necessary
        for i, target in enumerate(targets):
            if isinstance(target, str):
                if not os.path.isfile(target):
                    raise FileNotFoundError(f"File '{target}' not found.")
                # Load the image from file path
                targets[i] = cv2.imread(target)

        # Calculate mean color difference for each image compared to others
        mse_scores = []
        for i, target1 in enumerate(targets):
            total_mse = 0
            for j, target2 in enumerate(targets):
                if i != j:
                    mse = self.mse(target1, target2)
                    total_mse += mse
            mse_scores.append((i, total_mse))

        # Sort images based on mean color difference (MSE)
        sorted_indices = sorted(mse_scores, key=lambda x: x[1], reverse=True)

        # Reorder the targets array based on sorted indices
        ordered_targets = [targets[index] for index, _ in sorted_indices]

        # Save reordered images to the "defaults" folder
        folder_path = "defaults"
        os.makedirs(folder_path, exist_ok=True)
        for idx, image in enumerate(ordered_targets):
            image_path = os.path.join(folder_path, f"image_{idx}.jpg")
            cv2.imwrite(image_path, image)

        return ordered_targets
    
    
    def make_composit(self):
            self.targets = self.order_images(self.targets)

            self.composite_img = self.targets[0]


            for t in self.targets:
                    if self.composite_img.shape != t.shape:
                        raise ValueError("Images must have the same dimensions.")

                    # Combine the images using averaging
                    self.composite_img = (self.composite_img + t) // 2
            cv2.imwrite("defaults/comp_img.jpg", self.composite_img)



    def processNextUserSelect(self):
        self.make_composit()
        if self.sourceFolders:
            sourceFolder = self.sourceFolders.pop(0)
            totalFolders = len(self.sourceFolders) + 1
            self.progressBar.setValue(int((totalFolders - len(self.sourceFolders)) / totalFolders * 100))
            self.shotCountLabel.setText(f"Shots Identified: {totalFolders - len(self.sourceFolders)}/{totalFolders}")

            window = user_select(sourceFolder, self.target, f"Shot_{totalFolders - len(self.sourceFolders)}", self.composite_img)
            self.user_select_list.append(window) # Initialize user_select object
            window.finished.connect(self.on_finished) 
            window.show()
        else:
            # All user_select windows are closed, call process method for each correction object
            for correction in self.corrections:
                correction.process()

    def on_finished(self, result):
        self.corrections.append(result)
        # Check if all user_select windows are closed
        if all(window.isHidden() for window in self.user_select_list):
            # Process the next user_select window if available
            self.processNextUserSelect()

def main():
    # Launch the application
    app = QApplication(sys.argv)
    setupWidget = SetupWidget()
    setupWidget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
