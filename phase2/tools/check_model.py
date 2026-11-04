#!/usr/bin/env python3
"""Check that your model deployment works and can call tools, before you build anything on it.

    pip install openai
    cp .env.example .env      # then fill in the three values your mentors gave you (never commit .env)
    python tools/check_model.py

It sends one tiny request with one tool and prints whether the model asked to use the tool. It never prints your key.
"""
import json
import os
import sys
from pathlib import Path


def load_env():
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    load_env()
    missing = [k for k in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT") if not os.environ.get(k)]
    if missing:
        sys.exit(f"Missing: {', '.join(missing)}. Copy .env.example to .env and fill them in (ask your mentors for the values).")
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Run: pip install openai")
    client = OpenAI(base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/",
                    api_key=os.environ["AZURE_OPENAI_API_KEY"], timeout=60, max_retries=0)
    tool = {"type": "function", "function": {"name": "get_room_number", "description": "Look up the room number of a person.",
                                             "parameters": {"type": "object", "properties": {"person": {"type": "string"}},
                                                            "required": ["person"]}}}
    try:
        r = client.chat.completions.create(model=os.environ["AZURE_OPENAI_DEPLOYMENT"], tools=[tool],
                                           messages=[{"role": "user", "content": "Which room is Sara in? Use the tool."}])
    except Exception as e:  # the message from the service is what you need to read
        sys.exit(f"The call failed: {type(e).__name__}: {str(e)[:300]}")
    calls = r.choices[0].message.tool_calls or []
    if calls:
        print("OK: the deployment answered and asked to use the tool:", calls[0].function.name, json.loads(calls[0].function.arguments))
    else:
        print("The deployment answered but did NOT ask to use the tool. Tool calling may not be enabled for it: ask your mentors.")
        print("Reply was:", (r.choices[0].message.content or "")[:200])


if __name__ == "__main__":
    main()
