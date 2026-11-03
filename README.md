# Evaluated Guardrail Agent with Continuous Integration

This project implements a secure, production-ready RAG (Retrieval-Augmented Generation) agent architecture. It features multiple layers of security and validation to ensure that AI-generated responses are safe, factual, and free of sensitive information.

## 🏗️ Architecture Overview

The agent follows a multi-stage pipeline designed for enterprise-grade safety:

1.  **Permission Layer**: Validates the user's identity and permissions before any processing begins.
2.  **Input Guardrail**: Sanitizes the user query to prevent prompt injection, toxic input, or unauthorized requests.
3.  **Evidence Fetching & Redaction**:
    *   Retrieves evidence from internal sources (Mocked: Gmail, Jira, Notion).
    *   **PII Redactor**: Automatically identifies and masks Personally Identifiable Information (Emails, Phone numbers) before the data reaches the LLM.
4.  **OpenAI Orchestration**: Uses GPT-3.5-Turbo to generate a grounded response based strictly on the provided (and redacted) evidence.
5.  **NLI Output Guardrail**:
    *   Uses the **DeBERTa-v3-base-mnli-fever-anli** model to perform Natural Language Inference.
    *   Verifies that every claim in the generated answer is **entailed** by the evidence.
    *   Detects **hallucinations** and **contradictions**.
    *   Ensures all citations ([1], [2], etc.) are valid and accurate.

## 📁 Project Structure

*   `src/orchestrator/app.py`: The central logic that coordinates the entire pipeline.
*   `src/guardrails/input_guardrail.py`: Logic for filtering unsafe user inputs.
*   `src/guardrails/output_guardrail.py`: Advanced fact-checking using the DeBERTa-v3 NLI model.
*   `src/utils/pii_redactor.py`: Utility for masking sensitive information using regex.
*   `tests/test_agent.py`: Comprehensive test suite for all components.
*   `.github/workflows/ci.yml`: Continuous Integration pipeline for automated testing.
*   `template.yaml`: AWS SAM template for serverless deployment.

## 🚀 Getting Started

### Prerequisites
*   Python 3.12+
*   OpenAI API Key

### Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment:
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

### Running Tests
Verify the architecture and guardrails:
```bash
python -m pytest tests/test_agent.py
```

## 🛡️ Security & Compliance
*   **Least Privilege**: The AWS SAM template is configured for minimal IAM permissions.
*   **Data Privacy**: PII is redacted at the source before being processed by external AI providers.
*   **Factual Accuracy**: The NLI guardrail provides a mathematical confidence score for entailment, significantly reducing the risk of hallucinations.

## 🤖 Models Used
*   **Reasoning**: `gpt-3.5-turbo` (OpenAI)
*   **Fact-Checking (NLI)**: `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` (Hugging Face)
