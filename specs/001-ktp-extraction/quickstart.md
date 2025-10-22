# Quickstart Guide: KTP Data Extraction and Document Population

**Date**: 2025-10-20  
**Feature**: KTP Data Extraction and Document Population  
**Spec**: [specs/001-ktp-extraction/spec.md](spec.md)

## Overview

The KTP Data Extraction feature enables automatic extraction of structured data from Indonesian ID cards (KTP) using OCR technology with Tesseract. The system processes uploaded KTP images, extracts key information fields, and allows users to populate this data into various document templates for automatic document generation.

### Key Features

- **OCR-based Data Extraction**: Automatically extracts structured data from KTP images with confidence scoring
- **Manual Correction**: Allows users to review and correct extracted data before document generation
- **Template-based Document Generation**: Supports multiple document templates with customizable field mappings
- **Multiple Output Formats**: Generates documents in both PDF and DOCX formats
- **Real-time Preview**: Provides preview of documents with populated data before final generation

### Supported KTP Fields

- NIK (Indonesian ID Number)
- Full Name
- Place and Date of Birth
- Gender
- Address
- Religion
- Marital Status
- Occupation
- Validity Period

## Installation

### Prerequisites

- Python 3.11 or higher
- Tesseract OCR with Indonesian language pack
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Streamlit-Tesseract
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

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

### 4. Verify Installation

```bash
tesseract --version
tesseract --list-langs | grep ind
```

You should see Tesseract version information and "ind" (Indonesian) in the list of languages.

## Usage

### Starting the Application

```bash
streamlit run streamlit_app.py
```

The application will open in your web browser at `http://localhost:8501`.

### Basic Workflow

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

### API Usage

For programmatic access, you can use the REST API endpoints. See [contracts/api.md](contracts/api.md) for detailed API documentation.

#### Example: Upload KTP for Extraction

```python
import requests

# Upload KTP image
with open('ktp_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/ktp/upload',
        files={'image': f}
    )

ktp_data = response.json()
print(f"Extracted NIK: {ktp_data['ktp_data']['nik']}")
```

#### Example: Generate Document

```python
import requests

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

## Tips for Best Results

### Image Quality

- Use clear, high-resolution images
- Ensure good lighting and avoid shadows
- Place the KTP on a flat surface with high contrast
- Avoid blurry images and camera shake

### KTP Positioning

- Ensure the entire KTP is visible in the image
- Avoid cutting off any edges or corners
- Keep the KTP parallel to the camera to avoid distortion
- If the KTP is rotated, the system will attempt to auto-correct

### Data Review

- Always review extracted data before generating documents
- Pay special attention to fields with low confidence scores
- Verify critical fields like NIK (must be 16 digits)
- Check that dates are in the correct format

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   - Ensure Tesseract is installed and in your system PATH
   - Restart your terminal/command prompt after installation

2. **Indonesian language pack not available**
   - Verify the Indonesian language pack is installed
   - On Windows, you may need to reinstall Tesseract with the language pack selected

3. **Poor OCR results**
   - Try improving image quality with better lighting
   - Ensure the KTP is not blurry or distorted
   - Check that the Indonesian language pack is properly installed

4. **Application won't start**
   - Verify all Python dependencies are installed
   - Check that you're using Python 3.11 or higher
   - Review any error messages in the terminal

### Getting Help

For more technical details about implementation decisions, refer to the [research.md](research.md) document. For data model information, see [data-model.md](data-model.md).

## Performance Expectations

- **Image Processing**: Under 30 seconds for standard quality images
- **Full Workflow**: Under 3 minutes from upload to document generation
- **Accuracy**: 95% accuracy for key fields (NIK, name, address) on clear KTP images

## Next Steps

Once you're familiar with the basic workflow, you can:

1. Create custom document templates for your specific needs
2. Explore the API for integration with other systems
3. Customize field mappings for specialized documents
4. Implement batch processing for multiple KTP images