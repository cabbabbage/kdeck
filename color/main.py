from PIL import Image
import cv2
import os
import shutil
from tkinter import filedialog, Tk
import glob
from corrections import corrections  # Assuming this is implemented elsewhere

def analyze_video_and_save_shots(filename, file_names, threshold=60000):
    """
    Analyzes a video file, saving frames that meet the shot detection threshold.
    """
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

def apply_corrections_to_frame(color_correction, source_image_path, output_path, frame_num, strength=100):
    """
    Applies color corrections to a given frame and saves the output.
    """
    src_img = Image.open(source_image_path)
    pixels = src_img.load()

    for i in range(src_img.width):
        for j in range(src_img.height):
            current_pixel = pixels[i, j]
            corrected_pixel = color_correction.correct_color(current_pixel, strength)
            pixels[i, j] = tuple(map(int, corrected_pixel))

    output_file_name = os.path.join(output_path, f"frame_{frame_num}.jpg")
    src_img.save(output_file_name)

def clear_or_create_dir(path):
    """
    Clears the directory if it exists, or creates it if it does not.
    """
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def save_frames_from_video(video_path, output_folder, skip_frames=1):
    """
    Saves selected frames from the video to the output folder.
    """
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

def select_and_process_target_video():
    """
    Prompts the user to select a target video, then processes and saves its frames.
    """
    root = Tk()
    root.withdraw()
    video_path = filedialog.askopenfilename(title="Select Target Video", filetypes=[("MP4 Files", "*.mp4")])
    root.destroy()

    if video_path:
        target_folder = os.path.join("media", "target")
        save_frames_from_video(video_path, target_folder, 30)
        return os.path.abspath(target_folder)
    return ""

def select_and_process_source():
    """
    Prompts the user to select a source folder or MP4 file for processing.
    """
    root = Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select Source Folder or MP4 File", filetypes=[("MP4 Files", "*.mp4"), ("All Files", "*.*")])
    root.destroy()
    file_names = []

    if path:
        if os.path.isdir(path):
            video_paths = glob.glob(os.path.join(path, "*.mp4"))
            for index, video_path in enumerate(video_paths):
                shot_folder = os.path.join("media", f"shot_{index + 1}")
                save_frames_from_video(video_path, shot_folder)
                file_names.append(os.path.abspath(shot_folder))
        elif path.lower().endswith('.mp4'):
            analyze_video_and_save_shots(path, file_names)
            
    return file_names

def setup_environment():
    """
    Sets up the required directories and processes selected videos.
    """
    clear_or_create_dir("media")
    target = select_and_process_target_video()
    source_folders = select_and_process_source()
    clear_or_create_dir("final")
    return target, source_folders

def process_and_correct_images(source_folder, correction, frame_index):
    """
    Applies corrections to all images in the source folder and saves the results.
    """
    for image_path in sorted(glob.glob(f"{source_folder}/*.jpg")):
        apply_corrections_to_frame(correction, image_path, "final", frame_index, 100)
        frame_index += 1
    return frame_index

if __name__ == "__main__":
    target, source_folders = setup_environment()
    corrections_list = [corrections(source_folder, target) for source_folder in source_folders]
    frame_index = 0

    for i, source_folder in enumerate(source_folders):
        frame_index = process_and_correct_images(source_folder, corrections_list[i], frame_index)
