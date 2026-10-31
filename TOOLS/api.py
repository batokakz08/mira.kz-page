import base64
import json
import os
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:19040/v1"
MODEL = "DeepSeek-V4.1-Flash"


def chat(messages, max_tokens=1500, timeout=180, thinking=False):
    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
        "chat_template_kwargs": {"enable_thinking": bool(thinking)},
    }
    req = urllib.request.Request(
        BASE + "/chat/completions",
        json.dumps(body).encode(),
        {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:800]
        raise SystemExit(f"Model error {error.code}: {detail}")
    except urllib.error.URLError as error:
        raise SystemExit(f"Cannot reach the class model at {BASE}: {error.reason}")
    content = data["choices"][0]["message"].get("content")
    if not content:
        raise SystemExit("The model returned no text. Try again with a bigger max_tokens.")
    return content


def image_part(path):
    if not os.path.isfile(path):
        raise SystemExit(f"No such image: {path}")
    extension = os.path.splitext(path)[1].lower().lstrip(".") or "jpeg"
    mime = "jpeg" if extension == "jpg" else extension
    encoded = base64.b64encode(open(path, "rb").read()).decode()
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/{mime};base64,{encoded}"},
    }


def parse_json(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0]
    candidates = []
    for opening, closing in (("[", "]"), ("{", "}")):
        start = cleaned.find(opening)
        end = cleaned.rfind(closing)
        if start != -1 and end > start:
            candidates.append((start, cleaned[start : end + 1]))
    for _, candidate in sorted(candidates):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    raise SystemExit("The model did not return clean JSON:\n" + text[:800])
