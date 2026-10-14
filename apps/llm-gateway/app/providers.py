"""Model-based guardrail adapters chained after the deterministic rules.

Each adapter is enabled purely by environment variables, so the same container runs
on the laptop (Llama Guard via Ollama), on GCP (Model Armor), on AWS (Bedrock
ApplyGuardrail) and on Azure (AI Content Safety Prompt Shields). This is the
"cloud-agnostic guardrail control plane" pattern: one policy decision point,
many policy information points.

FAIL_MODE=closed  -> a detector outage blocks the request (BFSI default)
FAIL_MODE=open    -> a detector outage is logged and the request proceeds
"""
from __future__ import annotations

import asyncio
import logging
import os

import httpx

from .guardrails import Finding

log = logging.getLogger("gateway.providers")
TIMEOUT = float(os.getenv("DETECTOR_TIMEOUT_S", "5"))


class Detector:
    name = "base"

    def enabled(self) -> bool:
        return False

    async def scan(self, text: str, direction: str) -> list[Finding]:
        raise NotImplementedError


class LlamaGuardOllama(Detector):
    """Meta Llama Guard 3 served locally by Ollama (`ollama pull llama-guard3:1b`)."""
    name = "llama-guard"

    def enabled(self) -> bool:
        return bool(os.getenv("LLAMA_GUARD_URL"))

    async def scan(self, text: str, direction: str) -> list[Finding]:
        role = "user" if direction == "input" else "assistant"
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.post(f"{os.environ['LLAMA_GUARD_URL']}/api/chat", json={
                "model": os.getenv("LLAMA_GUARD_MODEL", "llama-guard3:1b"),
                "messages": [{"role": role, "content": text}], "stream": False})
            r.raise_for_status()
            verdict = r.json()["message"]["content"].strip().lower()
        if verdict.startswith("unsafe"):
            cats = verdict.split("\n", 1)[1] if "\n" in verdict else "?"
            return [Finding("LG-unsafe", f"llama-guard:{cats}", "high", "Llama Guard flagged content")]
        return []


class GoogleModelArmor(Detector):
    """Google Cloud Model Armor sanitizeUserPrompt / sanitizeModelResponse."""
    name = "model-armor"

    def enabled(self) -> bool:
        return bool(os.getenv("MODEL_ARMOR_TEMPLATE"))  # projects/P/locations/L/templates/T

    async def _token(self) -> str:
        if tok := os.getenv("GCP_ACCESS_TOKEN"):
            return tok
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:  # Cloud Run metadata server
            r = await c.get("http://metadata.google.internal/computeMetadata/v1/instance/"
                            "service-accounts/default/token", headers={"Metadata-Flavor": "Google"})
            r.raise_for_status()
            return r.json()["access_token"]

    async def scan(self, text: str, direction: str) -> list[Finding]:
        tpl = os.environ["MODEL_ARMOR_TEMPLATE"]
        location = tpl.split("/")[3]
        op, key = (("sanitizeUserPrompt", "userPromptData") if direction == "input"
                   else ("sanitizeModelResponse", "modelResponseData"))
        url = f"https://modelarmor.{location}.rep.googleapis.com/v1/{tpl}:{op}"
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.post(url, json={key: {"text": text}},
                             headers={"Authorization": f"Bearer {await self._token()}"})
            r.raise_for_status()
            result = r.json().get("sanitizationResult", {})
        if result.get("filterMatchState") == "MATCH_FOUND":
            return [Finding("MA-match", "model-armor", "high", "Model Armor filter matched")]
        return []


class AzurePromptShields(Detector):
    """Azure AI Content Safety - Prompt Shields (direct + indirect injection)."""
    name = "azure-prompt-shields"

    def enabled(self) -> bool:
        return bool(os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT") and os.getenv("AZURE_CONTENT_SAFETY_KEY"))

    async def scan(self, text: str, direction: str) -> list[Finding]:
        if direction != "input":
            return []
        url = (f"{os.environ['AZURE_CONTENT_SAFETY_ENDPOINT'].rstrip('/')}"
               "/contentsafety/text:shieldPrompt?api-version=2024-09-01")
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.post(url, json={"userPrompt": text, "documents": []},
                             headers={"Ocp-Apim-Subscription-Key": os.environ["AZURE_CONTENT_SAFETY_KEY"]})
            r.raise_for_status()
            body = r.json()
        if body.get("userPromptAnalysis", {}).get("attackDetected"):
            return [Finding("AZ-prompt-attack", "azure-prompt-shields", "high", "Prompt Shields attack")]
        return []


class BedrockGuardrail(Detector):
    """Amazon Bedrock ApplyGuardrail API (works without invoking a model)."""
    name = "bedrock-guardrail"

    def enabled(self) -> bool:
        return bool(os.getenv("BEDROCK_GUARDRAIL_ID"))

    async def scan(self, text: str, direction: str) -> list[Finding]:
        import asyncio

        import boto3  # optional dependency, only needed on AWS

        client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "ap-south-1"))
        resp = await asyncio.to_thread(
            client.apply_guardrail,
            guardrailIdentifier=os.environ["BEDROCK_GUARDRAIL_ID"],
            guardrailVersion=os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT"),
            source="INPUT" if direction == "input" else "OUTPUT",
            content=[{"text": {"text": text}}],
        )
        if resp.get("action") == "GUARDRAIL_INTERVENED":
            return [Finding("BR-intervened", "bedrock-guardrail", "high", "Bedrock Guardrail intervened")]
        return []


DETECTORS: list[Detector] = [LlamaGuardOllama(), GoogleModelArmor(), AzurePromptShields(), BedrockGuardrail()]


async def run_detectors(text: str, direction: str, allow=None) -> list[Finding]:
    """`allow(name) -> bool` lets the caller withhold the text from detectors it may not be sent to (data residency)."""
    fail_closed = os.getenv("FAIL_MODE", "closed") == "closed"
    enabled = [d for d in DETECTORS if d.enabled() and (allow is None or allow(d.name))]

    async def _one(d: "Detector") -> list[Finding]:
        try:
            return await d.scan(text, direction)
        except Exception as exc:  # noqa: BLE001 - detector outage handling is the point
            log.warning("detector %s failed: %s", d.name, exc)
            sev = "high" if fail_closed else "low"
            return [Finding(f"DET-unavailable-{d.name}", "availability", sev, str(exc)[:120])]

    # Run enabled detectors concurrently: per-request latency is the MAX of their round-trips,
    # not the sum (chat() calls this per message and per choice, so the saving compounds).
    results = await asyncio.gather(*[_one(d) for d in enabled])
    findings: list[Finding] = []
    for r in results:
        findings += r
    return findings


def active_detectors() -> list[str]:
    return [d.name for d in DETECTORS if d.enabled()]
