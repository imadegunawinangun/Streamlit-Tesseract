from io import BytesIO
from typing import Dict, List, Optional, Tuple, Any, Union
import os
import tempfile

import cv2
import numpy as np
import pdf2image
import streamlit as st
from pdf2image.exceptions import PDFInfoNotInstalledError
from pdf2image.exceptions import PDFPageCountError
from pdf2image.exceptions import PDFPopplerTimeoutError
from pdf2image.exceptions import PDFSyntaxError
from PIL import Image


# ============================================================================
# PDF TO IMAGE CONVERSION FUNCTIONS
# ============================================================================

@st.cache_data(show_spinner=False)
def pdftoimage(pdf_file: BytesIO, page: int = 1) -> tuple[np.ndarray, str]:
    """
    Convert a PDF page to an OpenCV image.
    
    Args:
        pdf_file: PDF file as BytesIO
        page: Page number to convert (1-based)
        
    Returns:
        Tuple of (image_array, error_message)
    """
    image, error = None, None
    try:
        image = convert(pdf_file=pdf_file, page=page)
        if image is not None:
            image = np.array(image)  # convert image to numpy array
            image = img2opencv2(image)
        else:
            error = "Invalid PDF page selected."
    except PDFInfoNotInstalledError:
        error = "PDFInfoNotInstalledError: PDFInfo is not installed?"
    except PDFPageCountError:
        error = "PDFPageCountError: Could not determine number of pages in PDF."
    except PDFSyntaxError:
        error = "PDFSyntaxError: PDF is damaged/corrupted?"
    except PDFPopplerTimeoutError:
        error = "PDFPopplerTimeoutError: PDF conversion timed out."
    except Exception as e:
        error = str(e)
    return (image, error)


@st.cache_data(show_spinner=False)
def convert(pdf_file: BytesIO, page: int = 1) -> np.ndarray:
    """
    Convert a PDF page to a PIL Image.
    
    Args:
        pdf_file: PDF file as BytesIO
        page: Page number to convert (1-based)
        
    Returns:
        PIL Image or None if conversion failed
    """
    images = pdf2image.convert_from_bytes(
        pdf_file=pdf_file.read(),
        dpi=300,
        single_file=True,
        output_file=None,
        output_folder=None,
        timeout=20,
        first_page=page,
    )
    return images[0] if images else None


@st.cache_data(show_spinner=False)
def img2opencv2(pil_image: np.ndarray) -> np.ndarray:
    """
    Convert PIL Image to OpenCV image format.
    
    Args:
        pil_image: PIL Image
        
    Returns:
        OpenCV image (BGR format)
    """
    return cv2.cvtColor(pil_image, cv2.COLOR_RGB2BGR)


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


# ============================================================================
# ENHANCED DOCUMENT FORMAT HANDLING FUNCTIONS
# ============================================================================

def get_supported_image_formats() -> Dict[str, List[str]]:
    """
    Get a dictionary of supported image formats by category.
    
    Returns:
        Dictionary mapping category to list of supported formats
    """
    return {
        "common": ["jpg", "jpeg", "png", "bmp", "tiff", "tif"],
        "document": ["pdf"],
        "all": ["jpg", "jpeg", "png", "bmp", "tiff", "tif", "pdf"]
    }


def validate_image_format(file_path: str, file_content: bytes) -> Tuple[bool, str, str]:
    """
    Validate the format of an image file.
    
    Args:
        file_path: Path or name of the file
        file_content: Raw file content
        
    Returns:
        Tuple of (is_valid, format_name, error_message)
    """
    # Get file extension
    file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    
    # Check if extension is supported
    supported_formats = get_supported_image_formats()["all"]
    if file_ext not in supported_formats:
        return (False, "", f"Unsupported file format: {file_ext}")
    
    # For PDF files, we can't validate content with PIL
    if file_ext == "pdf":
        return (True, "pdf", "")
    
    # For image files, validate with PIL
    try:
        with Image.open(BytesIO(file_content)) as img:
            format_name = img.format.lower() if img.format else file_ext
            return (True, format_name, "")
    except Exception as e:
        return (False, "", f"Invalid image file: {str(e)}")


