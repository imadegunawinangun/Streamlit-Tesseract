# Streamlit Tesseract OCR Development Guidelines

Auto-generated from all feature plans. Last updated: [DATE]

## Active Technologies
- Streamlit for web application framework
- Tesseract OCR for primary text extraction
- OpenCV for image preprocessing
- PDF2Image for PDF document handling
- NumPy for array operations
- SciPy for advanced image transformations
- python-docx for DOCX document generation
- reportlab for PDF document generation

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
├── requirements.txt          # Python dependencies
├── .specify/                 # Project governance and templates
└── .streamlit/               # Streamlit configuration
```

## Commands
- `streamlit run streamlit_app.py` - Run the application locally
- `pip install -r requirements.txt` - Install dependencies
- `ruff check .` - Run code quality checks
- `ruff format .` - Format code according to project standards

## Code Style
- Follow ruff configuration defined in pyproject.bak.toml
- Maximum line length: 160 characters
- Use 4 spaces for indentation
- Functions must have docstrings explaining parameters and behavior
- Streamlit components should be separated from business logic

## OCR Development Guidelines
- All image processing functions must be in helpers/opencv.py
- OCR engine integrations must follow the interface pattern in helpers/tesseract.py
- New preprocessing options must include preview functionality
- Error handling must provide user-friendly messages with actionable guidance
- All processing steps must show progress indicators
- Language pack validation must occur before OCR processing

## Document Generation Guidelines
- Document generation functions must be in helpers/document_gen.py
- Document templates must be stored in templates/ with appropriate subdirectories
- Template validation must occur before document generation
- Generated documents must include preview functionality
- Document formatting must be preserved during data insertion
- Error handling must provide specific guidance for template issues

## Recent Changes
[LAST 3 FEATURES AND WHAT THEY ADDED]

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
