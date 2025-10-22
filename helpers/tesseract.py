import shutil
import uuid
import time
import functools
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import pytesseract
import streamlit as st
from PIL import Image


# Tesseract configuration constants
pytesseract.pytesseract.tesseract_cmd = None

OEM_OPTIONS = [
    "Original Tesseract only",
    "Neural nets LSTM only  ",
    "Tesseract + LSTM       ",
    "Default                ",
]

PSM_OPTIONS = [
    "Orientation and script detection (OSD) only.                      ",
    "Automatic page segmentation with OSD.                             ",
    "Automatic page segmentation, but no OSD, or OCR. (not implemented)",
    "Fully automatic page segmentation, but no OSD. (Default)          ",
    "Assume a single column of text of variable sizes.                 ",
    "Assume a single uniform block of vertically aligned text.         ",
    "Assume a single uniform block of text.                            ",
    "Treat the image as a single text line.                            ",
    "Treat the image as a single word.                                 ",
    "Treat the image as a single word in a circle.                     ",
    "Treat the image as a single character.                            ",
    "Sparse text. Find as much text as possible in no particular order.",
    "Sparse text with OSD.                                             ",
    "Raw line. Treat the image as a single text line.                  ",
]

# For backward compatibility
oem = OEM_OPTIONS
psm = PSM_OPTIONS


# ============================================================================
# TESSERACT INITIALIZATION FUNCTIONS
# ============================================================================

@st.cache_resource(show_spinner=False)
def find_tesseract_binary() -> str:
    """Find Tesseract binary in system PATH."""
    return shutil.which("tesseract")


@st.cache_resource(show_spinner=False)
def set_tesseract_path(tesseract_path: str):
    """Set Tesseract binary path."""
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


@st.cache_resource(show_spinner=False)
def set_tesseract_binary():
    """Set Tesseract binary path using system PATH."""
    set_tesseract_path(find_tesseract_binary())


@st.cache_resource(show_spinner=False)
def get_tesseract_version() -> tuple[str, str]:
    """Get Tesseract version and check for errors."""
    tesseract_version, error = None, None
    try:
        tesseract_version = pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        error = "TesseractNotFoundError: Tesseract is not installed. Please install Tesseract."
    except Exception as e:
        error = str(e)
    return (tesseract_version, error)


@st.cache_resource(show_spinner=False)
def get_tesseract_languages() -> tuple[list[str], str]:
    """Get list of installed Tesseract language packs."""
    installed_languages, error = list(), None
    try:
        installed_languages = pytesseract.get_languages(config="")
    except pytesseract.TesseractError:
        error = "TesseractError: Tesseract reported an error during language data extraction."
    except pytesseract.TesseractNotFoundError:
        error = "TesseractNotFoundError: Tesseract is not installed. Please install Tesseract."
    except Exception as e:
        error = str(e)
    return (installed_languages, error)


# ============================================================================
# CONFIGURATION FUNCTIONS
# ============================================================================

@st.cache_resource(show_spinner=False)
def get_tesseract_config(oem_index: int, psm_index: int) -> str:
    """Create custom OEM and PSM configuration string."""
    return f"--oem {oem_index} --psm {psm_index}"


def configure_tesseract_for_ktp() -> str:
    """
    Get the optimal Tesseract configuration for KTP processing.
    
    Returns:
        Tesseract configuration string optimized for KTP documents
    """
    # Configuration optimized for Indonesian KTP documents
    # OEM 3: Default LSTM engine
    # PSM 6: Assume a single uniform block of text
    config = "--oem 3 --psm 6"
    
    # Additional parameters for better KTP processing
    # These can be adjusted based on testing
    config += " -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-.,/"
    
    return config


# ============================================================================
# TEXT EXTRACTION FUNCTIONS
# ============================================================================

@st.cache_data(show_spinner=False)
def image_to_string(image: bytes,
                    language_short: str,
                    config: str,
                    timeout: int) -> tuple[str, str]:
    """
    Extract text from image using Tesseract.
    
    Args:
        image: Image data
        language_short: Language code
        config: Tesseract configuration string
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (extracted_text, error_message)
    """
    text, error = None, None
    try:
        text = pytesseract.image_to_string(
                        image=image,
                        lang=language_short,
                        output_type=pytesseract.Output.STRING,
                        config=config,
                        timeout=timeout
                    )
    except pytesseract.TesseractError:
        error = "TesseractError: Tesseract reported an error during text extraction."
    except pytesseract.TesseractNotFoundError:
        error = "TesseractNotFoundError: Tesseract is not installed. Please install Tesseract."
    except RuntimeError:
        error = "RuntimeError: Tesseract timed out during text extraction."
    except Exception as e:
        error = str(e)

    return (text, error)