def get_image_info(image: Union[np.ndarray, Image.Image, bytes]) -> Dict[str, Any]:
    """
    Get detailed information about an image.
    
    Args:
        image: Image as numpy array, PIL Image, or bytes
        
    Returns:
        Dictionary with image information
    """
    info = {}
    
    try:
        # Convert to PIL Image if needed
        pil_image = _convert_to_pil(image)
        
        # Basic info
        info["width"] = pil_image.width
        info["height"] = pil_image.height
        info["mode"] = pil_image.mode
        info["format"] = pil_image.format
        
        # Calculate aspect ratio
        info["aspect_ratio"] = pil_image.width / pil_image.height
        
        # Calculate size in MB
        if isinstance(image, bytes):
            info["size_mb"] = len(image) / (1024 * 1024)
        else:
            with BytesIO() as buffer:
                pil_image.save(buffer, format="PNG")
                info["size_mb"] = buffer.tell() / (1024 * 1024)
        
        # Color information
        info.update(_get_color_info(pil_image))
        
        # Check if image might be a document
        info["is_document_like"] = _is_document_like(pil_image)
        
    except Exception as e:
        info["error"] = str(e)
    
    return info


def _convert_to_pil(image: Union[np.ndarray, Image.Image, bytes]) -> Image.Image:
    """
    Convert various image formats to PIL Image.
    
    Args:
        image: Image as numpy array, PIL Image, or bytes
        
    Returns:
        PIL Image
    """
    if isinstance(image, bytes):
        return Image.open(BytesIO(image))
    elif isinstance(image, np.ndarray):
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    else:
        return image


def _get_color_info(pil_image: Image.Image) -> Dict[str, Any]:
    """
    Get color information about a PIL Image.
    
    Args:
        pil_image: PIL Image
        
    Returns:
        Dictionary with color information
    """
    info = {}
    
    if pil_image.mode == "RGB":
        info["channels"] = 3
        info["color_space"] = "RGB"
    elif pil_image.mode == "RGBA":
        info["channels"] = 4
        info["color_space"] = "RGBA"
    elif pil_image.mode == "L":
        info["channels"] = 1
        info["color_space"] = "Grayscale"
    else:
        info["channels"] = len(pil_image.getbands())
        info["color_space"] = pil_image.mode
    
    return info


def _is_document_like(image: Image.Image) -> bool:
    """
    Determine if an image looks like a document based on its characteristics.
    
    Args:
        image: PIL Image
        
    Returns:
        True if the image appears to be a document
    """
    # Check aspect ratio (documents are typically portrait)
    aspect_ratio = image.width / image.height
    if aspect_ratio < 0.7 or aspect_ratio > 1.5:
        return False
    
    # Check if image is mostly white/light (common in documents)
    if image.mode == "RGB":
        # Convert to grayscale
        gray = image.convert("L")
        # Calculate average brightness
        avg_brightness = sum(gray.getdata()) / (gray.width * gray.height)
        # Documents typically have high average brightness
        if avg_brightness < 150:
            return False
    
    return True


def convert_image_format(image: Union[np.ndarray, Image.Image],
                        target_format: str,
                        quality: int = 95) -> bytes:
    """
    Convert an image to a different format.
    
    Args:
        image: Source image as numpy array or PIL Image
        target_format: Target format (jpg, png, etc.)
        quality: Quality for lossy formats (1-100)
        
    Returns:
        Converted image as bytes
    """
    # Convert to PIL Image if needed
    pil_image = _convert_to_pil(image)
    
    # Convert to RGB if saving as JPEG
    if target_format.lower() in ["jpg", "jpeg"] and pil_image.mode in ["RGBA", "LA"]:
        # Create a white background
        background = Image.new("RGB", pil_image.size, (255, 255, 255))
        if pil_image.mode == "RGBA":
            background.paste(pil_image, mask=pil_image.split()[-1])
        else:
            background.paste(pil_image, mask=pil_image.split()[-1])
        pil_image = background
    
    # Save to bytes
    with BytesIO() as buffer:
        if target_format.lower() in ["jpg", "jpeg"]:
            pil_image.save(buffer, format="JPEG", quality=quality, optimize=True)
        else:
            pil_image.save(buffer, format=target_format.upper(), optimize=True)
        return buffer.getvalue()


