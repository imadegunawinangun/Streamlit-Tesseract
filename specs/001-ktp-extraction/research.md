# Phase 0 Research: KTP Data Extraction and Document Population

**Date**: 2025-10-20  
**Feature**: KTP Data Extraction and Document Population  
**Spec**: [specs/001-ktp-extraction/spec.md](spec.md)

## Technology Decisions

### Python Version

**Decision**: Python 3.11  
**Rationale**: Python 3.11 offers significant performance improvements (10-60% faster) and better error handling compared to earlier versions. It's well-supported by all required dependencies and provides the latest language features for cleaner code. The existing codebase is already compatible with Python 3.11.  
**Alternatives considered**: Python 3.9 (more conservative but slower), Python 3.12 (newer but less compatibility testing with dependencies)

### Primary Dependencies

**Decision**: Tesseract OCR, Streamlit, OpenCV, Pillow, python-docx, reportlab  
**Rationale**: These dependencies align with the existing codebase and meet all functional requirements:
- Tesseract OCR is explicitly required by NFR-006 and is the primary OCR engine
- Streamlit provides the web interface framework already in use
- OpenCV is essential for image preprocessing optimized for KTP documents
- Pillow is required for image manipulation and format handling
- python-docx enables document generation in DOCX format as required by FR-007
- reportlab enables PDF generation as required by FR-007

**Alternatives considered**: 
- EasyOCR (as secondary OCR engine for multi-engine support)
- PaddleOCR (alternative OCR engine but less mature)
- ReportLab vs. WeasyPrint (ReportLab chosen for better template support)

### Storage Solution

**Decision**: File-based storage with JSON format for KTP data and templates directory  
**Rationale**: For the MVP scope, file-based storage provides simplicity and transparency. JSON format allows easy inspection and debugging of extracted KTP data. Templates directory aligns with the constitution requirement for storing templates in templates/ directory with clear naming conventions. This approach avoids database complexity while maintaining data persistence.  
**Alternatives considered**: SQLite (more structured but adds complexity), PostgreSQL (overkill for MVP), In-memory storage (no persistence)

### Testing Framework

**Decision**: pytest  
**Rationale**: pytest is the de facto standard for Python testing with excellent support for fixtures, parameterized testing, and clear assertion syntax. It integrates well with Streamlit applications and provides comprehensive coverage reporting. The existing codebase doesn't have tests yet, so pytest provides a clean start for the testing framework.  
**Alternatives considered**: unittest (built-in but more verbose), nose2 (less actively maintained), doctest (limited functionality)

### Target Platform

**Decision**: Web application via Streamlit  
**Rationale**: The existing application is already built on Streamlit, providing a consistent user experience. Streamlit's web interface is accessible across devices without requiring installation, making it ideal for document processing workflows. It also provides built-in file upload handling and image display capabilities essential for the KTP extraction feature.  
**Alternatives considered**: Desktop application (higher performance but requires installation), Mobile app (not aligned with current codebase), REST API (would require separate frontend development)

### Performance Goals

**Decision**: Process KTP images in under 30 seconds, complete full workflow in under 3 minutes  
**Rationale**: These targets align with the success criteria defined in SC-001 and SC-004. The 30-second image processing target allows for comprehensive preprocessing while maintaining user engagement. The 3-minute full workflow target encompasses upload, preprocessing, OCR extraction, field mapping, and document generation. These targets are achievable with the chosen technology stack.  
**Alternatives considered**: More aggressive targets (risk of poor user experience), Looser targets (not meeting success criteria)

### Constraints

**Decision**: Memory usage below 500MB, Tesseract OCR processing timeout of 20 seconds  
**Rationale**: These constraints align with the constitution's performance requirements. The 500MB memory limit ensures the application runs efficiently on standard hardware while processing images. The 20-second timeout for Tesseract matches the existing implementation and provides a balance between processing time and user patience.  
**Alternatives considered**: Higher memory limits (would exclude low-end devices), Shorter timeouts (may fail on complex images)

### Scale/Scope

**Decision**: Single user system for MVP  
**Rationale**: The feature specification indicates performance targets are not needed for MVP release (NFR-004). A single user system simplifies implementation while delivering core functionality. This approach allows focusing on the extraction quality and user experience before scaling to multi-user scenarios.  
**Alternatives considered**: Multi-user system (adds authentication complexity), Enterprise scale (overkill for MVP)

## KTP-Specific Implementation Research

### Indonesian Language Support

**Decision**: Add Indonesian language pack to Tesseract configuration  
**Rationale**: KTP documents contain Indonesian text elements. While most KTP data follows standardized formats, some fields like "Tempat Lahir" (Place of Birth) and addresses contain Indonesian text that requires proper language support for accurate OCR extraction.  
**Alternatives considered**: Relying on English only (poor accuracy for Indonesian text), Custom character training (complex for MVP)

### KTP Field Extraction Strategy

**Decision**: Pattern-based extraction with confidence scoring  
**Rationale**: KTP cards have standardized formats with predictable field patterns (e.g., NIK is always 16 digits). Pattern-based extraction provides high accuracy for these structured fields while confidence scoring allows identifying low-confidence extractions for manual review as required by NFR-005.  
**Alternatives considered**: Full text extraction with parsing (less accurate), Machine learning models (overkill for MVP)

### Document Template System

**Decision**: JSON-based template definitions with DOCX/PDF generation  
**Rationale**: JSON templates provide a simple, extensible format for defining field mappings and positions. The python-docx and reportlab libraries can then generate the final documents based on these templates. This approach balances flexibility with implementation simplicity for the MVP.  
**Alternatives considered**: HTML templates (less precise positioning), Custom binary format (proprietary and complex)

## Implementation Notes

1. **Indonesian Language Pack**: Must be added to constants.py and validated before processing
2. **KTP Field Validation**: Implement validation for NIK (16 digits) and other standardized fields
3. **Template Storage**: Create templates/ directory with example templates for common document types
4. **Error Handling**: Implement user-friendly error messages for OCR failures and missing language packs
5. **Performance Monitoring**: Add timing metrics to ensure performance targets are met

## Next Steps

1. Implement Indonesian language pack support in helpers/constants.py
2. Create KTP field extraction patterns and validation
3. Design document template structure and examples
4. Implement document generation with python-docx and reportlab
5. Add comprehensive error handling and user feedback