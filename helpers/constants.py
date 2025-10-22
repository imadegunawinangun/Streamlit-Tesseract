#  all application constants are defined here as dictionaries or lists
import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import os


# ============================================================================
# LANGUAGE CONFIGURATION
# ============================================================================

# Language configurations with flag emojis
LANGUAGES = {
    "eng": "🇬🇧 English",
    "spa": "🇪🇸 Spanish",
    "fra": "🇫🇷 French",
    "deu": "🇩🇪 German",
    "ita": "🇮🇹 Italian",
    "por": "🇵🇹 Portuguese",
    "ces": "🇨🇿 Czech",
    "pol": "🇵🇱 Polish",
    "ind": "🇮🇩 Indonesian",
}

# Sort languages by index
LANGUAGES_SORTED = dict(sorted(LANGUAGES.items(), key=lambda item: item[0]))
# Get index of English language as default
DEFAULT_LANGUAGE_INDEX = list(LANGUAGES_SORTED.keys()).index("eng")

# EasyOCR uses different language codes, so we need to map them
LANGUAGES_EASYOCR = {
    "eng": "en",
    "spa": "es",
    "fra": "fr",
    "deu": "de",
    "ita": "it",
    "por": "pt",
    "ces": "cs",
    "pol": "pl",
    "ind": "id",
}

# Flag emojis dictionary
FLAGS = {
    "eng": "🇬🇧",
    "spa": "🇪🇸",
    "fra": "🇫🇷",
    "deu": "🇩🇪",
    "ita": "🇮🇹",
    "por": "🇵🇹",
    "ces": "🇨🇿",
    "pol": "🇵🇱",
    "ind": "🇮🇩",
}

# Sort flags by index
FLAGS_SORTED = dict(sorted(FLAGS.items(), key=lambda item: item[0]))
FLAG_STRING = " ".join(FLAGS_SORTED.values())

# For backward compatibility
languages = LANGUAGES
languages_sorted = LANGUAGES_SORTED
default_language_index = DEFAULT_LANGUAGE_INDEX
languages_easyocr = LANGUAGES_EASYOCR
flags = FLAGS
flags_sorted = FLAGS_SORTED
flag_string = FLAG_STRING


# ============================================================================
# STORAGE PATHS
# ============================================================================

# Storage paths
DATA_DIR = "data"
KTP_DATA_DIR = os.path.join(DATA_DIR, "ktp_data")
TEMPLATES_DIR = os.path.join(DATA_DIR, "templates")
GENERATED_DOCUMENTS_DIR = os.path.join(DATA_DIR, "generated_documents")
MAPPINGS_DIR = os.path.join(DATA_DIR, "mappings")

# Create directories if they don't exist
for directory in [DATA_DIR, KTP_DATA_DIR, TEMPLATES_DIR, GENERATED_DOCUMENTS_DIR, MAPPINGS_DIR]:
    os.makedirs(directory, exist_ok=True)


# ============================================================================
# INDONESIAN CONSTANTS
# ============================================================================

# KTP field constants
KTP_FIELDS = [
    "nik",
    "name",
    "place_of_birth",
    "date_of_birth",
    "gender",
    "address",
    "religion",
    "marital_status",
    "occupation",
    "validity_period"
]

# Indonesian religions
INDONESIAN_RELIGIONS = [
    "Islam",
    "Kristen",
    "Katolik",
    "Hindu",
    "Buddha",
    "Konghucu"
]

# Indonesian marital status options
INDONESIAN_MARITAL_STATUS = [
    "Belum Kawin",
    "Kawin",
    "Cerai Hidup",
    "Cerai Mati"
]


# ============================================================================
# KTP DATA MODELS
# ============================================================================