def optimize_image_for_ocr(image: Union[np.ndarray, Image.Image],
                          target_dpi: int = 300) -> np.ndarray:
    """
    Optimize an image for OCR processing.
    
    Args:
        image: Source image as numpy array or PIL Image
        target_dpi: Target DPI for the optimized image
        
    Returns:
        Optimized image as numpy array
    """
    # Convert to PIL Image if needed
    pil_image = _convert_to_pil(image)
    
    # Get current DPI
    current_dpi = pil_image.info.get("dpi", (72, 72))[0]
    
    # Calculate scaling factor
    scale_factor = target_dpi / current_dpi
    
    # Resize if needed
    if scale_factor > 1.1:  # Only upscale if significantly needed
        new_width = int(pil_image.width * scale_factor)
        new_height = int(pil_image.height * scale_factor)
        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Convert back to numpy array
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


# ============================================================================
# PDF METADATA AND MULTI-PAGE FUNCTIONS
# ============================================================================

def extract_pdf_metadata(pdf_file: BytesIO) -> Dict[str, Any]:
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_file: PDF file as BytesIO
        
    Returns:
        Dictionary with PDF metadata
    """
    metadata = {}
    
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(pdf_file.read())
            temp_path = temp_file.name
        
        try:
            # Get page count
            pages = pdf2image.convert_from_bytes(
                open(temp_path, "rb").read(),
                dpi=150,
                output_folder=None,
                fmt="ppm"
            )
            metadata["page_count"] = len(pages)
            
            # Try to extract more metadata using PyPDF2 if available
            try:
                import PyPDF2
                with open(temp_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    if pdf_reader.metadata:
                        metadata.update({
                            "title": pdf_reader.metadata.get('/Title', ''),
                            "author": pdf_reader.metadata.get('/Author', ''),
                            "subject": pdf_reader.metadata.get('/Subject', ''),
                            "creator": pdf_reader.metadata.get('/Creator', ''),
                            "producer": pdf_reader.metadata.get('/Producer', ''),
                            "creation_date": str(pdf_reader.metadata.get('/CreationDate', '')),
                            "modification_date": str(pdf_reader.metadata.get('/ModDate', ''))
                        })
            except ImportError:
                metadata["note"] = "PyPDF2 not available for detailed metadata extraction"
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        metadata["error"] = str(e)
    
    return metadata


def extract_all_pdf_pages(pdf_file: BytesIO,
                         dpi: int = 300,
                         output_format: str = "numpy") -> List[Union[np.ndarray, Image.Image]]:
    """
    Extract all pages from a PDF file.
    
    Args:
        pdf_file: PDF file as BytesIO
        dpi: DPI for the extracted images
        output_format: Output format ("numpy" or "pil")
        
    Returns:
        List of extracted pages
    """
    try:
        # Extract all pages
        images = pdf2image.convert_from_bytes(
            pdf_file=pdf_file.read(),
            dpi=dpi,
            output_folder=None,
            fmt="ppm"
        )
        
        # Convert to requested format
        if output_format == "numpy":
            return [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in images]
        else:
            return images
            
    except Exception as e:
        raise RuntimeError(f"Error extracting PDF pages: {str(e)}")


def create_pdf_from_images(images: List[Union[np.ndarray, Image.Image]],
                          output_path: str,
                          quality: int = 95) -> bool:
    """
    Create a PDF from a list of images.
    
    Args:
        images: List of images as numpy arrays or PIL Images
        output_path: Path where the PDF will be saved
        quality: Quality for the images in the PDF
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert all images to PIL format
        pil_images = []
        for img in images:
            pil_img = _convert_to_pil(img)
            pil_images.append(pil_img)
        
        # Save as PDF
        pil_images[0].save(
            output_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=pil_images[1:],
            quality=quality
        )
        
        return True
        
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        return False


# ============================================================================
# DOCUMENT QUALITY ANALYSIS FUNCTIONS
# ============================================================================

