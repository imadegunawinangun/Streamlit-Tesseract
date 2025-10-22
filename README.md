<!-- markdownlint-disable MD026 -->
# Streamlit Tesseract OCR :mag_right: :page_facing_up:

Streamlit project with Tesseract OCR running on Streamlit Cloud, featuring specialized KTP (Indonesian ID Card) data extraction and document generation capabilities.

[![Streamlit](https://img.shields.io/badge/Go%20To-Streamlit%20Cloud%20Application-red?logo=streamlit)](https://tesseractocr.streamlit.app/)

## Features

### General OCR Capabilities
- Upload an image with text on it
- Select the language for OCR processing
- Apply image preprocessing options with preview
- Crop the image to the text area
- Run OCR and review results
- Download results as a text file

### KTP Data Extraction Feature :id:
- **Automated Data Extraction**: Extract structured data from Indonesian KTP (ID cards) using Tesseract OCR with Indonesian language support
- **Field Validation**: Automatic validation of extracted data (NIK 16 digits, etc.)
- **Confidence Scoring**: Confidence scores for all extracted fields
- **Manual Correction**: Interface for correcting low-confidence fields
- **Document Generation**: Populate extracted data into document templates
- **Multiple Output Formats**: Generate documents in PDF and DOCX formats
- **Template Management**: Support for custom document templates with field mapping

## Installation

### Prerequisites

- Python 3.11 or higher
- Tesseract OCR with Indonesian language pack
- Git

### Setup Instructions

```bash
# Clone the repository
git clone <repository-url>
cd Streamlit-Tesseract

# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract OCR

#### Windows
1. Download Tesseract installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer and make sure to check the "Indonesian" language pack during installation
3. Add Tesseract to your system PATH

#### macOS
```bash
brew install tesseract
brew install tesseract-lang
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-ind
```

#### Linux (CentOS/RHEL/Fedora)
```bash
sudo yum install tesseract
sudo yum install tesseract-langpack-ind
```

# Verify installation
tesseract --version
tesseract --list-langs | grep ind
```

### Indonesian Language Pack Setup

The Indonesian language pack is essential for KTP data extraction. If you encounter issues:

1. **Verify Installation**: After installing Tesseract, verify the Indonesian language pack is available:
   ```bash
   tesseract --list-langs | grep ind
   ```

2. **Manual Installation** (if not installed via package manager):
   - Download the Indonesian language data file (`ind.traineddata`) from the [tessdata repository](https://github.com/tesseract-ocr/tessdata)
   - Place the file in your Tesseract tessdata directory:
     - Windows: `C:\Program Files\Tesseract-OCR\tessdata`
     - Linux: `/usr/share/tesseract-ocr/4.00/tessdata`
     - macOS: `/usr/local/share/tessdata`

3. **Set Environment Variable** (if needed):
   ```bash
   export TESSDATA_PREFIX=/path/to/your/tessdata/directory
   ```

## Usage

### Starting the Application

```bash
streamlit run streamlit_app.py
```

The application will open in your web browser at `http://localhost:8501`.

### General OCR Workflow

1. Upload an image with text on it
2. Select the language
3. Select the image preprocessing options (if needed) and check the result in the preview
4. Crop the image to the text area (if needed)
5. Run the OCR and check the result in the text preview
6. Adjust the settings or image preprocessing and run the OCR again (if needed)
7. Download the result as a text file or copy from the text preview

### KTP Data Extraction Workflow

1. **Upload KTP Image**
   - Click the "Upload KTP Image" button
   - Select a clear image of an Indonesian ID card
   - Supported formats: JPG, PNG, BMP

2. **Review Extracted Data**
   - The system will automatically extract data from the KTP
   - Review the extracted fields and confidence scores
   - Fields with low confidence will be highlighted for manual review

3. **Edit Data if Needed**
   - Click on any field to edit the extracted value
   - Make corrections as necessary
   - Click "Save Changes" to update the data

4. **Select Document Template**
   - Choose from available document templates
   - Templates include forms, applications, and registration documents
   - Preview how your data will populate in the template

5. **Generate Document**
   - Review the document preview
   - Select output format (PDF or DOCX)
   - Click "Generate Document" to create the final document

6. **Download Document**
   - Download the generated document
   - The document will contain all your KTP data populated in the appropriate fields

### Usage Examples

#### Example 1: Basic KTP Extraction
```python
# This example shows how to use the application to extract KTP data
# 1. Start the application
streamlit run streamlit_app.py

# 2. Select "KTP Extraction & Document Generation" mode
# 3. Upload a KTP image using the file uploader
# 4. Click "Extract KTP Data" to process the image
# 5. Review the extracted data with confidence scores
# 6. Make any necessary corrections
# 7. Save the data for later use
```

#### Example 2: Document Generation
```python
# After extracting KTP data, you can generate documents:
# 1. Navigate to the "Document Generation" tab
# 2. Select a template from the available options
# 3. Choose the KTP data you want to use
# 4. Configure field mappings between KTP data and template placeholders
# 5. Preview the document with populated data
# 6. Generate and download the final document
```

#### Example 3: API Usage (Programmatic Access)
```python
import requests

# Upload KTP for extraction
with open('ktp_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/ktp/upload',
        files={'image': f}
    )

ktp_data = response.json()
print(f"Extracted NIK: {ktp_data['ktp_data']['nik']}")

# Generate document with KTP data
response = requests.post(
    'http://localhost:8000/api/v1/documents/generate',
    json={
        'ktp_id': 'uuid-of-ktp-data',
        'template_id': 'uuid-of-template',
        'output_format': 'PDF'
    }
)

document_info = response.json()
document_id = document_info['document_id']

# Download the generated document
download_response = requests.get(
    f'http://localhost:8000/api/v1/documents/{document_id}/download'
)

with open('generated_document.pdf', 'wb') as f:
    f.write(download_response.content)
```

## Supported KTP Fields

- NIK (Indonesian ID Number)
- Full Name
- Place and Date of Birth
- Gender
- Address
- Religion
- Marital Status
- Occupation
- Validity Period

## Languages :earth_africa:

Installed languages for Tesseract OCR

### 🇬🇧 🇪🇸 🇫🇷 🇩🇪 🇮🇹 🇵🇹 🇨🇿 🇵🇱 🇮🇩

## Performance Expectations

- **Image Processing**: Under 30 seconds for standard quality images
- **Full Workflow**: Under 3 minutes from upload to document generation
- **Accuracy**: 95% accuracy for key fields (NIK, name, address) on clear KTP images

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   - Ensure Tesseract is installed and in your system PATH
   - Restart your terminal/command prompt after installation
   - On Windows, you may need to add Tesseract to PATH manually

2. **Indonesian language pack not available**
   - Verify the Indonesian language pack is installed: `tesseract --list-langs | grep ind`
   - On Windows, you may need to reinstall Tesseract with the language pack selected
   - For manual installation, download `ind.traineddata` from the tessdata repository

3. **Poor OCR results**
   - Try improving image quality with better lighting
   - Ensure the KTP is not blurry or distorted
   - Check that the Indonesian language pack is properly installed
   - Try adjusting preprocessing options in the sidebar

4. **Application won't start**
   - Verify all Python dependencies are installed: `pip install -r requirements.txt`
   - Check that you're using Python 3.11 or higher
   - Review any error messages in the terminal

5. **Document generation fails**
   - Ensure you have created field mappings between KTP data and template placeholders
   - Check that the template file exists and is accessible
   - Verify that all required fields are populated with data

### Tips for Best Results

- Use clear, high-resolution images with good lighting
- Ensure the entire KTP is visible in the image
- Avoid shadows and reflections on the KTP
- Keep the KTP parallel to the camera to avoid distortion
- Always review extracted data before generating documents

## Status :heavy_check_mark:

> Streamlit application is working - 04.06.2024
> KTP Data Extraction feature implemented - 21.10.2025

## Project Structure

```
Streamlit-Tesseract/
├── streamlit_app.py          # Main Streamlit application
├── helpers/                  # Modular processing functions
│   ├── constants.py          # Configuration constants
│   ├── tesseract.py          # Tesseract OCR integration
│   ├── opencv.py             # Image preprocessing functions
│   ├── pdfimage.py           # PDF handling utilities
│   ├── document_gen.py       # Document generation functions
│   ├── easy_ocr.py           # EasyOCR integration (optional)
│   └── style.css             # Application styling
├── templates/                # Document templates for data insertion
│   ├── docx/                 # DOCX template files
│   └── pdf/                  # PDF template files
├── specs/001-ktp-extraction/ # Feature specification documents
└── requirements.txt          # Python dependencies
```

## Future Ideas :bulb:

- Use Pillow for image preprocessing instead of OpenCV
  - any advantages?
- Add Ace Editor for text preview
  - any advantages?
- Add other OCR engines and test them
- Add `easyocr` and test it
  - <https://github.com/JaidedAI/EasyOCR>
- Try `tesserocr` instead of `pytesseract`
  - <https://github.com/sirfz/tesserocr>
- Add `PyMuPDF` and test it
  - <https://github.com/pymupdf/PyMuPDF>
- Add `ocrmypdf` and test it
  - <https://github.com/ocrmypdf/OCRmyPDF>
- Add `PaddleOCR` and test it
  - <https://github.com/PaddlePaddle/PaddleOCR>
- Add `keras-ocr` and test it
  - <https://github.com/faustomorales/keras-ocr>

## Libraries :books:

### Tesseract

- Tesseract Documentation
  - <https://tesseract-ocr.github.io/>
- pytesseract Documentation
  - <https://github.com/madmaze/pytesseract>
- OCR with Tesseract
  - <https://nanonets.com/blog/ocr-with-tesseract/>

### EasyOCR

- <https://github.com/JaidedAI/EasyOCR>

### pdf2image

- <https://github.com/Belval/pdf2image>

### OpenCV

OpenCV is used for image preprocessing before running OCR with Tesseract.

- OpenCV Image Processing Documentation
  - <https://docs.opencv.org/4.x/d2/d96/tutorial_py_table_of_contents_imgproc.html>
- OpenCV Python Tutorial
  - <https://www.geeksforgeeks.org/opencv-python-tutorial/>
- OCR in Python Tutorials
  - <https://www.youtube.com/watch?v=tQGgGY8mTP0&list=PL2VXyKi-KpYuTAZz__9KVl1jQz74bDG7i>

### Pillow

- <https://pillow.readthedocs.io/en/stable/>

## Image Preprocessing :framed_picture:

### Grayscale Conversion

```python
import cv2
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# or
coefficients = [1,0,0] # Gives blue channel all the weight
# for standard gray conversion, coefficients = [0.114, 0.587, 0.299]
m = np.array(coefficients).reshape((1,3))
blue = cv2.transform(im, m)
```

### Brightness and Contrast

- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- <https://www.tutorialspoint.com/how-to-change-the-contrast-and-brightness-of-an-image-using-opencv-in-python>
- <https://stackoverflow.com/questions/50474302/how-do-i-adjust-brightness-contrast-and-vibrance-with-opencv-python>
- <https://stackoverflow.com/questions/32609098/how-to-fast-change-image-brightness-with-python-opencv>
- <https://github.com/milahu/document-photo-auto-threshold>
- <https://stackoverflow.com/questions/56905592/automatic-contrast-and-brightness-adjustment-of-a-color-photo-of-a-sheet-of-pape>
- <https://stackoverflow.com/questions/39308030/how-do-i-increase-the-contrast-of-an-image-in-python-opencv>
- <https://stackoverflow.com/questions/63243202/how-to-auto-adjust-contrast-and-brightness-of-a-scanned-image-with-opencv-python>

### Image Rotation :arrows_counterclockwise:

Methods to rotate an image with different libraries.

#### ... with Pillow :arrows_counterclockwise:

<https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.rotate>

```python
from PIL import Image
with Image.open("hopper.jpg") as im:
    # Rotate the image by 60 degrees counter clockwise
    theta = 60
    white = (255,255,255)
    # Angle is in degrees counter clockwise
    im_rotated = im.rotate(angle=theta, resample=Image.Resampling.BICUBIC, expand=1, fillcolor=white)
```

#### ... with OpenCV :arrows_counterclockwise:

> destructive rotation, loses image data

```python
import cv2
(h, w) = image.shape[:2]
center = (w // 2, h // 2)
M = cv2.getRotationMatrix2D(center, angle, 1)
rotated = cv2.warpAffine(image, M, (w, h))
```

#### ... with imutils :arrows_counterclockwise:

> non-destructive rotation, keeps image data

```python
import imutils
rotate = imutils.rotate_bound(image, angle)
```

#### ... with scipy :arrows_counterclockwise:

> destructive or non-destructive rotation, can be chosen py parameter `reshape`

```python
from scipy.ndimage import rotate as rotate_image
rotated_img1 = rotate_image(input, angle, reshape, mode, cval)
