"""The quote check is pure code, so it is tested on the real shared transcript with no model."""
import verify


def test_exact_quote_is_accepted_with_its_line(tr01):
    m = verify.best_match("We pay 45 GEL a month for a POS add-on", tr01)
    assert m.line == 11 and m.score == 100.0
    assert verify.is_supported(m)


def test_small_copy_error_still_passes_threshold(tr01):
    # "add-on" -> "addon": a model tidying a quote
    m = verify.best_match("We pay 45 GEL a month for a POS addon", tr01)
    assert m.line == 11 and verify.is_supported(m)


def test_invented_quote_is_rejected(tr01):
    m = verify.best_match("we lose most customers to Starbucks", tr01)
    assert not verify.is_supported(m)


def test_real_sentence_plus_invented_text_is_rejected(tr01):
    # partial_ratio alone would score this 100, because the real turn fits inside the quote
    real = next(t.text for t in tr01.turns if t.line == 9)
    padded = real + " and I spend 300 GEL a month on a stock app."
    m = verify.best_match(padded, tr01)
    assert not verify.is_supported(m)


def test_interviewer_words_are_not_evidence(tr01):
    m = verify.best_match("Wouldn't an app that predicts stock be great for you?", tr01)
    assert not verify.is_supported(m)