def analyze_document_quality(image: Union[np.ndarray, Image.Image]) -> Dict[str, Any]:
    """
    Analyze the quality of a document image.
    
    Args:
        image: Document image as numpy array or PIL Image
        
    Returns:
        Dictionary with quality metrics
    """
    # Convert to numpy array if needed
    if isinstance(image, Image.Image):
        np_image = np.array(image)
    else:
        np_image = image.copy()
    
    # Convert to grayscale if needed
    if len(np_image.shape) == 3:
        gray = cv2.cvtColor(np_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = np_image.copy()
    
    metrics = {}
    
    # Calculate sharpness using Laplacian variance
    metrics["sharpness"] = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Calculate contrast
    metrics["contrast"] = gray.std()
    
    # Calculate brightness
    metrics["brightness"] = gray.mean()
    
    # Calculate noise level
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    metrics["noise"] = np.mean(np.abs(gray.astype(float) - blurred.astype(float)))
    
    # Calculate text density (percentage of dark pixels)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    metrics["text_density"] = np.sum(binary == 255) / binary.size
    
    # Calculate overall quality score
    metrics["overall_quality"] = _calculate_quality_score(metrics)
    
    return metrics


def _calculate_quality_score(metrics: Dict[str, float]) -> float:
    """
    Calculate an overall quality score from individual metrics.
    
    Args:
        metrics: Dictionary with individual quality metrics
        
    Returns:
        Overall quality score (0-100)
    """
    quality_score = 0
    
    # Sharpness scoring
    if metrics["sharpness"] > 100:
        quality_score += 25
    elif metrics["sharpness"] > 50:
        quality_score += 15
    elif metrics["sharpness"] > 20:
        quality_score += 5
    
    # Contrast scoring
    if metrics["contrast"] > 50:
        quality_score += 25
    elif metrics["contrast"] > 30:
        quality_score += 15
    elif metrics["contrast"] > 15:
        quality_score += 5
    
    # Brightness scoring
    if 100 <= metrics["brightness"] <= 200:
        quality_score += 25
    elif 80 <= metrics["brightness"] <= 220:
        quality_score += 15
    elif 60 <= metrics["brightness"] <= 240:
        quality_score += 5
    
    # Noise scoring (lower is better)
    if metrics["noise"] < 5:
        quality_score += 25
    elif metrics["noise"] < 10:
        quality_score += 15
    elif metrics["noise"] < 20:
        quality_score += 5
    
    return min(quality_score, 100)


# ============================================================================
# DEMO/TEST FUNCTIONS
# ============================================================================

if __name__ == "__main__":
    """Just to test the functions in this file"""
    st.title("pdf2image 📝")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file is not None:
        # streamlit number input
        page = st.number_input("Page", min_value=1, max_value=100, value=1, step=1)
        cv2image = pdftoimage(uploaded_file, page=page)
        if cv2image is not None:
            cv2image = np.array(cv2image)  # convert image to numpy array
            cv2image = img2opencv2(cv2image)
            # rotate image with streamlit slider and opencv
            angle90 = st.slider(
                "Rotate rectangular [Degree]",
                min_value=0,
                max_value=270,
                value=0,
                step=90,
            )
            # cv2image = cv2.rotate(cv2image, angle90)
            angle = st.slider(
                "Rotate freely [Degree]", min_value=-180, max_value=180, value=0, step=1
            )
            height, width = cv2image.shape[:2]
            center = (width / 2, height / 2)
            rotate_matrix = cv2.getRotationMatrix2D(center=center, angle=angle, scale=1)
            cv2image = cv2.warpAffine(
                src=cv2image,
                M=rotate_matrix,
                dsize=(width, height),
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(255, 255, 255),
            )
            height, width = cv2image.shape[:2]
            cropleft = st.slider(
                "Crop from Left [Pixel]",
                min_value=0,
                max_value=width - 1,
                value=0,
                step=1,
            )
            cropright = st.slider(
                "Crop from Right [Pixel]",
                min_value=0,
                max_value=width - 1,
                value=0,
                step=1,
            )
            cropright = width - cropright
            croptop = st.slider(
                "Crop from Top [Pixel]",
                min_value=0,
                max_value=height - 1,
                value=0,
                step=1,
            )
            cropbottom = st.slider(
                "Crop from Bottom [Pixel]",
                min_value=0,
                max_value=height - 1,
                value=0,
                step=1,
            )
            cropbottom = height - cropbottom
            # check for invalid crop values
            if cropleft >= cropright or croptop >= cropbottom:
                st.warning("Invalid crop values")
                st.stop()
            else:
                cv2image = cv2image[croptop:cropbottom, cropleft:cropright]
                cv2image = grayscale(cv2image)
                st.image(cv2image, width=600)