@st.cache_data(show_spinner=False)
def extract_text_with_confidence(image: Image.Image,
                                 language: str = "ind",
                                 config: str = "--oem 3 --psm 6") -> Tuple[Dict[str, Any], str]:
    """
    Extract text from an image with confidence scores using Tesseract.
    
    Args:
        image: PIL Image object
        language: Language code for OCR (default: Indonesian)
        config: Tesseract configuration string
        
    Returns:
        Tuple[Dict[str, Any], str]: (extraction_data, error_message)
    """
    try:
        # Get detailed OCR data including confidence scores
        data = pytesseract.image_to_data(
            image=image,
            lang=language,
            config=config,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract words with confidence scores
        words = []
        confidences = []
        boxes = []
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:  # Filter out empty entries
                words.append(data['text'][i])
                confidences.append(int(data['conf'][i]) / 100.0)  # Convert to 0-1 scale
                boxes.append({
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i]
                })
        
        # Calculate overall confidence
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Get full text
        full_text = pytesseract.image_to_string(
            image=image,
            lang=language,
            config=config
        )
        
        extraction_data = {
            'text': full_text,
            'words': words,
            'confidences': confidences,
            'boxes': boxes,
            'overall_confidence': overall_confidence,
            'language': language,
            'config': config,
            'extraction_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat()
        }
        
        return (extraction_data, "")
        
    except pytesseract.TesseractError as e:
        return (None, f"TesseractError: {str(e)}")
    except pytesseract.TesseractNotFoundError:
        return (None, "TesseractNotFoundError: Tesseract is not installed. Please install Tesseract.")
    except RuntimeError:
        return (None, "RuntimeError: Tesseract timed out during text extraction.")
    except Exception as e:
        return (None, f"Unexpected error: {str(e)}")


# ============================================================================
# LANGUAGE PACK VALIDATION FUNCTIONS
# ============================================================================

@st.cache_resource(show_spinner=False)
def validate_indonesian_language_pack() -> Tuple[bool, str]:
    """
    Validate that the Indonesian language pack is available for Tesseract.
    
    Returns:
        Tuple[bool, str]: (is_available, error_message)
    """
    installed_languages, error = get_tesseract_languages()
    if error:
        return (False, error)
    
    if "ind" in installed_languages:
        return (True, "")
    else:
        return (False, "Indonesian language pack 'ind' is not installed. Please install it with: tesseract-ocr-ind")


@st.cache_resource(show_spinner=False)
def get_supported_languages() -> Dict[str, Dict[str, str]]:
    """
    Get a dictionary of supported languages with their codes and names.
    
    Returns:
        Dictionary mapping language codes to language information
    """
    return {
        "eng": {"name": "English", "native_name": "English"},
        "ind": {"name": "Indonesian", "native_name": "Bahasa Indonesia"},
        "fra": {"name": "French", "native_name": "Français"},
        "deu": {"name": "German", "native_name": "Deutsch"},
        "spa": {"name": "Spanish", "native_name": "Español"},
        "ita": {"name": "Italian", "native_name": "Italiano"},
        "por": {"name": "Portuguese", "native_name": "Português"},
        "nld": {"name": "Dutch", "native_name": "Nederlands"},
        "rus": {"name": "Russian", "native_name": "Русский"},
        "jpn": {"name": "Japanese", "native_name": "日本語"},
        "chi_sim": {"name": "Chinese (Simplified)", "native_name": "简体中文"},
        "chi_tra": {"name": "Chinese (Traditional)", "native_name": "繁體中文"},
        "kor": {"name": "Korean", "native_name": "한국어"},
        "ara": {"name": "Arabic", "native_name": "العربية"},
        "hin": {"name": "Hindi", "native_name": "हिन्दी"},
        "tha": {"name": "Thai", "native_name": "ไทย"},
        "vie": {"name": "Vietnamese", "native_name": "Tiếng Việt"},
    }


@st.cache_resource(show_spinner=False)
def check_language_pack_availability(language_code: str) -> Tuple[bool, str]:
    """
    Check if a specific language pack is available.
    
    Args:
        language_code: Language code to check
        
    Returns:
        Tuple of (is_available, error_message)
    """
    installed_languages, error = get_tesseract_languages()
    if error:
        return (False, error)
    
    if language_code in installed_languages:
        return (True, "")
    else:
        supported_languages = get_supported_languages()
        language_name = supported_languages.get(language_code, {}).get("name", language_code)
        return (False, f"Language pack '{language_name}' ({language_code}) is not installed")


