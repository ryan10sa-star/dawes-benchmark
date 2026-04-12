"""
DAWES Benchmark Runner
Domain-Adaptive Weights for Expert Systems

Core benchmark execution engine for scoring AI model responses
on Instrumentation & Controls domain knowledge.

Scoring: Each question scored 0-3
  0 = wrong
  1 = partial
  2 = correct
  3 = correct + reasoning

Max score per 60-question run: 180
Results reported as percentage.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Judge provider configurations
JUDGE_PROVIDERS = {
    "anthropic": {
        "name": "Anthropic Claude",
        "api_env": "ANTHROPIC_API_KEY",
        "model": "claude-3-5-sonnet-20241022",
    },
    "openai": {
        "name": "OpenAI GPT-4o",
        "api_env": "OPENAI_API_KEY",
        "model": "gpt-4o",
    },
    "gemini": {
        "name": "Google Gemini",
        "api_env": "GOOGLE_API_KEY",
        "model": "gemini-1.5-pro",
    },
}

JUDGE_SYSTEM_PROMPT = (
    "You are an expert scorer for the DAWES Benchmark — an Instrumentation "
    "& Controls domain knowledge test. Score the following answer on a 0-3 scale:\n"
    "  0 = Wrong or no answer\n"
    "  1 = Partially correct\n"
    "  2 = Correct\n"
    "  3 = Correct with strong reasoning\n\n"
    "Respond with ONLY a JSON object: {\"score\": <0-3>, \"reasoning\": \"<brief explanation>\"}"
)


def build_judge_prompt(question, reference_answer, model_answer, model_name=None):
    """Build the prompt sent to the judge model for scoring.

    Args:
        question: The benchmark question text.
        reference_answer: The reference/expected answer.
        model_answer: The model's response to score.
        model_name: The name of the model being scored. If None, model
                     identity is omitted (blind judging mode).

    Returns:
        Formatted judge prompt string.
    """
    parts = []
    parts.append(f"Question: {question}")
    parts.append(f"Reference Answer: {reference_answer}")
    if model_name is not None:
        parts.append(f"Model ({model_name}) Answer: {model_answer}")
    else:
        parts.append(f"Model Answer: {model_answer}")
    parts.append("\nScore this answer 0-3 according to the rubric.")
    return "\n\n".join(parts)


def call_judge_api(provider, prompt):
    """Call the judge API to score a model answer.

    This is a placeholder for actual API calls. In production, this would
    use the appropriate SDK (anthropic, openai, google-generativeai) to
    send the prompt and receive a score.

    Args:
        provider: Judge provider key (e.g., 'anthropic', 'openai', 'gemini').
        prompt: The formatted judge prompt.

    Returns:
        dict with 'score' (int 0-3) and 'reasoning' (str).

    Raises:
        ConnectionError: If the API call fails due to network issues.
        TimeoutError: If the API call times out.
        RuntimeError: If the API returns an invalid response.
    """
    config = JUDGE_PROVIDERS.get(provider)
    if not config:
        raise ValueError(f"Unknown judge provider: {provider}")

    api_key = os.environ.get(config["api_env"])
    if not api_key:
        raise EnvironmentError(
            f"Missing API key: {config['api_env']} not set in environment"
        )

    # --- Provider-specific API call ---
    # In production, this dispatches to the appropriate SDK.
    # For now, raises NotImplementedError to indicate where integration goes.
    raise NotImplementedError(
        f"API integration for {provider} ({config['model']}) not yet wired. "
        f"Set {config['api_env']} and implement the {provider} client call."
    )


JUDGE_MAX_RETRIES = 3
JUDGE_RETRY_BACKOFF_SECONDS = 5


def score_answer(question, reference_answer, model_answer, judge="anthropic",
                 model_name=None):
    """Score a single model answer using the specified judge.

    Includes retry logic for network resilience. If a judge API call fails
    due to a network error, it retries up to JUDGE_MAX_RETRIES times with
    JUDGE_RETRY_BACKOFF_SECONDS backoff between attempts. A score of 0 is
    only assigned when the *model* failed to answer — not when the judge
    fails to score. If all retries are exhausted, the result is flagged
    with ``judge_error: True``.

    Args:
        question: The benchmark question text.
        reference_answer: The reference/expected answer.
        model_answer: The model's response.
        judge: Judge provider key.
        model_name: Name of the model (omitted in blind mode).

    Returns:
        dict with:
            - score (int): 0-3
            - reasoning (str): Judge's explanation
            - judge (str): Provider used
            - judge_error (bool): Present and True when the judge failed
              after retries (score will be None in this case)
    """
    if not model_answer or not model_answer.strip():
        return {
            "score": 0,
            "reasoning": "Model provided no answer.",
            "judge": judge,
        }

    prompt = build_judge_prompt(question, reference_answer, model_answer,
                                model_name=model_name)

    last_error = None
    retried = False
    for attempt in range(1, JUDGE_MAX_RETRIES + 1):
        try:
            result = call_judge_api(judge, prompt)
            score_result = {
                "score": max(0, min(3, int(result.get("score", 0)))),
                "reasoning": result.get("reasoning", ""),
                "judge": judge,
            }
            if retried:
                score_result["judge_error"] = True
            return score_result
        except (ConnectionError, TimeoutError, OSError) as exc:
            last_error = exc
            retried = True
            logger.warning(
                "Judge API call failed (attempt %d/%d): %s",
                attempt, JUDGE_MAX_RETRIES, exc,
            )
            if attempt < JUDGE_MAX_RETRIES:
                time.sleep(JUDGE_RETRY_BACKOFF_SECONDS)

    # All retries exhausted — do NOT score 0 because the judge failed,
    # not the model. Flag for human review.
    logger.error(
        "Judge %s failed after %d retries: %s",
        judge, JUDGE_MAX_RETRIES, last_error,
    )
    return {
        "score": None,
        "reasoning": f"Judge scoring failed after {JUDGE_MAX_RETRIES} retries: {last_error}",
        "judge": judge,
        "judge_error": True,
    }


def run_benchmark(questions, model_fn, model_name="unknown",
                  judge="anthropic"):
    """Run the full benchmark against a model.

    Args:
        questions: List of question dicts with 'id', 'tier', 'question',
                   and 'reference_answer' keys.
        model_fn: Callable that takes a question string and returns the
                  model's answer string.
        model_name: Display name of the model being tested.
        judge: Judge provider key for scoring.

    Returns:
        dict with benchmark results including per-question scores and
        aggregate statistics.
    """
    results = []
    total_score = 0
    scored_count = 0
    judge_errors = 0
    max_possible = len(questions) * 3

    for q in questions:
        logger.info("Scoring question %s (tier %s)", q["id"], q["tier"])
        answer = model_fn(q["question"])
        score_result = score_answer(
            question=q["question"],
            reference_answer=q["reference_answer"],
            model_answer=answer,
            judge=judge,
            model_name=model_name,
        )
        if score_result["score"] is not None:
            total_score += score_result["score"]
            scored_count += 1
        if score_result.get("judge_error"):
            judge_errors += 1
        results.append({
            "question_id": q["id"],
            "tier": q["tier"],
            "model_answer": answer,
            **score_result,
        })

    effective_max = scored_count * 3
    percentage = (total_score / effective_max * 100) if effective_max > 0 else 0

    return {
        "model": model_name,
        "judge": judge,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_score": total_score,
        "max_score": max_possible,
        "scored_questions": scored_count,
        "judge_errors": judge_errors,
        "percentage": round(percentage, 2),
        "num_questions": len(questions),
        "results": results,
    }
