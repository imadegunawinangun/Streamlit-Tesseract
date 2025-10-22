from io import BytesIO
from typing import List, Tuple, Optional, Dict, Any
import functools
import time

import cv2
import numpy as np
import streamlit as st
from scipy.ndimage import rotate as rotate_image
from PIL import Image


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# Rotation angle constants
ANGLES = {
    0: None,
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}

# For backward compatibility
angles = ANGLES


# ============================================================================
# BASIC IMAGE PROCESSING FUNCTIONS
# ============================================================================

@st.cache_data(show_spinner=False)
def load_image(image_file: BytesIO) -> np.ndarray:
    """
    Load image from BytesIO to numpy array.
    
    Args:
        image_file: Image file in BytesIO format
        
    Returns:
        Image as numpy array
    """
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    return cv2.imdecode(file_bytes, 1)


@st.cache_data(show_spinner=False)
def grayscale(img: np.ndarray) -> np.ndarray:
    """
    Convert image to grayscale.
    
    Args:
        img: Input image
        
    Returns:
        Grayscale image
    """
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


@st.cache_data(show_spinner=False)
def remove_noise(img: np.ndarray) -> np.ndarray:
    """
    Remove noise using median blur.
    
    Args:
        img: Input image
        
    Returns:
        Denoised image
    """
    return cv2.medianBlur(img, 5)


@st.cache_data(show_spinner=False)
def denoising(img: np.ndarray, strength: int = 10) -> np.ndarray:
    """
    Advanced denoising using non-local means.
    
    Args:
        img: Input image
        strength: Denoising strength (1-40)
        
    Returns:
        Denoised image
    """
    if len(img.shape) == 3:
        return cv2.fastNlMeansDenoisingColored(img, None, strength, strength, 7, 21)
    else:
        return cv2.fastNlMeansDenoising(img, None, strength, 7, 21)


@st.cache_data(show_spinner=False)
def thresholding(img: np.ndarray, threshold: int = 128) -> np.ndarray:
    """
    Apply thresholding to create binary image.
    
    Args:
        img: Input image
        threshold: Threshold value (0-255)
        
    Returns:
        Binary image
    """
    # Convert the image to grayscale
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Apply the threshold
    _, img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    return img


@st.cache_data(show_spinner=False)
def dilate(img: np.ndarray) -> np.ndarray:
    """
    Apply dilation morphological operation.
    
    Args:
        img: Input image
        
    Returns:
        Dilated image
    """
    kernel = np.ones((5, 5), np.uint8)
    return cv2.dilate(img, kernel, iterations=1)


@st.cache_data(show_spinner=False)
def erode(img: np.ndarray) -> np.ndarray:
    """
    Apply erosion morphological operation.
    
    Args:
        img: Input image
        
    Returns:
        Eroded image
    """
    kernel = np.ones((5, 5), np.uint8)
    return cv2.erode(img, kernel, iterations=1)


@st.cache_data(show_spinner=False)
def opening(img: np.ndarray) -> np.ndarray:
    """
    Apply opening morphological operation (erosion followed by dilation).
    
    Args:
        img: Input image
        
    Returns:
        Processed image
    """
    kernel = np.ones((5, 5), np.uint8)
    return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)


@st.cache_data(show_spinner=False)
def convert_to_rgb(img: np.ndarray) -> np.ndarray:
    """
    Convert BGR image to RGB for display.
    
    Args:
        img: Input image
        
    Returns:
        RGB image
    """
    # Check if image is color
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    else:
        return img


# ============================================================================
# IMAGE TRANSFORMATION FUNCTIONS
# ============================================================================

@st.cache_data(show_spinner=False)
def rotate90(img, rotate: bool = None) -> np.ndarray:
    """
    Rotate the image by 90 degree steps.
    
    Args:
        img: Input image
        rotate: Rotation constant from cv2.ROTATE_*
        
    Returns:
        Rotated image
    """
    if rotate is not None:
        img = cv2.rotate(img, rotate)
    return img


@st.cache_data(show_spinner=False)
def rotate(img: np.ndarray, angle: int = None) -> np.ndarray:
    """
    Rotate the image by free angle degrees.
    Uses the OpenCV warpAffine function. Rotation losses the image corners.
    
    Args:
        img: Input image
        angle: Angle in degrees
        
    Returns:
        Rotated image
    """
    if angle is not None:
        height, width = img.shape[:2]
        center = (width / 2, height / 2)
        rotate_matrix = cv2.getRotationMatrix2D(center=center, angle=angle, scale=1)
        img = cv2.warpAffine(
            src=img,
            M=rotate_matrix,
            dsize=(width, height),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255),
        )
    return img


@st.cache_data(show_spinner=False)
def rotate_scipy(img: np.ndarray, angle: int = None, reshape: bool = True) -> np.ndarray:
    """
    Rotate the image by free angle degrees using scipy.
    
    Args:
        img: Input image
        angle: Angle in degrees
        reshape: If True, the image is reshaped to fit the rotated image
        
    Returns:
        Rotated image
    """
    if angle is not None:
        img = rotate_image(
            input=img, angle=angle, reshape=reshape, mode="constant", cval=255
        )
    return img


@st.cache_data(show_spinner=False)
def crop(img: np.ndarray, left: int = 0, right: int = 0, top: int = 0, bottom: int = 0) -> np.ndarray:
    """
    Crop the image from the edges.
    
    Args:
        img: Input image
        left: Number of percent to crop from the left
        right: Number of percent to crop from the right
        top: Number of percent to crop from the top
        bottom: Number of percent to crop from the bottom
        
    Returns:
        Cropped image
    """
    height, width = img.shape[:2]
    left = int(width * left / 100)
    right = int(width * right / 100)
    top = int(height * top / 100)
    bottom = int(height * bottom / 100)
    return img[top : height - bottom, left : width - right]


