"""Rank knowledge gaps and turn useful answers into memory candidates."""

from numbers import Real


WEIGHTS = {
    "utility": 0.35,
    "recurrence": 0.2,
    "confidence_gap": 0.25,
    "urgency": 0.2,
}

PENALTIES = {
    "interruption_cost": 0.5,
    "sensitivity": 0.5,
}


def _factor(gap, name):
    value = gap.get(name)
    if isinstance(value, bool) or not isinstance(value, Real):
        return 0.0
    return min(1.0, max(0.0, float(value)))


def score(gap):
    """Return the rounded value of a gap, including its penalties."""
    value = sum(weight * _factor(gap, name) for name, weight in WEIGHTS.items())
    value -= sum(weight * _factor(gap, name) for name, weight in PENALTIES.items())
    return round(value, 4)


def why(gap):
    """Explain the strongest positive factors and any applied penalties."""
    contributors = sorted(
        ((name, WEIGHTS[name] * _factor(gap, name)) for name in WEIGHTS),
        key=lambda item: (-item[1], item[0]),
    )
    parts = [f"{name} {_factor(gap, name):.2f}" for name, contribution in contributors[:3] if contribution > 0]
    explanation = f"score {score(gap):.2f}: " + ", ".join(parts)
    penalties = [
        f"{name} {_factor(gap, name):.2f}"
        for name in PENALTIES
        if _factor(gap, name) > 0
    ]
    if penalties:
        explanation += "; penalised by " + ", ".join(penalties)
    return explanation


def select_questions(gaps, *, budget=1, min_score=0.2, asked_ids=()):
    """Choose the highest-value unanswered questions within the budget."""
    asked = set(asked_ids)
    discarded = []
    candidates = []
    for gap in gaps:
        if not isinstance(gap, dict):
            continue
        gap_id = gap.get("id")
        question = gap.get("question")
        if not isinstance(gap_id, str) or not gap_id.strip() or not isinstance(question, str) or not question.strip():
            continue
        value = score(gap)
        item = {
            "id": gap_id,
            "question": question,
            "topic": gap.get("topic"),
            "score": value,
            "why": why(gap),
            "reason": None,
        }
        if gap_id in asked:
            item["reason"] = "already_asked"
            discarded.append(item)
        elif value < min_score:
            item["reason"] = "low_value"
            discarded.append(item)
        else:
            candidates.append(item)

    candidates.sort(key=lambda item: (-item["score"], item["id"]))
    count = max(budget, 0)
    selected = candidates[:count]
    deferred = candidates[count:]
    for item in deferred:
        item["reason"] = "over_budget"
    return {"ask": selected, "deferred": deferred, "discarded": discarded, "budget": budget}


def answer_to_candidate(gap, answer, *, source):
    """Represent a non-empty answer as a candidate preference memory."""
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("answer must be non-empty")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be non-empty")
    return {
        "kind": "preference_candidate",
        "statement": f"{gap['question'].strip()} -> {answer.strip()}",
        "evidence": [f"knowledge-gap:{gap['id']}", source],
        "confidence": 0.7,
    }
