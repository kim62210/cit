from __future__ import annotations


PRICING_PER_MILLION = {
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "opus": {"input": 15.0, "output": 75.0},
    "sonnet": {"input": 3.0, "output": 15.0},
}


def estimate_cost(model: str | None, input_tokens: int, output_tokens: int) -> float:
    if model is None:
        model = "claude-opus-4-6"
    pricing = PRICING_PER_MILLION.get(model, PRICING_PER_MILLION["claude-opus-4-6"])
    return round(
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"],
        2,
    )
