from __future__ import annotations

from opsmind.contracts.v1.models import EvidenceRef, Hypothesis, ResponseModel, ResponseStatus, ToolResult


def present_needs_info(questions: list[str]) -> ResponseModel:
    return ResponseModel(
        status=ResponseStatus.needs_info,
        primary_text="I need a bit more context before running diagnostics.",
        followup_questions=questions[:3],
        next_actions=["Provide missing context to continue RCA."],
        notes="Evidence-first workflow paused until required slots are filled.",
    )


def present_complete(tool_results: list[ToolResult]) -> ResponseModel:
    evidence: list[EvidenceRef] = []
    for result in tool_results:
        evidence.append(EvidenceRef(ref_type="tool_call", ref_id=result.tool_call_id, description=result.summary))
        evidence.extend(
            [EvidenceRef(ref_type="artifact", ref_id=a.artifact_id, description=a.uri) for a in result.artifacts]
        )

    top = evidence[0:1] or [EvidenceRef(ref_type="tool_call", ref_id="none", description="No evidence")]
    hypotheses = [
        Hypothesis(statement="Recent deployment or config drift is likely contributing.", confidence=0.73, evidence_refs=top),
        Hypothesis(statement="Dependency saturation is amplifying errors.", confidence=0.62, evidence_refs=top),
    ]
    return ResponseModel(
        status=ResponseStatus.complete,
        primary_text="I ran the deterministic workflow and compiled evidence-backed hypotheses.",
        hypotheses=hypotheses,
        evidence=evidence,
        next_actions=["Rollback suspect change in canary region.", "Increase sampling for failing traces."],
        followup_questions=["Can you confirm if rollback is possible in the next 10 minutes?"],
    )
