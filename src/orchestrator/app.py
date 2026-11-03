import json
import logging
import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def has_permission(user_id: str, action: str) -> bool:
    """
    Mock permission check.
    In production, this would integrate with IAM or an Identity Provider.
    """
    if user_id == "admin":
        return True
    if user_id == "authorized_user" and action == "search":
        return True
    return False

def lambda_handler(event, context):
    logger.info(f"Orchestrator received event: {json.dumps(event)}")
    
    user_query = event.get("query", "")
    user_id = event.get("user_id", "anonymous")
    
    # 0. Permission Layer
    if not has_permission(user_id, "search"):
        return {
            "statusCode": 403,
            "body": json.dumps({
                "error": "Permission denied",
                "details": f"User {user_id} does not have search permissions."
            })
        }
    
    # 1. Input Guardrail
    from guardrails.input_guardrail import check_input
    input_check = check_input(user_query)
    
    if input_check["status"] == "blocked":
        return {
            "statusCode": 403,
            "body": json.dumps({
                "error": "Input blocked by guardrails",
                "details": input_check["reason"]
            })
        }

    # 2. Decompose (Simulated)
    sub_queries = decompose_query(user_query)
    
    # 3. Fetch Evidence (Mocked company sources)
    evidence = fetch_evidence(sub_queries)
    
    # 4. PII Redaction
    from utils.pii_redactor import redact_pii
    redacted_evidence = [redact_pii(e) for e in evidence]
    
    # 5. Generate Final Answer with OpenAI
    final_answer = generate_openai_answer(user_query, redacted_evidence)
    
    # 6. Output Validation (NLI-based with DeBERTa-v3)
    from guardrails.output_guardrail import validate_output
    output_check = validate_output(final_answer, redacted_evidence)
    
    if output_check["status"] == "blocked":
         return {
            "statusCode": 403,
            "body": json.dumps({
                "error": "Output blocked by guardrails",
                "details": output_check["reason"]
            })
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "answer": final_answer,
            "citations": output_check.get("citations", []),
            "metadata": {
                "input_guardrail": "passed",
                "output_validation": "passed",
                "model_used": "gpt-3.5-turbo"
            }
        })
    }

def decompose_query(query: str) -> List[str]:
    return [f"Search company records for: {query}"]

def fetch_evidence(queries: List[str]) -> List[str]:
    # In production, this would connect to Gmail, Notion, Jira APIs
    return [
        "Project X status: Currently in development. Target launch: 2026-12-01.",
        "Team lead: Alice (alice@company.com). Contact: 555-0199."
    ]

def generate_openai_answer(query: str, evidence: List[str]) -> str:
    context = "\n".join([f"[{i+1}] {e}" for i, e in enumerate(evidence)])
    prompt = (
        f"You are a helpful assistant. Use the following evidence to answer the query: {query}\n\n"
        f"Evidence:\n{context}\n\n"
        f"Strictly follow these rules:\n"
        f"1. Cite the evidence using [1], [2], etc.\n"
        f"2. If the evidence doesn't contain the answer, say you don't know.\n"
        f"3. Do not include any PII in the final answer."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        return "Error generating response from AI provider."