# ============================================================================
# KTP-SPECIFIC PREPROCESSING FUNCTIONS
# ============================================================================

@st.cache_data(show_spinner=False)
def adaptive_threshold(img: np.ndarray, block_size: int = 11, c: int = 2) -> np.ndarray:
    """
    Apply adaptive thresholding to handle varying lighting conditions.
    
    Args:
        img: Input image (should be grayscale)
        block_size: Size of the neighborhood area
        c: Constant subtracted from the mean
        
    Returns:
        Thresholded image
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    return cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, block_size, c)


@st.cache_data(show_spinner=False)
def clahe_enhancement(img: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) to improve contrast.
    
    Args:
        img: Input image (should be grayscale)
        clip_limit: Threshold for contrast limiting
        tile_grid_size: Size of the grid for histogram equalization
        
    Returns:
        Enhanced image
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe.apply(img)


@st.cache_data(show_spinner=False)
def shadow_removal(img: np.ndarray) -> np.ndarray:
    """
    Remove shadows from the image using morphological operations.
    
    Args:
        img: Input image
        
    Returns:
        Image with shadows reduced
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Create a kernel for morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
    
    # Apply morphological opening to estimate background
    background = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    
    # Subtract background from original image
    normalized = cv2.normalize(img - background, None, 0, 255, cv2.NORM_MINMAX)
    
    return normalized


@st.cache_data(show_spinner=False)
def sharpen_image(img: np.ndarray) -> np.ndarray:
    """
    Apply sharpening filter to enhance text edges.
    
    Args:
        img: Input image
        
    Returns:
        Sharpened image
    """
    # Create a sharpening kernel
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    
    return cv2.filter2D(img, -1, kernel)


@st.cache_data(show_spinner=False)
def detect_edges(img: np.ndarray, low_threshold: int = 50, high_threshold: int = 150) -> np.ndarray:
    """
    Detect edges in the image using Canny edge detection.
    
    Args:
        img: Input image (should be grayscale)
        low_threshold: First threshold for the hysteresis procedure
        high_threshold: Second threshold for the hysteresis procedure
        
    Returns:
        Edge-detected image
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    return cv2.Canny(img, low_threshold, high_threshold)


@st.cache_data(show_spinner=False)
def detect_document_boundary(img: np.ndarray) -> Optional[np.ndarray]:
    """
    Detect the document boundary in the image.
    
    Args:
        img: Input image
        
    Returns:
        Contour of the document boundary or None if not found
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    
    # Apply edge detection
    edges = detect_edges(blurred)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Sort contours by area in descending order
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Find the largest contour with 4 points (assuming rectangular document)
    for contour in contours[:5]:  # Check the 5 largest contours
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        
        if len(approx) == 4:  # Found a quadrilateral
            return approx
    
    return None


@st.cache_data(show_spinner=False)
def perspective_transform(img: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """
    Apply perspective transformation to straighten the document.
    
    Args:
        img: Input image
        corners: Four corner points of the document
        
    Returns:
        Perspective-corrected image
    """
    # Order the corner points
    pts = corners.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    
    # Top-left point will have the smallest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    
    # Bottom-right point will have the largest sum
    rect[2] = pts[np.argmax(s)]
    
    # Compute the difference between the points
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    # Get the width and height of the destination image
    width_top = np.sqrt(((rect[1][0] - rect[0][0]) ** 2) + ((rect[1][1] - rect[0][1]) ** 2))
    width_bottom = np.sqrt(((rect[2][0] - rect[3][0]) ** 2) + ((rect[2][1] - rect[3][1]) ** 2))
    max_width = int(max(width_top, width_bottom))
    
    height_left = np.sqrt(((rect[3][0] - rect[0][0]) ** 2) + ((rect[3][1] - rect[0][1]) ** 2))
    height_right = np.sqrt(((rect[2][0] - rect[1][0]) ** 2) + ((rect[2][1] - rect[1][1]) ** 2))
    max_height = int(max(height_left, height_right))
    
    # Destination points
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]], dtype="float32")
    
    # Apply perspective transform
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (max_width, max_height))
    
    return warped


@st.cache_data(show_spinner=False)
def auto_rotate_document(img: np.ndarray) -> np.ndarray:
    """
    Automatically detect and correct document orientation.
    
    Args:
        img: Input image
        
    Returns:
        Rotated image with corrected orientation
    """
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return img
    
    # Find the largest contour (assumed to be the document)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get the minimum area rectangle
    rect = cv2.minAreaRect(largest_contour)
    angle = rect[-1]
    
    # Normalize the angle to be between -45 and 45 degrees
    if angle < -45:
        angle = -(90 + angle)
    elif angle > 45:
        angle = 90 - angle
    
    # If the angle is significant, rotate the image
    if abs(angle) > 1:
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h),
                                borderMode=cv2.BORDER_CONSTANT,
                                borderValue=(255, 255, 255) if len(img.shape) == 3 else 255)
        return rotated
    
    return img


