"""
File-based storage functions for KTP data extraction and document population.

This module provides functions for storing and retrieving KTP data, templates,
and generated documents using a file-based storage system.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import uuid

import helpers.constants as constants


# ============================================================================
# KTP DATA STORAGE FUNCTIONS
# ============================================================================

def save_ktp_data(ktp_data: constants.KTPData, 
                  confidence: Optional[constants.ExtractionConfidence] = None) -> Tuple[bool, str]:
    """
    Save KTP data to file-based storage.
    
    Args:
        ktp_data: KTPData object to save
        confidence: Optional ExtractionConfidence object
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create file path
        file_path = os.path.join(constants.KTP_DATA_DIR, f"{ktp_data.id}.json")
        
        # Prepare data for storage
        data = {
            "ktp_data": ktp_data.to_dict(),
            "confidence": confidence.to_dict() if confidence else None
        }
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return (True, f"KTP data saved successfully with ID: {ktp_data.id}")
    
    except Exception as e:
        return (False, f"Error saving KTP data: {str(e)}")


def load_ktp_data(ktp_id: str) -> Tuple[Optional[constants.KTPData], Optional[constants.ExtractionConfidence], str]:
    """
    Load KTP data from file-based storage.
    
    Args:
        ktp_id: ID of the KTP data to load
        
    Returns:
        Tuple of (ktp_data, confidence, error_message)
    """
    try:
        # Create file path
        file_path = os.path.join(constants.KTP_DATA_DIR, f"{ktp_id}.json")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return (None, None, f"KTP data with ID {ktp_id} not found")
        
        # Read from file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create objects
        ktp_data = constants.KTPData.from_dict(data["ktp_data"])
        confidence = None
        if data.get("confidence"):
            confidence = constants.ExtractionConfidence.from_dict(data["confidence"])
        
        return (ktp_data, confidence, "")
    
    except Exception as e:
        return (None, None, f"Error loading KTP data: {str(e)}")


def list_ktp_data() -> List[Dict[str, Any]]:
    """
    List all stored KTP data.
    
    Returns:
        List of KTP data summaries
    """
    return _list_json_files(constants.KTP_DATA_DIR, _create_ktp_summary)


def delete_ktp_data(ktp_id: str) -> Tuple[bool, str]:
    """
    Delete KTP data from file-based storage.
    
    Args:
        ktp_id: ID of the KTP data to delete
        
    Returns:
        Tuple of (success, message)
    """
    return _delete_json_file(constants.KTP_DATA_DIR, ktp_id, "KTP data")


# ============================================================================
# TEMPLATE STORAGE FUNCTIONS
# ============================================================================

def save_template(template: constants.DocumentTemplate, 
                  field_mappings: Optional[List[constants.FieldMapping]] = None) -> Tuple[bool, str]:
    """
    Save document template to file-based storage.
    
    Args:
        template: DocumentTemplate object to save
        field_mappings: Optional list of FieldMapping objects
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create file path
        file_path = os.path.join(constants.TEMPLATES_DIR, f"{template.id}.json")
        
        # Prepare data for storage
        data = {
            "template": template.to_dict(),
            "field_mappings": [fm.to_dict() for fm in field_mappings] if field_mappings else []
        }
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return (True, f"Template saved successfully with ID: {template.id}")
    
    except Exception as e:
        return (False, f"Error saving template: {str(e)}")


def load_template(template_id: str) -> Tuple[Optional[constants.DocumentTemplate], List[constants.FieldMapping], str]:
    """
    Load document template from file-based storage.
    
    Args:
        template_id: ID of the template to load
        
    Returns:
        Tuple of (template, field_mappings, error_message)
    """
    try:
        # Create file path
        file_path = os.path.join(constants.TEMPLATES_DIR, f"{template_id}.json")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return (None, [], f"Template with ID {template_id} not found")
        
        # Read from file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create objects
        template = constants.DocumentTemplate.from_dict(data["template"])
        field_mappings = []
        for fm_data in data.get("field_mappings", []):
            field_mappings.append(constants.FieldMapping.from_dict(fm_data))
        
        return (template, field_mappings, "")
    
    except Exception as e:
        return (None, [], f"Error loading template: {str(e)}")


def list_templates() -> List[Dict[str, Any]]:
    """
    List all stored templates.
    
    Returns:
        List of template summaries
    """
    return _list_json_files(constants.TEMPLATES_DIR, _create_template_summary)


def delete_template(template_id: str) -> Tuple[bool, str]:
    """
    Delete document template from file-based storage.
    
    Args:
        template_id: ID of the template to delete
        
    Returns:
        Tuple of (success, message)
    """
    return _delete_json_file(constants.TEMPLATES_DIR, template_id, "Template")


# ============================================================================
# GENERATED DOCUMENT STORAGE FUNCTIONS
# ============================================================================

def save_generated_document(doc: constants.GeneratedDocument) -> Tuple[bool, str]:
    """
    Save generated document metadata to file-based storage.
    
    Args:
        doc: GeneratedDocument object to save
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create file path
        file_path = os.path.join(constants.GENERATED_DOCUMENTS_DIR, f"{doc.id}.json")
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(doc.to_dict(), f, ensure_ascii=False, indent=2)
        
        return (True, f"Generated document saved successfully with ID: {doc.id}")
    
    except Exception as e:
        return (False, f"Error saving generated document: {str(e)}")


