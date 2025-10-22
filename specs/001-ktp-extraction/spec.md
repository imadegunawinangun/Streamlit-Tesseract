# Feature Specification: KTP Data Extraction and Document Population

**Feature Branch**: `001-ktp-extraction`  
**Created**: 2025-10-20  
**Status**: Draft  
**Input**: User description: "Structured data extraction from identity documents with automatic document population"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - KTP Scanning and Data Extraction (Priority: P1)

User uploads a KTP (Indonesian ID card) image and the system automatically extracts structured data fields like name, ID number, address, date of birth, etc.

**Why this priority**: This is the core functionality that enables all other features - without accurate data extraction, document population is impossible.

**Independent Test**: Can be fully tested by uploading a clear KTP image and verifying all data fields are correctly extracted and displayed to the user for review.

**Acceptance Scenarios**:

1. **Given** a user has uploaded a clear KTP image, **When** the OCR processing completes, **Then** all key fields (NIK, name, birth date, address, religion, marital status, occupation) are extracted and displayed in a structured form
2. **Given** a user uploads a blurry or partially obscured KTP, **When** OCR processing completes, **Then** the system extracts as many fields as possible and highlights low-confidence fields for manual review

---

### User Story 2 - Document Template Selection and Mapping (Priority: P1)

User selects a document template and maps the extracted KTP data fields to the appropriate locations in the template.

**Why this priority**: This enables the core value proposition of automatic document population, making the feature immediately useful.

**Independent Test**: Can be fully tested by selecting a template and verifying that extracted KTP data populates the correct fields in the preview.

**Acceptance Scenarios**:

1. **Given** extracted KTP data is available, **When** user selects a document template, **Then** the system shows a preview with KTP data populated in the correct template fields
2. **Given** a user wants to modify the field mapping, **When** they click on any populated field, **Then** they can select a different KTP data field to populate that location

---

### User Story 3 - Document Generation and Download (Priority: P2)

User generates the final document with populated data and downloads it in their preferred format.

**Why this priority**: This completes the user workflow and delivers the final value proposition of the feature.

**Independent Test**: Can be fully tested by generating a document and verifying the downloaded file contains the correct KTP data in the proper format.

**Acceptance Scenarios**:

1. **Given** a user has reviewed the document preview, **When** they click generate, **Then** the system creates a downloadable document with all KTP data properly formatted
2. **Given** a user wants to make final adjustments, **When** they edit any field before generation, **Then** the final document reflects their changes

---

## Clarifications

### Session 2025-10-20

- Q: What types of document templates should the system support initially? → A: Generic document templates that users can customize for any purpose
- Q: How should the system handle sensitive KTP data regarding storage and privacy? → A: Store KTP data indefinitely with user consent for future document generation
- Q: What are the specific performance targets for concurrent users and document processing volume? → A: Performance targets not needed for MVP release
- Q: What specific error recovery strategies should be implemented when OCR confidence is low? → A: Automatically suggest manual input for low-confidence fields while preserving high-confidence values
- Q: What OCR engine should be used as the primary solution for KTP text extraction? → A: Tesseract OCR with Indonesian language pack as the primary solution

### Edge Cases

- What happens when the KTP image is upside down or rotated?
- How does system handle KTP images with poor lighting or shadows?
- What happens when required fields cannot be extracted with sufficient confidence?
- How does system handle KTP images that are cropped or partially visible?
- What happens when the selected document template has incompatible field types?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract structured data from KTP images including NIK, name, place/date of birth, gender, address, religion, marital status, occupation, and validity period
- **FR-002**: System MUST provide confidence scores for each extracted data field
- **FR-003**: Users MUST be able to manually correct or edit extracted data fields before document generation
- **FR-004**: System MUST support multiple document templates (forms, applications, registrations)
- **FR-005**: System MUST allow users to map extracted KTP fields to template fields
- **FR-006**: System MUST provide real-time preview of documents with populated data
- **FR-007**: System MUST support document generation in multiple formats (PDF, DOCX)
- **FR-008**: System MUST validate extracted data format (e.g., NIK must be 16 digits)
- **FR-009**: System MUST handle image preprocessing specifically optimized for KTP documents
- **FR-010**: System MUST preserve original formatting and layout of document templates

