"""
Document generation functions for KTP data extraction and document population.

This module provides functions for generating documents (PDF, DOCX) with extracted KTP data.
"""

import os
import uuid
import json
import time
import functools
import hashlib
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Any, Union
from concurrent.futures import ThreadPoolExecutor

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

import helpers.constants as constants


# Template handling functions

def load_template(template_path: str) -> Tuple[Dict[str, Any], str]:
    """
    Load a document template and extract its structure.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        Tuple of (template_data, error_message)
    """
    try:
        if not os.path.exists(template_path):
            return (None, f"Template file not found: {template_path}")
        
        # Determine template type from file extension
        file_ext = os.path.splitext(template_path)[1].lower()
        
        if file_ext == ".docx":
            return _load_docx_template(template_path)
        elif file_ext == ".pdf":
            return _load_pdf_template(template_path)
        else:
            return (None, f"Unsupported template format: {file_ext}")
    
    except Exception as e:
        return (None, f"Error loading template: {str(e)}")


def _load_docx_template(template_path: str) -> Tuple[Dict[str, Any], str]:
    """Load a DOCX template and extract placeholders."""
    try:
        doc = Document(template_path)
        
        # Extract text and identify placeholders
        placeholders = []
        for paragraph in doc.paragraphs:
            text = paragraph.text
            # Look for placeholders in {{placeholder}} format
            import re
            matches = re.findall(r'\{\{([^}]+)\}\}', text)
            for match in matches:
                placeholders.append({
                    "name": match.strip(),
                    "type": "text",
                    "context": "paragraph",
                    "original_text": text
                })
        
        # Check tables for placeholders
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text = cell.text
                    matches = re.findall(r'\{\{([^}]+)\}\}', text)
                    for match in matches:
                        placeholders.append({
                            "name": match.strip(),
                            "type": "text",
                            "context": "table",
                            "original_text": text
                        })
        
        template_data = {
            "type": "docx",
            "path": template_path,
            "placeholders": placeholders,
            "document": doc
        }
        
        return (template_data, "")
    
    except Exception as e:
        return (None, f"Error loading DOCX template: {str(e)}")


def _load_pdf_template(template_path: str) -> Tuple[Dict[str, Any], str]:
    """Load a PDF template (placeholder for future implementation)."""
    # PDF template handling is more complex and would require additional libraries
    # For now, we'll return a basic structure
    template_data = {
        "type": "pdf",
        "path": template_path,
        "placeholders": [],  # Would need PDF parsing to extract
        "document": None
    }
    
    return (template_data, "PDF template support is limited")


def validate_template(template_path: str, format_type: str = "auto") -> Tuple[bool, str]:
    """
    Validate a document template.
    
    Args:
        template_path: Path to the template file
        format_type: Template format type ('auto', 'docx', 'pdf')
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if file exists
        if not os.path.exists(template_path):
            return (False, f"Template file not found: {template_path}")
        
        # Auto-detect format if needed
        if format_type == "auto":
            file_ext = os.path.splitext(template_path)[1].lower()
            if file_ext == ".docx":
                format_type = "docx"
            elif file_ext == ".pdf":
                format_type = "pdf"
            else:
                return (False, f"Unsupported template format: {file_ext}")
        
        # Validate based on format
        if format_type == "docx":
            return _validate_docx_template(template_path)
        elif format_type == "pdf":
            return _validate_pdf_template(template_path)
        else:
            return (False, f"Unsupported format type: {format_type}")
    
    except Exception as e:
        return (False, f"Error validating template: {str(e)}")


def _validate_docx_template(template_path: str) -> Tuple[bool, str]:
    """Validate a DOCX template."""
    try:
        doc = Document(template_path)
        
        # Check if document has content
        if len(doc.paragraphs) == 0 and len(doc.tables) == 0:
            return (False, "Template appears to be empty")
        
        # Check for placeholders
        has_placeholders = False
        for paragraph in doc.paragraphs:
            if "{{" in paragraph.text and "}}" in paragraph.text:
                has_placeholders = True
                break
        
        if not has_placeholders:
            return (False, "No placeholders found in template. Use {{placeholder}} format.")
        
        return (True, "Template is valid")
    
    except Exception as e:
        return (False, f"Error validating DOCX template: {str(e)}")


def _validate_pdf_template(template_path: str) -> Tuple[bool, str]:
    """Validate a PDF template."""
    # Basic validation - just check if file exists and has content
    if os.path.getsize(template_path) == 0:
        return (False, "Template file is empty")
    
    return (True, "PDF template validation is limited")


# Document generation functions

def generate_document(template_path: str,
                     output_path: str,
                     data: Dict[str, Any],
                     format_type: str = "auto",
                     field_mappings: Optional[List[constants.FieldMapping]] = None) -> Tuple[bool, str]:
    """
    Generate a document from a template with extracted data.
    
    Args:
        template_path: Path to the template file
        output_path: Path where the generated document will be saved
        data: Dictionary containing the data to insert into the template
        format_type: Output format type ('auto', 'pdf', 'docx')
        field_mappings: Optional list of field mappings
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Auto-detect format if needed
        if format_type == "auto":
            file_ext = os.path.splitext(template_path)[1].lower()
            if file_ext == ".docx":
                format_type = "docx"
            elif file_ext == ".pdf":
                format_type = "pdf"
            else:
                return (False, f"Unsupported template format: {file_ext}")
        
        # Apply field mappings if provided
        if field_mappings:
            mapped_data = {}
            for mapping in field_mappings:
                if mapping.ktp_field in data:
                    mapped_data[mapping.template_field] = data[mapping.ktp_field]
            data = mapped_data
        
        # Generate document based on format
        if format_type == "docx":
            return _generate_docx_document(template_path, output_path, data)
        elif format_type == "pdf":
            return _generate_pdf_document(template_path, output_path, data)
        else:
            return (False, f"Unsupported format type: {format_type}")
    
    except Exception as e:
        return (False, f"Error generating document: {str(e)}")


def _generate_docx_document(template_path: str, output_path: str, data: Dict[str, Any]) -> Tuple[bool, str]:
    """Generate a DOCX document from a template."""
    try:
        # Check if template exists
        if template_path and os.path.exists(template_path) and template_path.endswith('.docx'):
            # Load template
            doc = Document(template_path)
            
            # Replace placeholders in paragraphs
            for paragraph in doc.paragraphs:
                original_text = paragraph.text
                new_text = original_text
                
                for key, value in data.items():
                    placeholder = f"{{{{{key}}}}}"
                    if placeholder in new_text:
                        new_text = new_text.replace(placeholder, str(value))
                
                # Update paragraph text if changed
                if new_text != original_text:
                    paragraph.text = new_text
            
            # Replace placeholders in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        original_text = cell.text
                        new_text = original_text
                        
                        for key, value in data.items():
                            placeholder = f"{{{{{key}}}}}"
                            if placeholder in new_text:
                                new_text = new_text.replace(placeholder, str(value))
                        
                        # Update cell text if changed
                        if new_text != original_text:
                            cell.text = new_text
            
            # Save the document
            doc.save(output_path)
            
            return (True, f"DOCX document generated successfully: {output_path}")
        else:
            # Create a new document from data
            return _generate_docx_from_data(output_path, data)
    
    except Exception as e:
        return (False, f"Error generating DOCX document: {str(e)}")