def load_generated_document(doc_id: str) -> Tuple[Optional[constants.GeneratedDocument], str]:
    """
    Load generated document metadata from file-based storage.
    
    Args:
        doc_id: ID of the generated document to load
        
    Returns:
        Tuple of (document, error_message)
    """
    try:
        # Create file path
        file_path = os.path.join(constants.GENERATED_DOCUMENTS_DIR, f"{doc_id}.json")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return (None, f"Generated document with ID {doc_id} not found")
        
        # Read from file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create object
        doc = constants.GeneratedDocument.from_dict(data)
        
        return (doc, "")
    
    except Exception as e:
        return (None, f"Error loading generated document: {str(e)}")


def list_generated_documents() -> List[Dict[str, Any]]:
    """
    List all generated documents.
    
    Returns:
        List of generated document summaries
    """
    return _list_json_files(constants.GENERATED_DOCUMENTS_DIR, _create_document_summary)


def delete_generated_document(doc_id: str) -> Tuple[bool, str]:
    """
    Delete generated document from file-based storage.
    
    Args:
        doc_id: ID of the generated document to delete
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create file path
        metadata_path = os.path.join(constants.GENERATED_DOCUMENTS_DIR, f"{doc_id}.json")
        
        # Check if metadata file exists
        if not os.path.exists(metadata_path):
            return (False, f"Generated document with ID {doc_id} not found")
        
        # Load metadata to get file path
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Delete the actual document file if it exists
        doc_file_path = data.get("file_path")
        if doc_file_path and os.path.exists(doc_file_path):
            os.remove(doc_file_path)
        
        # Delete metadata file
        os.remove(metadata_path)
        
        return (True, f"Generated document with ID {doc_id} deleted successfully")
    
    except Exception as e:
        return (False, f"Error deleting generated document: {str(e)}")


# ============================================================================
# STORAGE MANAGEMENT FUNCTIONS
# ============================================================================

def get_storage_stats() -> Dict[str, Any]:
    """
    Get storage statistics.
    
    Returns:
        Dictionary with storage statistics
    """
    try:
        # Count files in each directory
        ktp_count = len([f for f in os.listdir(constants.KTP_DATA_DIR) if f.endswith('.json')])
        template_count = len([f for f in os.listdir(constants.TEMPLATES_DIR) if f.endswith('.json')])
        doc_count = len([f for f in os.listdir(constants.GENERATED_DOCUMENTS_DIR) if f.endswith('.json')])
        
        # Calculate directory sizes
        ktp_size = _calculate_directory_size(constants.KTP_DATA_DIR)
        template_size = _calculate_directory_size(constants.TEMPLATES_DIR)
        doc_size = _calculate_directory_size(constants.GENERATED_DOCUMENTS_DIR)
        
        return {
            "ktp_data": {
                "count": ktp_count,
                "size_bytes": ktp_size,
                "size_mb": round(ktp_size / (1024 * 1024), 2)
            },
            "templates": {
                "count": template_count,
                "size_bytes": template_size,
                "size_mb": round(template_size / (1024 * 1024), 2)
            },
            "generated_documents": {
                "count": doc_count,
                "size_bytes": doc_size,
                "size_mb": round(doc_size / (1024 * 1024), 2)
            },
            "total_size_bytes": ktp_size + template_size + doc_size,
            "total_size_mb": round((ktp_size + template_size + doc_size) / (1024 * 1024), 2)
        }
    
    except Exception as e:
        return {"error": f"Error getting storage stats: {str(e)}"}


def cleanup_old_data(days_old: int = 30) -> Tuple[int, str]:
    """
    Clean up old data from storage.
    
    Args:
        days_old: Age in days of data to clean up
        
    Returns:
        Tuple of (files_deleted, message)
    """
    try:
        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        # Clean up old KTP data
        deleted_count += _cleanup_old_files(constants.KTP_DATA_DIR, cutoff_date)
        
        # Clean up old generated documents
        deleted_count += _cleanup_old_documents(constants.GENERATED_DOCUMENTS_DIR, cutoff_date)
        
        return (deleted_count, f"Cleaned up {deleted_count} files older than {days_old} days")
    
    except Exception as e:
        return (0, f"Error cleaning up old data: {str(e)}")


def backup_storage(backup_path: str) -> Tuple[bool, str]:
    """
    Create a backup of the storage directory.
    
    Args:
        backup_path: Path where the backup will be created
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create backup directory if it doesn't exist
        os.makedirs(backup_path, exist_ok=True)
        
        # Copy data directory
        backup_data_path = os.path.join(backup_path, "data")
        if os.path.exists(backup_data_path):
            shutil.rmtree(backup_data_path)
        
        shutil.copytree(constants.DATA_DIR, backup_data_path)
        
        return (True, f"Storage backed up successfully to {backup_path}")
    
    except Exception as e:
        return (False, f"Error creating backup: {str(e)}")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _list_json_files(directory: str, summary_func) -> List[Dict[str, Any]]:
    """
    Generic function to list JSON files and create summaries.
    
    Args:
        directory: Directory to scan
        summary_func: Function to create summary from JSON data
        
    Returns:
        List of summaries
    """
    item_list = []
    
    try:
        # Get all JSON files in the directory
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                file_path = os.path.join(directory, filename)
                
                # Read file
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create summary
                summary = summary_func(data)
                item_list.append(summary)
    
    except Exception as e:
        print(f"Error listing items in {directory}: {str(e)}")
    
    return item_list


