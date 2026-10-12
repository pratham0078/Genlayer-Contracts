# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json
import typing


class EvidenceResolver(gl.Contract):
    """
    Resolves a claim by fetching live web evidence from fixed source URLs
    and extracting a structured binary outcome via LLM.
    Validators independently re-derive the key decision fields.
    """
    claim: str
    source_urls: str
    resolved: bool
    outcome_satisfied: bool
    outcome_details: str

    def __init__(self, claim: str, source_urls_json: str):
        self.claim = claim
        self.source_urls = source_urls_json
        self.resolved = False
        self.outcome_satisfied = False
        self.outcome_details = ""

    @gl.public.write
    def resolve(self) -> typing.Any:
        if self.resolved:
            return {"status": "already_resolved", "satisfied": self.outcome_satisfied}

        urls = json.loads(self.source_urls)

        def leader_fn() -> str:
            evidence_parts = []
            for url in urls:
                resp = gl.nondet.web.get(url)
                body = resp.body.decode("utf-8") if resp.body else ""
                evidence_parts.append(f"Source: {url}\n{body[:8000]}")
            evidence = "\n\n---\n\n".join(evidence_parts)

            prompt = f"""You are an impartial adjudicator.
Claim to evaluate: {self.claim}

Evidence from independent sources:
{evidence}

Determine whether the claim is satisfied based solely on the evidence.
Respond ONLY with valid JSON:
{{
  "satisfied": true or false,
  "confidence": "high" or "medium" or "low",
  "details": "brief factual summary citing evidence"
}}
No other text, no markdown fences.
"""
            raw = gl.nondet.exec_prompt(prompt)
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned)
            return json.dumps({
                "satisfied": bool(parsed["satisfied"]),
                "confidence": str(parsed.get("confidence", "medium")),
                "details": str(parsed.get("details", ""))[:500]
            }, sort_keys=True)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                my_raw = leader_fn()
                leader_data = json.loads(leader_result.calldata)
                my_data = json.loads(my_raw)
                return (
                    leader_data["satisfied"] == my_data["satisfied"]
                    and leader_data["confidence"] == my_data["confidence"]
                )
            except Exception:
                return False

        result_json = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))

        self.resolved = True
        self.outcome_satisfied = result_json["satisfied"]
        self.outcome_details = result_json["details"]
        return result_json

    @gl.public.view
    def get_outcome(self) -> typing.Any:
        return {
            "claim": self.claim,
            "resolved": self.resolved,
            "satisfied": self.outcome_satisfied,
            "details": self.outcome_details
        }
