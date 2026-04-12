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

import asyncio
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


MULTI_JUDGE_DISAGREEMENT_THRESHOLD = 15  # points on 0-100 scale

# ---------------------------------------------------------------------------
# OpenRouter multi-judge panel
# ---------------------------------------------------------------------------

JUDGE_PANEL = [
    "anthropic/claude-sonnet-4-6",
    "openai/gpt-4o",
    "google/gemini-2.5-flash",
    "meta-llama/llama-3.1-70b-instruct",
    "mistralai/mistral-large",
]

JUDGE_PANEL_NAMES = {
    "anthropic/claude-sonnet-4-6": "claude-sonnet",
    "openai/gpt-4o": "gpt-4o",
    "google/gemini-2.5-flash": "gemini-flash",
    "meta-llama/llama-3.1-70b-instruct": "llama-70b",
    "mistralai/mistral-large": "mistral-large",
}

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HTTP_REFERER = "https://relayforge.tools"
OPENROUTER_X_TITLE = "DAWES Benchmark"
PANEL_DISAGREEMENT_THRESHOLD = 15  # points on 0-100 scale

PANEL_JUDGE_SYSTEM_PROMPT = (
    "You are an expert scorer for the DAWES Benchmark — an Instrumentation "
    "& Controls domain knowledge test. Score the following answer on a 0-100 "
    "scale:\n"
    "  0-20   = Wrong or no answer\n"
    "  21-50  = Partially correct\n"
    "  51-80  = Correct\n"
    "  81-100 = Correct with strong reasoning\n\n"
    "Respond with ONLY a JSON object: "
    "{\"score\": <0-100>, \"reasoning\": \"<brief explanation>\"}"
)