def _create_ktp_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a summary for KTP data.
    
    Args:
        data: JSON data
        
    Returns:
        KTP data summary
    """
    ktp_data = data.get("ktp_data", {})
    return {
        "id": ktp_data.get("id"),
        "nik": ktp_data.get("nik"),
        "name": ktp_data.get("name"),
        "created_at": ktp_data.get("created_at"),
        "updated_at": ktp_data.get("updated_at"),
        "overall_confidence": data.get("confidence", {}).get("overall_confidence", 0.0)
    }


def _create_template_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a summary for template data.
    
    Args:
        data: JSON data
        
    Returns:
        Template summary
    """
    template_data = data.get("template", {})
    return {
        "id": template_data.get("id"),
        "name": template_data.get("name"),
        "description": template_data.get("description"),
        "template_type": template_data.get("template_type"),
        "output_format": template_data.get("output_format"),
        "created_at": template_data.get("created_at"),
        "updated_at": template_data.get("updated_at"),
        "field_mappings_count": len(data.get("field_mappings", []))
    }


def _create_document_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a summary for generated document data.
    
    Args:
        data: JSON data
        
    Returns:
        Document summary
    """
    return {
        "id": data.get("id"),
        "template_id": data.get("template_id"),
        "ktp_data_id": data.get("ktp_data_id"),
        "output_format": data.get("output_format"),
        "status": data.get("status"),
        "created_at": data.get("created_at"),
        "download_count": data.get("download_count", 0)
    }


def _delete_json_file(directory: str, item_id: str, item_type: str) -> Tuple[bool, str]:
    """
    Generic function to delete a JSON file.
    
    Args:
        directory: Directory containing the file
        item_id: ID of the item to delete
        item_type: Type of item (for error messages)
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create file path
        file_path = os.path.join(directory, f"{item_id}.json")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return (False, f"{item_type} with ID {item_id} not found")
        
        # Delete file
        os.remove(file_path)
        
        return (True, f"{item_type} with ID {item_id} deleted successfully")
    
    except Exception as e:
        return (False, f"Error deleting {item_type}: {str(e)}")


def _calculate_directory_size(directory: str) -> int:
    """
    Calculate the total size of a directory in bytes.
    
    Args:
        directory: Directory to calculate size for
        
    Returns:
        Total size in bytes
    """
    return sum(
        os.path.getsize(os.path.join(directory, f))
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
    )


def _cleanup_old_files(directory: str, cutoff_date: float) -> int:
    """
    Clean up old JSON files in a directory.
    
    Args:
        directory: Directory to clean
        cutoff_date: Timestamp cutoff date
        
    Returns:
        Number of files deleted
    """
    deleted_count = 0
    
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            if os.path.getmtime(file_path) < cutoff_date:
                os.remove(file_path)
                deleted_count += 1
    
    return deleted_count


def _cleanup_old_documents(directory: str, cutoff_date: float) -> int:
    """
    Clean up old generated documents and their files.
    
    Args:
        directory: Directory to clean
        cutoff_date: Timestamp cutoff date
        
    Returns:
        Number of files deleted
    """
    deleted_count = 0
    
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            if os.path.getmtime(file_path) < cutoff_date:
                # Also delete the actual document file
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                doc_file_path = data.get("file_path")
                if doc_file_path and os.path.exists(doc_file_path):
                    os.remove(doc_file_path)
                
                # Delete metadata
                os.remove(file_path)
                deleted_count += 1
    
    return deleted_count