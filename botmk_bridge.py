"""Persistent JSON-lines worker for the WhatsApp bridge."""
import json
import sys
from brain_adapter.fly_adapter import FlyBrainAdapter
from mind.modified_mind import ModifiedMind


def response_for(packet: dict) -> str:
    return ModifiedMind.verbalize(packet)


def main():
    mind = ModifiedMind(FlyBrainAdapter())
    for line in sys.stdin:
        try:
            request = json.loads(line)
            packet = mind.process(str(request.get("text", "")))
            print(json.dumps({"ok": True, "reply": response_for(packet), "result": packet}, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