*OCR-specific requirements examples:*

- **FR-011**: System MUST validate Tesseract language pack availability for Indonesian text before processing
- **FR-012**: System MUST provide preview of preprocessed KTP images before OCR execution
- **FR-013**: System MUST handle corrupted or unsupported image files with user-friendly messages
- **FR-018**: System MUST provide independently toggleable preprocessing steps allowing users to enable/disable specific image processing operations

*Document generation requirements examples:*

- **FR-014**: System MUST allow users to select from predefined document templates for data insertion
- **FR-015**: System MUST preserve formatting and structure of target documents during data insertion
- **FR-016**: System MUST provide preview of generated documents before download
- **FR-017**: System MUST support multiple output formats (DOCX, PDF) for generated documents

### Non-Functional Requirements

*Security & Privacy:*

- **NFR-001**: System MUST store KTP data indefinitely with explicit user consent for future document generation
- **NFR-002**: System MUST implement secure authentication for accessing stored KTP data
- **NFR-003**: System MUST encrypt KTP data both in transit and at rest

*Performance:*

- **NFR-004**: Performance targets for concurrent users and document processing volume are not required for MVP release
- **NFR-007**: System MUST complete all image preprocessing steps within 3 seconds for standard KTP images

*Error Handling:*

- **NFR-005**: System MUST automatically suggest manual input for low-confidence fields while preserving high-confidence values

*Technical Constraints:*

- **NFR-006**: System MUST use Tesseract OCR with Indonesian language pack as the primary solution for KTP text extraction
- **NFR-008**: System MUST require Python 3.11 or higher for all components and dependencies

### Key Entities *(include if feature involves data)*

- **KTP Data**: Extracted information from Indonesian ID cards including personal identifiers, demographic data, and validity information
- **Document Template**: Predefined document structures with field placeholders for data insertion
- **Field Mapping**: Association between extracted KTP data fields and template field locations
- **Generated Document**: Final output document with KTP data populated in template fields

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can extract data from a clear KTP image and generate a populated document in under 3 minutes
- **SC-002**: System achieves 95% accuracy for key fields (NIK, name, address) on clear KTP images
- **SC-003**: 90% of users successfully complete the full workflow (upload → extract → generate → download) on first attempt
- **SC-004**: System processes KTP images in under 30 seconds for standard quality images
- **SC-005**: Reduce manual data entry time for form filling by 80% compared to manual typing

## Edge Case Handling

### 1. Handling Upside Down or Rotated KTP Images

**Recommended Approach**:
- Implement automatic orientation detection using Tesseract's OSD (Orientation and Script Detection) mode (PSM 0)
- Provide manual rotation controls in 90° increments and free angle rotation
- Add a "Smart Auto-Rotate" feature that attempts all four orientations (0°, 90°, 180°, 270°) and selects the one with the highest OCR confidence score

**Implementation Considerations**:
- Utilize existing [`opencv.rotate90()`](helpers/opencv.py:105) and [`opencv.rotate_scipy()`](helpers/opencv.py:134) functions
- Implement a confidence scoring mechanism to evaluate OCR results at different orientations
- Add a new function in [`helpers/opencv.py`](helpers/opencv.py:1) for automatic orientation detection
- Consider using edge detection to identify KTP document boundaries for better rotation detection

**User Experience Implications**:
- Provide visual feedback showing the detected orientation
- Allow users to override automatic detection with manual controls
- Show a preview of the rotated image before OCR processing
- Display confidence scores for each orientation attempt

**Limitations or Constraints**:
- Automatic detection may fail with severely distorted or low-quality images
- Multiple orientation attempts will increase processing time
- Extreme rotation angles (>45°) may result in significant image cropping

### 2. Processing KTP Images with Poor Lighting or Shadows

