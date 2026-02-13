# Race Condition and Model Quota Fix Plan

## Objective
Fix the race condition and model quota issues by:
1.  Aligning the workflow sequentially: Ingestion Agent -> Strategist Agent.
2.  Downgrading the Condition Assessor model to `gemini-2.5-flash` to save quota/costs.
3.  Ensuring Strategist Agent correctly consumes the Ingestion Agent's output.

## Proposed Changes

### 1. Agents
#### `agents/condition-assessor/main.py`
-   **Change:** Update `VertexAIConditionAssessor` configuration.
-   **Detail:** Change `self.model_name` from `"gemini-2.5-pro"` to `"gemini-2.5-flash"`.

#### `agents/strategist-agent/main.py`
-   **Change:** Update `strategist_agent_main` to handle Ingestion Agent's message format.
-   **Detail:** The Ingestion Agent publishes messages with keys `book_id` and `user_id`. The Strategist Agent currently expects `bookId` and `uid`. Update the extraction logic to support both formats:
    ```python
    book_id = message_data.get('bookId') or message_data.get('book_id')
    uid = message_data.get('uid') or message_data.get('user_id')
    ```

### 2. Infrastructure / Deployment
#### `scripts/deploy_all.sh`
-   **Change:** Add a step to configure the Pub/Sub subscription for the Strategist Agent.
-   **Detail:** The Strategist Agent needs to trigger on the `condition-assessment-jobs` topic (Output of Ingestion Agent).
    -   Retrieve the Cloud Run service URL for `strategist-agent`.
    -   Create or update a Pub/Sub push subscription `strategist-agent-subscription` attached to topic `condition-assessment-jobs` with the push endpoint set to the service URL.

## Workflow Alignment
-   **Old Flow:** Ingestion -> `condition-assessment-jobs` -> Condition Assessor.
-   **New Flow:** Ingestion -> `condition-assessment-jobs` -> Strategist Agent (and potentially Condition Assessor parallel if not disabled, but Strategist is now the primary consumer).
-   **Note:** This change assumes the Strategist Agent acts as the orchestrator or next step. If the Condition Assessor still listens to `condition-assessment-jobs`, they will run in parallel. To strictly enforce sequentiality (Strategist -> Condition Assessor), the Condition Assessor's trigger would ideally be changed, but for this task, we focus on enabling the Strategist to listen to the Ingestion output.

