"""The one search helper: on a 403 rate limit, wait once and retry once (queue github-api-backoff)."""
import pytest

from lifecycle import ghsearch


class Result:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class Runner:
    """A fake subprocess.run: hands back each canned answer in turn and records the commands it was given."""

    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def __call__(self, cmd, **_kwargs):
        self.calls.append(cmd)
        return self.results.pop(0)


def test_a_rate_limit_waits_and_retries_exactly_once():
    runner = Runner([Result(403, stderr="API rate limit exceeded for user"), Result(0, stdout='{"items": []}')])
    slept = []
    answer = ghsearch.search("repo:acme/range is:open", run=runner, sleep=slept.append, wait=7)
    assert answer == '{"items": []}'
    assert slept == [7]
    assert len(runner.calls) == 2
    assert runner.calls[0] == ["gh", "api", "-X", "GET", "search/code", "-f", "q=repo:acme/range is:open"]


def test_a_second_rate_limit_raises_naming_the_wait():
    runner = Runner([Result(403, stderr="rate limit"), Result(403, stderr="rate limit")])
    slept = []
    with pytest.raises(RuntimeError, match="7"):
        ghsearch.search("x", run=runner, sleep=slept.append, wait=7)
    assert slept == [7]
    assert len(runner.calls) == 2


def test_any_other_error_is_raised_at_once_with_no_retry():
    runner = Runner([Result(500, stderr="boom")])
    slept = []
    with pytest.raises(RuntimeError, match="boom"):
        ghsearch.search("x", run=runner, sleep=slept.append, wait=7)
    assert slept == []
    assert len(runner.calls) == 1


def test_a_plain_failure_code_one_raises_and_does_not_look_like_success():
    runner = Runner([Result(1, stderr="not found")])
    with pytest.raises(RuntimeError, match="not found"):
        ghsearch.search("x", run=runner, sleep=[].append)
    assert len(runner.calls) == 1


def test_the_default_wait_is_sixty_seconds():
    runner = Runner([Result(403, stderr="rate limit"), Result(0, stdout="done")])
    slept = []
    assert ghsearch.search("x", run=runner, sleep=slept.append) == "done"
    assert slept == [60]


def test_capture_output_and_text_are_asked_of_the_runner():
    seen = []

    def runner(cmd, **kwargs):
        seen.append(kwargs)
        return Result(0, stdout="ok")

    assert ghsearch.search("x", run=runner) == "ok"
    assert seen == [{"capture_output": True, "text": True}]


def test_the_retry_also_asks_for_capture_output_and_text():
    seen = []

    def runner(cmd, **kwargs):
        seen.append(kwargs)
        if len(seen) == 1:
            return Result(403, stderr="rate limit")
        return Result(0, stdout="ok")

    assert ghsearch.search("x", run=runner, sleep=[].append) == "ok"
    assert seen == [{"capture_output": True, "text": True}] * 2


def test_an_error_shows_both_stdout_and_stderr():
    runner = Runner([Result(500, stdout="out-part", stderr="err-part")])
    with pytest.raises(RuntimeError) as caught:
        ghsearch.search("x", run=runner, sleep=[].append)
    assert "out-part" in str(caught.value)
    assert "err-part" in str(caught.value)
