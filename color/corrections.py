import os
from fix_it_2 import fix_it
import os
import cv2
import numpy as np
from PIL import Image

class corrections:
    def __init__(self, path, comp):
        self.path = path
        self.src_points = []  # To store source points after averaging
        self.target_points = []  # To store target points after averaging
        self.red_model = None
        self.green_model = None
        self.blue_model = None
        self.PTP = False  # Point-to-Point correction initialized
        self.Contrast = False
        self.Transfer = True
        self.PTP_Strength = 50  # Strength of Point-to-Point correction
        self.over_img = []  # Image used for color transfer
        self.current_frame = 0
        self.total_frames = 0
        self.output_dir = "out_frames"
        self.composite_img = None
        self.over_img.append(comp)













    def add_color_points(self, src_points, target_points):
        try:
            self.src_points =  src_points
            self.target_points =target_points
                
            # Print shapes for debugging
            print("Shapes of src_points and target_points:")
            print(len(src_points), len(target_points))
            
            src_reds, src_greens, src_blues = zip(*src_points)
            target_reds, target_greens, target_blues = zip(*target_points)
            
            # Convert sequences to lists
            src_reds = list(src_reds)
            src_greens = list(src_greens)
            src_blues = list(src_blues)
            target_reds = list(target_reds)
            target_greens = list(target_greens)
            target_blues = list(target_blues)
            
            if not self.PTP:
                self.red_model = fix_it(src_reds, target_reds)
                self.green_model = fix_it(src_greens, target_greens)
                self.blue_model = fix_it(src_blues, target_blues)
                self.PTP = True 
            else:
                self.red_model.add_xy(src_reds, target_reds)
                self.green_model.add_xy(src_greens, target_greens)
                self.blue_model.add_xy(src_blues, target_blues)
        except Exception as e:
            # Handle any other exceptions
            print(f"An error occurred: {e}")
            print("\n" + str(src_points))
            print("\n" + str(target_points))


    
    
    def apply_PTP(self, rgb):
        if len(rgb) != 3:
            print("Invalid RGB array. It must have three elements.")
            return None
        strength = max(0, min(100, self.PTP_Strength))
        r, g, b = rgb  # Unpack the RGB values from the array
        if self.red_model and self.green_model and self.blue_model:
            corrected_r = self.red_model.fix(r)
            corrected_g = self.green_model.fix(g)
            corrected_b = self.blue_model.fix(b)
            adjusted_r = r + (corrected_r - r) * (self.PTP_Strength / 100.0)
            adjusted_g = g + (corrected_g - g) * (self.PTP_Strength  / 100.0)
            adjusted_b = b + (corrected_b - b) * (self.PTP_Strength  / 100.0)
            return (adjusted_r, adjusted_g, adjusted_b)
        else:
            print("Regression models not initialized.")
            return rgb
        
    def set_contrast(self, contrast_val):
        self.contrast_amount = contrast_val
        self.Contrast = True
    
    def contrast_measure(self, image):
        # Convert the image to grayscale if it's in color
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = image

        # Calculate standard deviation of pixel intensities
        std_dev = np.std(gray_image)
        
        return std_dev

    def adjust_contrast(self, original_image, modified_image):
        original_contrast = self.contrast_measure(original_image)
        modified_contrast = self.contrast_measure(modified_image)
        contrast_ratio = original_contrast / modified_contrast
        adjusted_image = cv2.convertScaleAbs(modified_image, alpha=contrast_ratio, beta=0)
        
        return adjusted_image
    
    
    def set_PTP_strength(self, PTP_val):
        self.PTP_Strength = PTP_val


    



    def color_transfer(self, source_img, power=50):
        """
        Transfer color from source image(s) to the target image.

        Args:
        source_img: Source image from which colors will be transferred.
        power: Power of color transfer in percentage (default is 50%).

        Returns:
        target_img: Target image after color transfer.
        """
        target_img = source_img

        for im in self.over_img:
            source_img = im
            source_lab = cv2.cvtColor(source_img, cv2.COLOR_BGR2LAB).astype(np.float32)
            target_lab = cv2.cvtColor(target_img, cv2.COLOR_BGR2LAB).astype(np.float32)
            source_mean, source_std = cv2.meanStdDev(source_lab)
            target_mean, target_std = cv2.meanStdDev(target_lab)

            # Perform color transfer with the specified power
            transfer_power = power / 100.0
            for i in range(3):  # iterate over each channel (L, A, B)
                target_lab[:,:,i] = (1 - transfer_power) * target_lab[:,:,i] + transfer_power * ((target_lab[:,:,i] - target_mean[i]) * (source_std[i] / target_std[i]) + source_mean[i])

            # Clip values to ensure they are within valid range
            target_lab = np.clip(target_lab, 0, 255)

            # Convert back to BGR color space
            target_img = cv2.cvtColor(target_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

        return target_img
        

    def set_over(self, over_path):
        self.over_img.append(cv2.imread(over_path))
        

    
    
    def apply(self, src_img):
        # Assuming src_img is a PIL Image, convert to OpenCV format (NumPy array)
        if isinstance(src_img, Image.Image):
            src_img = np.array(src_img)
            # Convert RGB to BGR for OpenCV
            src_img = src_img[:, :, ::-1].copy()

        og_img = src_img.copy()
        
        # Apply PTP corrections if enabled
        if self.PTP:
            print("applying PTP correction")
            for i in range(src_img.shape[0]):  # Iterate over height
                for j in range(src_img.shape[1]):  # Iterate over width
                    # Get current pixel in BGR format
                    current_pixel = src_img[i, j]
                    # Apply PTP correction (make sure to adjust this method to accept and return BGR tuples)
                    corrected_pixel = self.apply_PTP(current_pixel)
                    # Update pixel in image
                    src_img[i, j] = np.array(corrected_pixel, dtype=np.uint8)

        # Apply contrast adjustment if enabled
        if self.Contrast:
            print("applying contrast")
            contrast_factor = 1.0 + (self.contrast_amount / 100.0)
            src_img = cv2.convertScaleAbs(src_img, alpha=contrast_factor, beta=0)


        # Assuming the TPT flag should be PTP in the original code
        # Apply specific contrast adjustments if needed
        
        # Apply color transfer if enabled
        if self.Transfer:
            src_img = self.color_transfer(src_img)
            print("transfer")
        
        # Convert back to PIL Image before returning if needed
        # src_img = Image.fromarray(cv2.cvtColor(src_img, cv2.COLOR_BGR2RGB))
        print("done")
        return src_img

    
    def process(self):
        self.total_frames = len([filename for filename in os.listdir(self.path) if filename.lower().endswith(('.jpg', '.jpeg', '.png'))])
        for filename in os.listdir(self.path):
            filepath = os.path.join(self.path, filename)
            if os.path.isfile(filepath) and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image = cv2.imread(filepath)
                corrected_image = self.apply(image)

                # Display frame number out of total frames
                print(f"Frame {self.current_frame + 1}/{self.total_frames}")
                # Write the corrected image to file
                output_path = os.path.join(self.output_dir, f"frame_{self.current_frame:04d}.jpg")
                cv2.imwrite(output_path, corrected_image)

                self.current_frame += 1