def _generate_docx_from_data(output_path: str, data: Dict[str, Any]) -> Tuple[bool, str]:
    """Generate a DOCX document from data."""
    try:
        # Create a new document
        doc = Document()
        
        # Add title
        title = doc.add_heading('Generated Document', 0)
        
        # Add data as a table
        if data:
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Field'
            hdr_cells[1].text = 'Value'
            
            for key, value in data.items():
                row_cells = table.add_row().cells
                row_cells[0].text = key.replace("_", " ").title()
                row_cells[1].text = str(value)
        
        # Add timestamp
        doc.add_paragraph(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save the document
        doc.save(output_path)
        
        return (True, f"DOCX document generated successfully: {output_path}")
    
    except Exception as e:
        return (False, f"Error generating DOCX from data: {str(e)}")


def _generate_pdf_document(template_path: str, output_path: str, data: Dict[str, Any]) -> Tuple[bool, str]:
    """Generate a PDF document from a template."""
    try:
        # Check if this is a template-based generation or a simple data table
        if template_path and os.path.exists(template_path) and template_path.endswith('.pdf'):
            # For actual PDF templates, we would need more complex PDF manipulation
            # For now, we'll create a simple PDF with the data
            return _generate_pdf_from_data(output_path, data)
        else:
            # Generate a simple PDF with the data
            return _generate_pdf_from_data(output_path, data)
    
    except Exception as e:
        return (False, f"Error generating PDF document: {str(e)}")


def _generate_pdf_from_data(output_path: str, data: Dict[str, Any]) -> Tuple[bool, str]:
    """Generate a PDF document from data."""
    try:
        # Create a new PDF document
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        
        # Get styles
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("Generated Document", title_style))
        story.append(Spacer(1, 12))
        
        # Add data as a table
        table_data = [["Field", "Value"]]
        for key, value in data.items():
            table_data.append([key.replace("_", " ").title(), str(value)])
        
        # Create table
        table = Table(table_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Add timestamp
        timestamp_style = ParagraphStyle(
            'Timestamp',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2  # Right alignment
        )
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", timestamp_style))
        
        # Build PDF
        doc.build(story)
        
        return (True, f"PDF document generated successfully: {output_path}")
    
    except Exception as e:
        return (False, f"Error generating PDF from data: {str(e)}")


def _generate_pdf_from_template(template_path: str, output_path: str, data: Dict[str, Any]) -> Tuple[bool, str]:
    """Generate a PDF document from a PDF template with data."""
    try:
        # This is a placeholder for PDF template manipulation
        # In a real implementation, you would use libraries like PyPDF2 or pdfrw
        # to manipulate the PDF template and insert data
        
        # For now, we'll create a simple PDF with the data
        return _generate_pdf_from_data(output_path, data)
    
    except Exception as e:
        return (False, f"Error generating PDF from template: {str(e)}")


def preview_document(template_path: str,
                    data: Dict[str, Any],
                    format_type: str = "auto",
                    field_mappings: Optional[List[constants.FieldMapping]] = None) -> Tuple[bytes, str]:
    """
    Generate a preview of a document with extracted data.
    
    Args:
        template_path: Path to the template file
        data: Dictionary containing the data to insert into the template
        format_type: Output format type ('auto', 'pdf', 'docx')
        field_mappings: Optional list of field mappings
        
    Returns:
        Tuple of (document_bytes, error_message)
    """
    try:
        # Create a temporary file for the preview
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf" if format_type == "pdf" else ".docx", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Generate the document
            success, message = generate_document(
                template_path=template_path,
                output_path=temp_path,
                data=data,
                format_type=format_type,
                field_mappings=field_mappings
            )
            
            if not success:
                return (None, message)
            
            # Read the generated file
            with open(temp_path, "rb") as f:
                document_bytes = f.read()
            
            return (document_bytes, "")
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        return (None, f"Error generating preview: {str(e)}")


def preview_document_with_annotations(template_path: str,
                                     data: Dict[str, Any],
                                     field_mappings: Optional[List[constants.FieldMapping]] = None) -> Tuple[bytes, str, Dict[str, Any]]:
    """
    Generate a preview of a document with annotations showing where data is placed.
    
    Args:
        template_path: Path to the template file
        data: Dictionary containing the data to insert into the template
        field_mappings: Optional list of field mappings
        
    Returns:
        Tuple of (document_bytes, error_message, annotation_info)
    """
    try:
        # Create a temporary file for the preview
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Apply field mappings if provided
            if field_mappings:
                mapped_data = {}
                for mapping in field_mappings:
                    if mapping.ktp_field in data:
                        mapped_data[mapping.template_field] = data[mapping.ktp_field]
                data = mapped_data
            
            # Generate the document
            success, message = generate_document(
                template_path=template_path,
                output_path=temp_path,
                data=data,
                format_type="pdf"
            )
            
            if not success:
                return (None, message, {})
            
            # Read the generated file
            with open(temp_path, "rb") as f:
                document_bytes = f.read()
            
            # Create annotation information
            annotation_info = {
                "template_path": template_path,
                "data_fields": list(data.keys()),
                "field_mappings": [m.to_dict() for m in field_mappings] if field_mappings else [],
                "data_values": {k: str(v)[:50] + "..." if len(str(v)) > 50 else str(v) for k, v in data.items()}
            }
            
            return (document_bytes, "", annotation_info)
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        return (None, f"Error generating annotated preview: {str(e)}", {})


def create_document_preview_html(template_path: str,
                                 data: Dict[str, Any],
                                 field_mappings: Optional[List[constants.FieldMapping]] = None) -> Tuple[str, str]:
    """
    Create an HTML preview of a document with highlighted fields.
    
    Args:
        template_path: Path to the template file
        data: Dictionary containing the data to insert into the template
        field_mappings: Optional list of field mappings
        
    Returns:
        Tuple of (html_content, error_message)
    """
    try:
        # Apply field mappings if provided
        if field_mappings:
            mapped_data = {}
            for mapping in field_mappings:
                if mapping.ktp_field in data:
                    mapped_data[mapping.template_field] = data[mapping.ktp_field]
            data = mapped_data
        
        # Load template
        template_data, error = load_template(template_path)
        
        if error:
            return (f"<p>Error loading template: {error}</p>", error)
        
        # Determine template type
        template_type = template_data.get("type", "").lower()
        
        # Create HTML preview based on template type
        if template_type == "docx":
            return _create_docx_preview_html(template_data, data)
        elif template_type == "pdf":
            return _create_pdf_preview_html(template_data, data)
        else:
            return ("<p>Unsupported template type for HTML preview</p>", "Unsupported template type")
    
    except Exception as e:
        return (f"<p>Error creating HTML preview: {str(e)}</p>", str(e))


def _create_docx_preview_html(template_data: Dict[str, Any], data: Dict[str, Any]) -> Tuple[str, str]:
    """Create an HTML preview for a DOCX template."""
    try:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Document Preview</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }
                .content { border: 1px solid #ccc; padding: 20px; min-height: 400px; }
                .placeholder { background-color: #ffeb3b; padding: 2px 4px; border-radius: 3px; }
                .field-mapping { margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #2196F3; }
                .field-name { font-weight: bold; color: #1976D2; }
                .field-value { color: #333; }
                .no-value { color: #999; font-style: italic; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Document Preview</h2>
                <p>This is a preview of how your data will appear in the document.</p>
            </div>
            <div class="content">
        """
        
        # Add content with placeholders highlighted
        if "document" in template_data:
            doc = template_data["document"]
            
            # Process paragraphs
            for paragraph in doc.paragraphs:
                text = paragraph.text
                # Replace placeholders with highlighted values
                for key, value in data.items():
                    placeholder = f"{{{{{key}}}}}"
                    if placeholder in text:
                        if value:
                            highlighted_value = f'<span class="placeholder">{value}</span>'
                            text = text.replace(placeholder, highlighted_value)
                        else:
                            highlighted_value = f'<span class="placeholder no-value">[No value for {key}]</span>'
                            text = text.replace(placeholder, highlighted_value)
                
                html_content += f"<p>{text}</p>"
            
            # Process tables
            for table in doc.tables:
                html_content += "<table border='1' style='border-collapse: collapse; width: 100%; margin: 10px 0;'>"
                
                for row in table.rows:
                    html_content += "<tr>"
                    for cell in row.cells:
                        text = cell.text
                        # Replace placeholders with highlighted values
                        for key, value in data.items():
                            placeholder = f"{{{{{key}}}}}"
                            if placeholder in text:
                                if value:
                                    highlighted_value = f'<span class="placeholder">{value}</span>'
                                    text = text.replace(placeholder, highlighted_value)
                                else:
                                    highlighted_value = f'<span class="placeholder no-value">[No value for {key}]</span>'
                                    text = text.replace(placeholder, highlighted_value)
                        
                        html_content += f"<td style='padding: 8px;'>{text}</td>"
                    html_content += "</tr>"
                
                html_content += "</table>"
        
        # Add field mapping summary
        html_content += """
            </div>
            <div class="header" style="margin-top: 20px;">
                <h3>Field Mapping Summary</h3>
            </div>
            <div class="content">
        """
        
        for key, value in data.items():
            if value:
                html_content += f"""
                <div class="field-mapping">
                    <span class="field-name">{key}:</span>
                    <span class="field-value">{value}</span>
                </div>
                """
            else:
                html_content += f"""
                <div class="field-mapping">
                    <span class="field-name">{key}:</span>
                    <span class="no-value">[No value provided]</span>
                </div>
                """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        return (html_content, "")
    
    except Exception as e:
        return (f"<p>Error creating DOCX preview: {str(e)}</p>", str(e))


def _create_pdf_preview_html(template_data: Dict[str, Any], data: Dict[str, Any]) -> Tuple[str, str]:
    """Create an HTML preview for a PDF template."""
    try:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Document Preview</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }
                .content { border: 1px solid #ccc; padding: 20px; min-height: 400px; }
                .field-mapping { margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #2196F3; }
                .field-name { font-weight: bold; color: #1976D2; }
                .field-value { color: #333; }
                .no-value { color: #999; font-style: italic; }
                .info { background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Document Preview</h2>
            </div>
            <div class="content">
                <div class="info">
                    <p><strong>Note:</strong> PDF templates cannot be previewed directly in HTML.
                    This preview shows the data that will be inserted into the PDF template.</p>
                </div>
                <h3>Data to be Inserted:</h3>
        """
        
        # Add field mapping summary
        for key, value in data.items():
            if value:
                html_content += f"""
                <div class="field-mapping">
                    <span class="field-name">{key}:</span>
                    <span class="field-value">{value}</span>
                </div>
                """
            else:
                html_content += f"""
                <div class="field-mapping">
                    <span class="field-name">{key}:</span>
                    <span class="no-value">[No value provided]</span>
                </div>
                """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        return (html_content, "")
    
    except Exception as e:
        return (f"<p>Error creating PDF preview: {str(e)}</p>", str(e))


def validate_document_preview(template_path: str,
                             data: Dict[str, Any],
                             field_mappings: Optional[List[constants.FieldMapping]] = None) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that a document can be generated with the provided data.
    
    Args:
        template_path: Path to the template file
        data: Dictionary containing the data to insert into the template
        field_mappings: Optional list of field mappings
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    try:
        # Check if template exists
        if not os.path.exists(template_path):
            errors.append(f"Template file not found: {template_path}")
            return (False, errors, warnings)
        
        # Load template
        template_data, error = load_template(template_path)
        
        if error:
            errors.append(f"Error loading template: {error}")
            return (False, errors, warnings)
        
        # Get template placeholders
        placeholders = [p["name"] for p in template_data.get("placeholders", [])]
        
        if not placeholders:
            warnings.append("Template has no placeholders")
            return (True, errors, warnings)
        
        # Apply field mappings if provided
        if field_mappings:
            mapped_data = {}
            for mapping in field_mappings:
                if mapping.ktp_field in data:
                    mapped_data[mapping.template_field] = data[mapping.ktp_field]
            data = mapped_data
        
        # Check for missing required fields
        missing_fields = []
        for placeholder in placeholders:
            if placeholder not in data or not data[placeholder]:
                missing_fields.append(placeholder)
        
        if missing_fields:
            warnings.append(f"Missing data for placeholders: {', '.join(missing_fields)}")
        
        # Check for extra data that won't be used
        unused_fields = []
        for key in data.keys():
            if key not in placeholders:
                unused_fields.append(key)
        
        if unused_fields:
            warnings.append(f"Data fields not used in template: {', '.join(unused_fields)}")
        
        # Try to generate a preview to validate the template
        preview_bytes, error = preview_document(template_path, data)
        
        if error:
            errors.append(f"Error generating preview: {error}")
            return (False, errors, warnings)
        
        return (True, errors, warnings)
    
    except Exception as e:
        errors.append(f"Error validating document preview: {str(e)}")
        return (False, errors, warnings)


# Integration with User Story 1 (KTP Data Extraction)

def extract_and_generate_document(ktp_image_path: str,
                                 template_id: str,
                                 field_mappings: Optional[List[constants.FieldMapping]] = None,
                                 output_format: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Extract KTP data from an image and generate a document in one operation.
        
        Args:
            ktp_image_path: Path to the KTP image file
            template_id: ID of the template to use
            field_mappings: Optional field mappings (will auto-generate if None)
            output_format: Optional output format (PDF or DOCX)
            
        Returns:
            Tuple of (success, message, output_file_path)
        """
        try:
            # Import here to avoid circular imports
            import helpers.tesseract as tesseract
            import helpers.opencv as opencv
            from PIL import Image as PILImage
            
            # Step 1: Load and preprocess KTP image
            image = opencv.load_image(ktp_image_path)
            if image is None:
                return (False, "Failed to load KTP image", None)
            
            # Apply KTP preprocessing
            processed_image = opencv.preprocess_ktp_image(
                img=image,
                enable_clahe=True,
                enable_shadow_removal=True,
                enable_sharpening=True,
                enable_auto_rotate=True,
                enable_adaptive_threshold=False
            )
            
            # Convert to PIL for OCR
            pil_image = opencv.convert_to_pil(processed_image)
            
            # Step 2: Extract KTP data using Tesseract
            ktp_config = tesseract.configure_tesseract_for_ktp()
            ktp_data_dict, error = tesseract.extract_ktp_data(
                image=pil_image,
                config=ktp_config
            )
            
            if error:
                return (False, f"KTP data extraction failed: {error}", None)
            
            if not ktp_data_dict:
                return (False, "No KTP data was extracted", None)
            
            # Create KTPData object
            ktp_data = constants.KTPData.from_dict(ktp_data_dict)
            ktp_data.image_path = ktp_image_path
            
            # Create ExtractionConfidence object
            ktp_confidence = constants.ExtractionConfidence(ktp_data.id)
            for field, confidence in ktp_data_dict.get('extraction_confidence', {}).items():
                ktp_confidence.set_field_confidence(field, confidence)
            
            # Step 3: Load template
            template, template_error = load_template_by_id(template_id)
            if template_error:
                return (False, f"Error loading template: {template_error}", None)
            
            # Step 4: Generate field mappings if not provided
            if not field_mappings:
                placeholders, error = get_template_placeholders(template_id)
                if error:
                    return (False, f"Error getting placeholders: {error}", None)
                
                # Create default mappings
                field_mappings = create_field_mapping_from_template(template.file_path)
                
                # Update template ID for mappings
                for mapping in field_mappings:
                    mapping.template_id = template_id
            
            # Step 5: Apply mappings to KTP data
            mapped_data = map_ktp_data_to_template(ktp_data, field_mappings)
            
            if not mapped_data:
                return (False, "No data to populate in document after mapping", None)
            
            # Step 6: Determine output format
            if not output_format:
                output_format = template.output_format
            
            # Step 7: Generate output file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_name = f"ktp_document_{timestamp}.{output_format.lower()}"
            output_path = os.path.join(constants.GENERATED_DOCUMENTS_DIR, output_file_name)
            
            # Step 8: Generate document
            success, message = generate_document(
                template_path=template.file_path,
                output_path=output_path,
                data=mapped_data,
                format_type=output_format.lower(),
                field_mappings=field_mappings
            )
            
            if not success:
                return (False, f"Document generation failed: {message}", None)
            
            # Step 9: Save KTP data for future use
            try:
                import helpers.storage as storage
                storage.save_ktp_data(ktp_data, ktp_confidence)
            except Exception as e:
                # Don't fail the whole operation if storage fails
                print(f"Warning: Failed to save KTP data: {str(e)}")
            
            return (True, f"Document generated successfully: {output_path}", output_path)
        
        except Exception as e:
            return (False, f"Error in extract and generate workflow: {str(e)}", None)
    
    
def validate_ktp_template_compatibility(ktp_data: constants.KTPData,
                                       template_id: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that KTP data is compatible with a template.
    
    Args:
        ktp_data: KTPData object
        template_id: ID of the template
        
    Returns:
        Tuple of (is_compatible, errors, warnings)
    """
    errors = []
    warnings = []
    
    try:
        # Load template
        template, error = load_template_by_id(template_id)
        if error:
            errors.append(f"Error loading template: {error}")
            return (False, errors, warnings)
        
        # Get template placeholders
        placeholders, error = get_template_placeholders(template_id)
        if error:
            errors.append(f"Error getting placeholders: {error}")
            return (False, errors, warnings)
        
        # Convert KTP data to dictionary
        ktp_dict = ktp_data.to_dict()
        
        # Check for missing required KTP fields
        missing_ktp_fields = []
        for field in constants.KTP_FIELDS:
            if field not in ktp_dict or not ktp_dict[field]:
                missing_ktp_fields.append(field)
        
        if missing_ktp_fields:
            warnings.append(f"Missing KTP data fields: {', '.join(missing_ktp_fields)}")
        
        # Check for template placeholders that can't be mapped
        unmapped_placeholders = []
        for placeholder in placeholders:
            if placeholder not in constants.KTP_FIELDS:
                unmapped_placeholders.append(placeholder)
        
        if unmapped_placeholders:
            warnings.append(f"Template placeholders that don't match KTP fields: {', '.join(unmapped_placeholders)}")
        
        # Check for missing template fields
        missing_template_fields = []
        for placeholder in placeholders:
            if placeholder in constants.KTP_FIELDS and (placeholder not in ktp_dict or not ktp_dict[placeholder]):
                missing_template_fields.append(placeholder)
        
        if missing_template_fields:
            errors.append(f"Missing KTP data for template fields: {', '.join(missing_template_fields)}")
        
        # Validate KTP data
        is_valid, validation_errors = ktp_data.validate()
        if not is_valid:
            errors.extend([f"KTP data validation: {error}" for error in validation_errors])
        
        return (len(errors) == 0, errors, warnings)
    
    except Exception as e:
        errors.append(f"Error validating compatibility: {str(e)}")
        return (False, errors, warnings)


def get_ktp_template_suggestions(ktp_data: constants.KTPData) -> List[Dict[str, Any]]:
    """
    Get template suggestions based on KTP data availability.
    
    Args:
        ktp_data: KTPData object
        
    Returns:
        List of template suggestions with compatibility scores
    """
    suggestions = []
    
    try:
        # Get all available templates
        templates = list_templates()
        
        # Convert KTP data to dictionary
        ktp_dict = ktp_data.to_dict()
        
        # Check each template for compatibility
        for template in templates:
            template_id = template["id"]
            template_name = template["name"]
            
            # Get template placeholders
            placeholders, error = get_template_placeholders(template_id)
            if error:
                continue
            
            # Calculate compatibility score
            compatible_placeholders = 0
            total_placeholders = len(placeholders)
            
            for placeholder in placeholders:
                if placeholder in constants.KTP_FIELDS and placeholder in ktp_dict and ktp_dict[placeholder]:
                    compatible_placeholders += 1
            
            # Calculate score (0-100)
            if total_placeholders > 0:
                compatibility_score = (compatible_placeholders / total_placeholders) * 100
            else:
                compatibility_score = 0
            
            # Add to suggestions if there's some compatibility
            if compatibility_score > 0:
                suggestions.append({
                    "template_id": template_id,
                    "template_name": template_name,
                    "template_format": template["output_format"],
                    "compatibility_score": compatibility_score,
                    "compatible_placeholders": compatible_placeholders,
                    "total_placeholders": total_placeholders
                })
        
        # Sort by compatibility score (highest first)
        suggestions.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        return suggestions
    
    except Exception as e:
        print(f"Error getting template suggestions: {str(e)}")
        return []


def create_ktp_workflow_session(ktp_data: constants.KTPData,
                               template_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a workflow session for KTP data extraction and document generation.
    
    Args:
        ktp_data: KTPData object
        template_id: Optional template ID to pre-select
        
    Returns:
        Dictionary with session information
    """
    session = {
        "session_id": str(uuid.uuid4()),
        "ktp_data": ktp_data.to_dict(),
        "created_at": datetime.now().isoformat(),
        "template_id": template_id,
        "status": "initialized"
    }
    
    # Get template suggestions if no template is pre-selected
    if not template_id:
        suggestions = get_ktp_template_suggestions(ktp_data)
        session["template_suggestions"] = suggestions
        
        # Auto-select the best template if available
        if suggestions:
            session["template_id"] = suggestions[0]["template_id"]
            session["auto_selected_template"] = True
        else:
            session["auto_selected_template"] = False
    else:
        # Validate compatibility with pre-selected template
        is_compatible, errors, warnings = validate_ktp_template_compatibility(ktp_data, template_id)
        session["template_compatibility"] = {
            "is_compatible": is_compatible,
            "errors": errors,
            "warnings": warnings
        }
    
    return session


# Template management functions

def create_sample_templates() -> Tuple[bool, str]:
    """
    Create sample document templates for testing.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        templates_dir = "templates"
        os.makedirs(templates_dir, exist_ok=True)
        
        # Create sample DOCX template
        docx_template_path = os.path.join(templates_dir, "sample_ktp_template.docx")
        _create_sample_docx_template(docx_template_path)
        
        return (True, f"Sample templates created in {templates_dir}")
    
    except Exception as e:
        return (False, f"Error creating sample templates: {str(e)}")


def _create_sample_docx_template(template_path: str):
    """Create a sample DOCX template with KTP placeholders."""
    doc = Document()
    
    # Add title
    title = doc.add_heading('KTP Data Form', 0)
    
    # Add placeholders
    doc.add_paragraph('Name: {{name}}')
    doc.add_paragraph('NIK: {{nik}}')
    doc.add_paragraph('Place of Birth: {{place_of_birth}}')
    doc.add_paragraph('Date of Birth: {{date_of_birth}}')
    doc.add_paragraph('Gender: {{gender}}')
    doc.add_paragraph('Address: {{address}}')
    doc.add_paragraph('Religion: {{religion}}')
    doc.add_paragraph('Marital Status: {{marital_status}}')
    doc.add_paragraph('Occupation: {{occupation}}')
    doc.add_paragraph('Validity Period: {{validity_period}}')
    
    # Add a table with placeholders
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Field'
    hdr_cells[1].text = 'Value'
    
    # Add more rows with placeholders
    row_cells = table.add_row().cells
    row_cells[0].text = '{{name}}'
    row_cells[1].text = '{{nik}}'
    
    # Save the template
    doc.save(template_path)


def get_template_info(template_path: str) -> Dict[str, Any]:
    """
    Get information about a template.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        Dictionary with template information
    """
    info = {
        "path": template_path,
        "exists": os.path.exists(template_path),
        "size": 0,
        "modified": None,
        "format": "",
        "placeholders": []
    }
    
    if info["exists"]:
        stat = os.stat(template_path)
        info["size"] = stat.st_size
        info["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        info["format"] = os.path.splitext(template_path)[1].lower()
        
        # Load template to get placeholders
        template_data, error = load_template(template_path)
        if template_data:
            info["placeholders"] = template_data.get("placeholders", [])
    
    return info


def map_ktp_data_to_template(ktp_data: constants.KTPData,
                             field_mappings: List[constants.FieldMapping]) -> Dict[str, Any]:
    """
    Map KTP data to template fields using field mappings.
    
    Args:
        ktp_data: KTPData object
        field_mappings: List of field mappings
        
    Returns:
        Dictionary with mapped data
    """
    mapped_data = {}
    
    # Convert KTPData to dictionary
    ktp_dict = ktp_data.to_dict()
    
    # Apply mappings
    for mapping in field_mappings:
        if mapping.ktp_field in ktp_dict:
            mapped_data[mapping.template_field] = ktp_dict[mapping.ktp_field]
    
    return mapped_data


def create_field_mapping_from_template(template_path: str) -> List[constants.FieldMapping]:
    """
    Create field mappings from template placeholders.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        List of FieldMapping objects
    """
    mappings = []
    
    try:
        # Load template
        template_data, error = load_template(template_path)
        if not template_data:
            return mappings
        
        # Create mappings for each placeholder
        for placeholder in template_data.get("placeholders", []):
            placeholder_name = placeholder["name"]
            
            # Check if placeholder matches a KTP field
            if placeholder_name in constants.KTP_FIELDS:
                mapping = constants.FieldMapping(
                    template_id="",  # Will be set when template is saved
                    ktp_field=placeholder_name,
                    template_field=placeholder_name
                )
                mappings.append(mapping)
    
    except Exception as e:
        print(f"Error creating field mappings: {str(e)}")
    
    return mappings


# Document Template Management Functions

def save_template(template: constants.DocumentTemplate) -> Tuple[bool, str]:
    """
    Save a document template to storage.
    
    Args:
        template: DocumentTemplate object to save
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create templates directory if it doesn't exist
        os.makedirs(constants.TEMPLATES_DIR, exist_ok=True)
        
        # Create template metadata file
        template_file = os.path.join(constants.TEMPLATES_DIR, f"{template.id}.json")
        
        # Save template metadata
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
        
        # Copy template file to templates directory if it exists elsewhere
        if template.file_path and os.path.exists(template.file_path):
            # Create a copy in the templates directory
            import shutil
            file_ext = os.path.splitext(template.file_path)[1]
            new_file_path = os.path.join(constants.TEMPLATES_DIR, f"{template.id}{file_ext}")
            shutil.copy2(template.file_path, new_file_path)
            
            # Update template file path
            template.file_path = new_file_path
            template.updated_at = datetime.now().isoformat()
            
            # Save updated template metadata
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
        
        return (True, f"Template '{template.name}' saved successfully")
    
    except Exception as e:
        return (False, f"Error saving template: {str(e)}")


def load_template_by_id(template_id: str) -> Tuple[Optional[constants.DocumentTemplate], str]:
    """
    Load a document template by ID.
    
    Args:
        template_id: ID of the template to load
        
    Returns:
        Tuple of (template, error_message)
    """
    try:
        template_file = os.path.join(constants.TEMPLATES_DIR, f"{template_id}.json")
        
        if not os.path.exists(template_file):
            return (None, f"Template with ID {template_id} not found")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        
        template = constants.DocumentTemplate.from_dict(template_data)
        return (template, "")
    
    except Exception as e:
        return (None, f"Error loading template: {str(e)}")


def list_templates() -> List[Dict[str, Any]]:
    """
    List all available document templates.
    
    Returns:
        List of template summaries
    """
    templates = []
    
    try:
        # Create templates directory if it doesn't exist
        os.makedirs(constants.TEMPLATES_DIR, exist_ok=True)
        
        # Get all JSON files in templates directory
        for file_name in os.listdir(constants.TEMPLATES_DIR):
            if file_name.endswith('.json'):
                template_id = file_name[:-5]  # Remove .json extension
                template, error = load_template_by_id(template_id)
                
                if template and not error:
                    # Create template summary
                    template_info = {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "template_type": template.template_type,
                        "output_format": template.output_format,
                        "created_at": template.created_at,
                        "updated_at": template.updated_at,
                        "file_exists": os.path.exists(template.file_path) if template.file_path else False
                    }
                    templates.append(template_info)
    
    except Exception as e:
        print(f"Error listing templates: {str(e)}")
    
    return templates


def delete_template(template_id: str) -> Tuple[bool, str]:
    """
    Delete a document template.
    
    Args:
        template_id: ID of the template to delete
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Load template to get file path
        template, error = load_template_by_id(template_id)
        
        if error:
            return (False, error)
        
        # Delete template metadata file
        template_file = os.path.join(constants.TEMPLATES_DIR, f"{template_id}.json")
        if os.path.exists(template_file):
            os.remove(template_file)
        
        # Delete template file if it exists
        if template.file_path and os.path.exists(template.file_path):
            os.remove(template.file_path)
        
        return (True, f"Template '{template.name}' deleted successfully")
    
    except Exception as e:
        return (False, f"Error deleting template: {str(e)}")


def create_template_from_file(file_path: str, name: str, description: str = "", template_type: str = "custom") -> Tuple[bool, str, Optional[constants.DocumentTemplate]]:
    """
    Create a new template from an uploaded file.
    
    Args:
        file_path: Path to the template file
        name: Name for the template
        description: Optional description
        template_type: Type of template
        
    Returns:
        Tuple of (success, message, template)
    """
    try:
        # Validate the template file
        is_valid, error = validate_template(file_path)
        if not is_valid:
            return (False, f"Template validation failed: {error}", None)
        
        # Determine output format from file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        output_format = file_ext[1:].upper()  # Remove dot and convert to uppercase
        
        # Create new template
        template = constants.DocumentTemplate(
            name=name,
            description=description,
            template_type=template_type,
            file_path=file_path,
            output_format=output_format
        )
        
        # Save template
        success, message = save_template(template)
        
        if success:
            return (True, message, template)
        else:
            return (False, message, None)
    
    except Exception as e:
        return (False, f"Error creating template: {str(e)}", None)


def get_template_placeholders(template_id: str) -> Tuple[List[str], str]:
    """
    Get placeholders from a template.
    
    Args:
        template_id: ID of the template
        
    Returns:
        Tuple of (placeholders, error_message)
    """
    try:
        # Load template
        template, error = load_template_by_id(template_id)
        
        if error:
            return ([], error)
        
        if not template.file_path:
            return ([], "Template file path not specified")
        
        # Load template data
        template_data, error = load_template(template.file_path)
        
        if error:
            return ([], error)
        
        # Extract placeholder names
        placeholders = []
        for placeholder in template_data.get("placeholders", []):
            placeholders.append(placeholder["name"])
        
        return (placeholders, "")
    
    except Exception as e:
        return ([], f"Error getting placeholders: {str(e)}")


def create_default_templates() -> Tuple[bool, str]:
    """
    Create default document templates for common use cases.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create templates directory if it doesn't exist
        os.makedirs(constants.TEMPLATES_DIR, exist_ok=True)
        
        # Create sample KTP form template
        sample_template_path = os.path.join(constants.TEMPLATES_DIR, "sample_ktp_template.docx")
        _create_sample_docx_template(sample_template_path)
        
        # Create template object
        template = constants.DocumentTemplate(
            name="Sample KTP Form",
            description="A sample form template for KTP data",
            template_type="form",
            file_path=sample_template_path,
            output_format="DOCX"
        )
        
        # Save template
        success, message = save_template(template)
        
        if success:
            return (True, "Default templates created successfully")
        else:
            return (False, f"Error saving default template: {message}")
    
    except Exception as e:
        return (False, f"Error creating default templates: {str(e)}")


# Template Validation and Compatibility Checking

def validate_template_structure(template_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate the structure of a document template.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    try:
        # Check if file exists
        if not os.path.exists(template_path):
            errors.append(f"Template file not found: {template_path}")
            return (False, errors, warnings)
        
        # Check file size
        file_size = os.path.getsize(template_path)
        if file_size == 0:
            errors.append("Template file is empty")
            return (False, errors, warnings)
        
        # Determine file type
        file_ext = os.path.splitext(template_path)[1].lower()
        
        if file_ext not in [".docx", ".pdf"]:
            errors.append(f"Unsupported template format: {file_ext}")
            return (False, errors, warnings)
        
        # Load template
        template_data, error = load_template(template_path)
        if error:
            errors.append(f"Error loading template: {error}")
            return (False, errors, warnings)
        
        # Check for placeholders
        placeholders = template_data.get("placeholders", [])
        if not placeholders:
            warnings.append("Template has no placeholders")
        else:
            # Validate placeholder format
            invalid_placeholders = []
            for placeholder in placeholders:
                placeholder_name = placeholder.get("name", "")
                if not placeholder_name:
                    invalid_placeholders.append("Empty placeholder name")
                elif not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', placeholder_name):
                    invalid_placeholders.append(f"Invalid placeholder name: {placeholder_name}")
            
            if invalid_placeholders:
                errors.append(f"Invalid placeholders: {', '.join(invalid_placeholders)}")
        
        # Format-specific validation
        if file_ext == ".docx":
            return _validate_docx_structure(template_data, errors, warnings)
        elif file_ext == ".pdf":
            return _validate_pdf_structure(template_data, errors, warnings)
        
        return (True, errors, warnings)
    
    except Exception as e:
        errors.append(f"Error validating template structure: {str(e)}")
        return (False, errors, warnings)


def _validate_docx_structure(template_data: Dict[str, Any], errors: List[str], warnings: List[str]) -> Tuple[bool, List[str], List[str]]:
    """Validate DOCX template structure."""
    try:
        doc = template_data.get("document")
        if not doc:
            errors.append("Invalid DOCX template structure")
            return (False, errors, warnings)
        
        # Check if document has content
        if len(doc.paragraphs) == 0 and len(doc.tables) == 0:
            warnings.append("Document appears to be empty")
        
        # Check for placeholder formatting
        placeholder_count = 0
        for paragraph in doc.paragraphs:
            if "{{" in paragraph.text and "}}" in paragraph.text:
                placeholder_count += 1
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if "{{" in cell.text and "}}" in cell.text:
                        placeholder_count += 1
        
        if placeholder_count == 0:
            warnings.append("No placeholders found in document")
        
        return (len(errors) == 0, errors, warnings)
    
    except Exception as e:
        errors.append(f"Error validating DOCX structure: {str(e)}")
        return (False, errors, warnings)


def _validate_pdf_structure(template_data: Dict[str, Any], errors: List[str], warnings: List[str]) -> Tuple[bool, List[str], List[str]]:
    """Validate PDF template structure."""
    try:
        # PDF validation is limited without additional libraries
        warnings.append("PDF template validation is limited")
        
        # Check if we can at least read the file
        if not template_data.get("document"):
            warnings.append("PDF template content could not be analyzed")
        
        return (len(errors) == 0, errors, warnings)
    
    except Exception as e:
        errors.append(f"Error validating PDF structure: {str(e)}")
        return (False, errors, warnings)


def check_template_ktp_compatibility(template_id: str) -> Tuple[bool, List[str], List[str], Dict[str, Any]]:
    """
    Check if a template is compatible with KTP data extraction.
    
    Args:
        template_id: ID of the template
        
    Returns:
        Tuple of (is_compatible, errors, warnings, compatibility_info)
    """
    errors = []
    warnings = []
    compatibility_info = {
        "template_id": template_id,
        "compatible_fields": [],
        "incompatible_fields": [],
        "missing_ktp_fields": [],
        "extra_template_fields": [],
        "compatibility_score": 0
    }
    
    try:
        # Load template
        template, error = load_template_by_id(template_id)
        if error:
            errors.append(f"Error loading template: {error}")
            return (False, errors, warnings, compatibility_info)
        
        # Get template placeholders
        placeholders, error = get_template_placeholders(template_id)
        if error:
            errors.append(f"Error getting placeholders: {error}")
            return (False, errors, warnings, compatibility_info)
        
        if not placeholders:
            warnings.append("Template has no placeholders")
            compatibility_info["compatibility_score"] = 0
            return (True, errors, warnings, compatibility_info)
        
        # Check each placeholder against KTP fields
        for placeholder in placeholders:
            if placeholder in constants.KTP_FIELDS:
                compatibility_info["compatible_fields"].append(placeholder)
            else:
                compatibility_info["incompatible_fields"].append(placeholder)
        
        # Check for missing KTP fields
        for ktp_field in constants.KTP_FIELDS:
            if ktp_field not in placeholders:
                compatibility_info["missing_ktp_fields"].append(ktp_field)
        
        # Check for extra template fields
        for placeholder in placeholders:
            if placeholder not in constants.KTP_FIELDS:
                compatibility_info["extra_template_fields"].append(placeholder)
        
        # Calculate compatibility score
        total_placeholders = len(placeholders)
        compatible_count = len(compatibility_info["compatible_fields"])
        
        if total_placeholders > 0:
            compatibility_info["compatibility_score"] = (compatible_count / total_placeholders) * 100
        
        # Determine compatibility
        if compatibility_info["compatibility_score"] >= 80:
            return (True, errors, warnings, compatibility_info)
        elif compatibility_info["compatibility_score"] >= 50:
            warnings.append(f"Template has partial compatibility ({compatibility_info['compatibility_score']:.1f}%)")
            return (True, errors, warnings, compatibility_info)
        else:
            errors.append(f"Template has low compatibility ({compatibility_info['compatibility_score']:.1f}%)")
            return (False, errors, warnings, compatibility_info)
    
    except Exception as e:
        errors.append(f"Error checking KTP compatibility: {str(e)}")
        return (False, errors, warnings, compatibility_info)


def validate_template_for_ktp_data(template_id: str, ktp_data: constants.KTPData) -> Tuple[bool, List[str], List[str], Dict[str, Any]]:
    """
    Validate that a template can be used with specific KTP data.
    
    Args:
        template_id: ID of the template
        ktp_data: KTPData object
        
    Returns:
        Tuple of (is_valid, errors, warnings, validation_info)
    """
    errors = []
    warnings = []
    validation_info = {
        "template_id": template_id,
        "ktp_data_id": ktp_data.id,
        "mappable_fields": [],
        "unmappable_template_fields": [],
        "missing_ktp_data": [],
        "unused_ktp_data": [],
        "validation_score": 0
    }
    
    try:
        # Load template
        template, error = load_template_by_id(template_id)
        if error:
            errors.append(f"Error loading template: {error}")
            return (False, errors, warnings, validation_info)
        
        # Get template placeholders
        placeholders, error = get_template_placeholders(template_id)
        if error:
            errors.append(f"Error getting placeholders: {error}")
            return (False, errors, warnings, validation_info)
        
        # Convert KTP data to dictionary
        ktp_dict = ktp_data.to_dict()
        
        # Check each placeholder
        for placeholder in placeholders:
            if placeholder in ktp_dict and ktp_dict[placeholder]:
                validation_info["mappable_fields"].append(placeholder)
            elif placeholder in ktp_dict:
                validation_info["missing_ktp_data"].append(placeholder)
            else:
                validation_info["unmappable_template_fields"].append(placeholder)
        
        # Check for unused KTP data
        for ktp_field in constants.KTP_FIELDS:
            if ktp_field in ktp_dict and ktp_dict[ktp_field] and ktp_field not in placeholders:
                validation_info["unused_ktp_data"].append(ktp_field)
        
        # Calculate validation score
        total_placeholders = len(placeholders)
        mappable_count = len(validation_info["mappable_fields"])
        
        if total_placeholders > 0:
            validation_info["validation_score"] = (mappable_count / total_placeholders) * 100
        
        # Generate warnings and errors
        if validation_info["missing_ktp_data"]:
            warnings.append(f"Template fields with missing KTP data: {', '.join(validation_info['missing_ktp_data'])}")
        
        if validation_info["unmappable_template_fields"]:
            errors.append(f"Template fields that don't match KTP data: {', '.join(validation_info['unmappable_template_fields'])}")
        
        if validation_info["unused_ktp_data"]:
            warnings.append(f"KTP data not used in template: {', '.join(validation_info['unused_ktp_data'])}")
        
        # Determine validity
        if validation_info["validation_score"] >= 80:
            return (True, errors, warnings, validation_info)
        elif validation_info["validation_score"] >= 50:
            warnings.append(f"Template has partial validation ({validation_info['validation_score']:.1f}%)")
            return (True, errors, warnings, validation_info)
        else:
            errors.append(f"Template validation failed ({validation_info['validation_score']:.1f}%)")
            return (False, errors, warnings, validation_info)
    
    except Exception as e:
        errors.append(f"Error validating template for KTP data: {str(e)}")
        return (False, errors, warnings, validation_info)


def get_template_validation_report(template_id: str) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report for a template.
    
    Args:
        template_id: ID of the template
        
    Returns:
        Dictionary with validation report
    """
    report = {
        "template_id": template_id,
        "timestamp": datetime.now().isoformat(),
        "structure_validation": {"status": "not_checked", "errors": [], "warnings": []},
        "ktp_compatibility": {"status": "not_checked", "errors": [], "warnings": [], "info": {}},
        "overall_status": "unknown"
    }
    
    try:
        # Load template
        template, error = load_template_by_id(template_id)
        if error:
            report["overall_status"] = "error"
            report["structure_validation"]["errors"].append(f"Error loading template: {error}")
            return report
        
        # Structure validation
        is_valid, errors, warnings = validate_template_structure(template.file_path)
        report["structure_validation"]["status"] = "valid" if is_valid else "invalid"
        report["structure_validation"]["errors"] = errors
        report["structure_validation"]["warnings"] = warnings
        
        # KTP compatibility check
        is_compatible, comp_errors, comp_warnings, comp_info = check_template_ktp_compatibility(template_id)
        report["ktp_compatibility"]["status"] = "compatible" if is_compatible else "incompatible"
        report["ktp_compatibility"]["errors"] = comp_errors
        report["ktp_compatibility"]["warnings"] = comp_warnings
        report["ktp_compatibility"]["info"] = comp_info
        
        # Overall status
        if is_valid and is_compatible:
            report["overall_status"] = "ready"
        elif is_valid and not is_compatible:
            report["overall_status"] = "needs_mapping"
        else:
            report["overall_status"] = "invalid"
        
        return report
    
    except Exception as e:
        report["overall_status"] = "error"
        report["structure_validation"]["errors"].append(f"Error generating report: {str(e)}")
        return report


# Document Status Tracking and History Functions

def save_document_status(document_id: str, status: str, message: str = "", metadata: Dict[str, Any] = None) -> Tuple[bool, str]:
    """
    Save document status and history.
    
    Args:
        document_id: ID of the document
        status: Status of the document (draft, preview, completed, error)
        message: Optional message describing the status
        metadata: Optional metadata to store with the status
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create status history file
        status_file = os.path.join(constants.GENERATED_DOCUMENTS_DIR, f"{document_id}_status.json")
        
        # Load existing status history if it exists
        status_history = []
        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as f:
                status_history = json.load(f)
        
        # Add new status entry
        status_entry = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        status_history.append(status_entry)
        
        # Save status history
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_history, f, ensure_ascii=False, indent=2)
        
        return (True, f"Document status saved: {status}")
    
    except Exception as e:
        return (False, f"Error saving document status: {str(e)}")


def get_document_status(document_id: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Get the latest status of a document.
    
    Args:
        document_id: ID of the document
        
    Returns:
        Tuple of (status_info, error_message)
    """
    try:
        # Create status history file path
        status_file = os.path.join(constants.GENERATED_DOCUMENTS_DIR, f"{document_id}_status.json")
        
        if not os.path.exists(status_file):
            return (None, f"Status file not found for document: {document_id}")
        
        # Load status history
        with open(status_file, 'r', encoding='utf-8') as f:
            status_history = json.load(f)
        
        if not status_history:
            return (None, f"No status history found for document: {document_id}")
        
        # Return the latest status
        latest_status = status_history[-1]
        return (latest_status, "")
    
    except Exception as e:
        return (None, f"Error getting document status: {str(e)}")


def get_document_history(document_id: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Get the complete status history of a document.
    
    Args:
        document_id: ID of the document
        
    Returns:
        Tuple of (status_history, error_message)
    """
    try:
        # Create status history file path
        status_file = os.path.join(constants.GENERATED_DOCUMENTS_DIR, f"{document_id}_status.json")
        
        if not os.path.exists(status_file):
            return ([], f"Status file not found for document: {document_id}")
        
        # Load status history
        with open(status_file, 'r', encoding='utf-8') as f:
            status_history = json.load(f)
        
        return (status_history, "")
    
    except Exception as e:
        return ([], f"Error getting document history: {str(e)}")


def list_generated_documents() -> List[Dict[str, Any]]:
    """
    List all generated documents with their status.
    
    Returns:
        List of document summaries
    """
    documents = []
    
    try:
        # Create documents directory if it doesn't exist
        os.makedirs(constants.GENERATED_DOCUMENTS_DIR, exist_ok=True)
        
        # Get all files in the documents directory
        for file_name in os.listdir(constants.GENERATED_DOCUMENTS_DIR):
            if file_name.endswith(('.docx', '.pdf')):
                # Extract document ID from filename
                document_id = os.path.splitext(file_name)[0]
                file_path = os.path.join(constants.GENERATED_DOCUMENTS_DIR, file_name)
                
                # Get file info
                stat = os.stat(file_path)
                
                # Get document status
                status_info, error = get_document_status(document_id)
                if error:
                    status_info = {
                        "status": "unknown",
                        "message": error,
                        "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                
                # Create document summary
                document_summary = {
                    "id": document_id,
                    "file_name": file_name,
                    "file_path": file_path,
                    "file_size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "status": status_info.get("status", "unknown"),
                    "status_message": status_info.get("message", ""),
                    "status_timestamp": status_info.get("timestamp", "")
                }
                
                documents.append(document_summary)
        
        # Sort by creation date (newest first)
        documents.sort(key=lambda x: x["created_at"], reverse=True)
        
        return documents
    
    except Exception as e:
        print(f"Error listing generated documents: {str(e)}")
        return []


def delete_generated_document(document_id: str) -> Tuple[bool, str]:
    """
    Delete a generated document and its status history.
    
    Args:
        document_id: ID of the document to delete
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Find document files
        document_files = []
        for file_name in os.listdir(constants.GENERATED_DOCUMENTS_DIR):
            if file_name.startswith(document_id):
                file_path = os.path.join(constants.GENERATED_DOCUMENTS_DIR, file_name)
                document_files.append(file_path)
        
        if not document_files:
            return (False, f"No files found for document: {document_id}")
        
        # Delete all document files
        for file_path in document_files:
            os.remove(file_path)
        
        return (True, f"Document {document_id} deleted successfully")
    
    except Exception as e:
        return (False, f"Error deleting document: {str(e)}")


# Document Editing Functions

def create_editable_document(template_path: str, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Create an editable document with form fields for final editing.
    
    Args:
        template_path: Path to the template file
        data: Dictionary containing the data to insert into the template
        
    Returns:
        Tuple of (success, message, editable_data)
    """
    try:
        # Load template
        template_data, error = load_template(template_path)
        
        if error:
            return (False, f"Error loading template: {error}", {})
        
        # Create editable data structure
        editable_data = {
            "template_path": template_path,
            "template_type": template_data.get("type", "unknown"),
            "original_data": data.copy(),
            "editable_fields": {},
            "field_metadata": {}
        }
        
        # Get template placeholders
        placeholders = [p["name"] for p in template_data.get("placeholders", [])]
        
        # Create editable fields for each placeholder
        for placeholder in placeholders:
            if placeholder in data:
                editable_data["editable_fields"][placeholder] = data[placeholder]
                editable_data["field_metadata"][placeholder] = {
                    "type": "text",
                    "required": True,
                    "original_value": data[placeholder]
                }
        
        return (True, "Editable document created successfully", editable_data)
    
    except Exception as e:
        return (False, f"Error creating editable document: {str(e)}", {})


def update_document_data(original_data: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update document data with user edits.
    
    Args:
        original_data: Original document data
        updates: Dictionary of field updates
        
    Returns:
        Updated document data
    """
    try:
        # Create a copy of the original data
        updated_data = original_data.copy()
        
        # Apply updates
        for field, value in updates.items():
            updated_data[field] = value
        
        return updated_data
    
    except Exception as e:
        print(f"Error updating document data: {str(e)}")
        return original_data


def validate_document_data(data: Dict[str, Any], required_fields: List[str] = None) -> Tuple[bool, List[str]]:
    """
    Validate document data before final generation.
    
    Args:
        data: Document data to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        errors = []
        required_fields = required_fields or []
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Required field '{field}' is missing or empty")
        
        # Validate specific field types
        if "nik" in data and data["nik"]:
            if not data["nik"].isdigit() or len(data["nik"]) != 16:
                errors.append("NIK must be exactly 16 digits")
        
        if "email" in data and data["email"]:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data["email"]):
                errors.append("Invalid email format")
        
        return (len(errors) == 0, errors)
    
    except Exception as e:
        return (False, [f"Error validating document data: {str(e)}"])


# ============================================================================
# PERFORMANCE OPTIMIZATION FUNCTIONS
# ============================================================================

def calculate_data_hash(data: Dict[str, Any]) -> str:
    """
    Calculate a hash of the data for caching purposes.
    
    Args:
        data: Dictionary containing the data
        
    Returns:
        String hash of the data
    """
    # Convert data to a sorted JSON string
    data_str = json.dumps(data, sort_keys=True)
    # Calculate MD5 hash
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()


def timed_document_cache(maxsize: int = 32, ttl: int = 1800):
    """
    A timed cache decorator specifically for document generation operations.
    
    Args:
        maxsize: Maximum number of items to cache
        ttl: Time to live in seconds
    """
    def decorator(func):
        cache = {}
        timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from data hash and parameters
            if len(args) > 1 and isinstance(args[1], dict):  # Check if second arg is data dict
                data_hash = calculate_data_hash(args[1])
                key = f"{data_hash}_{str(args[0])}_{str(args[2:])}_{str(sorted(kwargs.items()))}"
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


@timed_document_cache(maxsize=16, ttl=1800)  # Cache for 30 minutes
def optimized_generate_document(template_path: str,
                             output_path: str,
                             data: Dict[str, Any],
                             format_type: str = "auto",
                             field_mappings: Optional[List[constants.FieldMapping]] = None) -> Tuple[bool, str]:
    """
    Optimized document generation with caching.
    
    Args:
        template_path: Path to the template file
        output_path: Path where the generated document will be saved
        data: Dictionary containing the data to insert into the template
        format_type: Output format type ('auto', 'pdf', 'docx')
        field_mappings: Optional list of field mappings
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Auto-detect format if needed
        if format_type == "auto":
            file_ext = os.path.splitext(template_path)[1].lower()
            if file_ext == ".docx":
                format_type = "docx"
            elif file_ext == ".pdf":
                format_type = "pdf"
            else:
                return (False, f"Unsupported template format: {file_ext}")
        
        # Apply field mappings if provided
        if field_mappings:
            mapped_data = {}
            for mapping in field_mappings:
                if mapping.ktp_field in data:
                    mapped_data[mapping.template_field] = data[mapping.ktp_field]
            data = mapped_data
        
        # Generate document based on format
        if format_type == "docx":
            return _generate_docx_document(template_path, output_path, data)
        elif format_type == "pdf":
            return _generate_pdf_document(template_path, output_path, data)
        else:
            return (False, f"Unsupported format type: {format_type}")
    
    except Exception as e:
        return (False, f"Error generating document: {str(e)}")


@timed_document_cache(maxsize=8, ttl=1800)  # Cache for 30 minutes
def optimized_preview_document(template_path: str,
                            data: Dict[str, Any],
                            format_type: str = "auto",
                            field_mappings: Optional[List[constants.FieldMapping]] = None) -> Tuple[bytes, str]:
    """
    Optimized document preview generation with caching.
    
    Args:
        template_path: Path to the template file
        data: Dictionary containing the data to insert into the template
        format_type: Output format type ('auto', 'pdf', 'docx')
        field_mappings: Optional list of field mappings
        
    Returns:
        Tuple of (document_bytes, error_message)
    """
    try:
        # Create a temporary file for the preview
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf" if format_type == "pdf" else ".docx", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Generate the document using optimized function
            success, message = optimized_generate_document(
                template_path=template_path,
                output_path=temp_path,
                data=data,
                format_type=format_type,
                field_mappings=field_mappings
            )
            
            if not success:
                return (None, message)
            
            # Read the generated file
            with open(temp_path, "rb") as f:
                document_bytes = f.read()
            
            return (document_bytes, "")
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        return (None, f"Error generating preview: {str(e)}")


def batch_generate_documents(requests: List[Dict[str, Any]],
                           max_workers: int = 2) -> List[Tuple[bool, str]]:
    """
    Generate multiple documents in parallel for better performance.
    
    Args:
        requests: List of document generation requests, each containing:
                 - template_path: Path to the template file
                 - output_path: Path where the generated document will be saved
                 - data: Dictionary containing the data to insert into the template
                 - format_type: Output format type ('auto', 'pdf', 'docx')
                 - field_mappings: Optional list of field mappings
        max_workers: Maximum number of worker threads
        
    Returns:
        List of tuples containing (success, message) for each request
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all document generation tasks
        futures = []
        for request in requests:
            future = executor.submit(
                optimized_generate_document,
                template_path=request.get("template_path"),
                output_path=request.get("output_path"),
                data=request.get("data"),
                format_type=request.get("format_type", "auto"),
                field_mappings=request.get("field_mappings")
            )
            futures.append(future)
        
        # Collect results
        results = []
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                results.append((False, f"Error in batch generation: {str(e)}"))
        
        return results


def optimize_document_templates() -> Tuple[bool, str]:
    """
    Optimize document templates for faster processing.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create templates directory if it doesn't exist
        os.makedirs(constants.TEMPLATES_DIR, exist_ok=True)
        
        # Get all template files
        template_files = []
        for file_name in os.listdir(constants.TEMPLATES_DIR):
            if file_name.endswith(('.docx', '.pdf')):
                template_files.append(os.path.join(constants.TEMPLATES_DIR, file_name))
        
        # Process each template
        for template_file in template_files:
            try:
                # Load template and extract placeholders
                template_data, error = load_template(template_file)
                
                if error:
                    print(f"Error loading template {template_file}: {error}")
                    continue
                
                # Create a hash-based cache file for the template
                file_hash = hashlib.md5(template_file.encode('utf-8')).hexdigest()
                cache_file = os.path.join(constants.TEMPLATES_DIR, f"{file_hash}.cache")
                
                # Save template structure to cache file
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "file_path": template_file,
                        "placeholders": template_data.get("placeholders", []),
                        "type": template_data.get("type"),
                        "cached_at": datetime.now().isoformat()
                    }, f, ensure_ascii=False, indent=2)
                
            except Exception as e:
                print(f"Error processing template {template_file}: {str(e)}")
        
        return (True, "Document templates optimized successfully")
    
    except Exception as e:
        return (False, f"Error optimizing document templates: {str(e)}")


def measure_document_generation_performance(func: callable) -> callable:
    """
    Decorator to measure document generation performance.
    
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
        print(f"[DOC GEN PERFORMANCE] {func.__name__} took {processing_time:.3f} seconds")
        
        return result
    return wrapper


def create_optimized_document_pipeline() -> Dict[str, Any]:
    """
    Create an optimized document generation pipeline.
    
    Returns:
        Dictionary with pipeline configuration
    """
    pipeline = {
        "template_cache": {},
        "document_cache": {},
        "performance_metrics": {
            "template_load_time": 0,
            "document_generation_time": 0,
            "total_documents_generated": 0
        },
        "optimization_settings": {
            "enable_caching": True,
            "cache_ttl": 1800,  # 30 minutes
            "cache_max_size": 32,
            "enable_parallel_processing": True,
            "max_workers": 2
        }
    }
    
    # Optimize templates on pipeline creation
    success, message = optimize_document_templates()
    if success:
        print(f"[PIPELINE] {message}")
    else:
        print(f"[PIPELINE ERROR] {message}")
    
    return pipeline


def get_pipeline_performance_metrics(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get performance metrics from the document generation pipeline.
    
    Args:
        pipeline: Document generation pipeline
        
    Returns:
        Dictionary with performance metrics
    """
    metrics = pipeline.get("performance_metrics", {})
    
    # Calculate average times
    total_docs = metrics.get("total_documents_generated", 0)
    if total_docs > 0:
        metrics["average_template_load_time"] = metrics.get("template_load_time", 0) / total_docs
        metrics["average_document_generation_time"] = metrics.get("document_generation_time", 0) / total_docs
    else:
        metrics["average_template_load_time"] = 0
        metrics["average_document_generation_time"] = 0
    
    # Calculate cache hit ratios
    template_cache = pipeline.get("template_cache", {})
    document_cache = pipeline.get("document_cache", {})
    
    metrics["template_cache_size"] = len(template_cache)
    metrics["document_cache_size"] = len(document_cache)
    
    return metrics