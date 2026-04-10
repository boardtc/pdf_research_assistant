import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run the interactive CLI loop that forwards questions to the one-shot query helper."""
    while True:
        q = input("\nQuestion (or quit): ").strip()
        if q.lower() == "quit":
            return 0
        helper = Path(__file__).with_name("query_once.py")
        result = subprocess.run(
            [sys.executable, str(helper), q],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0 and not result.stdout.strip():
            print("\nQuery failed.")
            if result.stderr.strip():
                print(result.stderr.strip())
            continue
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            print("\nQuery failed.")
            if result.stderr.strip():
                print(result.stderr.strip())
            elif result.stdout.strip():
                print(result.stdout.strip())
            continue
        if payload.get("ok"):
            print("\n" + payload["answer"])
        else:
            print(f"\n{payload.get('error_type', 'Error')}: {payload.get('error', 'Unknown error')}")


if __name__ == "__main__":
    raise SystemExit(main())

