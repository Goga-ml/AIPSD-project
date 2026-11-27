"""Every test runs offline: no key, no network, no cost. Logs go to a temp folder."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="groundwork-tests-")
os.environ["GROUNDWORK_USAGE_LOG"] = os.path.join(_tmp, "usage.jsonl")
os.environ["GROUNDWORK_TOOL_LOG"] = os.path.join(_tmp, "tools.jsonl")
os.environ.pop("OPENROUTER_API_KEY", None)
os.environ.pop("GEMINI_API_KEY", None)
os.environ["GROUNDWORK_EMBED_CACHE"] = os.path.join(_tmp, "embeddings.json")
os.environ["GROUNDWORK_OFFLINE"] = "1"         # src/offline.py stands in for both model calls
os.environ["GROUNDWORK_ASK_MIN_SCORE"] = "0.35"  # offline embedder scale: related >= 0.41, off-topic <= 0.29
