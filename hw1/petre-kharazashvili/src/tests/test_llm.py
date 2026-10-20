from llm import Usage, log_usage


def test_log_usage_reports_tokens_cost_and_latency(capsys):
    # The spec's napkin-math request: 600 in, 120 out on gemini-3.8-flash is $0.0009.
    log_usage(Usage("gemini-3.8-flash", input_tokens=600, output_tokens=120), "ok", "vague", 1.234)
    line = capsys.readouterr().err
    assert "model=gemini-3.8-flash" in line
    assert "in=600 out=120" in line
    assert "cost=$0.000900" in line
    assert "time=1.23s" in line


def test_log_usage_says_when_the_price_is_unknown(capsys):
    log_usage(Usage("gemini-unpriced"), "ok", None, 0.5)
    assert "cost=unknown" in capsys.readouterr().err
