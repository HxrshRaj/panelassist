"""
Thin, shared LLM client wrapper used by both the baseline scorer and
PanelAssist, so cost/latency accounting is apples-to-apples between them.

Supports either Anthropic (Claude) or Google (Gemini) as the backing model,
picked automatically from whichever API key is set, or forced via
LLM_PROVIDER=anthropic|gemini. This is a genuine reproducibility choice:
a judge re-running this can use whichever provider they have a key for
without touching the agent/baseline/eval code, which only ever calls
call() / call_json() below.

Reads keys from the environment (or a local, gitignored .env file via
python-dotenv). Never hardcode a key here -- that's how it leaks into a
submission.
"""
import json
import os
import time
import urllib.request
import urllib.error

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"
_DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
_DEFAULT_LATENTSTACK_MODEL = "gemini-3.6-flash"
# The gateway has no thinkingConfig knob, and its backing model spends
# completion tokens on reasoning before content, so give it more headroom
# over the caller's answer budget than the direct-Gemini path needs.
_LATENTSTACK_REASONING_HEADROOM = 4096
_DEFAULT_LATENTSTACK_BASE_URL = "https://latentstack.dev/v1"

_anthropic_client = None
_call_log = []  # (label, input_tokens, output_tokens, seconds) -- used for cost/time reporting


def _provider() -> str:
    forced = os.environ.get("LLM_PROVIDER")
    if forced:
        return forced.lower()
    if os.environ.get("LATENTSTACK_API_KEY"):
        return "latentstack"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    raise RuntimeError(
        "No LLM API key found. Set LATENTSTACK_API_KEY, ANTHROPIC_API_KEY or "
        "GEMINI_API_KEY (directly or in a local .env file) before running the "
        "baseline, the agent, or the eval harness."
    )


