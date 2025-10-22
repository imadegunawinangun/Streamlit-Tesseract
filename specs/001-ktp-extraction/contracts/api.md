# API Contracts: KTP Data Extraction and Document Population

**Date**: 2025-10-20  
**Feature**: KTP Data Extraction and Document Population  
**Spec**: [specs/001-ktp-extraction/spec.md](spec.md)

## OpenAPI Schema

The following OpenAPI 3.0 schema defines the REST API endpoints for the KTP extraction feature. This content should be saved as `api.yaml` in the same directory.

```yaml
openapi: 3.0.3
info:
  title: KTP Data Extraction API
  description: API for extracting data from Indonesian ID cards (KTP) and generating documents
  version: 1.0.0
  contact:
    name: KTP Extraction Support
    email: support@example.com

servers:
  - url: http://localhost:8000/api/v1
    description: Development server

paths:
  # KTP Data Management Endpoints
  /ktp/upload:
    post:
      summary: Upload KTP image for data extraction
      description: Upload a KTP image and extract structured data using OCR
      operationId: uploadKtp
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                image:
                  type: string
                  format: binary
                  description: KTP image file
      responses:
        '200':
          description: Successful extraction
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/KtpExtractionResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
        '500':
          $ref: '#/components/responses/InternalServerError'

  /ktp/{ktpId}:
    get:
      summary: Get KTP data by ID
      description: Retrieve extracted KTP data by its unique identifier
      operationId: getKtpData
      parameters:
        - name: ktpId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Successful retrieval
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/KtpData'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'

    put:
      summary: Update KTP data
      description: Update extracted KTP data with manual corrections
      operationId: updateKtpData
      parameters:
        - name: ktpId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/KtpDataUpdate'
      responses:
        '200':
          description: Successful update
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/KtpData'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
        '500':
          $ref: '#/components/responses/InternalServerError'

  # Document Template Endpoints
  /templates:
    get:
      summary: List all document templates
      description: Retrieve a list of all available document templates
      operationId: listTemplates
      responses:
        '200':
          description: Successful retrieval
          content:
            application/json:
              schema:
                type: object
                properties:
                  templates:
                    type: array
                    items:
                      $ref: '#/components/schemas/DocumentTemplate'
        '500':
          $ref: '#/components/responses/InternalServerError'

    post:
      summary: Create a new document template
      description: Create a new document template for data population
      operationId: createTemplate
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocumentTemplateCreate'
      responses:
        '201':
          description: Template created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentTemplate'
        '400':
          $ref: '#/components/responses/BadRequest'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
        '500':
          $ref: '#/components/responses/InternalServerError'

  /templates/{templateId}:
    get:
      summary: Get document template by ID
      description: Retrieve a document template by its unique identifier
      operationId: getTemplate
      parameters:
        - name: templateId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Successful retrieval
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentTemplate'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'

  # Field Mapping Endpoints
  /templates/{templateId}/mappings:
    get:
      summary: Get field mappings for a template
      description: Retrieve field mappings for a specific document template
      operationId: getFieldMappings
      parameters:
        - name: templateId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Successful retrieval
          content:
            application/json:
              schema:
                type: object
                properties:
                  mappings:
                    type: array
                    items:
                      $ref: '#/components/schemas/FieldMapping'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'

    put:
      summary: Update field mappings for a template
      description: Update field mappings for a specific document template
      operationId: updateFieldMappings
      parameters:
        - name: templateId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                mappings:
                  type: array
                  items:
                    $ref: '#/components/schemas/FieldMappingUpdate'
      responses:
        '200':
          description: Successful update
          content:
            application/json:
              schema:
                type: object
                properties:
                  mappings:
                    type: array
                    items:
                      $ref: '#/components/schemas/FieldMapping'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
        '500':
          $ref: '#/components/responses/InternalServerError'

  # Document Generation Endpoints
  /documents/preview:
    post:
      summary: Generate document preview
      description: Generate a preview of a document with KTP data populated
      operationId: generatePreview
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocumentGenerationRequest'
      responses:
        '200':
          description: Preview generated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentPreviewResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
        '500':
          $ref: '#/components/responses/InternalServerError'

  /documents/generate:
    post:
      summary: Generate final document
      description: Generate the final document with KTP data populated
      operationId: generateDocument
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocumentGenerationRequest'
      responses:
        '200':
          description: Document generated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentGenerationResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
        '500':
          $ref: '#/components/responses/InternalServerError'

  /documents/{documentId}/download:
    get:
      summary: Download generated document
      description: Download a generated document by its unique identifier
      operationId: downloadDocument
      parameters:
        - name: documentId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Document download
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary
          headers:
            Content-Disposition:
              description: File disposition information
              schema:
                type: string
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'

components:
  schemas:
    KtpData:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique identifier for the KTP data record
        nik:
          type: string
          pattern: '^[0-9]{16}$'
          description: Indonesian ID number (16 digits)
        name:
          type: string
          description: Full name as shown on KTP
        place_of_birth:
          type: string
          description: Place of birth
        date_of_birth:
          type: string
          format: date
          description: Date of birth in YYYY-MM-DD format
        gender:
          type: string
          enum: [Laki-laki, Perempuan]
          description: Gender
        address:
          type: string
          description: Complete address
        religion:
          type: string
          description: Religion
        marital_status:
          type: string
          description: Marital status
        occupation:
          type: string
          description: Occupation
        validity_period:
          type: string
          description: Validity period
        image_path:
          type: string
          description: Path to the original KTP image
        created_at:
          type: string
          format: date-time
          description: Timestamp when the record was created
        updated_at:
          type: string
          format: date-time
          description: Timestamp when the record was last updated

    KtpDataUpdate:
      type: object
      properties:
        nik:
          type: string
          pattern: '^[0-9]{16}$'
          description: Indonesian ID number (16 digits)
        name:
          type: string
          description: Full name as shown on KTP
        place_of_birth:
          type: string
          description: Place of birth
        date_of_birth:
          type: string
          format: date
          description: Date of birth in YYYY-MM-DD format
        gender:
          type: string
          enum: [Laki-laki, Perempuan]
          description: Gender
        address:
          type: string
          description: Complete address
        religion:
          type: string
          description: Religion
        marital_status:
          type: string
          description: Marital status
        occupation:
          type: string
          description: Occupation
        validity_period:
          type: string
          description: Validity period

    ExtractionConfidence:
      type: object
      properties:
        field_name:
          type: string
          description: Name of the field
        confidence_score:
          type: number
          minimum: 0
          maximum: 1
          description: Confidence score for the extraction
        extraction_method:
          type: string
          description: Method used for extraction

    KtpExtractionResponse:
      type: object
      properties:
        ktp_data:
          $ref: '#/components/schemas/KtpData'
        confidence_scores:
          type: array
          items:
            $ref: '#/components/schemas/ExtractionConfidence'
        preprocessing_preview_url:
          type: string
          description: URL to preview the preprocessed image

    DocumentTemplate:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique identifier for the template
        name:
          type: string
          description: Human-readable name of the template
        description:
          type: string
          description: Brief description of the template purpose
        template_type:
          type: string
          description: Type of document
        file_path:
          type: string
          description: Path to the template file
        output_format:
          type: string
          enum: [DOCX, PDF]
          description: Output format
        created_at:
          type: string
          format: date-time
          description: Timestamp when the template was created
        updated_at:
          type: string
          format: date-time
          description: Timestamp when the template was last updated

    DocumentTemplateCreate:
      type: object
      required:
        - name
        - template_type
        - output_format
      properties:
        name:
          type: string
          description: Human-readable name of the template
        description:
          type: string
          description: Brief description of the template purpose
        template_type:
          type: string
          description: Type of document
        output_format:
          type: string
          enum: [DOCX, PDF]
          description: Output format

    FieldMapping:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique identifier for the field mapping
        template_id:
          type: string
          format: uuid
          description: Foreign key to DocumentTemplate
        ktp_field:
          type: string
          description: Name of the KTP data field
        template_field:
          type: string
          description: Name or identifier of the template field
        position_x:
          type: integer
          description: X coordinate for positioning
        position_y:
          type: integer
          description: Y coordinate for positioning
        created_at:
          type: string
          format: date-time
          description: Timestamp when the mapping was created

    FieldMappingUpdate:
      type: object
      required:
        - ktp_field
        - template_field
      properties:
        ktp_field:
          type: string
          description: Name of the KTP data field
        template_field:
          type: string
          description: Name or identifier of the template field
        position_x:
          type: integer
          description: X coordinate for positioning
        position_y:
          type: integer
          description: Y coordinate for positioning

    DocumentGenerationRequest:
      type: object
      required:
        - ktp_id
        - template_id
      properties:
        ktp_id:
          type: string
          format: uuid
          description: ID of the KTP data to use
        template_id:
          type: string
          format: uuid
          description: ID of the template to use
        output_format:
          type: string
          enum: [DOCX, PDF]
          description: Output format (overrides template default if specified)

    DocumentPreviewResponse:
      type: object
      properties:
        preview_url:
          type: string
          description: URL to the document preview
        preview_data:
          type: object
          description: Preview data for client-side rendering

    DocumentGenerationResponse:
      type: object
      properties:
        document_id:
          type: string
          format: uuid
          description: ID of the generated document
        download_url:
          type: string
          description: URL to download the generated document
        status:
          type: string
          description: Status of generation

    Error:
      type: object
      properties:
        error:
          type: string
          description: Error message
        details:
          type: object
          description: Additional error details

  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    UnprocessableEntity:
      description: Validation error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    InternalServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

## API Usage Examples

### Upload KTP for Extraction

```bash
curl -X POST "http://localhost:8000/api/v1/ktp/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@ktp_image.jpg"
```

### Update KTP Data

```bash
curl -X PUT "http://localhost:8000/api/v1/ktp/{ktpId}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "address": "Updated Address"
  }'
```

### Generate Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "ktp_id": "uuid-of-ktp-data",
    "template_id": "uuid-of-template",
    "output_format": "PDF"
  }'
```

### Download Document

```bash
curl -X GET "http://localhost:8000/api/v1/documents/{documentId}/download" \
  -o "generated_document.pdf"