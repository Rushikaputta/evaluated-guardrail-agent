import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def check_input(text: str) -> dict:
    """
    Evaluates input text for potential guardrail violations.
    In a real scenario, this might call a specialized model or use regex/lexicons.
    """
    # Simple example: check for forbidden keywords or toxic language
    forbidden_keywords = ["secret_password", "malicious_payload"]
    
    violations = []
    for keyword in forbidden_keywords:
        if keyword in text.lower():
            violations.append(f"Forbidden keyword detected: {keyword}")
            
    if violations:
        return {
            "status": "blocked",
            "reason": violations
        }
    
    return {
        "status": "passed",
        "reason": []
    }

def lambda_handler(event, context):
    logger.info(f"Input Guardrail received event: {json.dumps(event)}")
    
    text = event.get("text", "")
    result = check_input(text)
    
    return {
        "statusCode": 200,
        "body": result
    }