@st.cache_data(show_spinner=False)
def preprocess_ktp_image(img: np.ndarray,
                        enable_clahe: bool = True,
                        enable_shadow_removal: bool = True,
                        enable_sharpening: bool = True,
                        enable_auto_rotate: bool = True,
                        enable_adaptive_threshold: bool = False) -> np.ndarray:
    """
    Apply a complete preprocessing pipeline optimized for KTP documents.
    
    Args:
        img: Input image
        enable_clahe: Whether to apply CLAHE enhancement
        enable_shadow_removal: Whether to remove shadows
        enable_sharpening: Whether to apply sharpening
        enable_auto_rotate: Whether to automatically correct orientation
        enable_adaptive_threshold: Whether to apply adaptive thresholding
        
    Returns:
        Preprocessed image
    """
    # Make a copy of the original image
    processed = img.copy()
    
    # Auto-rotate the document if needed
    if enable_auto_rotate:
        processed = auto_rotate_document(processed)
    
    # Remove shadows
    if enable_shadow_removal:
        processed = shadow_removal(processed)
    
    # Apply CLAHE for contrast enhancement
    if enable_clahe:
        processed = clahe_enhancement(processed)
    
    # Apply sharpening
    if enable_sharpening:
        processed = sharpen_image(processed)
    
    # Apply adaptive threshold if requested
    if enable_adaptive_threshold:
        processed = adaptive_threshold(processed)
    
    return processed


# ============================================================================
# IMAGE FORMAT CONVERSION FUNCTIONS
# ============================================================================

@st.cache_data(show_spinner=False)
def convert_to_pil(img: np.ndarray) -> Image.Image:
    """
    Convert OpenCV image to PIL Image.
    
    Args:
        img: OpenCV image (BGR or grayscale)
        
    Returns:
        PIL Image
    """
    if len(img.shape) == 3:
        # Convert BGR to RGB for PIL
        return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    else:
        # Grayscale image
        return Image.fromarray(img)


