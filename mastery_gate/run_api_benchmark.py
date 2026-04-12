#!/usr/bin/env python3
"""
DAWES Benchmark — API Benchmark Runner CLI

Usage:
    python run_api_benchmark.py --model claude-3-5-sonnet --judge anthropic
    python run_api_benchmark.py --model gpt-4o --judge openai
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

from benchmark_runner import (
    JUDGE_PROVIDERS,
    run_benchmark,
    score_answer_multi_judge,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def load_questions(path=None):
    """Load questions from the question bank.

    Args:
        path: Optional path to a questions JSON file.
              Defaults to the standard question bank location.

    Returns:
        List of question dicts.
    """
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "questions",
                            "evaluation_sample.json")
    if not os.path.exists(path):
        logger.error("Question bank not found at %s", path)
        sys.exit(1)
    with open(path, "r") as f:
        return json.load(f)


def make_model_fn(model_name):
    """Create a callable that queries the specified model.

    In production, this dispatches to the correct API client based on
    model_name. Returns a placeholder function for now.

    Args:
        model_name: Identifier of the model to query.

    Returns:
        Callable that takes a question string and returns a response string.
    """
    def query_model(question):
        raise NotImplementedError(
            f"Model API call for '{model_name}' not yet implemented. "
            "Wire up the appropriate SDK client."
        )
    return query_model


def save_results(run_result, output_dir=None):
    """Save benchmark results to a JSON file.

    Args:
        run_result: The benchmark results dict.
        output_dir: Directory to save results in. Defaults to RESULTS_DIR.

    Returns:
        Path to the saved results file.
    """
    if output_dir is None:
        output_dir = RESULTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    model_slug = run_result.get("model", "unknown").replace(" ", "_").lower()
    filename = f"{timestamp}_{model_slug}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        json.dump(run_result, f, indent=2)

    logger.info("Results saved to %s", filepath)
    return filepath


def parse_args(argv=None):
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description="DAWES Benchmark — API Benchmark Runner"
    )
    parser.add_argument(
        "--model", required=True,
        help="Model identifier to benchmark (e.g., claude-3-5-sonnet, gpt-4o)"
    )
    parser.add_argument(
        "--judge", default="anthropic",
        choices=list(JUDGE_PROVIDERS.keys()),
        help="Single judge provider for scoring (default: anthropic). "
             "Ignored when --judges is specified."
    )
    parser.add_argument(
        "--judges", nargs="+", default=None,
        choices=list(JUDGE_PROVIDERS.keys()),
        metavar="JUDGE",
        help="Multiple judge providers for panel scoring (e.g., "
             "--judges anthropic openai gemini). Scores are averaged "
             "and disagreements > 15pts flagged for human review."
    )
    parser.add_argument(
        "--blind", action="store_true", default=False,
        help="Enable blind judging — strips model name from judge context "
             "so judges score without knowing which model answered."
    )
    parser.add_argument(
        "--questions", default=None,
        help="Path to questions JSON file (default: evaluation_sample.json)"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory to save results (default: results/)"
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Main entry point for the API benchmark runner."""
    args = parse_args(argv)

    judges_list = args.judges if args.judges else None
    judge_display = ", ".join(args.judges) if args.judges else args.judge
    logger.info("DAWES Benchmark Runner")
    logger.info("Model: %s | Judge(s): %s | Blind: %s",
                args.model, judge_display, args.blind)

    questions = load_questions(args.questions)
    logger.info("Loaded %d questions", len(questions))

    model_fn = make_model_fn(args.model)

    result = run_benchmark(
        questions=questions,
        model_fn=model_fn,
        model_name=args.model,
        judge=args.judge,
        judges=judges_list,
        blind=args.blind,
    )

    save_results(result, output_dir=args.output_dir)

    logger.info(
        "Benchmark complete: %s scored %.1f%% (%d/%d)",
        args.model, result["percentage"],
        result["total_score"], result["max_score"],
    )
    return result


if __name__ == "__main__":
    main()
