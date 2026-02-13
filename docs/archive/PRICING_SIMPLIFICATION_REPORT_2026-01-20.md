# Pricing Simplification Report

**Date:** 2026-01-20
**Status:** Implemented

## Summary
This report documents the architectural transition from a complex multi-agent pricing ecosystem to a single, consolidated "Pricing Agent" (implemented within the `strategist-agent`). This change dramatically simplifies the workflow, reduces latency, and leverages the advanced capabilities of next-generation models.

## New Workflow
The pipeline has been streamlined to a direct hand-off:

**`condition-assessor` -> `strategist-agent`**

1.  **Condition Assessor:** Analyzes book images to determine condition, ISBN, and basic metadata.
2.  **Strategist Agent (The "Pricing Agent"):** Receives the assessment and performs a comprehensive pricing analysis in a single, powerful step.

## Key Features

### 1. Gemini 2.5 Pro "Super Request"
We have transitioned to using **Gemini 2.5 Pro** to handle a "Super Request". Instead of chaining multiple smaller, specialized LLM calls (e.g., one for research, one for strategy, one for calculation), we now issue a single comprehensive prompt that covers all aspects of the pricing task.

### 2. Multimodal (Images + Text)
The agent now processes inputs multimodally. It ingests the book images (via GCS URIs) and the text metadata simultaneously. This allows the model to "see" the book's condition nuances while processing the market data, leading to more accurate value assessments.

### 3. Live Market Research (Google Search Tool)
The `strategist-agent` is equipped with the **Google Search Tool**. This enables:
*   Real-time lookup of current market prices.
*   Verification of bibliographic details against live web data.
*   Identification of competitor listings on major platforms.

### 4. Centralized Decision Making
All pricing logic is now centralized. This eliminates:
*   Overhead from inter-agent communication.
*   Conflicts between competing strategies (e.g., "aggressive" vs "conservative" agents).
*   Complexity in state management.

## Technical Details

### UserLLMManager Updates
The `UserLLMManager` (located in `shared/user_llm_manager`) has been upgraded to support:
*   **GCS URI Support:** The `google.py` provider now correctly formats and passes Google Cloud Storage URIs for images directly to the Gemini model, bypassing the need for local image downloads in the agent.
*   **Model Versioning:** Updated configurations to target `gemini-2.5-pro` (or the latest preview equivalent).

### Simplified Strategist Agent
The `strategist-agent` logic (`agents/strategist-agent/main.py`) has been refactored:
*   **Removed:** Complex state machines and sub-agent orchestration logic.
*   **Added:** A streamlined handler that constructs the "Super Request", invokes the LLM with search tools enabled, and parses the structured JSON response containing the final price and reasoning.
