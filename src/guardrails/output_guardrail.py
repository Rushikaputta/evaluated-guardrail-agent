import json
import logging
import re
import torch
from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Production NLI model for hallucination detection
MODEL_NAME = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"

# Global model and tokenizer instances
_tokenizer = None
_model = None

def get_nli_model():
    global _tokenizer, _model
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    return _tokenizer, _model

def validate_output(answer: str, evidence: List[str]) -> Dict:
    """
    Production Output Guardrail using DeBERTa-v3 NLI.
    Checks for:
    1. Citation presence and validity.
    2. Hallucinations (via entailment check).
    3. Contradictions.
    """
    violations = []
    
    # 1. Citation Syntax Validation
    citations = re.findall(r'\[(\d+)\]', answer)
    if not citations:
        violations.append("No citations found in the generated answer.")
    else:
        for cit in citations:
            idx = int(cit) - 1
            if idx < 0 or idx >= len(evidence):
                violations.append(f"Invalid citation index detected: [{cit}]")

    # 2. Hallucination Detection (NLI)
    # Break answer into sentences for granular verification
    sentences = re.split(r'(?<=[.!?]) +', answer)
    tokenizer, model = get_nli_model()
    
    for sentence in sentences:
        # Map sentence to its cited evidence
        sentence_citations = re.findall(r'\[(\d+)\]', sentence)
        relevant_evidence = []
        for c in sentence_citations:
            idx = int(c) - 1
            if 0 <= idx < len(evidence):
                relevant_evidence.append(evidence[idx])
        
        if not relevant_evidence:
            # Sentence lacks citations but might contain claims
            continue
            
        premise = " ".join(relevant_evidence)
        hypothesis = sentence
        
        # NLI Inference
        inputs = tokenizer(premise, hypothesis, truncation=True, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            # Labels: 0: entailment, 1: neutral, 2: contradiction
            probs = torch.softmax(outputs.logits, dim=1).tolist()[0]
            
        entailment_score = probs[0]
        neutral_score = probs[1]
        contradiction_score = probs[2]
        
        if contradiction_score > 0.4:
            violations.append(f"Contradiction found: Claim '{sentence}' contradicts cited evidence.")
        elif entailment_score < 0.2:
            violations.append(f"Hallucination suspected: Claim '{sentence}' is not supported by evidence.")

    if violations:
        return {
            "status": "blocked",
            "reason": violations,
            "citations": list(set(citations))
        }
    
    return {
        "status": "passed",
        "reason": [],
        "citations": list(set(citations))
    }

def lambda_handler(event, context):
    logger.info("Output Guardrail processing event.")
    answer = event.get("answer", "")
    evidence = event.get("evidence", [])
    
    result = validate_output(answer, evidence)
    
    return {
        "statusCode": 200,
        "body": result
    }
