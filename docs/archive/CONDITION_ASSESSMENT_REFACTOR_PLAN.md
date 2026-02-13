# Refactoring Plan: Generative AI Condition Assessor

## 1. Overview
We are refactoring the `condition-assessor` agent to move from a rule-based, component-specific approach (using Google Cloud Vision API) to a holistic, Generative AI approach using **Gemini Pro Vision** via the `UserLLMManager`.

**Goal:** utilize the "understanding" capabilities of Large Multimodal Models (LMMs) to assess book condition like a human specialist, handling unstructured image inputs without requiring pre-classification.

## 2. Architecture Changes

### 2.1. Current vs. Desired State

| Feature | Current State | Desired State |
| :--- | :--- | :--- |
| **Engine** | Google Cloud Vision API (Object/Text Detection) | Gemini 1.5 Pro (via `UserLLMManager`) |
| **Input** | Classified images (`type: cover`, etc.) | Flat list of images (Raw GCS URIs) |
| **Logic** | Mathematical rules, keyword matching, color analysis | LLM Reasoning (Prompt Engineering) |
| **Context** | Single image analysis, aggregated later | Multi-image simultaneous analysis |
| **Output** | Calculated score, inferred grade | Structured JSON with reasoning & grade |

### 2.2. Class Structure (`VertexAIConditionAssessor`)

The `VertexAIConditionAssessor` class in `agents/condition-assessor/main.py` will be significantly simplified.

**Key Changes:**
1.  **Remove:**
    *   `vision_client` and all related methods (`_detect_objects`, `_detect_text`, `_analyze_image_properties`, etc.).
    *   Hardcoded `defect_patterns` and scoring weights (let the LLM handle weighing).
    *   Complex aggregation logic (`_calculate_component_scores`, `_calculate_overall_score`).
2.  **Add/Update:**
    *   `llm_manager`: Ensure strictly typed usage of `UserLLMManager`.
    *   `assess_book_condition`: The main entry point. It will:
        1.  Download images from GCS URIs into memory (base64).
        2.  Construct a multi-modal prompt (Text Instructions + List of Base64 Images).
        3.  Call `llm_manager.generate_text()` with the constructed request.
        4.  Parse the JSON response from the LLM.
        5.  Map the LLM output to the system's expected data structure (`ConditionScore`).

### 2.3. Handling GCS Images
The `UserLLMManager` (Google Provider) expects base64 encoded image data for multi-modal requests. The Agent will be responsible for:
1.  Receiving the list of `gcs_uri`s from the input payload.
2.  Using `google.cloud.storage` to download the image bytes.
3.  Encoding bytes to base64 strings.
4.  Passing these to the LLM Manager.

## 3. Prompt Engineering

**Role:** Expert Antiquarian Bookseller & Professional Grader.
**Standard:** ABAA (Antiquarian Booksellers' Association of America).

**System Prompt Draft:**
```text
You are an expert antiquarian bookseller and professional book condition grader.
You have been provided with a set of images of a single book.

Your task is to:
1.  Analyze ALL images collectively to form a holistic understanding of the book.
2.  Identify the book components shown (Cover, Spine, Pages/Text Block, Binding).
3.  Detect specific physical defects (e.g., foxing, staining, tears, chipping, sunning, cracked hinges, detachment).
4.  Determine the overall condition grade based on standard ABAA criteria:
    *   **Fine (F):** Like new, no defects.
    *   **Very Fine (VF):** Exceptional condition, very minor signs of wear.
    *   **Good (G):** Complete and readable, but with average wear and defects.
    *   **Fair:** Worn, may be missing endpapers, text complete but binding loose.
    *   **Poor:** Reading copy only, significant damage.
5.  Assign a numerical score (0-100) that aligns with the grade.
6.  Estimate a "Price Factor" (0.1 to 1.0) representing how much of the "Mint" value this copy retains.

Output strictly valid JSON matching the defined schema.
```

## 4. Data Models & Schema

### 4.1. LLM Output JSON Schema
```json
{
  "grade": "Fine",
  "score": 92,
  "price_factor": 0.95,
  "confidence": 0.9,
  "summary": "An exceptional copy with bright boards...",
  "defects": [
    "Minor shelf wear on bottom edge",
    "Faint foxing on top text block"
  ],
  "components": {
    "cover": {
      "score": 90,
      "description": "Bright and clean, minimal wear."
    },
    "spine": {
      "score": 95,
      "description": "Intact, gold lettering bright."
    },
    "pages": {
      "score": 88,
      "description": "Clean, no marking, slight age toning."
    },
    "binding": {
      "score": 95,
      "description": "Tight and square."
    }
  }
}
```

### 4.2. Frontend/Database Compatibility
The result must map to the `ConditionScore` dataclass to ensure the `assess_condition_handler` writes correctly to Firestore.

*   `overall_score` &rarr; `score`
*   `grade` &rarr; `grade` (mapped to Enum)
*   `confidence` &rarr; `confidence`
*   `details` &rarr; Flattened `components` + `summary` + `defects` list.

## 5. Implementation Steps

1.  **Create Prompt Template:** Define the exact prompt in `prompts.py` (or inside `main.py` if simple).
2.  **Refactor `VertexAIConditionAssessor`:**
    *   Implement `_fetch_images(images_list)` helper.
    *   Implement `_construct_prompt(metadata)` helper.
    *   Rewrite `assess_book_condition` to use the LLM.
3.  **Update Dependencies:** Remove `google-cloud-vision` if fully replaced, or keep as fallback (unlikely needed). Ensure `google-cloud-storage` is available.
4.  **Testing:**
    *   Update `test_condition_assessment` to use real images or mock the LLM response.
    *   Verify JSON parsing resilience.

## 6. Risks & Mitigation
*   **Latency:** Processing multiple high-res images with Gemini can be slow.
    *   *Mitigation:* Resize images before sending to LLM if necessary (max 1024px).
*   **Cost:** Multimodal tokens are more expensive than Vision API labels.
    *   *Mitigation:* Use `gemini-1.5-flash` for a balance of speed/cost vs `pro`.
*   **Hallucination:** LLM might invent defects.
    *   *Mitigation:* High temperature setting? No, **Low temperature (0.1)** to ensure analytical consistency.