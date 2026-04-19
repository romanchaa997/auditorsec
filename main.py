from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI
import tiktoken
import redis.asyncio as redis
import json
import hashlib
import os
from datetime import datetime

app = FastAPI(
    title="AuditorSEC API",
    description="Crypto compliance & security audit platform",
    version="0.1.0"
)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))


class AuditRequest(BaseModel):
    project_name: str
    log_text: str
    audit_type: str = "health_check"


class AuditResponse(BaseModel):
    project_name: str
    audit_type: str
    anomalies: list[str]
    risk_level: str
    recommendations: list[str]
    token_count: int
    cached: bool
    timestamp: str


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def truncate_to_limit(text: str, max_tokens: int = 3000) -> str:
    """Truncates log to token limit - key memory optimization"""
    enc = tiktoken.encoding_for_model("gpt-4o")
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens]) + "\n[LOG TRUNCATED]"


def build_cache_key(project: str, log: str, audit_type: str) -> str:
    content = f"{project}:{audit_type}:{log[:500]}"
    return f"audit:{hashlib.sha256(content.encode()).hexdigest()[:16]}"


SYSTEM_PROMPTS = {
    "health_check": """You are a senior security auditor for Ukrainian crypto projects.
Analyze the provided log/description and return JSON with fields:
- anomalies: list of found issues (array of strings)
- risk_level: overall risk level (LOW/MEDIUM/HIGH/CRITICAL)
- recommendations: specific remediation steps (array, max 5)
Focus: key management, AML/KYC, operational security, UA regulatory risks.
Respond with ONLY valid JSON, no markdown.""",

    "threat_model": """You are a threat modeling expert for Ukrainian crypto businesses.
Analyze the system description and return JSON:
- anomalies: identified attack vectors and vulnerabilities
- risk_level: criticality (LOW/MEDIUM/HIGH/CRITICAL)
- recommendations: priority defensive measures
Consider: DFRR/DBR risks, sanctions risks, insider threats.
Respond with ONLY valid JSON.""",

    "key_mgmt": """You are a cryptographic key management auditor (NIS2-compliant).
Analyze the description and return JSON:
- anomalies: violations of key management best practices
- risk_level: risk level (LOW/MEDIUM/HIGH/CRITICAL)
- recommendations: steps toward NIS2 and UA standard compliance
Respond with ONLY valid JSON."""
}


@app.post("/api/v1/audit", response_model=AuditResponse)
async def run_audit(request: AuditRequest):
    if request.audit_type not in SYSTEM_PROMPTS:
        raise HTTPException(
            status_code=400,
            detail=f"audit_type must be one of: {list(SYSTEM_PROMPTS.keys())}"
        )

    cache_key = build_cache_key(request.project_name, request.log_text, request.audit_type)
    cached = await redis_client.get(cache_key)
    if cached:
        result = json.loads(cached)
        result["cached"] = True
        return AuditResponse(**result)

    truncated_log = truncate_to_limit(request.log_text, max_tokens=3000)
    token_count = count_tokens(truncated_log)
    user_message = f"Project: {request.project_name}\n\nLog/description for analysis:\n{truncated_log}"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS[request.audit_type]},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")

    try:
        llm_result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse LLM response")

    result = {
        "project_name": request.project_name,
        "audit_type": request.audit_type,
        "anomalies": llm_result.get("anomalies", []),
        "risk_level": llm_result.get("risk_level", "MEDIUM"),
        "recommendations": llm_result.get("recommendations", []),
        "token_count": token_count,
        "cached": False,
        "timestamp": datetime.utcnow().isoformat()
    }

    await redis_client.setex(cache_key, 3600, json.dumps(result))
    return AuditResponse(**result)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AuditorSEC API", "version": "0.1.0"}