@st.cache_data(show_spinner=False)
def convert_from_pil(pil_img: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to OpenCV image.
    
    Args:
        pil_img: PIL Image
        
    Returns:
        OpenCV image (BGR or grayscale)
    """
    if pil_img.mode == 'RGB':
        # Convert RGB to BGR for OpenCV
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    elif pil_img.mode == 'L':
        # Grayscale image
        return np.array(pil_img)
    else:
        # Convert to RGB first, then to BGR
        return cv2.cvtColor(np.array(pil_img.convert('RGB')), cv2.COLOR_RGB2BGR)


# ============================================================================
# IMAGE PROCESSING PIPELINE
# ============================================================================

class ImageProcessingPipeline:
    """
    A structured pipeline for image preprocessing with configurable steps.
    Enhanced with toggleable steps and better user interface integration.
    """
    
    def __init__(self):
        self.steps = []
        self.processed_images = {}
        self.current_step = 0
        self.step_enabled = {}  # Track which steps are enabled
    
    def add_step(self, step_name: str, function, enabled: bool = True, **kwargs) -> 'ImageProcessingPipeline':
        """
        Add a processing step to the pipeline.
        
        Args:
            step_name: Name of the processing step
            function: Function to apply
            enabled: Whether this step is enabled by default
            **kwargs: Arguments to pass to the function
             
        Returns:
            Self for method chaining
        """
        self.steps.append({
            "name": step_name,
            "function": function,
            "kwargs": kwargs
        })
        self.step_enabled[step_name] = enabled
        return self
    
    def toggle_step(self, step_name: str, enabled: bool) -> bool:
        """
        Enable or disable a processing step.
        
        Args:
            step_name: Name of the step to toggle
            enabled: Whether to enable the step
            
        Returns:
            True if successful, False if step not found
        """
        if step_name in self.step_enabled:
            self.step_enabled[step_name] = enabled
            return True
        return False
    
    def is_step_enabled(self, step_name: str) -> bool:
        """
        Check if a step is enabled.
        
        Args:
            step_name: Name of the step to check
            
        Returns:
            True if enabled, False otherwise
        """
        return self.step_enabled.get(step_name, False)
    
    def get_enabled_steps(self) -> List[Dict[str, Any]]:
        """
        Get all enabled steps in the pipeline.
        
        Returns:
            List of enabled step dictionaries
        """
        enabled_steps = []
        for step in self.steps:
            if self.step_enabled.get(step["name"], False):
                enabled_steps.append(step)
        return enabled_steps
    
    def process(self, image: np.ndarray, save_intermediate: bool = False) -> np.ndarray:
        """
        Process an image through the pipeline, skipping disabled steps.
        
        Args:
            image: Input image
            save_intermediate: Whether to save intermediate results
             
        Returns:
            Processed image
        """
        current_image = image.copy()
        
        if save_intermediate:
            self.processed_images["original"] = image.copy()
        
        # Only process enabled steps
        enabled_steps = self.get_enabled_steps()
        
        for i, step in enumerate(enabled_steps):
            try:
                # Apply the processing step
                current_image = step["function"](current_image, **step["kwargs"])
                
                if save_intermediate:
                    self.processed_images[step["name"]] = current_image.copy()
                
                self.current_step = i + 1
                
            except Exception as e:
                raise RuntimeError(f"Error in step '{step['name']}': {str(e)}")
        
        return current_image
    
    def get_step_names(self) -> List[str]:
        """
        Get the names of all steps in the pipeline.
        
        Returns:
            List of step names
        """
        return [step["name"] for step in self.steps]
    
    def get_enabled_step_names(self) -> List[str]:
        """
        Get the names of all enabled steps in the pipeline.
        
        Returns:
            List of enabled step names
        """
        return [step["name"] for step in self.steps if self.step_enabled.get(step["name"], False)]
    
    def get_processed_image(self, step_name: str) -> Optional[np.ndarray]:
        """
        Get the result of a specific step.
        
        Args:
            step_name: Name of the step
             
        Returns:
            Processed image or None if not found
        """
        return self.processed_images.get(step_name)
    
    def clear_intermediate_results(self):
        """Clear intermediate processing results."""
        self.processed_images.clear()
        self.current_step = 0
    
    def get_step_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all steps in the pipeline.
        
        Returns:
            Dictionary with step information
        """
        step_info = {}
        for step in self.steps:
            step_info[step["name"]] = {
                "enabled": self.step_enabled.get(step["name"], False),
                "function": step["function"].__name__,
                "kwargs": step["kwargs"]
            }
        return step_info


def create_ktp_preprocessing_pipeline(enable_clahe: bool = True,
                                    enable_shadow_removal: bool = True,
                                    enable_sharpening: bool = True,
                                    enable_auto_rotate: bool = True,
                                    enable_adaptive_threshold: bool = False) -> ImageProcessingPipeline:
    """
    Create a preprocessing pipeline optimized for KTP documents.
    
    Args:
        enable_clahe: Whether to apply CLAHE enhancement
        enable_shadow_removal: Whether to remove shadows
        enable_sharpening: Whether to apply sharpening
        enable_auto_rotate: Whether to automatically correct orientation
        enable_adaptive_threshold: Whether to apply adaptive thresholding
        
    Returns:
        Configured ImageProcessingPipeline
    """
    pipeline = ImageProcessingPipeline()
    
    # Auto-rotate the document if needed
    if enable_auto_rotate:
        pipeline.add_step("auto_rotate", auto_rotate_document)
    
    # Remove shadows
    if enable_shadow_removal:
        pipeline.add_step("shadow_removal", shadow_removal)
    
    # Apply CLAHE for contrast enhancement
    if enable_clahe:
        pipeline.add_step("clahe_enhancement", clahe_enhancement)
    
    # Apply sharpening
    if enable_sharpening:
        pipeline.add_step("sharpening", sharpen_image)
    
    # Apply adaptive threshold if requested
    if enable_adaptive_threshold:
        pipeline.add_step("adaptive_threshold", adaptive_threshold)
    
    return pipeline


def create_basic_preprocessing_pipeline() -> ImageProcessingPipeline:
    """
    Create a basic preprocessing pipeline with common steps.
    
    Returns:
        Configured ImageProcessingPipeline
    """
    pipeline = ImageProcessingPipeline()
    pipeline.add_step("grayscale", grayscale)
    pipeline.add_step("noise_removal", remove_noise)
    return pipeline


def create_advanced_preprocessing_pipeline() -> ImageProcessingPipeline:
    """
    Create an advanced preprocessing pipeline with all available steps.
    
    Returns:
        Configured ImageProcessingPipeline
    """
    pipeline = ImageProcessingPipeline()
    pipeline.add_step("auto_rotate", auto_rotate_document)
    pipeline.add_step("shadow_removal", shadow_removal)
    pipeline.add_step("grayscale", grayscale)
    pipeline.add_step("clahe_enhancement", clahe_enhancement)
    pipeline.add_step("denoising", denoising)
    pipeline.add_step("sharpening", sharpen_image)
    pipeline.add_step("adaptive_threshold", adaptive_threshold)
    return pipeline


def compare_preprocessing_results(original_image: np.ndarray,
                                pipelines: Dict[str, ImageProcessingPipeline],
                                save_intermediate: bool = True) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Compare results from multiple preprocessing pipelines with before/after comparison.
    
    Args:
        original_image: Original image to process
        pipelines: Dictionary of pipeline name to ImageProcessingPipeline
        save_intermediate: Whether to save intermediate results for each pipeline
        
    Returns:
        Dictionary of pipeline name to dictionary of processed images (including intermediate steps)
    """
    results = {"original": {"final": original_image.copy()}}
    
    for name, pipeline in pipelines.items():
        try:
            # Process with intermediate results if requested
            processed = pipeline.process(original_image, save_intermediate=save_intermediate)
            
            if save_intermediate:
                # Create a dictionary with all intermediate steps
                pipeline_results = {"final": processed}
                for step_name, step_image in pipeline.processed_images.items():
                    pipeline_results[step_name] = step_image.copy()
                results[name] = pipeline_results
            else:
                # Just save the final result
                results[name] = {"final": processed}
                
        except Exception as e:
            print(f"Error in pipeline '{name}': {str(e)}")
            # Add a copy of the original as a fallback
            results[name] = {"final": original_image.copy()}
    
    return results


# ============================================================================
# IMAGE ANALYSIS FUNCTIONS
# ============================================================================

def analyze_image_quality(image: np.ndarray) -> Dict[str, float]:
    """
    Analyze the quality of an image.
    
    Args:
        image: Input image
        
    Returns:
        Dictionary with quality metrics
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Calculate metrics
    metrics = {}
    
    # Blur metric (Laplacian variance)
    metrics["blur"] = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Contrast metric (standard deviation)
    metrics["contrast"] = gray.std()
    
    # Brightness metric (mean intensity)
    metrics["brightness"] = gray.mean()
    
    # Noise metric (difference between original and blurred)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    metrics["noise"] = np.mean(np.abs(gray.astype(float) - blurred.astype(float)))
    
    # Edge density metric
    edges = cv2.Canny(gray, 50, 150)
    metrics["edge_density"] = np.sum(edges > 0) / edges.size
    
    return metrics


def suggest_preprocessing_options(image: np.ndarray) -> Dict[str, Any]:
    """
    Suggest preprocessing options based on image quality analysis.
    
    Args:
        image: Input image
        
    Returns:
        Dictionary with suggested preprocessing options
    """
    quality = analyze_image_quality(image)
    suggestions = {
        "enable_clahe": True,
        "enable_shadow_removal": False,
        "enable_sharpening": False,
        "enable_auto_rotate": False,
        "enable_adaptive_threshold": False,
        "reasons": []
    }
    
    # Check for blur
    if quality["blur"] < 100:
        suggestions["enable_sharpening"] = True
        suggestions["reasons"].append("Image appears blurry, sharpening recommended")
    
    # Check for low contrast
    if quality["contrast"] < 50:
        suggestions["enable_clahe"] = True
        suggestions["reasons"].append("Low contrast detected, CLAHE enhancement recommended")
    
    # Check for brightness issues
    if quality["brightness"] < 100:
        suggestions["enable_clahe"] = True
        suggestions["reasons"].append("Image appears dark, contrast enhancement recommended")
    elif quality["brightness"] > 200:
        suggestions["enable_shadow_removal"] = True
        suggestions["reasons"].append("Image appears bright, shadow removal recommended")
    
    # Check for noise
    if quality["noise"] > 10:
        suggestions["enable_denoising"] = True
        suggestions["reasons"].append("High noise detected, denoising recommended")
    
    # Check for low edge density (might indicate rotation issues)
    if quality["edge_density"] < 0.02:
        suggestions["enable_auto_rotate"] = True
        suggestions["reasons"].append("Low edge density, auto-rotation recommended")
    
    return suggestions


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_preprocessing_options() -> Dict[str, Dict[str, Any]]:
    """
    Get available preprocessing options with their default values and descriptions.
    
    Returns:
        Dictionary of preprocessing options
    """
    return {
        "enable_clahe": {
            "default": True,
            "description": "Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) to improve contrast",
            "name": "Contrast Enhancement"
        },
        "enable_shadow_removal": {
            "default": True,
            "description": "Remove shadows using morphological operations",
            "name": "Shadow Removal"
        },
        "enable_sharpening": {
            "default": True,
            "description": "Apply sharpening filter to enhance text edges",
            "name": "Sharpening"
        },
        "enable_auto_rotate": {
            "default": True,
            "description": "Automatically detect and correct document orientation",
            "name": "Auto Rotate"
        },
        "enable_adaptive_threshold": {
            "default": False,
            "description": "Apply adaptive thresholding to handle varying lighting conditions",
            "name": "Adaptive Threshold"
        }
    }


def create_custom_pipeline(steps: List[Dict[str, Any]]) -> ImageProcessingPipeline:
    """
    Create a custom preprocessing pipeline from a list of steps.
    
    Args:
        steps: List of step dictionaries with 'name', 'function', and 'kwargs'
        
    Returns:
        Configured ImageProcessingPipeline
    """
    pipeline = ImageProcessingPipeline()
    
    for step in steps:
        pipeline.add_step(
            step["name"],
            step["function"],
            **step.get("kwargs", {})
        )
    
    return pipeline


def get_available_preprocessing_functions() -> Dict[str, Dict[str, Any]]:
    """
    Get a dictionary of available preprocessing functions.
    
    Returns:
        Dictionary mapping function names to function info
    """
    return {
        "grayscale": {
            "function": grayscale,
            "description": "Convert image to grayscale",
            "parameters": []
        },
        "remove_noise": {
            "function": remove_noise,
            "description": "Remove noise using median blur",
            "parameters": []
        },
        "denoising": {
            "function": denoising,
            "description": "Advanced denoising using non-local means",
            "parameters": [
                {"name": "strength", "type": "int", "default": 10, "min": 1, "max": 40}
            ]
        },
        "thresholding": {
            "function": thresholding,
            "description": "Apply thresholding to create binary image",
            "parameters": [
                {"name": "threshold", "type": "int", "default": 128, "min": 0, "max": 255}
            ]
        },
        "adaptive_threshold": {
            "function": adaptive_threshold,
            "description": "Apply adaptive thresholding for varying lighting",
            "parameters": [
                {"name": "block_size", "type": "int", "default": 11, "min": 3, "max": 51},
                {"name": "c", "type": "int", "default": 2, "min": 0, "max": 20}
            ]
        },
        "clahe_enhancement": {
            "function": clahe_enhancement,
            "description": "Apply Contrast Limited Adaptive Histogram Equalization",
            "parameters": [
                {"name": "clip_limit", "type": "float", "default": 2.0, "min": 0.1, "max": 10.0},
                {"name": "tile_grid_size", "type": "tuple", "default": (8, 8)}
            ]
        },
        "shadow_removal": {
            "function": shadow_removal,
            "description": "Remove shadows using morphological operations",
            "parameters": []
        },
        "sharpen_image": {
            "function": sharpen_image,
            "description": "Apply sharpening filter to enhance edges",
            "parameters": []
        },
        "auto_rotate_document": {
            "function": auto_rotate_document,
            "description": "Automatically detect and correct document orientation",
            "parameters": []
        },
        "rotate90": {
            "function": rotate90,
            "description": "Rotate image by 90 degree steps",
            "parameters": [
                {"name": "rotate", "type": "enum", "options": [None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]}
            ]
        },
        "rotate": {
            "function": rotate,
            "description": "Rotate image by free angle degrees",
            "parameters": [
                {"name": "angle", "type": "int", "default": 0, "min": -180, "max": 180}
            ]
        },
        "rotate_scipy": {
            "function": rotate_scipy,
            "description": "Rotate image by free angle degrees with reshape option",
            "parameters": [
                {"name": "angle", "type": "int", "default": 0, "min": -180, "max": 180},
                {"name": "reshape", "type": "bool", "default": True}
            ]
        },
        "crop": {
            "function": crop,
            "description": "Crop image from edges",
            "parameters": [
                {"name": "left", "type": "int", "default": 0, "min": 0, "max": 50},
                {"name": "right", "type": "int", "default": 0, "min": 0, "max": 50},
                {"name": "top", "type": "int", "default": 0, "min": 0, "max": 50},
                {"name": "bottom", "type": "int", "default": 0, "min": 0, "max": 50}
            ]
        }
    }


# ============================================================================
# PERFORMANCE OPTIMIZATION FUNCTIONS
# ============================================================================

def timed_cache(maxsize: int = 128, ttl: int = 3600):
    """
    A timed cache decorator that expires entries after a specified time.
    
    Args:
        maxsize: Maximum number of items to cache
        ttl: Time to live in seconds
    """
    def decorator(func):
        cache = {}
        timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # Check if cache entry exists and is not expired
            if key in cache and current_time - timestamps[key] < ttl:
                return cache[key]
            
            # Compute result and cache it
            result = func(*args, **kwargs)
            
            # Remove oldest entry if cache is full
            if len(cache) >= maxsize:
                oldest_key = min(timestamps, key=timestamps.get)
                del cache[oldest_key]
                del timestamps[oldest_key]
            
            cache[key] = result
            timestamps[key] = current_time
            
            return result
        
        return wrapper
    return decorator


@timed_cache(maxsize=64, ttl=1800)  # Cache for 30 minutes
def optimized_clahe_enhancement(img_hash: str, img: np.ndarray,
                              clip_limit: float = 2.0,
                              tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Optimized CLAHE enhancement with caching based on image hash.
    
    Args:
        img_hash: Hash of the input image for caching
        img: Input image (should be grayscale)
        clip_limit: Threshold for contrast limiting
        tile_grid_size: Size of the grid for histogram equalization
        
    Returns:
        Enhanced image
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe.apply(img)


@timed_cache(maxsize=32, ttl=1800)  # Cache for 30 minutes
def optimized_shadow_removal(img_hash: str, img: np.ndarray) -> np.ndarray:
    """
    Optimized shadow removal with caching based on image hash.
    
    Args:
        img_hash: Hash of the input image for caching
        img: Input image
        
    Returns:
        Image with shadows reduced
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Create a kernel for morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
    
    # Apply morphological opening to estimate background
    background = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    
    # Subtract background from original image
    normalized = cv2.normalize(img - background, None, 0, 255, cv2.NORM_MINMAX)
    
    return normalized


def calculate_image_hash(img: np.ndarray) -> str:
    """
    Calculate a hash of the image for caching purposes.
    
    Args:
        img: Input image
        
    Returns:
        String hash of the image
    """
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Resize to a small standard size for hashing
    resized = cv2.resize(img, (8, 8))
    
    # Calculate average pixel value
    avg = resized.mean()
    
    # Generate hash
    hash_str = ""
    for i in range(8):
        for j in range(8):
            hash_str += "1" if resized[i, j] > avg else "0"
    
    return hash_str


def optimized_preprocess_ktp_image(img: np.ndarray,
                                 enable_clahe: bool = True,
                                 enable_shadow_removal: bool = True,
                                 enable_sharpening: bool = True,
                                 enable_auto_rotate: bool = True,
                                 enable_adaptive_threshold: bool = False) -> np.ndarray:
    """
    Optimized KTP preprocessing with caching and performance improvements.
    
    Args:
        img: Input image
        enable_clahe: Whether to apply CLAHE enhancement
        enable_shadow_removal: Whether to remove shadows
        enable_sharpening: Whether to apply sharpening
        enable_auto_rotate: Whether to automatically correct orientation
        enable_adaptive_threshold: Whether to apply adaptive thresholding
        
    Returns:
        Preprocessed image
    """
    # Make a copy of the original image
    processed = img.copy()
    
    # Calculate image hash for caching
    img_hash = calculate_image_hash(img)
    
    # Auto-rotate the document if needed
    if enable_auto_rotate:
        processed = auto_rotate_document(processed)
    
    # Remove shadows with caching
    if enable_shadow_removal:
        processed = optimized_shadow_removal(img_hash, processed)
    
    # Apply CLAHE for contrast enhancement with caching
    if enable_clahe:
        processed = optimized_clahe_enhancement(img_hash, processed)
    
    # Apply sharpening
    if enable_sharpening:
        processed = sharpen_image(processed)
    
    # Apply adaptive threshold if requested
    if enable_adaptive_threshold:
        processed = adaptive_threshold(processed)
    
    return processed


def create_optimized_ktp_preprocessing_pipeline(enable_clahe: bool = True,
                                             enable_shadow_removal: bool = True,
                                             enable_sharpening: bool = True,
                                             enable_auto_rotate: bool = True,
                                             enable_adaptive_threshold: bool = False) -> ImageProcessingPipeline:
    """
    Create an optimized preprocessing pipeline with caching for KTP documents.
    
    Args:
        enable_clahe: Whether to apply CLAHE enhancement
        enable_shadow_removal: Whether to remove shadows
        enable_sharpening: Whether to apply sharpening
        enable_auto_rotate: Whether to automatically correct orientation
        enable_adaptive_threshold: Whether to apply adaptive thresholding
        
    Returns:
        Configured ImageProcessingPipeline with optimizations
    """
    pipeline = ImageProcessingPipeline()
    
    # Auto-rotate the document if needed
    if enable_auto_rotate:
        pipeline.add_step("auto_rotate", auto_rotate_document)
    
    # Remove shadows with optimized version
    if enable_shadow_removal:
        pipeline.add_step("shadow_removal", lambda img: optimized_shadow_removal(calculate_image_hash(img), img))
    
    # Apply CLAHE for contrast enhancement with optimized version
    if enable_clahe:
        pipeline.add_step("clahe_enhancement", lambda img: optimized_clahe_enhancement(calculate_image_hash(img), img))
    
    # Apply sharpening
    if enable_sharpening:
        pipeline.add_step("sharpening", sharpen_image)
    
    # Apply adaptive threshold if requested
    if enable_adaptive_threshold:
        pipeline.add_step("adaptive_threshold", adaptive_threshold)
    
    return pipeline


def batch_process_images(images: List[np.ndarray],
                        processing_func: callable,
                        max_workers: int = 4) -> List[np.ndarray]:
    """
    Process multiple images in parallel for better performance.
    
    Args:
        images: List of input images
        processing_func: Function to apply to each image
        max_workers: Maximum number of worker threads
        
    Returns:
        List of processed images
    """
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        processed_images = list(executor.map(processing_func, images))
    
    return processed_images


def resize_image_if_needed(img: np.ndarray, max_width: int = 2000, max_height: int = 2000) -> np.ndarray:
    """
    Resize image if it exceeds maximum dimensions to improve processing speed.
    
    Args:
        img: Input image
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized image if needed, original image otherwise
    """
    height, width = img.shape[:2]
    
    # Check if resizing is needed
    if width <= max_width and height <= max_height:
        return img
    
    # Calculate new dimensions
    if width > height:
        new_width = max_width
        new_height = int(height * (max_width / width))
    else:
        new_height = max_height
        new_width = int(width * (max_height / height))
    
    # Resize image
    resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return resized


def measure_processing_time(func: callable) -> callable:
    """
    Decorator to measure processing time of functions.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function that measures execution time
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Log the processing time
        processing_time = end_time - start_time
        print(f"[PERFORMANCE] {func.__name__} took {processing_time:.3f} seconds")
        
        return result
    return wrapper


# ============================================================================
# INTERACTIVE KTP PREPROCESSING PIPELINE
# ============================================================================

def create_interactive_ktp_pipeline() -> ImageProcessingPipeline:
    """
    Create an interactive KTP preprocessing pipeline with all available steps.
    
    Returns:
        Configured ImageProcessingPipeline with all KTP preprocessing steps
    """
    pipeline = ImageProcessingPipeline()
    
    # Add all available preprocessing steps
    pipeline.add_step("auto_rotate", auto_rotate_document, enabled=True)
    pipeline.add_step("shadow_removal", shadow_removal, enabled=True)
    pipeline.add_step("clahe_enhancement", clahe_enhancement, enabled=True)
    pipeline.add_step("denoising", denoising, enabled=False)
    pipeline.add_step("sharpening", sharpen_image, enabled=True)
    pipeline.add_step("adaptive_threshold", adaptive_threshold, enabled=False)
    
    return pipeline


def smart_auto_enhance(image: np.ndarray) -> Dict[str, Any]:
    """
    Analyze image and automatically suggest optimal preprocessing settings.
    
    Args:
        image: Input image to analyze
        
    Returns:
        Dictionary with suggested preprocessing settings and reasons
    """
    # Analyze image quality
    quality = analyze_image_quality(image)
    
    # Initialize suggestions with default values
    suggestions = {
        "auto_rotate": True,
        "shadow_removal": False,
        "clahe_enhancement": True,
        "denoising": False,
        "sharpening": False,
        "adaptive_threshold": False,
        "reasons": []
    }
    
    # Check for rotation issues
    if quality["edge_density"] < 0.02:
        suggestions["auto_rotate"] = True
        suggestions["reasons"].append("Low edge density detected, auto-rotation recommended")
    
    # Check for shadow issues
    if quality["brightness"] > 180:
        suggestions["shadow_removal"] = True
        suggestions["reasons"].append("Bright image with potential shadows, shadow removal recommended")
    
    # Check for contrast issues
    if quality["contrast"] < 50:
        suggestions["clahe_enhancement"] = True
        suggestions["reasons"].append("Low contrast detected, CLAHE enhancement recommended")
    
    # Check for noise
    if quality["noise"] > 10:
        suggestions["denoising"] = True
        suggestions["reasons"].append("High noise detected, denoising recommended")
    
    # Check for blur
    if quality["blur"] < 100:
        suggestions["sharpening"] = True
        suggestions["reasons"].append("Image appears blurry, sharpening recommended")
    
    # Check for thresholding needs
    if quality["contrast"] > 80 and quality["brightness"] < 120:
        suggestions["adaptive_threshold"] = True
        suggestions["reasons"].append("Good contrast but low brightness, adaptive thresholding may help")
    
    return suggestions


def apply_smart_enhancement(pipeline: ImageProcessingPipeline, image: np.ndarray) -> ImageProcessingPipeline:
    """
    Apply smart auto-enhancement suggestions to a pipeline.
    
    Args:
        pipeline: ImageProcessingPipeline to configure
        image: Input image to analyze
        
    Returns:
        Configured pipeline with smart settings applied
    """
    # Get smart suggestions
    suggestions = smart_auto_enhance(image)
    
    # Apply suggestions to pipeline
    for step_name, enabled in suggestions.items():
        if step_name != "reasons" and step_name in pipeline.step_enabled:
            pipeline.toggle_step(step_name, enabled)
    
    return pipeline


def create_preview_comparison(original_image: np.ndarray,
                            pipeline: ImageProcessingPipeline,
                            enabled_steps: Optional[List[str]] = None) -> Dict[str, np.ndarray]:
    """
    Create a before/after comparison for specific pipeline steps.
    
    Args:
        original_image: Original image to process
        pipeline: ImageProcessingPipeline to use
        enabled_steps: List of specific steps to preview (None for all enabled)
        
    Returns:
        Dictionary with step names and their processed images
    """
    # Save current enabled state
    original_enabled = pipeline.step_enabled.copy()
    
    # Create results dictionary
    results = {"original": original_image.copy()}
    
    # Determine which steps to preview
    steps_to_preview = enabled_steps if enabled_steps else pipeline.get_enabled_step_names()
    
    # Process each step individually
    current_image = original_image.copy()
    
    for step_name in steps_to_preview:
        if step_name in pipeline.step_enabled:
            # Enable only this step
            for name in pipeline.step_enabled:
                pipeline.toggle_step(name, name == step_name)
            
            # Process with just this step
            try:
                step_result = pipeline.process(original_image, save_intermediate=False)
                results[step_name] = step_result.copy()
            except Exception as e:
                print(f"Error processing step '{step_name}': {str(e)}")
                results[step_name] = current_image.copy()
    
    # Restore original enabled state
    for name, enabled in original_enabled.items():
        pipeline.toggle_step(name, enabled)
    
    return results


def create_streamlit_preprocessing_interface(pipeline: ImageProcessingPipeline,
                                          image: np.ndarray,
                                          key_prefix: str = "ktp_preprocess") -> Dict[str, Any]:
    """
    Create a Streamlit interface for interactive preprocessing configuration.
    
    Args:
        pipeline: ImageProcessingPipeline to configure
        image: Input image for analysis
        key_prefix: Prefix for Streamlit widget keys
        
    Returns:
        Dictionary with user selections and processed image
    """
    import streamlit as st
    
    st.subheader("Interactive Preprocessing Configuration")
    
    # Get smart suggestions
    suggestions = smart_auto_enhance(image)
    
    # Display suggestions
    if suggestions["reasons"]:
        st.info("🤖 **Smart Suggestions:** " + "; ".join(suggestions["reasons"]))
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Basic Preprocessing:**")
        
        # Auto-rotate
        auto_rotate = st.checkbox(
            "Auto Rotate Document",
            value=suggestions["auto_rotate"],
            help="Automatically detect and correct document orientation",
            key=f"{key_prefix}_auto_rotate"
        )
        
        # Shadow removal
        shadow_removal = st.checkbox(
            "Shadow Removal",
            value=suggestions["shadow_removal"],
            help="Remove shadows using morphological operations",
            key=f"{key_prefix}_shadow_removal"
        )
        
        # CLAHE enhancement
        clahe_enhancement = st.checkbox(
            "Contrast Enhancement (CLAHE)",
            value=suggestions["clahe_enhancement"],
            help="Improve contrast using adaptive histogram equalization",
            key=f"{key_prefix}_clahe_enhancement"
        )
    
    with col2:
        st.write("**Advanced Preprocessing:**")
        
        # Denoising
        denoising = st.checkbox(
            "Denoising",
            value=suggestions["denoising"],
            help="Remove noise using advanced filtering",
            key=f"{key_prefix}_denoising"
        )
        
        # Sharpening
        sharpening = st.checkbox(
            "Sharpening",
            value=suggestions["sharpening"],
            help="Enhance text edges for better OCR",
            key=f"{key_prefix}_sharpening"
        )
        
        # Adaptive threshold
        adaptive_threshold = st.checkbox(
            "Adaptive Threshold",
            value=suggestions["adaptive_threshold"],
            help="Apply adaptive thresholding for varying lighting",
            key=f"{key_prefix}_adaptive_threshold"
        )
    
    # Apply user selections to pipeline
    pipeline.toggle_step("auto_rotate", auto_rotate)
    pipeline.toggle_step("shadow_removal", shadow_removal)
    pipeline.toggle_step("clahe_enhancement", clahe_enhancement)
    pipeline.toggle_step("denoising", denoising)
    pipeline.toggle_step("sharpening", sharpening)
    pipeline.toggle_step("adaptive_threshold", adaptive_threshold)
    
    # Create action buttons
    col_preview, col_apply, col_reset = st.columns(3)
    
    with col_preview:
        preview_mode = st.selectbox(
            "Preview Mode",
            options=["Final Result", "Step-by-Step", "Before/After"],
            key=f"{key_prefix}_preview_mode"
        )
    
    with col_apply:
        apply_processing = st.button(
            "Apply Processing",
            type="primary",
            key=f"{key_prefix}_apply"
        )
    
    with col_reset:
        reset_to_defaults = st.button(
            "Reset to Smart Defaults",
            key=f"{key_prefix}_reset"
        )
    
    # Handle reset button
    if reset_to_defaults:
        # Apply smart suggestions
        pipeline = apply_smart_enhancement(pipeline, image)
        st.experimental_rerun()
    
    # Process image if requested
    processed_image = None
    if apply_processing or st.session_state.get(f"{key_prefix}_processed", False):
        with st.spinner("Processing image..."):
            processed_image = pipeline.process(image, save_intermediate=True)
            st.session_state[f"{key_prefix}_processed"] = True
    
    # Return configuration and results
    return {
        "pipeline": pipeline,
        "processed_image": processed_image,
        "settings": {
            "auto_rotate": auto_rotate,
            "shadow_removal": shadow_removal,
            "clahe_enhancement": clahe_enhancement,
            "denoising": denoising,
            "sharpening": sharpening,
            "adaptive_threshold": adaptive_threshold,
            "preview_mode": preview_mode
        },
        "suggestions": suggestions
    }