def _call_anthropic(system: str, user: str, max_tokens: int, temperature: float,
                    json_mode: bool = False) -> tuple:
    # Claude reliably returns a bare JSON object when the prompt asks for one,
    # so json_mode is accepted for a uniform signature but needs no special
    # request flag here.
    global _anthropic_client
    if _anthropic_client is None:
        # Imported lazily so the Gemini / LatentStack paths -- and the
        # no-LLM eval scripts -- run with only python-dotenv installed.
        from anthropic import Anthropic
        _anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("ANTHROPIC_MODEL", _DEFAULT_ANTHROPIC_MODEL)
    resp = _anthropic_client.messages.create(
        model=model, max_tokens=max_tokens, temperature=temperature,
        system=system, messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return text, resp.usage.input_tokens, resp.usage.output_tokens


# gemini-3.6-flash is a "thinking" model: it spends output tokens on hidden
# reasoning before the visible answer, and that reasoning counts against
# maxOutputTokens. We therefore give the request an explicit thinking budget
# ON TOP of the caller's answer budget, so a caller asking for N answer tokens
# always gets N answer tokens regardless of how much the model decides to
# think. Thinking cannot be disabled on this model (thinkingBudget=0 -> HTTP
# 400), only bounded.
_GEMINI_THINKING_BUDGET = 2048
_GEMINI_TIMEOUT_S = 180
_GEMINI_NET_RETRIES = 2
# 429 handling: on the paid tier a 429 is a transient per-minute (RPM) spike
# that clears in seconds, so we retry a few times honouring the server's
# retryDelay (capped). On the free tier a 429 is the per-DAY request cap
# (quotaId GenerateRequestsPerDayPerProjectPerModel-FreeTier, value 20) --
# retrying cannot fix that, so after the retries we raise a message that says
# so plainly instead of a bare "429".
_GEMINI_429_RETRIES = 4
_GEMINI_429_MAX_SLEEP_S = 45


def _retry_delay_seconds(body: str) -> float:
    try:
        err = json.loads(body).get("error", {})
        for d in err.get("details", []):
            if d.get("@type", "").endswith("RetryInfo"):
                return float(str(d.get("retryDelay", "0s")).rstrip("s"))
    except (ValueError, TypeError):
        pass
    return 0.0


def _call_gemini(system: str, user: str, max_tokens: int, temperature: float,
                 json_mode: bool = False) -> tuple:
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.environ.get("GEMINI_MODEL", _DEFAULT_GEMINI_MODEL)
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    gen_config = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens + _GEMINI_THINKING_BUDGET,
        "thinkingConfig": {"thinkingBudget": _GEMINI_THINKING_BUDGET},
    }
    if json_mode:
        # Native structured-output mode: the model is constrained to emit a
        # single well-formed JSON value, so we don't have to hope it wraps
        # the object in a ```json fence and then regex it back out.
        gen_config["responseMimeType"] = "application/json"
    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": gen_config,
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json"},
    )
    last_err = None
    rate_limit_hits = 0
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=_GEMINI_TIMEOUT_S) as resp:
                data = json.loads(resp.read().decode())
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429 and rate_limit_hits < _GEMINI_429_RETRIES:
                rate_limit_hits += 1
                sleep_s = min(_retry_delay_seconds(body) or 5.0, _GEMINI_429_MAX_SLEEP_S)
                time.sleep(sleep_s)
                continue
            if e.code == 429:
                raise RuntimeError(
                    "Gemini API 429 after "
                    f"{_GEMINI_429_RETRIES} retries. If quotaId is "
                    "'...PerDayPerProjectPerModel-FreeTier' this is the free-tier "
                    "per-day request cap (20/day for gemini-3.6-flash) and will "
                    "not clear until it resets -- enable billing on the API "
                    "project, or switch to LLM_PROVIDER=anthropic in .env. "
                    f"Raw: {body[:400]}"
                )
            # Other HTTP errors are deterministic (bad model, bad key, bad
            # request) -- retrying won't help, so surface the body immediately.
            raise RuntimeError(f"Gemini API error {e.code}: {body[:500]}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last_err = e
            attempt += 1
            if attempt <= _GEMINI_NET_RETRIES:
                time.sleep(2 * attempt)
                continue
            raise RuntimeError(
                f"Gemini request failed after {_GEMINI_NET_RETRIES + 1} attempts "
                f"({_GEMINI_TIMEOUT_S}s timeout each): {last_err!r}"
            )
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {json.dumps(data)[:500]}")
    cand = candidates[0]
    finish = cand.get("finishReason")
    parts = cand.get("content", {}).get("parts", [])
    # Skip any thought parts (only present if includeThoughts is set, but be
    # defensive) and join the visible answer text.
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    if finish == "MAX_TOKENS":
        raise RuntimeError(
            f"Gemini hit MAX_TOKENS before finishing the answer "
            f"(answer budget={max_tokens}, thinking budget={_GEMINI_THINKING_BUDGET}). "
            f"Partial answer (last 300 chars): {text[-300:]!r}"
        )
    usage = data.get("usageMetadata", {})
    return text, usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0)


