import pytest

import x_url_summarizer

class DummyResp:
    def __init__(self, content):
        self._content = content
    def get(self, key, default=None):
        if key == "choices":
            return [{"message": {"content": self._content}}]
        return default

@pytest.fixture
def mock_openai(monkeypatch):
    def fake_create(*args, **kwargs):
        return DummyResp("This is a dummy summary.")
    monkeypatch.setattr("openai.ChatCompletion.create", fake_create)

def test_summarize_url_with_gpt(monkeypatch, mock_openai):
    # モック化された openai.ChatCompletion.create が呼ばれる
    summary = x_url_summarizer.summarize_url_with_gpt("https://example.com")
    assert summary is not None
    assert "dummy summary" in summary.lower()
