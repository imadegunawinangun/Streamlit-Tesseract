import streamlit as st
import traceback
from typing import Optional, Tuple, Dict, Any
import time
import os
from datetime import datetime

import helpers.constants as constants
import helpers.opencv as opencv
import helpers.pdfimage as pdfimage
import helpers.tesseract as tesseract
import helpers.storage as storage
import helpers.document_gen as document_gen

language_options_list = list(constants.languages_sorted.values())


def initialize_session_state():
    """Initialize all session state variables and their default values."""
    init_sidebar_values()
    init_session_state_variables()


def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="KTP OCR & Document Generation",
        page_icon="🆔",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def load_custom_css():
    """Load custom CSS styling for the application."""
    try:
        with open(file="helpers/style.css", mode='r', encoding='utf-8') as css:
            st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Custom CSS file not found. Using default styling.")


def display_ktp_data_editing(ktp_data, ktp_confidence):
    """
    Display KTP data editing interface with confidence indicators.
    
    Args:
        ktp_data: KTPData object
        ktp_confidence: ExtractionConfidence object
    """
    ktp_dict = ktp_data.to_dict()
    
    # Helper function to get confidence score and color
    def get_confidence_indicator(field_name):
        if ktp_confidence:
            conf_score = ktp_confidence.get_field_confidence(field_name)
            if conf_score is not None:
                if conf_score < 0.6:
                    return "🔴", f"{conf_score:.1%}", "Low confidence - Please verify"
                elif conf_score < 0.8:
                    return "🟡", f"{conf_score:.1%}", "Medium confidence - Review recommended"
                else:
                    return "🟢", f"{conf_score:.1%}", "High confidence"
        return "⚪", "N/A", "No confidence data"
    
    # Create editable fields for KTP data with confidence indicators
    col1, col2 = st.columns(2)
    
    with col1:
        # NIK field
        nik_indicator, nik_conf, nik_tooltip = get_confidence_indicator('nik')
        nik_value = st.text_input(
            f"NIK (Nomor Induk Kependudukan) {nik_indicator}",
            value=ktp_dict.get('nik', ''),
            key="edit_nik",
            help=f"16-digit Indonesian ID number | Confidence: {nik_conf} | {nik_tooltip}"
        )
        
        # Name field
        name_indicator, name_conf, name_tooltip = get_confidence_indicator('name')
        name_value = st.text_input(
            f"Name {name_indicator}",
            value=ktp_dict.get('name', ''),
            key="edit_name",
            help=f"Full name as printed on KTP | Confidence: {name_conf} | {name_tooltip}"
        )
        
        # Place of birth field
        pob_indicator, pob_conf, pob_tooltip = get_confidence_indicator('place_of_birth')
        pob_value = st.text_input(
            f"Place of Birth {pob_indicator}",
            value=ktp_dict.get('place_of_birth', ''),
            key="edit_pob",
            help=f"City of birth | Confidence: {pob_conf} | {pob_tooltip}"
        )
        
        # Date of birth field
        dob_indicator, dob_conf, dob_tooltip = get_confidence_indicator('date_of_birth')
        dob_value = st.text_input(
            f"Date of Birth {dob_indicator}",
            value=ktp_dict.get('date_of_birth', ''),
            key="edit_dob",
            help=f"Format: DD-MM-YYYY | Confidence: {dob_conf} | {dob_tooltip}"
        )
        
        # Gender field
        gender_indicator, gender_conf, gender_tooltip = get_confidence_indicator('gender')
        gender_options = ["", "Laki-laki", "Perempuan"]
        gender_index = 0
        if ktp_dict.get('gender') == "Laki-laki":
            gender_index = 1
        elif ktp_dict.get('gender') == "Perempuan":
            gender_index = 2
        
        gender_value = st.selectbox(
            f"Gender {gender_indicator}",
            options=gender_options,
            index=gender_index,
            key="edit_gender",
            help=f"Gender as printed on KTP | Confidence: {gender_conf} | {gender_tooltip}"
        )
    
    with col2:
        # Address field
        address_indicator, address_conf, address_tooltip = get_confidence_indicator('address')
        address_value = st.text_area(
            f"Address {address_indicator}",
            value=ktp_dict.get('address', ''),
            key="edit_address",
            height=100,
            help=f"Complete address including street, RT/RW | Confidence: {address_conf} | {address_tooltip}"
        )
        
        # Religion field
        religion_indicator, religion_conf, religion_tooltip = get_confidence_indicator('religion')
        religion_options = [""] + constants.INDONESIAN_RELIGIONS
        religion_index = 0
        if ktp_dict.get('religion') in constants.INDONESIAN_RELIGIONS:
            religion_index = constants.INDONESIAN_RELIGIONS.index(ktp_dict.get('religion')) + 1
        
        religion_value = st.selectbox(
            f"Religion {religion_indicator}",
            options=religion_options,
            index=religion_index,
            key="edit_religion",
            help=f"Religion as printed on KTP | Confidence: {religion_conf} | {religion_tooltip}"
        )
        
        # Marital status field
        marital_indicator, marital_conf, marital_tooltip = get_confidence_indicator('marital_status')
        marital_options = [""] + constants.INDONESIAN_MARITAL_STATUS
        marital_index = 0
        if ktp_dict.get('marital_status') in constants.INDONESIAN_MARITAL_STATUS:
            marital_index = constants.INDONESIAN_MARITAL_STATUS.index(ktp_dict.get('marital_status')) + 1
        
        marital_value = st.selectbox(
            f"Marital Status {marital_indicator}",
            options=marital_options,
            index=marital_index,
            key="edit_marital",
            help=f"Marital status as printed on KTP | Confidence: {marital_conf} | {marital_tooltip}"
        )
        
        # Occupation field
        occupation_indicator, occupation_conf, occupation_tooltip = get_confidence_indicator('occupation')
        occupation_value = st.text_input(
            f"Occupation {occupation_indicator}",
            value=ktp_dict.get('occupation', ''),
            key="edit_occupation",
            help=f"Occupation as printed on KTP | Confidence: {occupation_conf} | {occupation_tooltip}"
        )
        
        # Validity period field
        validity_indicator, validity_conf, validity_tooltip = get_confidence_indicator('validity_period')
        validity_value = st.text_input(
            f"Validity Period {validity_indicator}",
            value=ktp_dict.get('validity_period', ''),
            key="edit_validity",
            help=f"Format: DD-MM-YYYY | Confidence: {validity_conf} | {validity_tooltip}"
        )
    
    # Update KTP data if corrections were made
    corrections_made = (
        nik_value != ktp_dict.get('nik', '') or
        name_value != ktp_dict.get('name', '') or
        pob_value != ktp_dict.get('place_of_birth', '') or
        dob_value != ktp_dict.get('date_of_birth', '') or
        gender_value != ktp_dict.get('gender', '') or
        address_value != ktp_dict.get('address', '') or
        religion_value != ktp_dict.get('religion', '') or
        marital_value != ktp_dict.get('marital_status', '') or
        occupation_value != ktp_dict.get('occupation', '') or
        validity_value != ktp_dict.get('validity_period', '')
    )
    
    if corrections_made:
        # Update KTP data with corrections
        st.session_state.ktp_data.nik = nik_value
        st.session_state.ktp_data.name = name_value
        st.session_state.ktp_data.place_of_birth = pob_value
        st.session_state.ktp_data.date_of_birth = dob_value
        st.session_state.ktp_data.gender = gender_value
        st.session_state.ktp_data.address = address_value
        st.session_state.ktp_data.religion = religion_value
        st.session_state.ktp_data.marital_status = marital_value
        st.session_state.ktp_data.occupation = occupation_value
        st.session_state.ktp_data.validity_period = validity_value
        
        # Update timestamp
        from datetime import datetime
        st.session_state.ktp_data.updated_at = datetime.now().isoformat()
    
    return corrections_made


def init_tesseract():
    tess_version = None
    # set tesseract binary path
    tesseract.set_tesseract_binary()
    if not tesseract.find_tesseract_binary():
        st.error("Tesseract binary not found in PATH. Please install Tesseract.")
        st.stop()
    # check if tesseract is installed
    tess_version, error = tesseract.get_tesseract_version()
    if error:
        st.error(error)
        st.stop()
    elif not tess_version:
        st.error("Tesseract is not installed. Please install Tesseract.")
        st.stop()
    return tess_version


def show_error(message: str, exception: Optional[Exception] = None) -> None:
    """
    Display an error message with optional exception details.
    
    Args:
        message: Error message to display
        exception: Optional exception object for additional details
    """
    st.error(f"❌ {message}")
    if exception:
        with st.expander("Error Details"):
            st.code(str(exception))
            st.code(traceback.format_exc())


def show_warning(message: str) -> None:
    """
    Display a warning message.
    
    Args:
        message: Warning message to display
    """
    st.warning(f"⚠️ {message}")


def show_success(message: str) -> None:
    """
    Display a success message.
    
    Args:
        message: Success message to display
    """
    st.success(f"✅ {message}")


def show_info(message: str) -> None:
    """
    Display an informational message.
    
    Args:
        message: Information message to display
    """
    st.info(f"ℹ️ {message}")


def progress_with_time(operation_name: str, max_time: int = 60) -> None:
    """
    Display a progress bar with timeout for long operations.
    
    Args:
        operation_name: Name of the operation
        max_time: Maximum time in seconds
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        progress = min(elapsed / max_time, 1.0)
        
        progress_bar.progress(progress)
        status_text.text(f"{operation_name}... ({elapsed:.1f}s)")
        
        if elapsed >= max_time:
            break
            
        time.sleep(0.1)
    
    progress_bar.empty()
    status_text.empty()


def validate_file_upload(uploaded_file) -> Tuple[bool, str]:
    """
    Validate the uploaded file.
    
    Args:
        uploaded_file: Uploaded file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if uploaded_file is None:
        return (False, "No file uploaded")
    
    # Check file size (max 10MB)
    if uploaded_file.size > 10 * 1024 * 1024:
        return (False, "File size exceeds 10MB limit")
    
    # Check file type
    valid_extensions = ["png", "jpg", "jpeg", "bmp", "tif", "tiff", "pdf"]
    file_extension = uploaded_file.name.lower().split('.')[-1]
    
    if file_extension not in valid_extensions:
        return (False, f"Unsupported file type: {file_extension}. Supported types: {', '.join(valid_extensions)}")
    
    return (True, "")


def handle_error_with_recovery(error_message: str, recovery_suggestions: list) -> None:
    """
    Display an error message with recovery suggestions.
    
    Args:
        error_message: Error message to display
        recovery_suggestions: List of recovery suggestions
    """
    show_error(error_message)
    
    if recovery_suggestions:
        st.write("**Recovery Suggestions:**")
        for i, suggestion in enumerate(recovery_suggestions, 1):
            st.write(f"{i}. {suggestion}")


def validate_tesseract_setup() -> Tuple[bool, str]:
    """
    Validate Tesseract setup including Indonesian language pack.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if Tesseract is installed
    if not tesseract.find_tesseract_binary():
        return (False, "Tesseract is not installed or not in PATH. Please install Tesseract OCR.")
    
    # Check Tesseract version
    version, error = tesseract.get_tesseract_version()
    if error:
        return (False, f"Error checking Tesseract version: {error}")
    
    # Check Indonesian language pack
    is_indonesian_available, error = tesseract.validate_indonesian_language_pack()
    if not is_indonesian_available:
        return (False, f"Indonesian language pack not available: {error}")
    
    return (True, f"Tesseract {version} with Indonesian language pack is ready")


def check_system_resources() -> Dict[str, Any]:
    """
    Check system resources and return status.
    
    Returns:
        Dictionary with system resource information
    """
    import psutil
    
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Get memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Get disk usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
        "memory_available_gb": memory.available / (1024**3),
        "disk_free_gb": disk.free / (1024**3)
    }


def show_system_status() -> None:
    """
    Display system status in the sidebar.
    """
    with st.sidebar:
        st.markdown("---")
        st.header("System Status")
        
        # Check Tesseract setup
        is_valid, message = validate_tesseract_setup()
        if is_valid:
            st.success(message)
        else:
            st.error(message)
        
        # Check system resources
        try:
            resources = check_system_resources()
            
            # CPU indicator
            if resources["cpu_percent"] < 80:
                st.success(f"CPU: {resources['cpu_percent']:.1f}%")
            else:
                st.warning(f"CPU: {resources['cpu_percent']:.1f}% (High)")
            
            # Memory indicator
            if resources["memory_percent"] < 80:
                st.success(f"Memory: {resources['memory_percent']:.1f}%")
            else:
                st.warning(f"Memory: {resources['memory_percent']:.1f}% (High)")
            
            # Disk indicator
            if resources["disk_percent"] < 90:
                st.success(f"Disk: {resources['disk_percent']:.1f}%")
            else:
                st.warning(f"Disk: {resources['disk_percent']:.1f}% (Low Space)")
            
        except Exception as e:
            st.warning(f"Could not check system resources: {str(e)}")


def show_processing_status(operation: str, start_time: float, timeout: int = 60) -> bool:
    """
    Show processing status with timeout.
    
    Args:
        operation: Name of the operation
        start_time: Start time in seconds
        timeout: Timeout in seconds
        
    Returns:
        True if operation completed within timeout, False otherwise
    """
    elapsed = time.time() - start_time
    
    if elapsed > timeout:
        show_error(f"Operation '{operation}' timed out after {timeout} seconds",
                  [f"Try reducing image size or complexity",
                   "Check if system resources are available"])
        return False
    
    # Update progress
    progress = min(elapsed / timeout, 0.99)
    progress_bar = st.progress(progress)
    status_text = st.text(f"{operation}... ({elapsed:.1f}s / {timeout}s)")
    
    return True


def initialize_error_handling() -> None:
    """
    Initialize error handling infrastructure.
    """
    # Set up error handling for the app
    st.set_option('logger.level', 'ERROR')
    
    # Add custom exception handler
    def exception_handler(e: Exception) -> None:
        show_error(f"An unexpected error occurred: {str(e)}", e)
    
    # Register the exception handler
    if hasattr(st, 'exception_handler'):
        st.exception_handler = exception_handler


def init_sidebar_values():
    '''Initialize all sidebar values of buttons/sliders to default values.
    '''
    if "psm" not in st.session_state:
        st.session_state.psm = tesseract.psm[3]
    if "timeout" not in st.session_state:
        st.session_state.timeout = 20
    if "cGrayscale" not in st.session_state:
        st.session_state.cGrayscale = True
    if "cDenoising" not in st.session_state:
        st.session_state.cDenoising = False
    if "cDenoisingStrength" not in st.session_state:
        st.session_state.cDenoisingStrength = 10
    if "cThresholding" not in st.session_state:
        st.session_state.cThresholding = False
    if "cThresholdLevel" not in st.session_state:
        st.session_state.cThresholdLevel = 128
    if "cRotate90" not in st.session_state:
        st.session_state.cRotate90 = False
    if "angle90" not in st.session_state:
        st.session_state.angle90 = 0
    if "cRotateFree" not in st.session_state:
        st.session_state.cRotateFree = False
    if "angle" not in st.session_state:
        st.session_state.angle = 0


def reset_sidebar_values():
    '''Reset all sidebar values of buttons/sliders to default values.
    '''
    st.session_state.psm = tesseract.psm[3]
    st.session_state.timeout = 20
    st.session_state.cGrayscale = True
    st.session_state.cDenoising = False
    st.session_state.cDenoisingStrength = 10
    st.session_state.cThresholding = False
    st.session_state.cThresholdLevel = 128
    st.session_state.cRotate90 = False
    st.session_state.angle90 = 0
    st.session_state.cRotateFree = False
    st.session_state.angle = 0


def init_session_state_variables():
    '''Initialize all session state values.
    '''
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "raw_image" not in st.session_state:
        st.session_state.raw_image = None
    if "image" not in st.session_state:
        st.session_state.image = None
    if "preview_processed_image" not in st.session_state:
        st.session_state.preview_processed_image = False
    if "crop_image" not in st.session_state:
        st.session_state.crop_image = False
    if "text" not in st.session_state:
        st.session_state.text = None
    
    # KTP-specific session state variables
    if "ktp_mode" not in st.session_state:
        st.session_state.ktp_mode = False
    if "ktp_data" not in st.session_state:
        st.session_state.ktp_data = None
    if "ktp_confidence" not in st.session_state:
        st.session_state.ktp_confidence = None
    if "ktp_extracted" not in st.session_state:
        st.session_state.ktp_extracted = False
    if "ktp_corrections" not in st.session_state:
        st.session_state.ktp_corrections = {}


# streamlit config
st.set_page_config(
    page_title="KTP OCR & Document Generation",
    page_icon="🆔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize error handling
initialize_error_handling()

# init tesseract
tesseract_version = init_tesseract()
init_sidebar_values()
init_session_state_variables()

# apply custom css
with open(file="helpers/style.css", mode='r', encoding='utf-8') as css:
    st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

# App mode selection
app_mode = st.sidebar.selectbox(
    "Select Application Mode",
    ["General OCR", "KTP Extraction & Document Generation"],
    index=0
)

st.session_state.ktp_mode = (app_mode == "KTP Extraction & Document Generation")

if st.session_state.ktp_mode:
    st.title(f"KTP Data Extraction & Document Generation :id: :flag-id:")
    st.markdown("Extract structured data from Indonesian ID cards (KTP) and generate documents")
    
    # Add tabs for KTP workflow
    tab1, tab2, tab3 = st.tabs(["Extract New KTP", "View Stored KTP Data", "Document Generation"])
    
    with tab1:
        st.markdown("---")
else:
    st.title(f"Tesseract OCR :mag_right: {constants.flag_string}")
st.markdown("---")

# Show system status in sidebar
show_system_status()

with st.sidebar:
    st.success(f"Tesseract V **{tesseract_version}** installed")
    
    if st.session_state.ktp_mode:
        st.header("KTP Processing Settings")
        st.button('Reset KTP parameters to default', on_click=reset_sidebar_values)
        
        # KTP-specific preprocessing options
        st.write("KTP-optimized preprocessing options:")
        enable_clahe = st.checkbox("Contrast Enhancement (CLAHE)", value=True, key="ktp_clahe")
        enable_shadow_removal = st.checkbox("Shadow Removal", value=True, key="ktp_shadow")
        enable_sharpening = st.checkbox("Sharpening", value=True, key="ktp_sharpen")
        enable_auto_rotate = st.checkbox("Auto Rotate Document", value=True, key="ktp_rotate")
        enable_adaptive_threshold = st.checkbox("Adaptive Threshold", value=False, key="ktp_threshold")
        
        # KTP language validation
        is_indonesian_valid, indonesian_error = tesseract.validate_indonesian_language_pack()
        if is_indonesian_valid:
            st.success("✅ Indonesian language pack is installed")
        else:
            st.error(f"❌ {indonesian_error}")
            st.info("Install with: `sudo apt-get install tesseract-ocr-ind` (Linux) or download from tessdata repo (Windows)")
    else:
        st.header("Tesseract OCR Settings")
        st.button('Reset OCR parameters to default', on_click=reset_sidebar_values)
        # FIXME: OEM option does not work in tesseract 4.1.1
        # oem = st.selectbox(label="OCR Engine mode (not working)", options=constants.oem, index=3, disabled=True)
        psm = st.selectbox(label="Page segmentation mode", options=tesseract.psm, key="psm")
        timeout = st.slider(label="Tesseract OCR timeout [sec]", min_value=1, max_value=60, value=20, step=1, key="timeout")
        st.markdown("---")
        st.header("Image Preprocessing")
        st.write("Check the boxes below to apply preprocessing to the image.")
        cGrayscale = st.checkbox(label="Grayscale", value=True, key="cGrayscale")
        cDenoising = st.checkbox(label="Denoising", value=False, key="cDenoising")
        cDenoisingStrength = st.slider(label="Denoising Strength", min_value=1, max_value=40, value=10, step=1, key="cDenoisingStrength")
        cThresholding = st.checkbox(label="Thresholding", value=False, key="cThresholding")
        cThresholdLevel = st.slider(label="Threshold Level", min_value=0, max_value=255, value=128, step=1, key="cThresholdLevel")
        cRotate90 = st.checkbox(label="Rotate in 90° steps", value=False, key="cRotate90")
        angle90 = st.slider("Rotate rectangular [Degree]", min_value=0, max_value=270, value=0, step=90, key="angle90")
        cRotateFree = st.checkbox(label="Rotate in free degrees", value=False, key="cRotateFree")
        angle = st.slider("Rotate freely [Degree]", min_value=-180, max_value=180, value=0, step=1, key="angle")
    
    st.markdown(
        """---
# About
Streamlit app to extract text from images using Tesseract OCR
## GitHub
<https://github.com/Franky1/Streamlit-Tesseract>
""",
        unsafe_allow_html=True,
    )

# Initialize Tesseract configuration based on mode
if st.session_state.ktp_mode:
    # Use KTP-optimized configuration
    custom_oem_psm_config = tesseract.configure_tesseract_for_ktp()
    # Check Indonesian language pack
    is_indonesian_valid, indonesian_error = tesseract.validate_indonesian_language_pack()
    if not is_indonesian_valid:
        st.error(indonesian_error)
        st.stop()
else:
    # get index of selected oem parameter
    # FIXME: OEM option does not work in tesseract 4.1.1
    # oem_index = tesseract.oem.index(oem)
    oem_index = 3
    # get index of selected psm parameter
    psm_index = tesseract.psm.index(psm)
    # create custom oem and psm config string
    custom_oem_psm_config = tesseract.get_tesseract_config(oem_index=oem_index, psm_index=psm_index)

# check if installed languages are available
installed_languages, error = tesseract.get_tesseract_languages()
if error:
    st.error(error)
    st.stop()


if st.session_state.ktp_mode:
    if 'tab1' in locals():
        # KTP Processing Interface
        col_upload_1, col_upload_2 = st.columns(spec=2, gap="small")
    
    with col_upload_1:
        st.subheader("Upload KTP Image :arrow_up:")
        st.session_state.uploaded_file = st.file_uploader(
            "Upload KTP Image", type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"],
            help="Upload a clear image of an Indonesian ID card (KTP)"
        )
        
        if st.session_state.uploaded_file is None:
            st.session_state.raw_image = None
            st.session_state.image = None
            st.session_state.ktp_data = None
            st.session_state.ktp_confidence = None
            st.session_state.ktp_extracted = False
        elif st.session_state.uploaded_file is not None:
            # Validate uploaded file
            is_valid, error_message = validate_file_upload(st.session_state.uploaded_file)
            if not is_valid:
                handle_error_with_recovery(error_message, [
                    "Check if the file is a valid image",
                    "Ensure file size is under 10MB",
                    "Try uploading a different image"
                ])
                st.stop()
            
            try:
                start_time = time.time()
                with st.spinner("Loading KTP image..."):
                    # convert uploaded file to numpy array
                    st.session_state.raw_image = opencv.load_image(st.session_state.uploaded_file)
                    if not show_processing_status("Image Loading", start_time, timeout=10):
                        st.stop()
            except Exception as e:
                handle_error_with_recovery("Exception during Image Conversion", [
                    "Check if the file is a valid image format",
                    "Try uploading a different image",
                    "Ensure the image is not corrupted"
                ], e)
                st.stop()
            
            try:
                start_time = time.time()
                with st.spinner("Preprocessing KTP image..."):
                    # Apply optimized KTP-specific preprocessing
                    processed_image = opencv.optimized_preprocess_ktp_image(
                        img=st.session_state.raw_image,
                        enable_clahe=enable_clahe,
                        enable_shadow_removal=enable_shadow_removal,
                        enable_sharpening=enable_sharpening,
                        enable_auto_rotate=enable_auto_rotate,
                        enable_adaptive_threshold=enable_adaptive_threshold
                    )
                    st.session_state.image = processed_image
                    
                    if not show_processing_status("KTP Image Preprocessing", start_time, timeout=30):
                        st.stop()
            except Exception as e:
                handle_error_with_recovery("Error during KTP image preprocessing", [
                    "Try disabling some preprocessing options",
                    "Check if the image is too large or complex",
                    "Ensure the image format is supported"
                ], e)
                st.stop()
            
            st.session_state.preview_processed_image = st.toggle("Preview Preprocessed Image", value=True)
    
    with col_upload_2:
        st.subheader("KTP Processing Options :id:")
        
        if st.session_state.uploaded_file is not None and st.session_state.image is not None:
            st.markdown("---")
            st.subheader("Extract KTP Data :mag_right:")
            if st.button("Extract KTP Data", type="primary"):
                # Create a progress container
                progress_container = st.container()
                with progress_container:
                    # Create progress bar and status text
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Initialize progress
                    progress_bar.progress(0)
                    status_text.text("Initializing KTP data extraction...")
                
                start_time = time.time()
                try:
                    # Step 1: Image conversion
                    progress_bar.progress(10)
                    status_text.text("Converting image for OCR processing...")
                    pil_image = opencv.convert_to_pil(st.session_state.image)
                    
                    # Step 2: OCR preprocessing
                    progress_bar.progress(30)
                    status_text.text("Optimizing image for text recognition...")
                    time.sleep(0.5)  # Small delay for visual feedback
                    
                    # Step 3: Text extraction
                    progress_bar.progress(50)
                    status_text.text("Extracting text from KTP image...")
                    
                    # Extract KTP data with optimized confidence scoring
                    ktp_data, error = tesseract.optimized_extract_ktp_data(
                        image=pil_image,
                        config=custom_oem_psm_config
                    )
                    
                    # Step 4: Data processing
                    progress_bar.progress(80)
                    status_text.text("Processing extracted data...")
                    time.sleep(0.5)  # Small delay for visual feedback
                    
                    # Step 5: Finalizing
                    progress_bar.progress(95)
                    status_text.text("Finalizing extraction results...")
                    
                    if error:
                        progress_bar.empty()
                        status_text.empty()
                        handle_error_with_recovery(f"KTP Extraction Error: {error}", [
                            "Ensure the KTP image is clear and well-lit",
                            "Try adjusting the preprocessing options",
                            "Make sure the entire KTP is visible in the image"
                        ])
                    elif ktp_data:
                        # Create KTPData object and ExtractionConfidence
                        st.session_state.ktp_data = constants.KTPData.from_dict(ktp_data)
                        st.session_state.ktp_confidence = constants.ExtractionConfidence(
                            st.session_state.ktp_data.id
                        )
                        
                        # Set confidence scores
                        for field, confidence in ktp_data.get('extraction_confidence', {}).items():
                            st.session_state.ktp_confidence.set_field_confidence(field, confidence)
                        
                        # Complete progress
                        progress_bar.progress(100)
                        status_text.text("KTP data extraction completed!")
                        
                        # Show success message with processing time
                        processing_time = time.time() - start_time
                        show_success(f"KTP data extracted successfully in {processing_time:.1f}s! Overall confidence: {ktp_data.get('overall_confidence', 0):.2%}")
                        
                        # Clear progress after a short delay
                        time.sleep(1)
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.session_state.ktp_extracted = True
                    else:
                        progress_bar.empty()
                        status_text.empty()
                        show_warning("No KTP data was extracted. Try adjusting preprocessing options.")
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    show_error("Exception during KTP data extraction", e)
            
            # Add interactive preprocessing interface
            if st.session_state.image is not None:
                with st.expander("Interactive Preprocessing Configuration", expanded=False):
                    # Create interactive pipeline
                    pipeline = opencv.create_interactive_ktp_pipeline()
                    
                    # Create the interface
                    interface_result = opencv.create_streamlit_preprocessing_interface(
                        pipeline=pipeline,
                        image=st.session_state.raw_image,
                        key_prefix="ktp_interactive"
                    )
                    
                    # Display results based on preview mode
                    if interface_result["processed_image"] is not None:
                        preview_mode = interface_result["settings"]["preview_mode"]
                        
                        if preview_mode == "Final Result":
                            st.subheader("Final Processed Image")
                            processed_rgb = opencv.convert_to_rgb(interface_result["processed_image"])
                            st.image(processed_rgb, use_column_width=True)
                            
                            # Update session state with processed image
                            st.session_state.image = interface_result["processed_image"]
                            
                        elif preview_mode == "Step-by-Step":
                            st.subheader("Step-by-Step Processing")
                            
                            # Get all enabled steps
                            enabled_steps = interface_result["pipeline"].get_enabled_step_names()
                            
                            if enabled_steps:
                                # Create preview for each step
                                step_results = opencv.create_preview_comparison(
                                    original_image=st.session_state.raw_image,
                                    pipeline=interface_result["pipeline"],
                                    enabled_steps=enabled_steps
                                )
                                
                                # Display original and each step
                                cols = st.columns(min(3, len(step_results)))
                                col_idx = 0
                                
                                for step_name, step_image in step_results.items():
                                    with cols[col_idx]:
                                        st.write(f"**{step_name.replace('_', ' ').title()}**")
                                        step_rgb = opencv.convert_to_rgb(step_image)
                                        st.image(step_rgb, use_column_width=True)
                                    
                                    col_idx = (col_idx + 1) % len(cols)
                            
                        elif preview_mode == "Before/After":
                            st.subheader("Before/After Comparison")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Original Image**")
                                original_rgb = opencv.convert_to_rgb(st.session_state.raw_image)
                                st.image(original_rgb, use_column_width=True)
                            
                            with col2:
                                st.write("**Processed Image**")
                                processed_rgb = opencv.convert_to_rgb(interface_result["processed_image"])
                                st.image(processed_rgb, use_column_width=True)
                            
                            # Update session state with processed image
                            st.session_state.image = interface_result["processed_image"]
                        
                        # Add a button to apply the processing to the main workflow
                        if st.button("Apply to Main Workflow", type="secondary"):
                            st.session_state.image = interface_result["processed_image"]
                            st.success("Processing applied to main workflow!")
    
    # Add the second tab for viewing stored KTP data
    if 'tab2' in locals():
        with tab2:
            st.subheader("Stored KTP Data :floppy_disk:")
            
            # Get all stored KTP data
            ktp_list = storage.list_ktp_data()
            
            if not ktp_list:
                st.info("No KTP data has been stored yet. Extract and save KTP data to see it here.")
            else:
                # Display options
                col_view, col_filter = st.columns([3, 1])
                
                with col_filter:
                    # Filter options
                    st.write("**Filter Options**")
                    sort_by = st.selectbox(
                        "Sort by",
                        options=["Created At", "Name", "NIK", "Overall Confidence"],
                        key="sort_by"
                    )
                    
                    sort_order = st.radio(
                        "Sort order",
                        options=["Descending", "Ascending"],
                        key="sort_order"
                    )
                
                with col_view:
                    # Apply sorting
                    if sort_by == "Created At":
                        ktp_list.sort(key=lambda x: x.get('created_at', ''),
                                    reverse=(sort_order == "Descending"))
                    elif sort_by == "Name":
                        ktp_list.sort(key=lambda x: x.get('name', ''),
                                    reverse=(sort_order == "Descending"))
                    elif sort_by == "NIK":
                        ktp_list.sort(key=lambda x: x.get('nik', ''),
                                    reverse=(sort_order == "Descending"))
                    elif sort_by == "Overall Confidence":
                        ktp_list.sort(key=lambda x: x.get('overall_confidence', 0),
                                    reverse=(sort_order == "Descending"))
                    
                    # Display KTP data
                    for i, ktp_summary in enumerate(ktp_list):
                        with st.expander(f"KTP Data - {ktp_summary.get('name', 'Unknown')} ({ktp_summary.get('nik', 'No NIK')})", expanded=i==0):
                            # Load full KTP data
                            ktp_data, ktp_confidence, error = storage.load_ktp_data(ktp_summary['id'])
                            
                            if error:
                                st.error(f"Error loading KTP data: {error}")
                                continue
                            
                            if not ktp_data:
                                st.error("KTP data not found")
                                continue
                            
                            # Display KTP information in columns
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Personal Information**")
                                st.write(f"- **NIK**: {ktp_data.nik}")
                                st.write(f"- **Name**: {ktp_data.name}")
                                st.write(f"- **Place of Birth**: {ktp_data.place_of_birth}")
                                st.write(f"- **Date of Birth**: {ktp_data.date_of_birth}")
                                st.write(f"- **Gender**: {ktp_data.gender}")
                            
                            with col2:
                                st.write("**Address & Other Information**")
                                st.write(f"- **Address**: {ktp_data.address}")
                                st.write(f"- **Religion**: {ktp_data.religion}")
                                st.write(f"- **Marital Status**: {ktp_data.marital_status}")
                                st.write(f"- **Occupation**: {ktp_data.occupation}")
                                st.write(f"- **Validity Period**: {ktp_data.validity_period}")
                            
                            # Show extraction confidence if available
                            if ktp_confidence:
                                st.write("**Extraction Confidence**")
                                conf_data = {}
                                for field in constants.KTP_FIELDS:
                                    conf_score = ktp_confidence.get_field_confidence(field)
                                    if conf_score is not None:
                                        conf_data[field.replace('_', ' ').title()] = conf_score
                                
                                if conf_data:
                                    import pandas as pd
                                    conf_df = pd.DataFrame(list(conf_data.items()),
                                                        columns=['Field', 'Confidence'])
                                    conf_df['Confidence'] = conf_df['Confidence'].apply(lambda x: f"{x:.2%}")
                                    st.dataframe(conf_df, use_container_width=True)
                                    
                                    # Overall confidence
                                    st.metric("Overall Confidence", f"{ktp_confidence.overall_confidence:.2%}")
                            
                            # Show metadata
                            st.write("**Metadata**")
                            st.write(f"- **ID**: {ktp_data.id}")
                            st.write(f"- **Created At**: {ktp_data.created_at}")
                            st.write(f"- **Updated At**: {ktp_data.updated_at}")
                            
                            # Action buttons
                            col_download, col_delete = st.columns(2)
                            
                            with col_download:
                                # Download options
                                export_format = st.selectbox(
                                    "Export Format",
                                    options=["JSON", "CSV"],
                                    key=f"export_format_{ktp_data.id}"
                                )
                                
                                if st.button(f"Export {ktp_data.name}", key=f"export_{ktp_data.id}"):
                                    if export_format == "JSON":
                                        export_data = {
                                            "ktp_data": ktp_data.to_dict(),
                                            "confidence": ktp_confidence.to_dict() if ktp_confidence else None
                                        }
                                        import json
                                        export_json = json.dumps(export_data, ensure_ascii=False, indent=2)
                                        st.download_button(
                                            label="Download JSON",
                                            data=export_json,
                                            file_name=f"ktp_data_{ktp_data.id}.json",
                                            mime="application/json",
                                            key=f"download_json_{ktp_data.id}"
                                        )
                                    elif export_format == "CSV":
                                        import pandas as pd
                                        ktp_df = pd.DataFrame([ktp_data.to_dict()])
                                        csv = ktp_df.to_csv(index=False)
                                        st.download_button(
                                            label="Download CSV",
                                            data=csv,
                                            file_name=f"ktp_data_{ktp_data.id}.csv",
                                            mime="text/csv",
                                            key=f"download_csv_{ktp_data.id}"
                                        )
                            
                            with col_delete:
                                if st.button(f"Delete {ktp_data.name}", key=f"delete_{ktp_data.id}"):
                                    success, message = storage.delete_ktp_data(ktp_data.id)
                                    if success:
                                        show_success(message)
                                        st.experimental_rerun()
                                    else:
                                        show_error(message)
                    
                    # Add a section for bulk operations
                    st.markdown("---")
                    st.subheader("Bulk Operations")
                    
                    col_export_all, col_stats = st.columns(2)
                    
                    with col_export_all:
                        if st.button("Export All KTP Data", type="secondary"):
                            # Create a combined export of all KTP data
                            all_data = []
                            for ktp_summary in ktp_list:
                                ktp_data, ktp_confidence, error = storage.load_ktp_data(ktp_summary['id'])
                                if not error and ktp_data:
                                    all_data.append({
                                        "ktp_data": ktp_data.to_dict(),
                                        "confidence": ktp_confidence.to_dict() if ktp_confidence else None
                                    })
                            
                            if all_data:
                                import json
                                export_json = json.dumps(all_data, ensure_ascii=False, indent=2)
                                st.download_button(
                                    label="Download All KTP Data (JSON)",
                                    data=export_json,
                                    file_name=f"all_ktp_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    mime="application/json"
                                )
                    
                    with col_stats:
                        if st.button("Show Storage Statistics"):
                            stats = storage.get_storage_stats()
                            
                            if "error" in stats:
                                st.error(f"Error getting storage stats: {stats['error']}")
                            else:
                                st.write("**Storage Statistics**")
                                st.write(f"- **KTP Records**: {stats['ktp_data']['count']}")
                                st.write(f"- **Storage Used**: {stats['ktp_data']['size_mb']} MB")
                                st.write(f"- **Total Storage**: {stats['total_size_mb']} MB")
    
    # Add the third tab for document generation
    if 'tab3' in locals():
        with tab3:
            st.subheader("Document Generation & Template Management :page_facing_up:")
            
            # Initialize session state variables for document generation
            if "selected_template_id" not in st.session_state:
                st.session_state.selected_template_id = None
            if "selected_ktp_id" not in st.session_state:
                st.session_state.selected_ktp_id = None
            if "field_mappings" not in st.session_state:
                st.session_state.field_mappings = []
            if "document_preview_ready" not in st.session_state:
                st.session_state.document_preview_ready = False
            if "document_edit_mode" not in st.session_state:
                st.session_state.document_edit_mode = False
            if "editable_document_data" not in st.session_state:
                st.session_state.editable_document_data = {}
            
            # Create two columns for template selection and KTP data selection
            col_template, col_ktp = st.columns(2)
            
            with col_template:
                st.subheader("Select Template :scroll:")
                
                # Get all available templates
                templates = document_gen.list_templates()
                
                if not templates:
                    st.info("No templates available. Create or upload a template to get started.")
                    
                    # Button to create default templates
                    if st.button("Create Default Templates", type="secondary"):
                        success, message = document_gen.create_default_templates()
                        if success:
                            show_success(message)
                            st.experimental_rerun()
                        else:
                            show_error(message)
                else:
                    # Template selection
                    template_options = {f"{t['name']} ({t['output_format']})": t['id'] for t in templates}
                    selected_template_display = st.selectbox(
                        "Available Templates",
                        options=list(template_options.keys()),
                        index=0 if st.session_state.selected_template_id is None else
                               list(template_options.keys()).index(
                                   next((k for k, v in template_options.items()
                                        if v == st.session_state.selected_template_id),
                                       list(template_options.keys())[0])
                               ),
                        key="template_selection"
                    )
                    
                    # Update selected template ID
                    if selected_template_display:
                        st.session_state.selected_template_id = template_options[selected_template_display]
                    
                    # Show template details
                    if st.session_state.selected_template_id:
                        template, error = document_gen.load_template_by_id(st.session_state.selected_template_id)
                        
                        if error:
                            show_error(error)
                        elif template:
                            st.write("**Template Details:**")
                            st.write(f"- **Name**: {template.name}")
                            st.write(f"- **Description**: {template.description or 'No description'}")
                            st.write(f"- **Type**: {template.template_type}")
                            st.write(f"- **Format**: {template.output_format}")
                            st.write(f"- **Created**: {template.created_at}")
                            
                            # Show template placeholders
                            placeholders, error = document_gen.get_template_placeholders(st.session_state.selected_template_id)
                            if error:
                                show_error(error)
                            elif placeholders:
                                st.write(f"- **Placeholders**: {', '.join(placeholders)}")
                            
                            # Template management buttons
                            col_view, col_delete = st.columns(2)
                            
                            with col_view:
                                if st.button("View Template Details", key="view_template"):
                                    with st.expander("Template Information", expanded=True):
                                        st.json(template.to_dict())
                            
                            with col_delete:
                                if st.button("Delete Template", key="delete_template"):
                                    success, message = document_gen.delete_template(st.session_state.selected_template_id)
                                    if success:
                                        show_success(message)
                                        st.session_state.selected_template_id = None
                                        st.experimental_rerun()
                                    else:
                                        show_error(message)
            
            with col_ktp:
                st.subheader("Select KTP Data :id:")
                
                # Get all stored KTP data
                ktp_list = storage.list_ktp_data()
                
                if not ktp_list:
                    st.info("No KTP data available. Extract and save KTP data to get started.")
                else:
                    # KTP data selection
                    ktp_options = {f"{k.get('name', 'Unknown')} ({k.get('nik', 'No NIK')})": k['id'] for k in ktp_list}
                    selected_ktp_display = st.selectbox(
                        "Available KTP Data",
                        options=list(ktp_options.keys()),
                        index=0 if st.session_state.selected_ktp_id is None else
                               list(ktp_options.keys()).index(
                                   next((k for k, v in ktp_options.items()
                                        if v == st.session_state.selected_ktp_id),
                                       list(ktp_options.keys())[0])
                               ),
                        key="ktp_selection"
                    )
                    
                    # Update selected KTP ID
                    if selected_ktp_display:
                        st.session_state.selected_ktp_id = ktp_options[selected_ktp_display]
                    
                    # Show KTP data details
                    if st.session_state.selected_ktp_id:
                        ktp_data, ktp_confidence, error = storage.load_ktp_data(st.session_state.selected_ktp_id)
                        
                        if error:
                            show_error(error)
                        elif ktp_data:
                            st.write("**KTP Data Summary:**")
                            st.write(f"- **Name**: {ktp_data.name}")
                            st.write(f"- **NIK**: {ktp_data.nik}")
                            st.write(f"- **Address**: {ktp_data.address}")
                            
                            # Show overall confidence if available
                            if ktp_confidence:
                                st.write(f"- **Overall Confidence**: {ktp_confidence.overall_confidence:.2%}")
                            
                            # View KTP details button
                            if st.button("View KTP Details", key="view_ktp"):
                                with st.expander("KTP Information", expanded=True):
                                    st.json(ktp_data.to_dict())
            
            # Field mapping section
            st.markdown("---")
            st.subheader("Field Mapping :link:")
            
            if st.session_state.selected_template_id and st.session_state.selected_ktp_id:
                # Load template and KTP data
                template, template_error = document_gen.load_template_by_id(st.session_state.selected_template_id)
                ktp_data, ktp_confidence, ktp_error = storage.load_ktp_data(st.session_state.selected_ktp_id)
                
                if template_error:
                    show_error(template_error)
                elif ktp_error:
                    show_error(ktp_error)
                elif template and ktp_data:
                    # Get template placeholders
                    placeholders, error = document_gen.get_template_placeholders(st.session_state.selected_template_id)
                    
                    if error:
                        show_error(error)
                    else:
                        # Get existing mappings for this template
                        existing_mappings = helpers.constants.field_mapping_manager.get_template_mappings(st.session_state.selected_template_id)
                        
                        # Create mapping interface
                        st.write("**Map KTP fields to template placeholders:**")
                        
                        # Auto-suggest mappings button
                        if st.button("Auto-Suggest Mappings", key="auto_suggest"):
                            suggestions = helpers.constants.template_validator.suggest_field_mappings(st.session_state.selected_template_id)
                            
                            if suggestions:
                                st.success("Field mapping suggestions generated!")
                                
                                # Create mappings from suggestions
                                new_mappings = []
                                for suggestion in suggestions:
                                    if suggestion["ktp_field"]:  # Only create mappings for non-empty KTP fields
                                        mapping = helpers.constants.field_mapping_manager.create_mapping(
                                            template_id=st.session_state.selected_template_id,
                                            ktp_field=suggestion["ktp_field"],
                                            template_field=suggestion["template_field"]
                                        )
                                        new_mappings.append(mapping)
                                
                                # Save new mappings
                                for mapping in new_mappings:
                                    success, message = helpers.constants.field_mapping_manager.save_mapping(mapping)
                                    if not success:
                                        show_error(f"Error saving mapping: {message}")
                                
                                if new_mappings:
                                    show_success(f"Created {len(new_mappings)} field mappings")
                                    st.experimental_rerun()
                            else:
                                show_warning("No field mapping suggestions available")
                        
                        # Manual mapping interface with visual feedback
                        if placeholders:
                            st.write("**Manual Field Mapping:**")
                            
                            # Get KTP fields
                            ktp_dict = ktp_data.to_dict()
                            ktp_field_options = [""] + list(constants.KTP_FIELDS)
                            
                            # Create a visual mapping table
                            st.write("**Field Mapping Table:**")
                            
                            # Create columns for the mapping table
                            col_placeholder, col_ktp, col_status, col_value = st.columns([2, 2, 1, 2])
                            
                            with col_placeholder:
                                st.write("**Template Placeholder**")
                            
                            with col_ktp:
                                st.write("**KTP Field**")
            
                            with col_status:
                                st.write("**Status**")
            
                            with col_value:
                                st.write("**Current Value**")
                            
                            st.write("---")
            
                            # Create mapping for each placeholder
                            mappings_to_save = []
                            
                            for placeholder in placeholders:
                                # Find existing mapping for this placeholder
                                existing_mapping = next((m for m in existing_mappings if m.template_field == placeholder), None)
                                
                                # Default selection
                                default_index = 0
                                if existing_mapping and existing_mapping.ktp_field in ktp_field_options:
                                    default_index = ktp_field_options.index(existing_mapping.ktp_field)
                                
                                # Create columns for this row
                                col_placeholder, col_ktp, col_status, col_value = st.columns([2, 2, 1, 2])
                                
                                with col_placeholder:
                                    st.write(f"**{placeholder}**")
                                
                                with col_ktp:
                                    # Create selectbox for mapping
                                    selected_ktp_field = st.selectbox(
                                        f"Map '{placeholder}' to:",
                                        options=ktp_field_options,
                                        index=default_index,
                                        key=f"map_{placeholder}",
                                        help="Select the KTP field to map to this template placeholder",
                                        label_visibility="collapsed"
                                    )
                                
                                with col_status:
                                    # Show mapping status
                                    if selected_ktp_field:
                                        if existing_mapping and existing_mapping.ktp_field == selected_ktp_field:
                                            st.success("✓")
                                        else:
                                            st.info("🔄")
                                    else:
                                        if existing_mapping:
                                            st.warning("⚠️")
                                        else:
                                            st.error("✗")
                                
                                with col_value:
                                    # Show current KTP value if mapped
                                    if selected_ktp_field and selected_ktp_field in ktp_dict:
                                        value = ktp_dict[selected_ktp_field]
                                        if value:
                                            # Truncate long values
                                            display_value = value[:30] + "..." if len(str(value)) > 30 else value
                                            st.write(display_value)
                                        else:
                                            st.write("*(empty)*")
                                    else:
                                        st.write("*(not mapped)*")
                                
                                if selected_ktp_field:
                                    mappings_to_save.append({
                                        "template_field": placeholder,
                                        "ktp_field": selected_ktp_field
                                    })
                            
                            # Add a visual mapping summary
                            st.write("---")
                            st.write("**Mapping Summary:**")
                            
                            # Calculate mapping statistics
                            total_placeholders = len(placeholders)
                            mapped_placeholders = len([m for m in mappings_to_save if m["ktp_field"]])
                            unmapped_placeholders = total_placeholders - mapped_placeholders
            
                            # Create progress bar
                            progress = mapped_placeholders / total_placeholders if total_placeholders > 0 else 0
                            st.progress(progress)
                            st.write(f"**{mapped_placeholders}/{total_placeholders} placeholders mapped** ({progress:.1%})")
                            
                            # Show mapping details in an expander
                            with st.expander("View Mapping Details", expanded=False):
                                if mappings_to_save:
                                    import pandas as pd
                                    mapping_df = pd.DataFrame(mappings_to_save)
                                    st.dataframe(mapping_df, use_container_width=True)
                                else:
                                    st.info("No mappings configured")
                            
                            # Save mappings button
                            col_save, col_reset = st.columns(2)
                            
                            with col_save:
                                if st.button("Save Mappings", type="primary", key="save_mappings"):
                                    # Delete existing mappings for this template
                                    for mapping in existing_mappings:
                                        success, message = helpers.constants.field_mapping_manager.delete_mapping(mapping.id)
                                        if not success:
                                            show_error(f"Error deleting old mapping: {message}")
                                    
                                    # Create new mappings
                                    saved_count = 0
                                    for mapping_data in mappings_to_save:
                                        mapping = helpers.constants.field_mapping_manager.create_mapping(
                                            template_id=st.session_state.selected_template_id,
                                            ktp_field=mapping_data["ktp_field"],
                                            template_field=mapping_data["template_field"]
                                        )
                                        
                                        success, message = helpers.constants.field_mapping_manager.save_mapping(mapping)
                                        if success:
                                            saved_count += 1
                                        else:
                                            show_error(f"Error saving mapping: {message}")
                                    
                                    if saved_count > 0:
                                        show_success(f"Saved {saved_count} field mappings")
                                        st.experimental_rerun()
                                    else:
                                        show_error("No mappings were saved")
                            
                            with col_reset:
                                if st.button("Reset Mappings", key="reset_mappings"):
                                    # Delete all existing mappings for this template
                                    for mapping in existing_mappings:
                                        success, message = helpers.constants.field_mapping_manager.delete_mapping(mapping.id)
                                        if not success:
                                            show_error(f"Error deleting mapping: {message}")
                                    
                                    if existing_mappings:
                                        show_success(f"Reset {len(existing_mappings)} field mappings")
                                        st.experimental_rerun()
                                    else:
                                        show_info("No mappings to reset")
                        else:
                            st.info("No placeholders found in this template")
            else:
                st.info("Please select both a template and KTP data to configure field mapping")
            
            # Document preview section
            st.markdown("---")
            st.subheader("Document Preview :eye:")
            
            if st.session_state.selected_template_id and st.session_state.selected_ktp_id:
                # Check if mappings exist
                mappings = helpers.constants.field_mapping_manager.get_template_mappings(st.session_state.selected_template_id)
                
                if not mappings:
                    st.warning("No field mappings configured. Please set up field mappings above.")
                else:
                    # Generate preview button
                    if st.button("Generate Document Preview", type="primary", key="generate_preview"):
                        with st.spinner("Generating document preview..."):
                            # Load template and KTP data
                            template, template_error = document_gen.load_template_by_id(st.session_state.selected_template_id)
                            ktp_data, ktp_confidence, ktp_error = storage.load_ktp_data(st.session_state.selected_ktp_id)
                            
                            if template_error:
                                show_error(template_error)
                            elif ktp_error:
                                show_error(ktp_error)
                            elif template and ktp_data:
                                # Apply mappings to KTP data
                                mapped_data = helpers.constants.field_mapping_manager.apply_mappings(ktp_data, mappings)
                                
                                if not mapped_data:
                                    show_error("No data to populate in document. Check field mappings.")
                                else:
                                    # Generate optimized preview
                                    preview_bytes, error = document_gen.optimized_preview_document(
                                        template_path=template.file_path,
                                        data=mapped_data,
                                        format_type=template.output_format.lower(),
                                        field_mappings=mappings
                                    )
                                    
                                    if error:
                                        show_error(f"Error generating preview: {error}")
                                    elif preview_bytes:
                                        st.session_state.document_preview_ready = True
                                        st.session_state.preview_bytes = preview_bytes
                                        st.session_state.preview_format = template.output_format.lower()
                                        show_success("Document preview generated successfully!")
            
            # Display preview if ready
            if st.session_state.document_preview_ready and hasattr(st.session_state, 'preview_bytes'):
                st.write("**Document Preview:**")
                
                # Display preview based on format
                if st.session_state.preview_format == "pdf":
                    st.write("PDF Preview:")
                    # Display PDF using iframe
                    import base64
                    b64 = base64.b64encode(st.session_state.preview_bytes).decode()
                    pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600px"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    # For DOCX, show a download button
                    st.write("DOCX Preview:")
                    st.info("DOCX preview is not supported in the browser. Use the download button below to view the document.")
                
                # Download button
                st.download_button(
                    label=f"Download Preview ({st.session_state.preview_format.upper()})",
                    data=st.session_state.preview_bytes,
                    file_name=f"document_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{st.session_state.preview_format}",
                    mime="application/pdf" if st.session_state.preview_format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                # Generate final document button
                if st.button("Generate Final Document", type="primary", key="generate_final"):
                    with st.spinner("Generating final document..."):
                        # Load template and KTP data
                        template, template_error = document_gen.load_template_by_id(st.session_state.selected_template_id)
                        ktp_data, ktp_confidence, ktp_error = storage.load_ktp_data(st.session_state.selected_ktp_id)
                        
                        if template_error:
                            show_error(template_error)
                        elif ktp_error:
                            show_error(ktp_error)
                        elif template and ktp_data:
                            # Apply mappings to KTP data
                            mappings = helpers.constants.field_mapping_manager.get_template_mappings(st.session_state.selected_template_id)
                            mapped_data = helpers.constants.field_mapping_manager.apply_mappings(ktp_data, mappings)
                            
                            if not mapped_data:
                                show_error("No data to populate in document. Check field mappings.")
                            else:
                                # Generate final document
                                output_path = os.path.join(
                                    constants.GENERATED_DOCUMENTS_DIR,
                                    f"final_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{template.output_format.lower()}"
                                )
                                
                                success, message = document_gen.generate_document(
                                    template_path=template.file_path,
                                    output_path=output_path,
                                    data=mapped_data,
                                    format_type=template.output_format.lower(),
                                    field_mappings=mappings
                                )
                                
                                if success:
                                    show_success(message)
                                    
                                    # Provide download link
                                    with open(output_path, "rb") as f:
                                        final_bytes = f.read()
                                    
                                    st.download_button(
                                        label=f"Download Final Document ({template.output_format})",
                                        data=final_bytes,
                                        file_name=os.path.basename(output_path),
                                        mime="application/pdf" if template.output_format == "PDF" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    )
                                else:
                                    show_error(message)
            
            # Document editing section
            st.markdown("---")
            st.subheader("Document Editing & Final Generation :pencil2:")
            
            if st.session_state.selected_template_id and st.session_state.selected_ktp_id:
                # Check if mappings exist
                mappings = helpers.constants.field_mapping_manager.get_template_mappings(st.session_state.selected_template_id)
                
                if not mappings:
                    st.warning("No field mappings configured. Please set up field mappings above.")
                else:
                    # Load template and KTP data
                    template, template_error = document_gen.load_template_by_id(st.session_state.selected_template_id)
                    ktp_data, ktp_confidence, ktp_error = storage.load_ktp_data(st.session_state.selected_ktp_id)
                    
                    if template_error:
                        show_error(template_error)
                    elif ktp_error:
                        show_error(ktp_error)
                    elif template and ktp_data:
                        # Apply mappings to KTP data
                        mapped_data = helpers.constants.field_mapping_manager.apply_mappings(ktp_data, mappings)
                        
                        if not mapped_data:
                            show_error("No data to populate in document. Check field mappings.")
                        else:
                            # Create editable document
                            if not st.session_state.document_edit_mode:
                                if st.button("Enable Document Editing", type="secondary"):
                                    success, message, editable_data = document_gen.create_editable_document(
                                        template_path=template.file_path,
                                        data=mapped_data
                                    )
                                    
                                    if success:
                                        st.session_state.editable_document_data = editable_data
                                        st.session_state.document_edit_mode = True
                                        show_success(message)
                                    else:
                                        show_error(message)
                            
                            # Document editing interface
                            if st.session_state.document_edit_mode:
                                st.write("**Edit Document Data:**")
                                st.info("You can edit the data below before generating the final document.")
                                
                                # Create editable fields
                                edited_data = {}
                                for field_name, field_value in st.session_state.editable_document_data.get("editable_fields", {}).items():
                                    field_metadata = st.session_state.editable_document_data.get("field_metadata", {}).get(field_name, {})
                                    
                                    # Create appropriate input based on field type
                                    if field_metadata.get("type") == "text":
                                        edited_value = st.text_input(
                                            field_name.replace("_", " ").title(),
                                            value=field_value,
                                            key=f"edit_field_{field_name}"
                                        )
                                        edited_data[field_name] = edited_value
                                
                                # Action buttons
                                col_save, col_cancel, col_generate = st.columns(3)
                                
                                with col_save:
                                    if st.button("Save Changes", type="primary", key="save_edits"):
                                        # Update document data
                                        updated_data = document_gen.update_document_data(
                                            st.session_state.editable_document_data["original_data"],
                                            edited_data
                                        )
                                        
                                        # Validate updated data
                                        is_valid, errors = document_gen.validate_document_data(updated_data)
                                        
                                        if is_valid:
                                            st.session_state.editable_document_data["original_data"] = updated_data
                                            for field_name, field_value in edited_data.items():
                                                st.session_state.editable_document_data["editable_fields"][field_name] = field_value
                                            
                                            show_success("Changes saved successfully!")
                                        else:
                                            show_error("Validation errors: " + "; ".join(errors))
                                
                                with col_cancel:
                                    if st.button("Cancel Editing", key="cancel_edits"):
                                        st.session_state.document_edit_mode = False
                                        st.session_state.editable_document_data = {}
                                        show_info("Editing cancelled")
                                
                                with col_generate:
                                    if st.button("Generate Final Document", type="primary", key="generate_from_edited"):
                                        # Validate data before generation
                                        is_valid, errors = document_gen.validate_document_data(
                                            st.session_state.editable_document_data["original_data"]
                                        )
                                        
                                        if is_valid:
                                            # Generate document with edited data
                                            output_path = os.path.join(
                                                constants.GENERATED_DOCUMENTS_DIR,
                                                f"final_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{template.output_format.lower()}"
                                            )
                                            
                                            # Create document ID for status tracking
                                            document_id = os.path.splitext(os.path.basename(output_path))[0]
                                            
                                            # Save initial status
                                            document_gen.save_document_status(
                                                document_id=document_id,
                                                status="draft",
                                                message="Document generation started"
                                            )
                                            
                                            # Generate document
                                            success, message = document_gen.generate_document(
                                                template_path=template.file_path,
                                                output_path=output_path,
                                                data=st.session_state.editable_document_data["original_data"],
                                                format_type=template.output_format.lower(),
                                                field_mappings=mappings
                                            )
                                            
                                            if success:
                                                # Update status to completed
                                                document_gen.save_document_status(
                                                    document_id=document_id,
                                                    status="completed",
                                                    message="Document generated successfully"
                                                )
                                                
                                                show_success(message)
                                                
                                                # Provide download link
                                                with open(output_path, "rb") as f:
                                                    final_bytes = f.read()
                                                
                                                st.download_button(
                                                    label=f"Download Final Document ({template.output_format})",
                                                    data=final_bytes,
                                                    file_name=os.path.basename(output_path),
                                                    mime="application/pdf" if template.output_format == "PDF" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                                )
                                                
                                                # Reset edit mode
                                                st.session_state.document_edit_mode = False
                                                st.session_state.editable_document_data = {}
                                            else:
                                                # Update status to error
                                                document_gen.save_document_status(
                                                    document_id=document_id,
                                                    status="error",
                                                    message=f"Document generation failed: {message}"
                                                )
                                                
                                                show_error(message)
                                        else:
                                            show_error("Cannot generate document due to validation errors: " + "; ".join(errors))
            
            # Document history section
            st.markdown("---")
            st.subheader("Document History :history:")
            
            # Get all generated documents
            documents = document_gen.list_generated_documents()
            
            if not documents:
                st.info("No documents have been generated yet.")
            else:
                # Display documents in a table
                import pandas as pd
                
                # Create a dataframe for display
                doc_data = []
                for doc in documents:
                    doc_data.append({
                        "Name": doc["id"],
                        "Format": os.path.splitext(doc["file_name"])[1].upper(),
                        "Status": doc["status"],
                        "Created": doc["created_at"][:19].replace("T", " "),
                        "Size": f"{doc['file_size'] / 1024:.1f} KB"
                    })
                
                df = pd.DataFrame(doc_data)
                st.dataframe(df, use_container_width=True)
                
                # Document details
                selected_doc = st.selectbox(
                    "Select a document to view details:",
                    options=[doc["id"] for doc in documents],
                    format_func=lambda x: f"{x} ({next(d['status'] for d in documents if d['id'] == x)})"
                )
                
                if selected_doc:
                    # Get document details
                    doc_details = next(d for d in documents if d["id"] == selected_doc)
                    
                    # Display document information
                    col_info, col_history, col_actions = st.columns(3)
                    
                    with col_info:
                        st.write("**Document Information:**")
                        st.write(f"- **ID**: {doc_details['id']}")
                        st.write(f"- **Format**: {os.path.splitext(doc_details['file_name'])[1].upper()}")
                        st.write(f"- **Size**: {doc_details['file_size'] / 1024:.1f} KB")
                        st.write(f"- **Created**: {doc_details['created_at'][:19].replace('T', ' ')}")
                        st.write(f"- **Status**: {doc_details['status']}")
                        if doc_details['status_message']:
                            st.write(f"- **Message**: {doc_details['status_message']}")
                    
                    with col_history:
                        st.write("**Status History:**")
                        history, error = document_gen.get_document_history(doc_details['id'])
                        
                        if error:
                            st.error(f"Error loading history: {error}")
                        elif history:
                            for status_entry in history:
                                timestamp = status_entry['timestamp'][:19].replace('T', ' ')
                                st.write(f"- **{timestamp}**: {status_entry['status']}")
                                if status_entry['message']:
                                    st.write(f"  {status_entry['message']}")
                        else:
                            st.info("No history available")
                    
                    with col_actions:
                        st.write("**Actions:**")
                        
                        # Download button
                        if os.path.exists(doc_details['file_path']):
                            with open(doc_details['file_path'], 'rb') as f:
                                file_bytes = f.read()
                            
                            file_ext = os.path.splitext(doc_details['file_name'])[1].lower()
                            mime_type = "application/pdf" if file_ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            
                            st.download_button(
                                label="Download Document",
                                data=file_bytes,
                                file_name=doc_details['file_name'],
                                mime=mime_type
                            )
                        
                        # Delete button
                        if st.button(f"Delete {doc_details['id']}", key=f"delete_doc_{doc_details['id']}"):
                            success, message = document_gen.delete_generated_document(doc_details['id'])
                            
                            if success:
                                show_success(message)
                                st.experimental_rerun()
                            else:
                                show_error(message)
            
            # Template upload section
            st.markdown("---")
            st.subheader("Upload New Template :arrow_up:")
            
            uploaded_template = st.file_uploader(
                "Upload a document template",
                type=["docx", "pdf"],
                help="Upload a DOCX or PDF file with placeholders in {{placeholder}} format"
            )
            
            if uploaded_template is not None:
                # Get template details
                template_name = st.text_input("Template Name", value=uploaded_template.name.split('.')[0])
                template_description = st.text_area("Template Description (Optional)", "")
                template_type = st.selectbox("Template Type", ["form", "letter", "application", "other"])
                
                if st.button("Upload Template", key="upload_template"):
                    if not template_name:
                        show_error("Template name is required")
                    else:
                        # Save uploaded file
                        upload_dir = "temp_uploads"
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        file_path = os.path.join(upload_dir, uploaded_template.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_template.getbuffer())
                        
                        # Create template
                        success, message, template = document_gen.create_template_from_file(
                            file_path=file_path,
                            name=template_name,
                            description=template_description,
                            template_type=template_type
                        )
                        
                        if success:
                            show_success(message)
                            st.experimental_rerun()
                        else:
                            show_error(message)
                        
                        # Clean up temporary file
                        if os.path.exists(file_path):
                            os.remove(file_path)
else:
    # General OCR Interface (original code)
    col_upload_1, col_upload_2 = st.columns(spec=2, gap="small")

    with col_upload_1:
        # upload image
        st.subheader("Upload Image :arrow_up:")
        st.session_state.uploaded_file = st.file_uploader(
            "Upload Image or PDF", type=["png", "jpg", "jpeg", "bmp", "tif", "tiff", "pdf"]
        )
        if st.session_state.uploaded_file is None:
            st.session_state.raw_image = None
            st.session_state.image = None
            st.session_state.text = None
        elif st.session_state.uploaded_file is not None:
            # Validate uploaded file
            is_valid, error_message = validate_file_upload(st.session_state.uploaded_file)
            if not is_valid:
                handle_error_with_recovery(error_message, [
                    "Check if the file is a valid image or PDF",
                    "Ensure file size is under 10MB",
                    "Try uploading a different file"
                ])
                st.stop()
            
            # check if uploaded file is pdf
            if st.session_state.uploaded_file.name.lower().endswith(".pdf"):
                page = st.number_input("Select Page of PDF", min_value=1, max_value=100, value=1, step=1)
                start_time = time.time()
                try:
                    with st.spinner("Extracting page from PDF..."):
                        st.session_state.raw_image, error = pdfimage.pdftoimage(pdf_file=st.session_state.uploaded_file, page=page)
                        if not show_processing_status("PDF Processing", start_time, timeout=30):
                            st.stop()
                    
                    if error:
                        handle_error_with_recovery(f"Error processing PDF: {error}", [
                            "Check if the PDF is password protected",
                            "Try selecting a different page",
                            "Ensure the PDF contains valid images"
                        ])
                        st.stop()
                    elif st.session_state.raw_image is None:
                        show_error("No image was extracted from PDF.", [
                            "The selected page might not contain any images",
                            "Try selecting a different page"
                        ])
                        st.stop()
                except Exception as e:
                    show_error("Exception during PDF processing", e)
                    st.stop()
            # else uploaded file is image file
            else:
                try:
                    start_time = time.time()
                    with st.spinner("Loading image..."):
                        # convert uploaded file to numpy array
                        st.session_state.raw_image = opencv.load_image(st.session_state.uploaded_file)
                        if not show_processing_status("Image Loading", start_time, timeout=10):
                            st.stop()
                except Exception as e:
                    handle_error_with_recovery("Exception during Image Conversion", [
                        "Check if the file is a valid image format",
                        "Try uploading a different image",
                        "Ensure the image is not corrupted"
                    ], e)
                    st.stop()
            
            try:
                start_time = time.time()
                with st.spinner("Preprocessing Image..."):
                    image = st.session_state.raw_image.copy()
                    if cGrayscale:
                        image = opencv.grayscale(img=image)
                    if cDenoising:
                        image = opencv.denoising(img=image, strength=cDenoisingStrength)
                    if cThresholding:
                        image = opencv.thresholding(img=image, threshold=cThresholdLevel)
                    if cRotate90:
                        angle90 = opencv.angles.get(angle90, None)  # convert angle to opencv2 enum
                        image = opencv.rotate90(img=image, rotate=angle90)
                    if cRotateFree:
                        image = opencv.rotate_scipy(img=image, angle=angle, reshape=True)
                    st.session_state.image = image.copy()
                    
                    if not show_processing_status("Image Preprocessing", start_time, timeout=30):
                        st.stop()
            except Exception as e:
                handle_error_with_recovery("Error during image preprocessing", [
                    "Try disabling some preprocessing options",
                    "Check if the image is too large or complex",
                    "Ensure the image format is supported"
                ], e)
                st.stop()
            st.session_state.preview_processed_image = st.toggle("Preview Preprocessed Image", value=True)
            st.session_state.crop_image = st.toggle("Crop Image", value=True, disabled=True)

    with col_upload_2:
        st.subheader("Select Language :globe_with_meridians:")
        language = st.selectbox(
            label="Select Language",
            options=language_options_list,
            index=constants.default_language_index,
        )
        language_short = list(constants.languages_sorted.keys())[list(constants.languages_sorted.values()).index(language)]
        if language_short not in installed_languages:
            handle_error_with_recovery(f'Selected language "{language}" is not installed.', [
                "Install the language pack for Tesseract",
                "Select a different language from the dropdown",
                "Check Tesseract documentation for language pack installation"
            ])
            st.stop()
        if st.session_state.uploaded_file is not None:
            if st.session_state.image is not None:
                st.markdown("---")
                st.subheader("Run OCR on preprocessed image :mag_right:")
                if st.button("Extract Text"):
                    start_time = time.time()
                    try:
                        with st.spinner("Extracting Text..."):
                            st.session_state.text, error = tesseract.image_to_string(
                                image=st.session_state.image,
                                language_short=language_short,
                                config=custom_oem_psm_config,
                                timeout=timeout,
                            )
                            
                            if not show_processing_status("Text Extraction", start_time, timeout=timeout):
                                st.stop()
                            
                            if error:
                                handle_error_with_recovery(f"OCR Error: {error}", [
                                    "Try adjusting the preprocessing options",
                                    "Check if the image text is clear and readable",
                                    "Try a different page segmentation mode",
                                    "Ensure the selected language matches the text in the image"
                                ])
                            elif st.session_state.text and st.session_state.text.strip():
                                show_success(f"Text extracted successfully! ({time.time() - start_time:.1f}s)")
                            else:
                                show_warning("No text was extracted. Try adjusting preprocessing options.")
                    except Exception as e:
                        show_error("Exception during text extraction", e)

if st.session_state.uploaded_file is not None:
    st.markdown("---")
    
    if st.session_state.ktp_mode:
        # KTP Data Display
        if st.session_state.ktp_extracted and st.session_state.ktp_data:
            st.subheader("Extracted KTP Data :id:")
            
            # Display KTP data with confidence scores
            col1, col2 = st.columns(spec=2, gap="small")
            
            with col1:
                st.subheader("Image Preview :eye:")
                if st.session_state.preview_processed_image and st.session_state.image is not None:
                    image = opencv.convert_to_rgb(st.session_state.image) # convert BGR to RGB
                    st.image(image, caption="Preprocessed KTP Image", use_column_width=True)
                elif st.session_state.raw_image is not None:
                    raw_image = opencv.convert_to_rgb(st.session_state.raw_image)  # convert BGR to RGB
                    st.image(raw_image, caption="Original KTP Image", use_column_width=True)
            
            with col2:
                st.subheader("Extracted Information :clipboard:")
                
                # Show confidence-based correction guidance
                if st.session_state.ktp_confidence:
                    low_confidence_fields = []
                    medium_confidence_fields = []
                    high_confidence_fields = []
                    
                    for field in constants.KTP_FIELDS:
                        conf_score = st.session_state.ktp_confidence.get_field_confidence(field)
                        if conf_score is not None:
                            if conf_score < 0.6:
                                low_confidence_fields.append(field)
                            elif conf_score < 0.8:
                                medium_confidence_fields.append(field)
                            else:
                                high_confidence_fields.append(field)
                    
                    # Show confidence summary
                    st.info(f"""
                    **Extraction Confidence Summary:**
                    - 🔴 Low confidence (<60%): {len(low_confidence_fields)} fields
                    - 🟡 Medium confidence (60-80%): {len(medium_confidence_fields)} fields
                    - 🟢 High confidence (>80%): {len(high_confidence_fields)} fields
                    """)
                    
                    if low_confidence_fields:
                        st.warning(f"⚠️ **Low Confidence Fields**: Please review and correct: {', '.join([f.replace('_', ' ').title() for f in low_confidence_fields])}")
                
                # Display KTP data editing interface
                corrections_made = display_ktp_data_editing(
                    st.session_state.ktp_data,
                    st.session_state.ktp_confidence
                )
                
                # Add a section for bulk corrections
                with st.expander("Bulk Corrections & Validation", expanded=False):
                    st.write("Use this section to make multiple corrections at once or validate all fields:")
                    
                    # Get current form values
                    ktp_dict = st.session_state.ktp_data.to_dict()
                    
                    # Auto-correction suggestions
                    if st.button("Suggest Corrections for Low Confidence Fields"):
                        suggestions = {}
                        
                        # Suggest corrections for common OCR errors
                        if ktp_dict.get('nik') and st.session_state.ktp_confidence.get_field_confidence('nik') and st.session_state.ktp_confidence.get_field_confidence('nik') < 0.6:
                            # Check for common OCR errors in NIK
                            original_nik = ktp_dict.get('nik', '')
                            if original_nik:
                                # Replace common OCR mistakes
                                suggested_nik = original_nik.replace('O', '0').replace('I', '1').replace('S', '5').replace('Z', '2')
                                if suggested_nik != original_nik and suggested_nik.isdigit() and len(suggested_nik) == 16:
                                    suggestions['nik'] = suggested_nik
                        
                        if suggestions:
                            st.success("Correction suggestions:")
                            for field, suggestion in suggestions.items():
                                st.write(f"- **{field.replace('_', ' ').title()}**: {suggestion}")
                            
                            if st.button("Apply Suggestions"):
                                for field, suggestion in suggestions.items():
                                    if field == 'nik':
                                        st.session_state.edit_nik = suggestion
                                st.experimental_rerun()
                        else:
                            st.info("No automatic correction suggestions available.")
                    
                    # Validate all fields
                    if st.button("Validate All Fields"):
                        # Get current form values
                        nik_value = st.session_state.get('edit_nik', ktp_dict.get('nik', ''))
                        name_value = st.session_state.get('edit_name', ktp_dict.get('name', ''))
                        pob_value = st.session_state.get('edit_pob', ktp_dict.get('place_of_birth', ''))
                        dob_value = st.session_state.get('edit_dob', ktp_dict.get('date_of_birth', ''))
                        gender_value = st.session_state.get('edit_gender', ktp_dict.get('gender', ''))
                        address_value = st.session_state.get('edit_address', ktp_dict.get('address', ''))
                        religion_value = st.session_state.get('edit_religion', ktp_dict.get('religion', ''))
                        marital_value = st.session_state.get('edit_marital', ktp_dict.get('marital_status', ''))
                        occupation_value = st.session_state.get('edit_occupation', ktp_dict.get('occupation', ''))
                        validity_value = st.session_state.get('edit_validity', ktp_dict.get('validity_period', ''))
                        
                        # Create a temporary KTPData object with current values
                        temp_ktp = constants.KTPData(
                            nik=nik_value,
                            name=name_value,
                            place_of_birth=pob_value,
                            date_of_birth=dob_value,
                            gender=gender_value,
                            address=address_value,
                            religion=religion_value,
                            marital_status=marital_value,
                            occupation=occupation_value,
                            validity_period=validity_value
                        )
                        
                        # Validate the data
                        is_valid, messages = temp_ktp.validate()
                        
                        if is_valid:
                            st.success("✅ All fields are valid!")
                        else:
                            st.error("❌ Validation errors found:")
                            for message in messages:
                                st.error(f"• {message}")
                
                # Confidence scores display
                if st.session_state.ktp_confidence:
                    st.subheader("Extraction Confidence :chart_with_upwards_trend:")
                    confidence_data = {}
                    
                    for field in constants.KTP_FIELDS:
                        conf_score = st.session_state.ktp_confidence.get_field_confidence(field)
                        if conf_score is not None:
                            confidence_data[field.replace('_', ' ').title()] = conf_score
                    
                    if confidence_data:
                        # Create a dataframe for better display
                        import pandas as pd
                        confidence_df = pd.DataFrame(list(confidence_data.items()),
                                                    columns=['Field', 'Confidence'])
                        confidence_df['Confidence'] = confidence_df['Confidence'].apply(lambda x: f"{x:.2%}")
                        st.dataframe(confidence_df, use_container_width=True)
                        
                        # Overall confidence
                        overall_conf = st.session_state.ktp_confidence.overall_confidence
                        st.metric("Overall Confidence", f"{overall_conf:.2%}")
                
                # Validation status
                is_valid, errors = st.session_state.ktp_data.validate()
                st.subheader("Validation Status :check_mark:")
                if is_valid:
                    st.success("✅ All data is valid")
                else:
                    st.error("❌ Validation errors found:")
                    for error in errors:
                        st.error(f"• {error}")
                
                # Action buttons
                st.markdown("---")
                col_save, col_export = st.columns(2)
                
                with col_save:
                    if st.button("Save KTP Data", type="primary"):
                        success, message = storage.save_ktp_data(
                            st.session_state.ktp_data,
                            st.session_state.ktp_confidence
                        )
                        if success:
                            show_success(message)
                        else:
                            show_error(message)
                
                with col_export:
                    # Export options
                    export_format = st.selectbox(
                        "Export Format",
                        options=["JSON", "CSV"],
                        key="export_format"
                    )
                    
                    if st.button("Export Data"):
                        if export_format == "JSON":
                            # Create JSON export
                            export_data = {
                                "ktp_data": st.session_state.ktp_data.to_dict(),
                                "confidence": st.session_state.ktp_confidence.to_dict() if st.session_state.ktp_confidence else None
                            }
                            import json
                            export_json = json.dumps(export_data, ensure_ascii=False, indent=2)
                            st.download_button(
                                label="Download JSON",
                                data=export_json,
                                file_name=f"ktp_data_{st.session_state.ktp_data.id}.json",
                                mime="application/json"
                            )
                        elif export_format == "CSV":
                            # Create CSV export
                            import pandas as pd
                            ktp_df = pd.DataFrame([st.session_state.ktp_data.to_dict()])
                            csv = ktp_df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"ktp_data_{st.session_state.ktp_data.id}.csv",
                                mime="text/csv"
                            )
        else:
            # Show image preview if no KTP data extracted yet
            col1, col2 = st.columns(spec=2, gap="small")
            
            with col1:
                if st.session_state.preview_processed_image and st.session_state.image is not None:
                    st.subheader("Preview after Preprocessing :eye:")
                    image = opencv.convert_to_rgb(st.session_state.image) # convert BGR to RGB
                    st.image(image, caption="Image Preview after Preprocessing", use_column_width=True)
                else:
                    st.subheader("Preview after Upload :eye:")
                    if st.session_state.raw_image is not None:
                        raw_image = opencv.convert_to_rgb(st.session_state.raw_image)  # convert BGR to RGB
                        st.image(raw_image, caption="Image Preview after Upload", use_column_width=True)
            
            with col2:
                st.subheader("KTP Processing Status :id:")
                if st.session_state.image is not None:
                    st.info("Upload a KTP image and click 'Extract KTP Data' to begin processing")
                else:
                    st.warning("Please upload a KTP image to begin extraction")
    else:
        # General OCR Display (original code)
        col1, col2 = st.columns(spec=2, gap="small")

        with col1:
            if st.session_state.preview_processed_image:
                st.subheader("Preview after Preprocessing :eye:")
                if st.session_state.image is not None:
                    image = opencv.convert_to_rgb(st.session_state.image) # convert BGR to RGB
                    st.image(image, caption="Image Preview after Preprocessing", use_column_width=True)
            else:
                st.subheader("Preview after Upload :eye:")
                if st.session_state.raw_image is not None:
                    raw_image = opencv.convert_to_rgb(st.session_state.raw_image)  # convert BGR to RGB
                    st.image(raw_image, caption="Image Preview after Upload", use_column_width=True)

        with col2:
            st.subheader("Extracted Text :eye:")
            if st.session_state.text:
                st.text_area(label="Extracted Text", value=st.session_state.text, height=500)
                st.download_button(
                    label="Download Extracted Text",
                    data=st.session_state.text.encode("utf-8"),
                    file_name=st.session_state.uploaded_file.name + ".txt",
                    mime="text/plain",
                )
            else:
                st.warning("No text was extracted.")
