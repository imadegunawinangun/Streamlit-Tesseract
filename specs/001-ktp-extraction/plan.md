# Implementation Plan: KTP Data Extraction and Document Population

**Branch**: `001-ktp-extraction` | **Date**: 2025-10-20 | **Spec**: specs/001-ktp-extraction/spec.md
**Input**: Feature specification from `/specs/001-ktp-extraction/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The KTP Data Extraction feature will implement OCR-based extraction of structured data from Indonesian ID cards using Tesseract OCR with Indonesian language support. The system will include image preprocessing, field validation, document template mapping, and document generation capabilities in PDF and DOCX formats.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11 or NEEDS CLARIFICATION
**Primary Dependencies**: Tesseract OCR, Streamlit, OpenCV, Pillow, python-docx, reportlab or NEEDS CLARIFICATION
**Storage**: File-based storage for KTP data and templates or NEEDS CLARIFICATION
**Testing**: pytest or NEEDS CLARIFICATION
**Target Platform**: Web application via Streamlit or NEEDS CLARIFICATION
**Project Type**: Web application
**Performance Goals**: Process KTP images in under 30 seconds, complete full workflow in under 3 minutes or NEEDS CLARIFICATION
**Constraints**: Memory usage below 500MB, Tesseract OCR processing timeout of 20 seconds or NEEDS CLARIFICATION
**Scale/Scope**: Single user system for MVP or NEEDS CLARIFICATION

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Image Processing Excellence: Does the feature preserve text integrity and provide non-destructive transformations?
  - **Status**: PARTIALLY COMPLIANT
  - **Evidence**: [`research.md`](research.md:21-22) mentions OpenCV for image preprocessing, [`quickstart.md`](quickstart.md:187) mentions auto-correction for rotated images, and [`contracts/api.md`](contracts/api.md:456-458) includes preprocessing preview URL.
  - **Gap**: No explicit mention of independently toggleable preprocessing steps.

- [x] Multi-Engine OCR Support: Is the architecture compatible with multiple OCR engines?
  - **Status**: PARTIALLY COMPLIANT
  - **Evidence**: [`research.md`](research.md:26-29) mentions EasyOCR as a considered alternative, and [`data-model.md`](data-model.md:38) includes extraction_method field.
  - **Gap**: No explicit architecture details for engine swapping or independent testing.

- [x] Language Accessibility: Are language pack validation and user-friendly error messages included?
  - **Status**: FULLY COMPLIANT
  - **Evidence**: [`research.md`](research.md:71-73) addresses Indonesian language support, [`quickstart.md`](quickstart.md:76-82) provides verification instructions, and [`quickstart.md`](quickstart.md:203-205) includes troubleshooting for missing language packs.

- [x] Document Format Flexibility: Does the feature handle both images and PDFs consistently?
  - **Status**: NON-COMPLIANT
  - **Evidence**: [`quickstart.md`](quickstart.md:99) only lists JPG, PNG, BMP as supported formats.
  - **Gap**: No mention of PDF input support, page selection, or maintaining image quality during PDF conversion.
  - **Justification**: KTP cards are physical documents that are typically photographed rather than scanned to PDF. Image input focus aligns with user behavior for this specific use case.

- [x] User Experience Transparency: Are there clear progress indicators and previews for all processing steps?
  - **Status**: FULLY COMPLIANT
  - **Evidence**: [`quickstart.md`](quickstart.md:101-104) mentions confidence scores, [`quickstart.md`](quickstart.md:106-109) describes editable extracted data, and [`quickstart.md`](quickstart.md:117) mentions document preview before generation.

- [x] Document Generation Capability: Does the feature support inserting extracted data into DOCX/PDF templates?
  - **Status**: FULLY COMPLIANT
  - **Evidence**: [`research.md`](research.md:23-24) mentions python-docx and reportlab, [`data-model.md`](data-model.md:41-80) defines comprehensive entities for templates and mappings, and [`contracts/api.md`](contracts/api.md:257-339) includes complete API endpoints.

- [x] Performance Requirements: Will the feature complete within the defined time and memory constraints?
  - **Status**: PARTIALLY COMPLIANT
  - **Evidence**: [`research.md`](research.md:57-58) confirms 500MB memory limit and 20-second timeout, and [`quickstart.md`](quickstart.md:223-224) specifies performance expectations.
  - **Gap**: No explicit mention of 3-second image preprocessing requirement or application responsiveness during processing.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Document Format Flexibility (PDF input support) | KTP cards are physical documents that are typically photographed rather than scanned to PDF. The implementation focuses on image input which aligns with natural user behavior for this specific use case. | Adding PDF support would increase complexity without significant user benefit for KTP processing, as most users will capture images with mobile devices. |