async def _call_openrouter_judge_async(model, prompt, api_key):
    """Async call to a single OpenRouter judge model.

    Args:
        model: OpenRouter model identifier (e.g., ``openai/gpt-4o``).
        prompt: Formatted judge prompt string.
        api_key: OpenRouter API key.

    Returns:
        dict with ``score`` (int 0-100) and ``reasoning`` (str).

    Raises:
        RuntimeError: If the response cannot be parsed.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": OPENROUTER_HTTP_REFERER,
            "X-Title": OPENROUTER_X_TITLE,
        },
    )
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PANEL_JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content.strip()
    data = json.loads(content)
    return {
        "score": max(0, min(100, int(data["score"]))),
        "reasoning": data.get("reasoning", ""),
    }


async def _score_panel_async(prompt, api_key):
    """Dispatch prompt to all panel judges simultaneously.

    Args:
        prompt: Formatted judge prompt string.
        api_key: OpenRouter API key.

    Returns:
        List of results or exceptions, one per entry in ``JUDGE_PANEL``.
    """
    tasks = [
        _call_openrouter_judge_async(model, prompt, api_key)
        for model in JUDGE_PANEL
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)


def score_answer_judge_panel(question, reference_answer, model_answer,
                             model_name=None):
    """Score a single model answer using the OpenRouter multi-judge panel.

    Sends the answer to all five panel judges simultaneously via asyncio,
    then:
      1. Drops the single highest and single lowest score (outlier removal).
      2. Averages the remaining three scores.
      3. Flags the answer as ``contested`` when any two judges disagree by
         more than ``PANEL_DISAGREEMENT_THRESHOLD`` points.

    Args:
        question: The benchmark question text.
        reference_answer: The reference/expected answer.
        model_answer: The model's response.
        model_name: Name of the model (omitted in blind mode).

    Returns:
        dict with:
            - score (int or None): Final averaged 0-100 score (``total``).
            - total (int or None): Alias for ``score`` (matches result spec).
            - judge_scores (dict): Per-judge short-name → raw 0-100 score.
            - contested (bool): True if any pair of judges disagree > 15 pts.
            - outliers_dropped (list[str]): ``"name:score"`` strings for the
              dropped high/low judges.
            - judge_error (bool): Present and True when at least one judge
              failed.
    """
    if not model_answer or not model_answer.strip():
        return {
            "score": 0,
            "total": 0,
            "judge_scores": {name: None for name in JUDGE_PANEL_NAMES.values()},
            "contested": False,
            "outliers_dropped": [],
        }

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY not set in environment")

    prompt = build_judge_prompt(
        question, reference_answer, model_answer, model_name=model_name
    )

    raw_results = asyncio.run(_score_panel_async(prompt, api_key))

    judge_scores = {}
    valid_raw = []  # list of (short_name, score)
    any_error = False

    for model, result in zip(JUDGE_PANEL, raw_results):
        name = JUDGE_PANEL_NAMES[model]
        if isinstance(result, Exception):
            logger.error("Panel judge %s failed: %s", name, result)
            judge_scores[name] = None
            any_error = True
        else:
            judge_scores[name] = result["score"]
            valid_raw.append((name, result["score"]))

    if not valid_raw:
        result_dict = {
            "score": None,
            "total": None,
            "judge_scores": judge_scores,
            "contested": True,
            "outliers_dropped": [],
            "judge_error": True,
        }
        return result_dict

    # Drop highest and lowest outliers (requires >= 3 valid scores)
    outliers_dropped = []
    scores_for_avg = valid_raw

    if len(valid_raw) >= 3:
        sorted_scores = sorted(valid_raw, key=lambda x: x[1])
        low_name, low_score = sorted_scores[0]
        high_name, high_score = sorted_scores[-1]
        outliers_dropped = [
            f"{low_name}:{low_score}",
            f"{high_name}:{high_score}",
        ]
        scores_for_avg = sorted_scores[1:-1]

    avg = sum(s for _, s in scores_for_avg) / len(scores_for_avg)
    total = round(avg)

    # Contested: any two judges disagree by more than threshold
    all_valid_scores = [s for _, s in valid_raw]
    contested = any(
        abs(all_valid_scores[i] - all_valid_scores[j]) > PANEL_DISAGREEMENT_THRESHOLD
        for i in range(len(all_valid_scores))
        for j in range(i + 1, len(all_valid_scores))
    )

    result_dict = {
        "score": total,
        "total": total,
        "judge_scores": judge_scores,
        "contested": contested,
        "outliers_dropped": outliers_dropped,
    }
    if any_error:
        result_dict["judge_error"] = True
    return result_dict


# Benchmark result versioning
BENCHMARK_VERSION_BASE = "v1.0"       # Single-judge, non-blind runs
BENCHMARK_VERSION_ENHANCED = "v1.2"   # Multi-judge and/or blind runs


def determine_benchmark_version(multi_judge=False, blind=False):
    """Determine the benchmark version string for a run.

    Args:
        multi_judge: Whether multi-judge panel scoring is enabled.
        blind: Whether blind judging is enabled.

    Returns:
        Version string (e.g., "v1.0" or "v1.2").
    """
    if multi_judge or blind:
        return BENCHMARK_VERSION_ENHANCED
    return BENCHMARK_VERSION_BASE


def score_answer_multi_judge(question, reference_answer, model_answer,
                             judges, model_name=None):
    """Score a single model answer using multiple judges (panel scoring).

    Each judge scores the answer independently. The final score is the
    average of all successful judge scores. If judges disagree by more than
    MULTI_JUDGE_DISAGREEMENT_THRESHOLD points (on a 0-100 scale derived
    from the 0-3 rubric), the question is flagged for human review.

    Args:
        question: The benchmark question text.
        reference_answer: The reference/expected answer.
        model_answer: The model's response.
        judges: List of judge provider keys.
        model_name: Name of the model (omitted in blind mode).

    Returns:
        dict with:
            - score (float or None): Average score across judges
            - reasoning (str): Combined reasoning summary
            - judges_used (list[str]): Providers that participated
            - judge_scores (list[dict]): Individual judge results
            - judge_error (bool): True if any judge had errors
            - human_review (bool): True if judge disagreement exceeds
              threshold
    """
    if not model_answer or not model_answer.strip():
        return {
            "score": 0,
            "reasoning": "Model provided no answer.",
            "judges_used": judges,
            "judge_scores": [],
        }

    individual_scores = []
    any_error = False

    for judge in judges:
        result = score_answer(
            question=question,
            reference_answer=reference_answer,
            model_answer=model_answer,
            judge=judge,
            model_name=model_name,
        )
        individual_scores.append(result)
        if result.get("judge_error"):
            any_error = True

    # Compute average from judges that returned valid scores
    valid_scores = [r["score"] for r in individual_scores
                    if r["score"] is not None]

    if not valid_scores:
        return {
            "score": None,
            "reasoning": "All judges failed to score.",
            "judges_used": judges,
            "judge_scores": individual_scores,
            "judge_error": True,
            "human_review": True,
        }

    avg_score = sum(valid_scores) / len(valid_scores)

    # Check for disagreement: convert 0-3 scores to 0-100 scale
    scores_pct = [(s / 3) * 100 for s in valid_scores]
    disagreement = max(scores_pct) - min(scores_pct) if len(scores_pct) > 1 else 0
    needs_review = disagreement > MULTI_JUDGE_DISAGREEMENT_THRESHOLD

    combined_reasoning = "; ".join(
        f"[{r['judge']}] {r.get('reasoning', '')}" for r in individual_scores
        if r["score"] is not None
    )

    result = {
        "score": round(avg_score, 2),
        "reasoning": combined_reasoning,
        "judges_used": judges,
        "judge_scores": individual_scores,
    }
    if any_error:
        result["judge_error"] = True
    if needs_review:
        result["human_review"] = True
        result["judge_disagreement_pct"] = round(disagreement, 2)
    return result


def run_benchmark(questions, model_fn, model_name="unknown",
                  judge="anthropic", judges=None, blind=False,
                  judge_panel=False):
    """Run the full benchmark against a model.

    Args:
        questions: List of question dicts with 'id', 'tier', 'question',
                   and 'reference_answer' keys.
        model_fn: Callable that takes a question string and returns the
                  model's answer string.
        model_name: Display name of the model being tested.
        judge: Single judge provider key for scoring (used when judges
               is not specified).
        judges: List of judge provider keys for multi-judge panel scoring.
                When provided, overrides the single ``judge`` parameter.
        blind: When True, strips model name from judge context before
               scoring (blind judging mode).
        judge_panel: When True, uses the OpenRouter multi-judge panel
                     (``score_answer_judge_panel``) which scores on a 0-100
                     scale, drops outliers, and flags contested answers.

    Returns:
        dict with benchmark results including per-question scores and
        aggregate statistics.
    """
    use_multi = judges is not None and len(judges) > 1
    effective_model_name = None if blind else model_name

    # Panel mode uses 0-100 per question; standard mode uses 0-3.
    score_max_per_question = 100 if judge_panel else 3

    results = []
    total_score = 0
    scored_count = 0
    judge_errors = 0
    human_review_count = 0
    contested_count = 0
    max_possible = len(questions) * score_max_per_question

    for q in questions:
        logger.info("Scoring question %s (tier %s)", q["id"], q["tier"])
        answer = model_fn(q["question"])

        if judge_panel:
            score_result = score_answer_judge_panel(
                question=q["question"],
                reference_answer=q["reference_answer"],
                model_answer=answer,
                model_name=effective_model_name,
            )
        elif use_multi:
            score_result = score_answer_multi_judge(
                question=q["question"],
                reference_answer=q["reference_answer"],
                model_answer=answer,
                judges=judges,
                model_name=effective_model_name,
            )
        else:
            active_judge = judges[0] if judges else judge
            score_result = score_answer(
                question=q["question"],
                reference_answer=q["reference_answer"],
                model_answer=answer,
                judge=active_judge,
                model_name=effective_model_name,
            )

        if score_result["score"] is not None:
            total_score += score_result["score"]
            scored_count += 1
        if score_result.get("judge_error"):
            judge_errors += 1
        if score_result.get("human_review"):
            human_review_count += 1
        if score_result.get("contested"):
            contested_count += 1
        results.append({
            "question_id": q["id"],
            "tier": q["tier"],
            "model_answer": answer,
            **score_result,
        })

    effective_max = scored_count * score_max_per_question
    percentage = (total_score / effective_max * 100) if effective_max > 0 else 0

    run_result = {
        "model": model_name,
        "benchmark_version": determine_benchmark_version(
            multi_judge=(use_multi or judge_panel), blind=blind
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_score": round(total_score, 2),
        "max_score": max_possible,
        "scored_questions": scored_count,
        "judge_errors": judge_errors,
        "percentage": round(percentage, 2),
        "num_questions": len(questions),
        "blind": blind,
        "results": results,
    }

    if judge_panel:
        run_result["judge_panel"] = JUDGE_PANEL
        run_result["contested_flagged"] = contested_count
        run_result["human_review_flagged"] = human_review_count
    elif use_multi:
        run_result["judges"] = judges
        run_result["human_review_flagged"] = human_review_count
    else:
        run_result["judge"] = judges[0] if judges else judge

    return run_result