class KTPData:
    """
    Represents the extracted information from Indonesian ID cards.
    """
    
    def __init__(self,
                 nik: Optional[str] = None,
                 name: Optional[str] = None,
                 place_of_birth: Optional[str] = None,
                 date_of_birth: Optional[str] = None,
                 gender: Optional[str] = None,
                 address: Optional[str] = None,
                 religion: Optional[str] = None,
                 marital_status: Optional[str] = None,
                 occupation: Optional[str] = None,
                 validity_period: Optional[str] = None,
                 image_path: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.nik = nik
        self.name = name
        self.place_of_birth = place_of_birth
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.address = address
        self.religion = religion
        self.marital_status = marital_status
        self.occupation = occupation
        self.validity_period = validity_period
        self.image_path = image_path
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert KTPData to dictionary."""
        return {
            "id": self.id,
            "nik": self.nik,
            "name": self.name,
            "place_of_birth": self.place_of_birth,
            "date_of_birth": self.date_of_birth,
            "gender": self.gender,
            "address": self.address,
            "religion": self.religion,
            "marital_status": self.marital_status,
            "occupation": self.occupation,
            "validity_period": self.validity_period,
            "image_path": self.image_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KTPData':
        """Create KTPData from dictionary."""
        ktp = cls()
        ktp.id = data.get("id", str(uuid.uuid4()))
        ktp.nik = data.get("nik")
        ktp.name = data.get("name")
        ktp.place_of_birth = data.get("place_of_birth")
        ktp.date_of_birth = data.get("date_of_birth")
        ktp.gender = data.get("gender")
        ktp.address = data.get("address")
        ktp.religion = data.get("religion")
        ktp.marital_status = data.get("marital_status")
        ktp.occupation = data.get("occupation")
        ktp.validity_period = data.get("validity_period")
        ktp.image_path = data.get("image_path")
        ktp.created_at = data.get("created_at", datetime.now().isoformat())
        ktp.updated_at = data.get("updated_at", ktp.created_at)
        return ktp
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate KTP data fields."""
        errors = []
        warnings = []
        
        # Validate NIK (16 digits)
        if self.nik:
            if not self.nik.isdigit() or len(self.nik) != 16:
                errors.append("NIK must be exactly 16 digits")
            # Additional NIK validation checks
            elif self.nik[0:6] == "000000":
                warnings.append("NIK province code appears invalid (000000)")
            elif self.nik[6:8] == "00":
                warnings.append("NIK regency code appears invalid (00)")
            elif self.nik[8:12] == "0000":
                warnings.append("NIK district code appears invalid (0000)")
        else:
            errors.append("NIK is required")
        
        # Validate required fields
        if not self.name or len(self.name.strip()) < 3:
            errors.append("Name is required and must be at least 3 characters")
        elif len(self.name) > 100:
            warnings.append("Name is unusually long (>100 characters)")
        
        if not self.place_of_birth or len(self.place_of_birth.strip()) < 3:
            errors.append("Place of birth is required and must be at least 3 characters")
        
        if not self.date_of_birth:
            errors.append("Date of birth is required")
        else:
            # Try multiple date formats
            date_valid, date_errors = _validate_date(self.date_of_birth, "Date of birth")
            if not date_valid:
                errors.extend(date_errors)
        
        # Validate gender
        if not self.gender:
            errors.append("Gender is required")
        elif self.gender not in ["Laki-laki", "Perempuan"]:
            errors.append("Gender must be 'Laki-laki' or 'Perempuan'")
        
        if not self.address or len(self.address.strip()) < 10:
            errors.append("Address is required and must be at least 10 characters")
        
        # Validate religion
        if self.religion and self.religion not in INDONESIAN_RELIGIONS:
            warnings.append(f"Religion '{self.religion}' is not one of the recognized Indonesian religions")
        
        # Validate marital status
        if self.marital_status and self.marital_status not in INDONESIAN_MARITAL_STATUS:
            warnings.append(f"Marital status '{self.marital_status}' is not one of the recognized statuses")
        
        # Validate validity period
        if self.validity_period:
            date_valid, date_errors = _validate_date(self.validity_period, "Validity period", allow_past=True)
            if not date_valid:
                warnings.extend(date_errors)
        
        # Validate RT/RW format
        if hasattr(self, 'rt_rw') and self.rt_rw:
            if not re.match(r'^\d+/\d+$', self.rt_rw):
                warnings.append("RT/RW format should be 'RT/RW' (e.g., '001/002')")
        
        # Return errors and warnings
        all_messages = errors + warnings
        
        # If there are any errors, return False with all messages
        if errors:
            return (False, all_messages)
        
        # If only warnings, return True but include warnings
        if warnings:
            return (True, all_messages)
        
        # All good
        return (True, [])
    
    def get_validation_status(self) -> Dict[str, Any]:
        """
        Get detailed validation status for each field.
        
        Returns:
            Dictionary with validation status for each field
        """
        status = {
            "nik": {"valid": True, "message": ""},
            "name": {"valid": True, "message": ""},
            "place_of_birth": {"valid": True, "message": ""},
            "date_of_birth": {"valid": True, "message": ""},
            "gender": {"valid": True, "message": ""},
            "address": {"valid": True, "message": ""},
            "religion": {"valid": True, "message": ""},
            "marital_status": {"valid": True, "message": ""},
            "validity_period": {"valid": True, "message": ""},
            "rt_rw": {"valid": True, "message": ""}
        }
        
        # Validate NIK
        if not self.nik:
            status["nik"]["valid"] = False
            status["nik"]["message"] = "NIK is required"
        elif not self.nik.isdigit() or len(self.nik) != 16:
            status["nik"]["valid"] = False
            status["nik"]["message"] = "NIK must be exactly 16 digits"
        elif self.nik[0:6] == "000000":
            status["nik"]["valid"] = False
            status["nik"]["message"] = "NIK province code appears invalid"
        
        # Validate Name
        if not self.name or len(self.name.strip()) < 3:
            status["name"]["valid"] = False
            status["name"]["message"] = "Name is required and must be at least 3 characters"
        
        # Validate Place of Birth
        if not self.place_of_birth or len(self.place_of_birth.strip()) < 3:
            status["place_of_birth"]["valid"] = False
            status["place_of_birth"]["message"] = "Place of birth is required and must be at least 3 characters"
        
        # Validate Date of Birth
        if not self.date_of_birth:
            status["date_of_birth"]["valid"] = False
            status["date_of_birth"]["message"] = "Date of birth is required"
        else:
            date_valid, date_errors = _validate_date(self.date_of_birth, "Date of birth")
            if not date_valid:
                status["date_of_birth"]["valid"] = False
                status["date_of_birth"]["message"] = "; ".join(date_errors)
        
        # Validate Gender
        if not self.gender:
            status["gender"]["valid"] = False
            status["gender"]["message"] = "Gender is required"
        elif self.gender not in ["Laki-laki", "Perempuan"]:
            status["gender"]["valid"] = False
            status["gender"]["message"] = "Gender must be 'Laki-laki' or 'Perempuan'"
        
        # Validate Address
        if not self.address or len(self.address.strip()) < 10:
            status["address"]["valid"] = False
            status["address"]["message"] = "Address is required and must be at least 10 characters"
        
        # Validate Religion
        if self.religion and self.religion not in INDONESIAN_RELIGIONS:
            status["religion"]["valid"] = False
            status["religion"]["message"] = f"Religion '{self.religion}' is not recognized"
        
        # Validate Marital Status
        if self.marital_status and self.marital_status not in INDONESIAN_MARITAL_STATUS:
            status["marital_status"]["valid"] = False
            status["marital_status"]["message"] = f"Marital status '{self.marital_status}' is not recognized"
        
        # Validate Validity Period
        if self.validity_period:
            date_valid, date_errors = _validate_date(self.validity_period, "Validity period", allow_past=True)
            if not date_valid:
                status["validity_period"]["valid"] = False
                status["validity_period"]["message"] = "; ".join(date_errors)
        
        # Validate RT/RW
        if hasattr(self, 'rt_rw') and self.rt_rw:
            if not re.match(r'^\d+/\d+$', self.rt_rw):
                status["rt_rw"]["valid"] = False
                status["rt_rw"]["message"] = "RT/RW format should be 'RT/RW' (e.g., '001/002')"
        
        return status


class ExtractionConfidence:
    """
    Represents confidence scores for each extracted data field.
    """
    
    def __init__(self, ktp_data_id: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.ktp_data_id = ktp_data_id
        self.field_confidence = {}
        self.overall_confidence = 0.0
        self.extraction_method = "tesseract"
        self.created_at = datetime.now().isoformat()
    
    def set_field_confidence(self, field_name: str, confidence_score: float):
        """Set confidence score for a specific field."""
        if 0.0 <= confidence_score <= 1.0:
            self.field_confidence[field_name] = confidence_score
            self._calculate_overall_confidence()
        else:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
    
    def get_field_confidence(self, field_name: str) -> Optional[float]:
        """Get confidence score for a specific field."""
        return self.field_confidence.get(field_name)
    
    def _calculate_overall_confidence(self):
        """Calculate overall confidence from field confidences."""
        if self.field_confidence:
            self.overall_confidence = sum(self.field_confidence.values()) / len(self.field_confidence)
        else:
            self.overall_confidence = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ExtractionConfidence to dictionary."""
        return {
            "id": self.id,
            "ktp_data_id": self.ktp_data_id,
            "field_confidence": self.field_confidence,
            "overall_confidence": self.overall_confidence,
            "extraction_method": self.extraction_method,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractionConfidence':
        """Create ExtractionConfidence from dictionary."""
        confidence = cls(data.get("ktp_data_id"))
        confidence.id = data.get("id", str(uuid.uuid4()))
        confidence.field_confidence = data.get("field_confidence", {})
        confidence.overall_confidence = data.get("overall_confidence", 0.0)
        confidence.extraction_method = data.get("extraction_method", "tesseract")
        confidence.created_at = data.get("created_at", datetime.now().isoformat())
        return confidence


class DocumentTemplate:
    """
    Represents predefined document structures with field placeholders.
    """
    
    def __init__(self,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 template_type: Optional[str] = None,
                 file_path: Optional[str] = None,
                 output_format: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.template_type = template_type
        self.file_path = file_path
        self.output_format = output_format
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DocumentTemplate to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type,
            "file_path": self.file_path,
            "output_format": self.output_format,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentTemplate':
        """Create DocumentTemplate from dictionary."""
        template = cls()
        template.id = data.get("id", str(uuid.uuid4()))
        template.name = data.get("name")
        template.description = data.get("description")
        template.template_type = data.get("template_type")
        template.file_path = data.get("file_path")
        template.output_format = data.get("output_format")
        template.created_at = data.get("created_at", datetime.now().isoformat())
        template.updated_at = data.get("updated_at", template.created_at)
        return template
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate document template."""
        errors = []
        
        if not self.name:
            errors.append("Template name is required")
        
        if not self.template_type:
            errors.append("Template type is required")
        
        if self.output_format and self.output_format not in ["DOCX", "PDF"]:
            errors.append("Output format must be 'DOCX' or 'PDF'")
        
        if self.file_path and not os.path.exists(self.file_path):
            errors.append(f"Template file not found: {self.file_path}")
        
        return (len(errors) == 0, errors)


class FieldMapping:
    """
    Represents the association between extracted KTP data fields and template field locations.
    """
    
    def __init__(self,
                 template_id: Optional[str] = None,
                 ktp_field: Optional[str] = None,
                 template_field: Optional[str] = None,
                 position_x: Optional[int] = None,
                 position_y: Optional[int] = None):
        self.id = str(uuid.uuid4())
        self.template_id = template_id
        self.ktp_field = ktp_field
        self.template_field = template_field
        self.position_x = position_x
        self.position_y = position_y
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FieldMapping to dictionary."""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "ktp_field": self.ktp_field,
            "template_field": self.template_field,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldMapping':
        """Create FieldMapping from dictionary."""
        mapping = cls()
        mapping.id = data.get("id", str(uuid.uuid4()))
        mapping.template_id = data.get("template_id")
        mapping.ktp_field = data.get("ktp_field")
        mapping.template_field = data.get("template_field")
        mapping.position_x = data.get("position_x")
        mapping.position_y = data.get("position_y")
        mapping.created_at = data.get("created_at", datetime.now().isoformat())
        return mapping


class GeneratedDocument:
    """
    Represents the final output document with KTP data populated in template fields.
    """
    
    def __init__(self,
                 template_id: Optional[str] = None,
                 ktp_data_id: Optional[str] = None,
                 file_path: Optional[str] = None,
                 output_format: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.template_id = template_id
        self.ktp_data_id = ktp_data_id
        self.file_path = file_path
        self.output_format = output_format
        self.status = "draft"
        self.created_at = datetime.now().isoformat()
        self.download_count = 0
    
    def mark_as_completed(self):
        """Mark document as completed."""
        self.status = "completed"
    
    def mark_as_error(self, error_message: str):
        """Mark document as having an error."""
        self.status = f"error: {error_message}"
    
    def increment_download_count(self):
        """Increment the download count."""
        self.download_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert GeneratedDocument to dictionary."""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "ktp_data_id": self.ktp_data_id,
            "file_path": self.file_path,
            "output_format": self.output_format,
            "status": self.status,
            "created_at": self.created_at,
            "download_count": self.download_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratedDocument':
        """Create GeneratedDocument from dictionary."""
        doc = cls()
        doc.id = data.get("id", str(uuid.uuid4()))
        doc.template_id = data.get("template_id")
        doc.ktp_data_id = data.get("ktp_data_id")
        doc.file_path = data.get("file_path")
        doc.output_format = data.get("output_format")
        doc.status = data.get("status", "draft")
        doc.created_at = data.get("created_at", datetime.now().isoformat())
        doc.download_count = data.get("download_count", 0)
        return doc


# ============================================================================
# FIELD MAPPING INTERFACE AND DATA STRUCTURES
# ============================================================================

class FieldMappingManager:
    """
    Manages field mappings between KTP data and document templates.
    """
    
    def __init__(self):
        self.mappings = {}
    
    def create_mapping(self, template_id: str, ktp_field: str, template_field: str,
                      position_x: Optional[int] = None, position_y: Optional[int] = None) -> FieldMapping:
        """
        Create a new field mapping.
        
        Args:
            template_id: ID of the template
            ktp_field: KTP field name
            template_field: Template field name
            position_x: X position in template (optional)
            position_y: Y position in template (optional)
             
        Returns:
            FieldMapping object
        """
        mapping = FieldMapping(
            template_id=template_id,
            ktp_field=ktp_field,
            template_field=template_field,
            position_x=position_x,
            position_y=position_y
        )
        return mapping
    
    def save_mapping(self, mapping: FieldMapping) -> Tuple[bool, str]:
        """
        Save a field mapping to storage.
        
        Args:
            mapping: FieldMapping object to save
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create mappings directory if it doesn't exist
            os.makedirs(MAPPINGS_DIR, exist_ok=True)
            
            # Create mapping file
            mapping_file = os.path.join(MAPPINGS_DIR, f"{mapping.id}.json")
            
            # Save mapping
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping.to_dict(), f, ensure_ascii=False, indent=2)
            
            return (True, f"Field mapping saved successfully")
        
        except Exception as e:
            return (False, f"Error saving field mapping: {str(e)}")
    
    def load_mapping(self, mapping_id: str) -> Tuple[Optional[FieldMapping], str]:
        """
        Load a field mapping by ID.
        
        Args:
            mapping_id: ID of the mapping to load
            
        Returns:
            Tuple of (mapping, error_message)
        """
        try:
            mapping_file = os.path.join(MAPPINGS_DIR, f"{mapping_id}.json")
            
            if not os.path.exists(mapping_file):
                return (None, f"Field mapping with ID {mapping_id} not found")
            
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
            
            mapping = FieldMapping.from_dict(mapping_data)
            return (mapping, "")
        
        except Exception as e:
            return (None, f"Error loading field mapping: {str(e)}")
    
    def get_template_mappings(self, template_id: str) -> List[FieldMapping]:
        """
        Get all field mappings for a template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            List of FieldMapping objects
        """
        mappings = []
        
        try:
            # Create mappings directory if it doesn't exist
            os.makedirs(MAPPINGS_DIR, exist_ok=True)
            
            # Get all JSON files in mappings directory
            for file_name in os.listdir(MAPPINGS_DIR):
                if file_name.endswith('.json'):
                    mapping_id = file_name[:-5]  # Remove .json extension
                    mapping, error = self.load_mapping(mapping_id)
                    
                    if mapping and not error and mapping.template_id == template_id:
                        mappings.append(mapping)
        
        except Exception as e:
            print(f"Error getting template mappings: {str(e)}")
        
        return mappings
    
    def delete_mapping(self, mapping_id: str) -> Tuple[bool, str]:
        """
        Delete a field mapping.
        
        Args:
            mapping_id: ID of the mapping to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            mapping_file = os.path.join(MAPPINGS_DIR, f"{mapping_id}.json")
            
            if os.path.exists(mapping_file):
                os.remove(mapping_file)
                return (True, f"Field mapping deleted successfully")
            else:
                return (False, f"Field mapping with ID {mapping_id} not found")
        
        except Exception as e:
            return (False, f"Error deleting field mapping: {str(e)}")
    
    def create_default_mappings(self, template_id: str, template_placeholders: List[str]) -> List[FieldMapping]:
        """
        Create default field mappings for a template based on placeholder names.
        
        Args:
            template_id: ID of the template
            template_placeholders: List of placeholder names in the template
            
        Returns:
            List of created FieldMapping objects
        """
        mappings = []
        
        try:
            for placeholder in template_placeholders:
                # Check if placeholder matches a KTP field
                if placeholder in KTP_FIELDS:
                    mapping = self.create_mapping(
                        template_id=template_id,
                        ktp_field=placeholder,
                        template_field=placeholder
                    )
                    
                    # Save mapping
                    success, message = self.save_mapping(mapping)
                    if success:
                        mappings.append(mapping)
                    else:
                        print(f"Error saving mapping: {message}")
        
        except Exception as e:
            print(f"Error creating default mappings: {str(e)}")
        
        return mappings
    
    def apply_mappings(self, ktp_data: KTPData, mappings: List[FieldMapping]) -> Dict[str, Any]:
        """
        Apply field mappings to KTP data.
        
        Args:
            ktp_data: KTPData object
            mappings: List of FieldMapping objects
            
        Returns:
            Dictionary with mapped data
        """
        mapped_data = {}
        
        try:
            # Convert KTPData to dictionary
            ktp_dict = ktp_data.to_dict()
            
            # Apply mappings
            for mapping in mappings:
                if mapping.ktp_field in ktp_dict:
                    mapped_data[mapping.template_field] = ktp_dict[mapping.ktp_field]
        
        except Exception as e:
            print(f"Error applying mappings: {str(e)}")
        
        return mapped_data
    
    def validate_mapping(self, mapping: FieldMapping) -> Tuple[bool, List[str]]:
        """
        Validate a field mapping.
        
        Args:
            mapping: FieldMapping object to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check if KTP field is valid
        if mapping.ktp_field not in KTP_FIELDS:
            errors.append(f"Invalid KTP field: {mapping.ktp_field}")
        
        # Check if template field is provided
        if not mapping.template_field:
            errors.append("Template field is required")
        
        # Check if template ID is provided
        if not mapping.template_id:
            errors.append("Template ID is required")
        
        return (len(errors) == 0, errors)


# ============================================================================
# TEMPLATE VALIDATION AND COMPATIBILITY CHECKING
# ============================================================================

class TemplateValidator:
    """
    Validates document templates and checks compatibility with KTP data.
    """
    
    def validate_template_compatibility(self, template_id: str, ktp_data: KTPData) -> Tuple[bool, List[str]]:
        """
        Validate template compatibility with KTP data.
        
        Args:
            template_id: ID of the template
            ktp_data: KTPData object
            
        Returns:
            Tuple of (is_compatible, messages)
        """
        messages = []
        
        try:
            # Load template
            from helpers import document_gen
            template, error = document_gen.load_template_by_id(template_id)
            
            if error:
                return (False, [f"Error loading template: {error}"])
            
            # Get template placeholders
            placeholders, error = document_gen.get_template_placeholders(template_id)
            
            if error:
                return (False, [f"Error getting placeholders: {error}"])
            
            # Check if template has placeholders
            if not placeholders:
                messages.append("Template has no placeholders")
                return (len(messages) == 0, messages)
            
            # Get KTP data fields
            ktp_dict = ktp_data.to_dict()
            ktp_fields = list(ktp_dict.keys())
            
            # Check for missing required fields
            missing_fields = []
            for placeholder in placeholders:
                if placeholder in KTP_FIELDS and placeholder not in ktp_fields or not ktp_dict.get(placeholder):
                    missing_fields.append(placeholder)
            
            if missing_fields:
                messages.append(f"Missing KTP data for fields: {', '.join(missing_fields)}")
            
            # Check for unmapped template fields
            unmapped_fields = []
            for placeholder in placeholders:
                if placeholder not in KTP_FIELDS:
                    unmapped_fields.append(placeholder)
            
            if unmapped_fields:
                messages.append(f"Template fields that don't match KTP fields: {', '.join(unmapped_fields)}")
            
            # Check if template file exists
            if template.file_path and not os.path.exists(template.file_path):
                messages.append(f"Template file not found: {template.file_path}")
            
            return (len(messages) == 0, messages)
        
        except Exception as e:
            return (False, [f"Error validating template compatibility: {str(e)}"])
    
    def suggest_field_mappings(self, template_id: str) -> List[Dict[str, Any]]:
        """
        Suggest field mappings for a template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            List of suggested mappings
        """
        suggestions = []
        
        try:
            # Load template
            from helpers import document_gen
            template, error = document_gen.load_template_by_id(template_id)
            
            if error:
                return suggestions
            
            # Get template placeholders
            placeholders, error = document_gen.get_template_placeholders(template_id)
            
            if error:
                return suggestions
            
            # Create suggestions for each placeholder
            for placeholder in placeholders:
                # Direct match
                if placeholder in KTP_FIELDS:
                    suggestions.append({
                        "template_field": placeholder,
                        "ktp_field": placeholder,
                        "confidence": 1.0,
                        "reason": "Direct field name match"
                    })
                else:
                    # Fuzzy matching
                    best_match = None
                    best_score = 0.0
                    
                    for ktp_field in KTP_FIELDS:
                        # Simple fuzzy matching based on common variations
                        score = self._calculate_field_similarity(placeholder, ktp_field)
                        if score > best_score and score > 0.5:  # Threshold for suggestions
                            best_match = ktp_field
                            best_score = score
                    
                    if best_match:
                        suggestions.append({
                            "template_field": placeholder,
                            "ktp_field": best_match,
                            "confidence": best_score,
                            "reason": f"Fuzzy match ({best_score:.2f})"
                        })
                    else:
                        # No match found
                        suggestions.append({
                            "template_field": placeholder,
                            "ktp_field": "",
                            "confidence": 0.0,
                            "reason": "No matching KTP field found"
                        })
        
        except Exception as e:
            print(f"Error suggesting field mappings: {str(e)}")
        
        return suggestions
    
    def _calculate_field_similarity(self, field1: str, field2: str) -> float:
        """
        Calculate similarity between two field names.
        
        Args:
            field1: First field name
            field2: Second field name
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Convert to lowercase for comparison
        f1 = field1.lower()
        f2 = field2.lower()
        
        # Direct match
        if f1 == f2:
            return 1.0
        
        # Check for common variations
        variations = {
            "nik": ["nomor_induk_kependudukan", "no_ktp", "nomor_ktp", "id_number"],
            "name": ["nama", "full_name", "nama_lengkap"],
            "place_of_birth": ["tempat_lahir", "birth_place", "pob"],
            "date_of_birth": ["tanggal_lahir", "birth_date", "dob"],
            "gender": ["jenis_kelamin", "sex"],
            "address": ["alamat"],
            "religion": ["agama"],
            "marital_status": ["status_perkawinan", "marital_status"],
            "occupation": ["pekerjaan", "job"],
            "validity_period": ["masa_berlaku", "expiry_date", "valid_until"]
        }
        
        # Check if field1 is a variation of field2
        for ktp_field, vars_list in variations.items():
            if ktp_field == f2 and f1 in vars_list:
                return 0.8
            elif ktp_field == f1 and f2 in vars_list:
                return 0.8
        
        # Check for partial matches
        if f1 in f2 or f2 in f1:
            return 0.6
        
        # No match
        return 0.0


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _validate_date(date_str: str, field_name: str, allow_past: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate a date string in multiple formats.
    
    Args:
        date_str: Date string to validate
        field_name: Name of the field for error messages
        allow_past: Whether past dates are allowed
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    date_valid = False
    date_formats = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            date_valid = True
            
            # Check if date is reasonable
            now = datetime.now()
            if parsed_date > now:
                errors.append(f"{field_name} cannot be in the future")
            elif not allow_past and (now - parsed_date).days > 365 * 120:  # 120 years
                errors.append(f"{field_name} indicates age over 120 years")
            break
        except ValueError:
            continue
    
    if not date_valid:
        errors.append(f"{field_name} must be in DD-MM-YYYY or DD/MM/YYYY format")
    
    return (date_valid, errors)


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

field_mapping_manager = FieldMappingManager()
template_validator = TemplateValidator()


# ============================================================================
# TESTING CODE
# ============================================================================

if __name__ == "__main__":
    """This is a constants file, not meant to be run directly.
    Only for testing purposes of this module."""
    print(LANGUAGES_SORTED.keys())
    print(FLAGS_SORTED.keys())
    print(DEFAULT_LANGUAGE_INDEX)
    
    # Test data models
    ktp = KTPData(
        nik="1234567890123456",
        name="Test User",
        address="Test Address"
    )
    print("KTP Data:", ktp.to_dict())
    
    confidence = ExtractionConfidence(ktp.id)
    confidence.set_field_confidence("nik", 0.95)
    confidence.set_field_confidence("name", 0.85)
    print("Extraction Confidence:", confidence.to_dict())
