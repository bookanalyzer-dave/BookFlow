# Integration Plan: On-Demand Condition Assessment

## Overview

The goal is to enable users to trigger a professional condition assessment for any ingested book with a single click. The assessment will utilize all existing images and metadata (e.g., publication year) already collected during ingestion.

## Requirements

1.  **User Interface:** A "Assess Condition" (Zustand bewerten) button in the book detail view.
2.  **Data Source:** Use existing `imageUrls` (GCS URIs) and metadata from the book document.
3.  **Processing:**
    *   `condition-assessor` agent must accept GCS URIs directly (no download/re-upload).
    *   Agent must handle unclassified images (process all provided images).
    *   Agent should consider book metadata for context.

## Design

### 1. Backend API (`dashboard/backend/main.py`)

Update the `POST /api/books/assess-condition` endpoint:
*   **Input:** Accepts `bookId`.
*   **Logic:**
    1.  Fetch the book document from Firestore using `bookId`.
    2.  Extract `imageUrls` and relevant metadata (`title`, `authors`, `publication_year`, `edition`, `publisher`).
    3.  Create a payload for `condition_assessment_requests`:
        ```json
        {
          "book_id": "...",
          "uid": "...",
          "status": "pending",
          "images": [
            { "gcs_uri": "gs://...", "type": "unknown" },
            ...
          ],
          "metadata": {
            "title": "...",
            "year": "...",
            ...
          }
        }
        ```
    4.  Write to Firestore to trigger the agent.
    5.  Update book status to `condition_assessment_pending`.

### 2. Condition Assessor Agent (`agents/condition-assessor/main.py`)

*   **`assess_condition_handler`:** Update to parse the new payload structure (list of `gcs_uri`).
*   **`VertexAIConditionAssessor`:**
    *   Update `_analyze_image` to support `vision.ImageSource(gcs_image_uri=...)`.
    *   Relax image type requirements (handle "unknown" types gracefully, perhaps by trying to infer or just assessing general physical condition).
    *   Incorporate `book_metadata` (e.g., year) into the assessment logic (e.g., older books might have different standards for "Fine").

### 3. Frontend (`dashboard/frontend`)

*   **`components/BookList.jsx`:**
    *   Add a "Zustand bewerten" button in the expanded book view.
    *   Call `POST /api/books/assess-condition`.
    *   Display loading state while request is initiated.
    *   (Optional) Refresh/poll for status or listen to snapshot updates (which `BookList` already does) to show the result when ready.

*   **`components/ConditionAssessment.jsx`:**
    *   Update to support "Assessing existing images" mode if needed, or primarily rely on `BookList` for the trigger and display results there or link to this component. *Decision: Keep `ConditionAssessment.jsx` for detailed view/manual upload, but add the quick trigger to `BookList`.*

## Implementation Steps

1.  **Modify `agents/condition-assessor/main.py`**: Support GCS URIs and generic image inputs.
2.  **Modify `dashboard/backend/main.py`**: Update logic to fetch book data and create the simplified trigger payload.
3.  **Modify `dashboard/frontend/src/components/BookList.jsx`**: Add the button and handler.

## Questions/Clarifications resolved from User
*   "Types of images don't matter" -> Agent will treat them as generic views.
*   "Use collected metadata" -> Backend will forward `publication_year`, etc.