**Recommended Approach**:
- Implement adaptive histogram equalization (CLAHE) to improve contrast
- Add shadow detection and removal algorithms
- Provide multiple preprocessing options with preview functionality
- Implement automatic quality assessment to suggest optimal preprocessing

**Implementation Considerations**:
- Extend [`helpers/opencv.py`](helpers/opencv.py:1) with new functions for:
  - CLAHE (Contrast Limited Adaptive Histogram Equalization)
  - Shadow detection using gradient analysis
  - Local contrast enhancement
- Add quality assessment metrics to evaluate image improvement
- Implement a "Smart Enhance" option that automatically applies optimal preprocessing

**User Experience Implications**:
- Provide before/after preview of preprocessing effects
- Allow users to adjust enhancement parameters with real-time preview
- Show quality scores to guide users in selecting optimal preprocessing
- Include recommended preprocessing settings based on image analysis

**Limitations or Constraints**:
- Extremely poor lighting conditions may not be fully correctable
- Shadow removal may inadvertently remove important text regions
- Multiple preprocessing steps will increase processing time
- Some enhancement techniques may amplify noise in already clear images

### 3. Managing Required Fields with Low Confidence Extraction

**Recommended Approach**:
- Implement confidence thresholding for each extracted field
- Provide visual indicators for low-confidence fields (color coding, warning icons)
- Enable manual correction interface for low-confidence fields
- Implement field validation based on KTP format specifications

**Implementation Considerations**:
- Extend [`helpers/tesseract.py`](helpers/tesseract.py:1) to return confidence scores for each word/field
- Add field-specific validation functions in a new helper module
- Implement a confidence-based highlighting system in the UI
- Create a structured data model for KTP fields with validation rules

**User Experience Implications**:
- Clearly highlight low-confidence fields with distinct visual indicators
- Provide inline editing capabilities for manual correction
- Show confidence scores alongside extracted values
- Implement smart suggestions based on partial information and KTP format patterns

**Limitations or Constraints**:
- Manual correction increases user effort and time
- Some fields may be impossible to verify without external reference
- Confidence scores may not always correlate with actual accuracy
- Complex validation rules may reject valid but unusual KTP formats

### 4. Handling Cropped or Partially Visible KTP Images

**Recommended Approach**:
- Implement document boundary detection to identify visible regions
- Provide partial extraction capabilities for available fields
- Add manual region selection tools for users to highlight text areas
- Implement intelligent field location based on partial document structure

**Implementation Considerations**:
- Add document boundary detection using edge detection and contour analysis
- Implement region-of-interest (ROI) selection in [`helpers/opencv.py`](helpers/opencv.py:1)
- Create a field mapping system that can work with partial information
- Add zoom and pan functionality for precise region selection

**User Experience Implications**:
- Provide visual indicators showing which parts of the KTP are detected
- Allow users to manually select text regions for OCR processing
- Show progress indicators for field extraction based on visible areas
- Provide clear messaging about which fields cannot be extracted

**Limitations or Constraints**:
- Critical fields may be missing from cropped images
- Manual region selection requires user effort and expertise
- Partial information may not be sufficient for document generation
- Edge detection may fail with complex backgrounds or poor contrast

### 5. Dealing with Incompatible Field Types in Templates

**Recommended Approach**:
- Implement automatic field type conversion with validation
- Provide a mapping interface for users to associate KTP fields with template fields
- Add data transformation functions for common type conversions
- Create a template validation system to check compatibility

**Implementation Considerations**:
- Create a new helper module for document generation and template handling
- Implement field type detection and conversion functions
- Add a template validation system that checks field compatibility
- Create a flexible mapping system that can handle various field types

**User Experience Implications**:
- Provide clear error messages when field types are incompatible
- Show suggested conversions with preview of results
- Allow users to manually override automatic conversions
- Include a template compatibility checker before document generation

**Limitations or Constraints**:
- Some data types may not be convertible without information loss
- Complex templates may require manual configuration
- Automatic conversion may introduce formatting errors
- Template handling represents a significant scope expansion beyond basic OCR
