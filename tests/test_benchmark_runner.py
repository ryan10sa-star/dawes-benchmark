from mastery_gate import benchmark_runner as runner


def test_empty_model_answer_scores_zero_without_judge_call(monkeypatch):
    def fail_call(*_args, **_kwargs):
        raise AssertionError("judge API should not be called for an empty answer")

    monkeypatch.setattr(runner, "call_judge_api", fail_call)

    result = runner.score_answer(
        question="What does 3.6 mA indicate?",
        reference_answer="Fault or underrange depending on standard/context.",
        model_answer="   ",
    )

    assert result["score"] == 0
    assert result["judge"] == "anthropic"


def test_score_answer_clamps_provider_score(monkeypatch):
    monkeypatch.setattr(
        runner,
        "call_judge_api",
        lambda *_args, **_kwargs: {"score": 9, "reasoning": "too high"},
    )

    result = runner.score_answer("q", "ref", "answer", judge="openai")

    assert result == {"score": 3, "reasoning": "too high", "judge": "openai"}


def test_multi_judge_flags_disagreement(monkeypatch):
    scores = {"anthropic": 3, "openai": 0}

    def fake_score_answer(*, judge, **_kwargs):
        return {"score": scores[judge], "reasoning": f"{judge} says so", "judge": judge}

    monkeypatch.setattr(runner, "score_answer", fake_score_answer)

    result = runner.score_answer_multi_judge(
        question="q",
        reference_answer="ref",
        model_answer="answer",
        judges=["anthropic", "openai"],
    )

    assert result["score"] == 1.5
    assert result["human_review"] is True
    assert result["judge_disagreement_pct"] == 100


def test_run_benchmark_uses_scored_question_count_for_percentage(monkeypatch):
    questions = [
        {"id": "Q1", "tier": "recall", "question": "q1", "reference_answer": "r1"},
        {"id": "Q2", "tier": "recall", "question": "q2", "reference_answer": "r2"},
    ]
    answers = {"q1": "answer", "q2": "answer"}

    def fake_score_answer(**kwargs):
        if kwargs["question"] == "q1":
            return {"score": 3, "reasoning": "ok", "judge": kwargs["judge"]}
        return {
            "score": None,
            "reasoning": "judge failed",
            "judge_error": True,
            "judge": kwargs["judge"],
        }

    monkeypatch.setattr(runner, "score_answer", fake_score_answer)

    result = runner.run_benchmark(
        questions=questions,
        model_fn=lambda question: answers[question],
        model_name="fixture-model",
    )

    assert result["total_score"] == 3
    assert result["max_score"] == 6
    assert result["scored_questions"] == 1
    assert result["judge_errors"] == 1
    assert result["percentage"] == 100