@st.cache_resource(show_spinner=False)
def get_language_pack_status() -> Dict[str, Dict[str, Any]]:
    """
    Get the status of all language packs.
    
    Returns:
        Dictionary with language pack status information
    """
    installed_languages, error = get_tesseract_languages()
    if error:
        return {"error": error}
    
    supported_languages = get_supported_languages()
    language_status = {}
    
    for code, info in supported_languages.items():
        is_installed = code in installed_languages
        language_status[code] = {
            "name": info["name"],
            "native_name": info["native_name"],
            "is_installed": is_installed,
            "is_recommended": code in ["eng", "ind"]  # English and Indonesian are recommended
        }
    
    return language_status


@st.cache_resource(show_spinner=False)
def validate_language_configuration(language_codes: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate a list of language codes.
    
    Args:
        language_codes: List of language codes to validate
        
    Returns:
        Tuple of (all_valid, error_messages)
    """
    if not language_codes:
        return (False, ["No language codes provided"])
    
    installed_languages, error = get_tesseract_languages()
    if error:
        return (False, [error])
    
    error_messages = []
    supported_languages = get_supported_languages()
    
    for code in language_codes:
        if code not in installed_languages:
            language_name = supported_languages.get(code, {}).get("name", code)
            error_messages.append(f"Language pack '{language_name}' ({code}) is not installed")
    
    return (len(error_messages) == 0, error_messages)


def get_language_pack_installation_instructions() -> Dict[str, str]:
    """
    Get installation instructions for language packs by platform.
    
    Returns:
        Dictionary with installation instructions by platform
    """
    return {
        "Windows": (
            "1. Download the language data from "
            "https://github.com/tesseract-ocr/tessdata\n"
            "2. Copy the .traineddata files to the tessdata directory "
            "(usually C:\\Program Files\\Tesseract-OCR\\tessdata)\n"
            "3. Ensure the TESSDATA_PREFIX environment variable is set "
            "to the tessdata directory"
        ),
        "Linux (Ubuntu/Debian)": (
            "1. Run: sudo apt-get install tesseract-ocr-ind\n"
            "2. For other languages: sudo apt-get install tesseract-ocr-[lang]\n"
            "3. Example for French: sudo apt-get install tesseract-ocr-fra"
        ),
        "Linux (CentOS/RHEL/Fedora)": (
            "1. Run: sudo yum install tesseract-langpack-ind\n"
            "2. For other languages: sudo yum install tesseract-langpack-[lang]"
        ),
        "macOS": (
            "1. Run: brew install tesseract-lang\n"
            "2. This installs all available language packs"
        )
    }


def get_optimal_language_config(detected_text: str = "") -> Tuple[str, float]:
    """
    Determine the optimal language configuration based on detected text.
    
    Args:
        detected_text: Sample text for language detection
        
    Returns:
        Tuple of (recommended_language_code, confidence_score)
    """
    # Default to Indonesian for KTP processing
    default_language = "ind"
    
    if not detected_text:
        return (default_language, 0.5)
    
    # Simple heuristic based on character patterns
    # In a real implementation, this would use more sophisticated language detection
    indonesian_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-,./")
    text_chars = set(detected_text)
    
    # Calculate similarity to Indonesian character set
    common_chars = len(indonesian_chars.intersection(text_chars))
    total_chars = len(text_chars.intersection(indonesian_chars))
    
    if total_chars > 0:
        confidence = common_chars / total_chars
        if confidence > 0.8:
            return (default_language, confidence)
    
    # Fallback to English if Indonesian confidence is low
    return ("eng", 0.3)


# ============================================================================
# KTP DATA EXTRACTION FUNCTIONS
# ============================================================================

@st.cache_data(show_spinner=False)
def extract_ktp_data(image: Image.Image, config: str = "--oem 3 --psm 6") -> Tuple[Dict[str, Any], str]:
    """
    Extract structured KTP data from an image using Tesseract OCR with Indonesian language support.
    
    Args:
        image: PIL Image object
        config: Tesseract configuration string
        
    Returns:
        Tuple[Dict[str, Any], str]: (ktp_data, error_message)
    """
    # First validate Indonesian language pack
    is_valid, error = validate_indonesian_language_pack()
    if not is_valid:
        return (None, error)
    
    # Extract text with confidence
    extraction_data, error = extract_text_with_confidence(image, "ind", config)
    if error:
        return (None, error)
    
    # Process the extracted text to identify KTP fields
    text = extraction_data['text']
    words = extraction_data['words']
    confidences = extraction_data['confidences']
    boxes = extraction_data['boxes']
    
    # Initialize KTP data structure
    ktp_data = _initialize_ktp_data_structure()
    
    # Enhanced pattern matching for KTP fields
    import re
    
    # Split text into lines and clean up
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Extract various KTP fields
    _extract_nik(ktp_data, lines, words, confidences)
    _extract_name(ktp_data, lines, words, confidences)
    _extract_birth_info(ktp_data, lines, words, confidences)
    _extract_gender(ktp_data, lines, words, confidences)
    _extract_address(ktp_data, lines, words, confidences)
    _extract_rt_rw(ktp_data, lines, words, confidences)
    _extract_kelurahan(ktp_data, lines, words, confidences)
    _extract_kecamatan(ktp_data, lines, words, confidences)
    _extract_religion(ktp_data, lines, words, confidences)
    _extract_marital_status(ktp_data, lines, words, confidences)
    _extract_occupation(ktp_data, lines, words, confidences)
    _extract_validity_period(ktp_data, lines, words, confidences)
    
    # Calculate overall confidence
    if ktp_data['extraction_confidence']:
        overall_confidence = sum(ktp_data['extraction_confidence'].values()) / len(ktp_data['extraction_confidence'])
        ktp_data['overall_confidence'] = overall_confidence
    else:
        ktp_data['overall_confidence'] = 0.0
    
    return (ktp_data, "")


def _initialize_ktp_data_structure() -> Dict[str, Any]:
    """Initialize the KTP data structure with default values."""
    return {
        'id': str(uuid.uuid4()),
        'nik': None,
        'name': None,
        'place_of_birth': None,
        'date_of_birth': None,
        'gender': None,
        'address': None,
        'religion': None,
        'marital_status': None,
        'occupation': None,
        'validity_period': None,
        'rt_rw': None,
        'kelurahan': None,
        'kecamatan': None,
        'extraction_confidence': {},
        'extraction_method': 'tesseract',
        'timestamp': datetime.now().isoformat()
    }


def _extract_nik(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract NIK (16-digit ID number) from KTP text."""
    import re
    
    # Pattern: 16 consecutive digits
    nik_pattern = r'\b(\d{16})\b'
    for i, line in enumerate(lines):
        # Direct NIK pattern
        nik_match = re.search(nik_pattern, line)
        if nik_match:
            ktp_data['nik'] = nik_match.group(1)
            # Find corresponding confidence
            if ktp_data['nik'] in words:
                idx = words.index(ktp_data['nik'])
                ktp_data['extraction_confidence']['nik'] = confidences[idx]
            break
        
        # Look for NIK label
        if 'NIK' in line and i + 1 < len(lines):
            potential_nik = re.search(nik_pattern, lines[i + 1])
            if potential_nik:
                ktp_data['nik'] = potential_nik.group(1)
                # Find corresponding confidence
                if ktp_data['nik'] in words:
                    idx = words.index(ktp_data['nik'])
                    ktp_data['extraction_confidence']['nik'] = confidences[idx]
                break


def _extract_name(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract name from KTP text."""
    import re
    
    for i, line in enumerate(lines):
        if 'Nama' in line:
            # Try to extract name from the same line
            name_match = re.search(r'Nama\s*[:\-]?\s*(.+)', line)
            if name_match:
                name = name_match.group(1).strip()
                if name:
                    ktp_data['name'] = name
                    name_confidence = _calculate_word_confidence(name, words, confidences)
                    ktp_data['extraction_confidence']['name'] = name_confidence
            # If not found in same line, check next line
            elif i + 1 < len(lines) and not any(keyword in lines[i+1] for keyword in ['Tempat', 'Alamat', 'RT/RW']):
                ktp_data['name'] = lines[i + 1].strip()
                name_confidence = _calculate_word_confidence(ktp_data['name'], words, confidences)
                ktp_data['extraction_confidence']['name'] = name_confidence
            break


def _extract_birth_info(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract place and date of birth from KTP text."""
    import re
    
    for line in lines:
        birth_match = re.search(r'Tempat[/]?Tgl\s*Lahir\s*[:\-]?\s*([^,]+),?\s*(\d{2}[-/]\d{2}[-/]\d{4})?', line)
        if birth_match:
            ktp_data['place_of_birth'] = birth_match.group(1).strip()
            if birth_match.group(2):
                ktp_data['date_of_birth'] = birth_match.group(2).strip()
            
            # Calculate confidence
            if ktp_data['place_of_birth']:
                pob_confidence = _calculate_word_confidence(ktp_data['place_of_birth'], words, confidences)
                ktp_data['extraction_confidence']['place_of_birth'] = pob_confidence
            
            if ktp_data['date_of_birth']:
                dob_confidence = _calculate_word_confidence(ktp_data['date_of_birth'], words, confidences)
                ktp_data['extraction_confidence']['date_of_birth'] = dob_confidence
            break


def _extract_gender(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract gender from KTP text."""
    gender_keywords = ['Laki-laki', 'Perempuan', 'LAKI-LAKI', 'PEREMPUAN']
    for i, line in enumerate(lines):
        for keyword in gender_keywords:
            if keyword in line:
                # Normalize gender value
                if keyword.upper() in ['LAKI-LAKI', 'LAKI-LAKI']:
                    ktp_data['gender'] = 'Laki-laki'
                else:
                    ktp_data['gender'] = 'Perempuan'
                
                # Calculate confidence
                gender_confidence = _calculate_word_confidence(keyword, words, confidences)
                ktp_data['extraction_confidence']['gender'] = gender_confidence
                break
        if ktp_data['gender']:
            break


def _extract_address(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract address from KTP text."""
    import re
    
    address_found = False
    for i, line in enumerate(lines):
        if 'Alamat' in line and not address_found:
            # Try to extract address from the same line
            address_match = re.search(r'Alamat\s*[:\-]?\s*(.+)', line)
            if address_match:
                address = address_match.group(1).strip()
                if address:
                    ktp_data['address'] = address
                    address_found = True
            
            # If not found in same line, collect next lines until we hit another field
            if not address_found and i + 1 < len(lines):
                address_lines = []
                j = i + 1
                # Collect next few lines as address until we hit another field
                while j < len(lines) and lines[j].strip() and not any(
                    keyword in lines[j] for keyword in ['RT/RW', 'Kelurahan', 'Kecamatan', 'Agama', 'Status']
                ):
                    address_lines.append(lines[j].strip())
                    j += 1
                
                if address_lines:
                    ktp_data['address'] = ' '.join(address_lines)
                    address_found = True
            
            if address_found:
                # Calculate confidence
                address_confidence = _calculate_word_confidence(ktp_data['address'], words, confidences)
                ktp_data['extraction_confidence']['address'] = address_confidence
            break


def _extract_rt_rw(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract RT/RW from KTP text."""
    import re
    
    for line in lines:
        rt_rw_match = re.search(r'RT[/]?RW\s*[:\-]?\s*(\d+)[/\s]*(\d+)', line)
        if rt_rw_match:
            ktp_data['rt_rw'] = f"{rt_rw_match.group(1)}/{rt_rw_match.group(2)}"
            rt_rw_confidence = _calculate_word_confidence(ktp_data['rt_rw'], words, confidences)
            ktp_data['extraction_confidence']['rt_rw'] = rt_rw_confidence
            break


def _extract_kelurahan(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract Kelurahan/Desa from KTP text."""
    import re
    
    for line in lines:
        kelurahan_match = re.search(r'Kelurahan\s*[:\-]?\s*(.+)', line)
        if kelurahan_match:
            ktp_data['kelurahan'] = kelurahan_match.group(1).strip()
            kelurahan_confidence = _calculate_word_confidence(ktp_data['kelurahan'], words, confidences)
            ktp_data['extraction_confidence']['kelurahan'] = kelurahan_confidence
            break


def _extract_kecamatan(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract Kecamatan from KTP text."""
    import re
    
    for line in lines:
        kecamatan_match = re.search(r'Kecamatan\s*[:\-]?\s*(.+)', line)
        if kecamatan_match:
            ktp_data['kecamatan'] = kecamatan_match.group(1).strip()
            kecamatan_confidence = _calculate_word_confidence(ktp_data['kecamatan'], words, confidences)
            ktp_data['extraction_confidence']['kecamatan'] = kecamatan_confidence
            break


def _extract_religion(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract religion from KTP text."""
    import re
    
    for line in lines:
        if 'Agama' in line:
            religion_match = re.search(r'Agama\s*[:\-]?\s*(.+)', line)
            if religion_match:
                religion = religion_match.group(1).strip()
                # Normalize religion value
                religion = _normalize_religion(religion)
                ktp_data['religion'] = religion
                
                # Calculate confidence
                religion_confidence = _calculate_word_confidence(ktp_data['religion'], words, confidences)
                ktp_data['extraction_confidence']['religion'] = religion_confidence
            break


def _normalize_religion(religion: str) -> str:
    """Normalize religion value to standard format."""
    religion_lower = religion.lower()
    if religion_lower in ['islam', 'islam ']:
        return 'Islam'
    elif religion_lower in ['kristen', 'kristen ']:
        return 'Kristen'
    elif religion_lower in ['katolik', 'katolik ']:
        return 'Katolik'
    elif religion_lower in ['hindu', 'hindu ']:
        return 'Hindu'
    elif religion_lower in ['buddha', 'buddha ']:
        return 'Buddha'
    elif religion_lower in ['konghucu', 'konghucu ']:
        return 'Konghucu'
    else:
        return religion


def _extract_marital_status(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract marital status from KTP text."""
    import re
    
    for line in lines:
        if 'Status' in line or 'Kawin' in line:
            status_match = re.search(r'Status\s*Perkawinan\s*[:\-]?\s*(.+)', line)
            if not status_match:
                status_match = re.search(r'Kawin\s*[:\-]?\s*(.+)', line)
            
            if status_match:
                status = status_match.group(1).strip()
                # Normalize marital status value
                status = _normalize_marital_status(status)
                ktp_data['marital_status'] = status
                
                # Calculate confidence
                marital_confidence = _calculate_word_confidence(ktp_data['marital_status'], words, confidences)
                ktp_data['extraction_confidence']['marital_status'] = marital_confidence
            break


def _normalize_marital_status(status: str) -> str:
    """Normalize marital status value to standard format."""
    status_lower = status.lower()
    if status_lower in ['belum kawin', 'belum']:
        return 'Belum Kawin'
    elif status_lower in ['kawin', 'kawin ']:
        return 'Kawin'
    elif status_lower in ['cerai hidup', 'cerai hidup']:
        return 'Cerai Hidup'
    elif status_lower in ['cerai mati', 'cerai mati']:
        return 'Cerai Mati'
    else:
        return status


def _extract_occupation(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract occupation from KTP text."""
    import re
    
    for line in lines:
        if 'Pekerjaan' in line:
            occupation_match = re.search(r'Pekerjaan\s*[:\-]?\s*(.+)', line)
            if occupation_match:
                ktp_data['occupation'] = occupation_match.group(1).strip()
                occupation_confidence = _calculate_word_confidence(ktp_data['occupation'], words, confidences)
                ktp_data['extraction_confidence']['occupation'] = occupation_confidence
            break


def _extract_validity_period(ktp_data: Dict[str, Any], lines: List[str], words: List[str], confidences: List[float]) -> None:
    """Extract validity period from KTP text."""
    import re
    
    for line in lines:
        if 'Berlaku' in line or 'Hingga' in line:
            validity_match = re.search(r'Berlaku\s*Hingga\s*[:\-]?\s*(\d{2}[-/]\d{2}[-/]\d{4})', line)
            if validity_match:
                ktp_data['validity_period'] = validity_match.group(1).strip()
                validity_confidence = _calculate_word_confidence(ktp_data['validity_period'], words, confidences)
                ktp_data['extraction_confidence']['validity_period'] = validity_confidence
            break


def _calculate_word_confidence(text: str, words: List[str], confidences: List[float]) -> float:
    """
    Calculate average confidence for a text based on its constituent words.
    
    Args:
        text: Text to calculate confidence for
        words: List of words extracted by OCR
        confidences: List of confidence scores for each word
        
    Returns:
        Average confidence score (0.0 to 1.0)
    """
    if not text or not words:
        return 0.0
    
    # Split text into words
    text_words = text.split()
    if not text_words:
        return 0.0
    
    # Find confidence scores for each word
    word_confidences = []
    for word in text_words:
        # Clean word for matching
        clean_word = word.strip('.,;:()[]{}"\'')
        if not clean_word:
            continue
            
        # Find the word in the OCR results
        found_confidence = None
        for i, ocr_word in enumerate(words):
            if clean_word.lower() == ocr_word.lower():
                found_confidence = confidences[i]
                break
        
        if found_confidence is not None:
            word_confidences.append(found_confidence)
    
    # Return average confidence
    if word_confidences:
        return sum(word_confidences) / len(word_confidences)
    else:
        # Default confidence if no words matched
        return 0.5


# ============================================================================
# INITIALIZATION AND VALIDATION FUNCTIONS
# ============================================================================

def initialize_tesseract() -> Tuple[bool, str]:
    """
    Initialize Tesseract with Indonesian language support.
    
    Returns:
        Tuple[bool, str]: (success, error_message)
    """
    # Set Tesseract binary path
    set_tesseract_binary()
    
    # Check Tesseract version
    version, error = get_tesseract_version()
    if error:
        return (False, error)
    
    # Validate Indonesian language pack
    is_valid, error = validate_indonesian_language_pack()
    if not is_valid:
        return (False, error)
    
    return (True, f"Tesseract {version} initialized with Indonesian language support")


def validate_ktp_language_setup() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate the complete language setup for KTP processing.
    
    Returns:
        Tuple of (is_valid, message, setup_details)
    """
    setup_details = {}
    
    # Check Tesseract installation
    if not find_tesseract_binary():
        return (False, "Tesseract is not installed or not in PATH", setup_details)
    
    # Check Tesseract version
    version, error = get_tesseract_version()
    if error:
        return (False, f"Error checking Tesseract version: {error}", setup_details)
    
    setup_details["tesseract_version"] = str(version)
    
    # Check Indonesian language pack
    is_indonesian_available, error = validate_indonesian_language_pack()
    if not is_indonesian_available:
        return (False, f"Indonesian language pack not available: {error}", setup_details)
    
    setup_details["indonesian_pack_available"] = True
    
    # Check English language pack (fallback)
    is_english_available, _ = check_language_pack_availability("eng")
    setup_details["english_pack_available"] = is_english_available
    
    # Get optimal configuration
    setup_details["recommended_config"] = configure_tesseract_for_ktp()
    
    # Get language pack status
    setup_details["language_status"] = get_language_pack_status()
    
    return (True, f"Tesseract {version} with Indonesian language support is ready for KTP processing", setup_details)


def get_language_pack_recommendations() -> Dict[str, Any]:
    """
    Get recommendations for language pack installation.
    
    Returns:
        Dictionary with language pack recommendations
    """
    installed_languages, error = get_tesseract_languages()
    if error:
        return {"error": error}
    
    recommendations = {
        "required": [],
        "optional": [],
        "installation_instructions": get_language_pack_installation_instructions()
    }
    
    # Check required languages
    if "ind" not in installed_languages:
        recommendations["required"].append({
            "code": "ind",
            "name": "Indonesian",
            "reason": "Required for KTP document processing"
        })
    
    if "eng" not in installed_languages:
        recommendations["required"].append({
            "code": "eng",
            "name": "English",
            "reason": "Fallback language for mixed text"
        })
    
    # Check optional languages
    optional_languages = ["fra", "deu", "spa", "nld"]
    for lang in optional_languages:
        if lang not in installed_languages:
            recommendations["optional"].append({
                "code": lang,
                "name": get_supported_languages().get(lang, {}).get("name", lang),
                "reason": "Optional for multilingual documents"
            })
    
    return recommendations


# ============================================================================
# PERFORMANCE OPTIMIZATION FUNCTIONS
# ============================================================================

def calculate_image_hash_for_ocr(image: Image.Image) -> str:
    """
    Calculate a hash of the image for OCR caching purposes.
    
    Args:
        image: PIL Image object
        
    Returns:
        String hash of the image
    """
    # Convert to grayscale if needed
    if image.mode != 'L':
        image = image.convert('L')
    
    # Resize to a small standard size for hashing
    image = image.resize((8, 8))
    
    # Calculate average pixel value
    pixels = list(image.getdata())
    avg = sum(pixels) / len(pixels)
    
    # Generate hash
    hash_str = ""
    for pixel in pixels:
        hash_str += "1" if pixel > avg else "0"
    
    return hash_str


def timed_ocr_cache(maxsize: int = 64, ttl: int = 1800):
    """
    A timed cache decorator specifically for OCR operations.
    
    Args:
        maxsize: Maximum number of items to cache
        ttl: Time to live in seconds
    """
    def decorator(func):
        cache = {}
        timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from image hash and parameters
            if len(args) > 0 and hasattr(args[0], 'getdata'):  # Check if first arg is an image
                image_hash = calculate_image_hash_for_ocr(args[0])
                key = f"{image_hash}_{str(args[1:])}_{str(sorted(kwargs.items()))}"
            else:
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


@timed_ocr_cache(maxsize=32, ttl=1800)  # Cache for 30 minutes
def optimized_extract_text_with_confidence(image: Image.Image,
                                         language: str = "ind",
                                         config: str = "--oem 3 --psm 6") -> Tuple[Dict[str, Any], str]:
    """
    Optimized text extraction with confidence scoring using Tesseract OCR with caching.
    
    Args:
        image: PIL Image object
        language: Language code for OCR (default: Indonesian)
        config: Tesseract configuration string
        
    Returns:
        Tuple[Dict[str, Any], str]: (extraction_data, error_message)
    """
    try:
        # Get detailed OCR data including confidence scores
        data = pytesseract.image_to_data(
            image=image,
            lang=language,
            config=config,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract words with confidence scores
        words = []
        confidences = []
        boxes = []
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:  # Filter out empty entries
                words.append(data['text'][i])
                confidences.append(int(data['conf'][i]) / 100.0)  # Convert to 0-1 scale
                boxes.append({
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i]
                })
        
        # Calculate overall confidence
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Get full text
        full_text = pytesseract.image_to_string(
            image=image,
            lang=language,
            config=config
        )
        
        extraction_data = {
            'text': full_text,
            'words': words,
            'confidences': confidences,
            'boxes': boxes,
            'overall_confidence': overall_confidence,
            'language': language,
            'config': config,
            'extraction_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat()
        }
        
        return (extraction_data, "")
        
    except pytesseract.TesseractError as e:
        return (None, f"TesseractError: {str(e)}")
    except pytesseract.TesseractNotFoundError:
        return (None, "TesseractNotFoundError: Tesseract is not installed. Please install Tesseract.")
    except RuntimeError:
        return (None, "RuntimeError: Tesseract timed out during text extraction.")
    except Exception as e:
        return (None, f"Unexpected error: {str(e)}")


@timed_ocr_cache(maxsize=16, ttl=1800)  # Cache for 30 minutes
def optimized_extract_ktp_data(image: Image.Image, config: str = "--oem 3 --psm 6") -> Tuple[Dict[str, Any], str]:
    """
    Optimized KTP data extraction with caching.
    
    Args:
        image: PIL Image object
        config: Tesseract configuration string
        
    Returns:
        Tuple[Dict[str, Any], str]: (ktp_data, error_message)
    """
    # First validate Indonesian language pack
    is_valid, error = validate_indonesian_language_pack()
    if not is_valid:
        return (None, error)
    
    # Extract text with confidence using optimized function
    extraction_data, error = optimized_extract_text_with_confidence(image, "ind", config)
    if error:
        return (None, error)
    
    # Process the extracted text to identify KTP fields
    text = extraction_data['text']
    words = extraction_data['words']
    confidences = extraction_data['confidences']
    boxes = extraction_data['boxes']
    
    # Initialize KTP data structure
    ktp_data = _initialize_ktp_data_structure()
    
    # Enhanced pattern matching for KTP fields
    import re
    
    # Split text into lines and clean up
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Extract various KTP fields
    _extract_nik(ktp_data, lines, words, confidences)
    _extract_name(ktp_data, lines, words, confidences)
    _extract_birth_info(ktp_data, lines, words, confidences)
    _extract_gender(ktp_data, lines, words, confidences)
    _extract_address(ktp_data, lines, words, confidences)
    _extract_rt_rw(ktp_data, lines, words, confidences)
    _extract_kelurahan(ktp_data, lines, words, confidences)
    _extract_kecamatan(ktp_data, lines, words, confidences)
    _extract_religion(ktp_data, lines, words, confidences)
    _extract_marital_status(ktp_data, lines, words, confidences)
    _extract_occupation(ktp_data, lines, words, confidences)
    _extract_validity_period(ktp_data, lines, words, confidences)
    
    # Calculate overall confidence
    if ktp_data['extraction_confidence']:
        overall_confidence = sum(ktp_data['extraction_confidence'].values()) / len(ktp_data['extraction_confidence'])
        ktp_data['overall_confidence'] = overall_confidence
    else:
        ktp_data['overall_confidence'] = 0.0
    
    return (ktp_data, "")


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Preprocess image for optimal OCR performance.
    
    Args:
        image: PIL Image object
        
    Returns:
        Preprocessed PIL Image
    """
    # Convert to grayscale if needed
    if image.mode != 'L':
        image = image.convert('L')
    
    # Resize if too large (OCR works better with moderate-sized images)
    width, height = image.size
    if width > 3000 or height > 3000:
        ratio = min(3000/width, 3000/height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image


def batch_extract_ktp_data(images: List[Image.Image],
                          config: str = "--oem 3 --psm 6",
                          max_workers: int = 2) -> List[Tuple[Dict[str, Any], str]]:
    """
    Extract KTP data from multiple images in parallel.
    
    Args:
        images: List of PIL Image objects
        config: Tesseract configuration string
        max_workers: Maximum number of worker threads
        
    Returns:
        List of tuples containing (ktp_data, error_message) for each image
    """
    from concurrent.futures import ThreadPoolExecutor
    import functools
    
    # Create a partial function with the config parameter
    extract_func = functools.partial(optimized_extract_ktp_data, config=config)
    
    # Process images in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(extract_func, images))
    
    return results


def measure_ocr_performance(func: callable) -> callable:
    """
    Decorator to measure OCR processing time.
    
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
        print(f"[OCR PERFORMANCE] {func.__name__} took {processing_time:.3f} seconds")
        
        return result
    return wrapper
