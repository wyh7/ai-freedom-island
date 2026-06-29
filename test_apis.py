"""
Quick connectivity test for all API providers.
Run this before launching a full simulation to verify keys and endpoints.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env before importing router
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip()

import requests
from models.router import PROVIDER_CONFIG, MODEL_TO_PROVIDER, _get_api_key


def test_provider(name: str, cfg: dict):
    model = cfg["models"][0]
    print(f"  Testing {name} / {model} ...", end=" ", flush=True)

    try:
        api_key = _get_api_key(cfg)
        if cfg.get("is_anthropic_format"):
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }
            body = {
                "model": model,
                "max_tokens": 16,
                "messages": [{"role": "user", "content": "Reply with the single word: OK"}],
            }
            resp = requests.post(
                f"{cfg['base_url']}/messages",
                headers=headers, json=body, timeout=20
            )
        else:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            body = {
                "model": model,
                "max_tokens": 16,
                "messages": [
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Reply with the single word: OK"},
                ],
            }
            resp = requests.post(
                f"{cfg['base_url']}/chat/completions",
                headers=headers, json=body, timeout=20
            )

        if resp.status_code == 200:
            print(f"OK ({resp.status_code})")
            return True
        else:
            print(f"FAIL ({resp.status_code}): {resp.text[:120]}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    print("\n=== API Connectivity Test ===\n")
    results = {}
    for name, cfg in PROVIDER_CONFIG.items():
        results[name] = test_provider(name, cfg)
    print("\n--- Summary ---")
    for name, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")
    print()
    failed = [n for n, ok in results.items() if not ok]
    if failed:
        print(f"Failed providers: {failed}")
        sys.exit(1)
    else:
        print("All providers reachable.")


if __name__ == "__main__":
    main()
