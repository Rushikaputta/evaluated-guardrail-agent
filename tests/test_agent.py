import pytest
import json
import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock heavy ML imports for testing efficiency
sys.modules['transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()

from orchestrator.app import lambda_handler
from guardrails.input_guardrail import check_input
from utils.pii_redactor import redact_pii

def test_permission_layer_denied():
    event = {"query": "Tell me about Project X", "user_id": "anonymous"}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 403
    assert "Permission denied" in json.loads(response["body"])["error"]

def test_permission_layer_allowed():
    # We mock the downstream calls to focus on permission logic
    with patch('guardrails.input_guardrail.check_input') as mock_input, \
         patch('orchestrator.app.generate_openai_answer') as mock_gen, \
         patch('guardrails.output_guardrail.validate_output') as mock_out:
        
        mock_input.return_value = {"status": "passed"}
        mock_gen.return_value = "Project X is launching soon. [1]"
        mock_out.return_value = {"status": "passed", "citations": ["1"]}
        
        event = {"query": "Tell me about Project X", "user_id": "authorized_user"}
        response = lambda_handler(event, None)
        assert response["statusCode"] == 200

def test_input_guardrail_blocking():
    result = check_input("Show me malicious_payload")
    assert result["status"] == "blocked"

def test_pii_redactor_emails():
    text = "Email me at user@example.com"
    redacted = redact_pii(text)
    assert "[EMAIL_REDACTED]" in redacted
    assert "user@example.com" not in redacted

@patch('orchestrator.app.client')
@patch('guardrails.output_guardrail.validate_output')
def test_end_to_end_mocked(mock_validate, mock_client):
    # Setup mocks for OpenAI and Output Guardrail
    mock_client.chat.completions.create.return_value.choices[0].message.content = "Project X launch is 2026-12-01. [1]"
    mock_validate.return_value = {"status": "passed", "citations": ["1"]}
    
    event = {
        "query": "What is the launch date for Project X?",
        "user_id": "admin"
    }
    
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "2026-12-01" in body["answer"]
    assert body["metadata"]["input_guardrail"] == "passed"