def _call_latentstack(system: str, user: str, max_tokens: int, temperature: float,
                      json_mode: bool = False) -> tuple:
    """LatentStack gateway -- an OpenAI-compatible /chat/completions endpoint
    that routes to a backing model (default gemini/gemini-3.6-flash). Used
    for the real runs because the direct Google AI Studio free tier caps
    gemini-3.6-flash at 20 requests/day. Plain urllib, same as _call_gemini,
    so no extra dependency."""
    api_key = os.environ["LATENTSTACK_API_KEY"]
    base = os.environ.get("LATENTSTACK_BASE_URL", _DEFAULT_LATENTSTACK_BASE_URL).rstrip("/")
    model = os.environ.get("LATENTSTACK_MODEL", _DEFAULT_LATENTSTACK_MODEL)
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        # Headroom: the backing model may be a reasoning model that spends
        # part of the budget on internal tokens before emitting content.
        "max_tokens": max_tokens + _LATENTSTACK_REASONING_HEADROOM,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        base + "/chat/completions", data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    attempt = 0
    rate_limit_hits = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=_GEMINI_TIMEOUT_S) as resp:
                data = json.loads(resp.read().decode())
            break
        except urllib.error.HTTPError as e:
            edata = e.read().decode()
            if e.code == 429 and rate_limit_hits < _GEMINI_429_RETRIES:
                rate_limit_hits += 1
                time.sleep(min(_retry_delay_seconds(edata) or 5.0, _GEMINI_429_MAX_SLEEP_S))
                continue
            raise RuntimeError(f"LatentStack API error {e.code}: {edata[:500]}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            attempt += 1
            if attempt <= _GEMINI_NET_RETRIES:
                time.sleep(2 * attempt)
                continue
            raise RuntimeError(
                f"LatentStack request failed after {_GEMINI_NET_RETRIES + 1} "
                f"attempts ({_GEMINI_TIMEOUT_S}s timeout each): {e!r}"
            )
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(f"LatentStack returned no choices: {json.dumps(data)[:500]}")
    choice = choices[0]
    text = (choice.get("message", {}) or {}).get("content", "") or ""
    if choice.get("finish_reason") == "length":
        raise RuntimeError(
            f"LatentStack response truncated at max_tokens (answer budget "
            f"{max_tokens}). Partial (last 300 chars): {text[-300:]!r}"
        )
    usage = data.get("usage", {}) or {}
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def call(system: str, user: str, label: str = "unlabeled", max_tokens: int = 2000,
          temperature: float = 0.0, json_mode: bool = False) -> str:
    """One LLM call. Returns the raw text response. Logs cost/latency."""
    provider = _provider()
    start = time.time()
    if provider == "anthropic":
        text, in_tok, out_tok = _call_anthropic(system, user, max_tokens, temperature, json_mode)
    elif provider == "gemini":
        text, in_tok, out_tok = _call_gemini(system, user, max_tokens, temperature, json_mode)
    elif provider == "latentstack":
        text, in_tok, out_tok = _call_latentstack(system, user, max_tokens, temperature, json_mode)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
    elapsed = time.time() - start
    _call_log.append({
        "label": label, "provider": provider,
        "input_tokens": in_tok, "output_tokens": out_tok,
        "seconds": round(elapsed, 3),
    })
    return text


def _extract_json_object(raw: str):
    """Returns a parsed dict, or None if the response looks truncated /
    doesn't contain a balanced JSON object yet."""
    text = raw.strip()
    # Native JSON mode (Gemini responseMimeType / Claude following instructions)
    # returns a bare object -- try that first before any fence stripping.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def call_json(system: str, user: str, label: str = "unlabeled", max_tokens: int = 2000) -> dict:
    """Call the LLM in JSON mode and parse a single JSON object from the
    response.

    On Gemini this sets responseMimeType=application/json so the model is
    constrained to emit well-formed JSON directly -- no ```json fence to
    strip, no prose to skip past. _extract_json_object still tolerates a
    fenced block for the Anthropic path and as a belt-and-braces fallback.

    "Thinking" Gemini models spend output tokens on hidden reasoning before
    the answer; _call_gemini reserves a separate thinking budget so the
    caller's answer budget is never eaten by it. The retry-with-larger-budget
    below is a last resort for the rare case a response still comes back
    unparseable."""
    raw = call(system, user, label=label, max_tokens=max_tokens, json_mode=True)
    parsed = _extract_json_object(raw)
    if parsed is not None:
        return parsed

    retry_tokens = max(max_tokens * 3, 4000)
    raw2 = call(system, user, label=f"{label}:retry", max_tokens=retry_tokens, json_mode=True)
    parsed2 = _extract_json_object(raw2)
    if parsed2 is not None:
        return parsed2

    raise ValueError(
        f"No JSON object found in response for '{label}' even after "
        f"retrying with max_tokens={retry_tokens}. Raw (first 500 chars): "
        f"{raw2[:500]}"
    )


def get_call_log() -> list:
    return list(_call_log)


def reset_call_log() -> None:
    _call_log.clear()


# Rough list-price estimates per million tokens, at time of writing. Override
# by passing explicit rates if your actual model's pricing differs -- these
# exist to give a directional cost-per-task number, not an invoice.
_RATES = {
    "anthropic": (3.0, 15.0),
    "gemini": (0.10, 0.40),
    # LatentStack billed by its backing model; default routes to a
    # gemini-flash-class model, so use the same directional rate.
    "latentstack": (0.10, 0.40),
}


def cost_estimate_usd(input_tokens: int, output_tokens: int, provider: str = None) -> float:
    # Pass provider explicitly (e.g. from a saved call log) so this works
    # with no API key set -- it is a pure arithmetic helper and must not
    # require an LLM to be configured.
    if provider is None:
        try:
            provider = _provider()
        except RuntimeError:
            provider = "latentstack"
    in_rate, out_rate = _RATES.get(provider, (3.0, 15.0))
    return (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate
