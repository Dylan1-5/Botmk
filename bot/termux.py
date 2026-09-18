"""Consola para probar Botmk en Termux y guardar actividad para el decoder."""
import json
from datetime import datetime, timezone
from pathlib import Path

from brain_adapter.fly_adapter import FlyBrainAdapter


LOG = Path("data/brain_runs.jsonl")


def main():
    brain = FlyBrainAdapter()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    print("Botmk · modo Termux")
    print("Escribe 'mariposa ' seguido de una frase. 'salir' termina.")
    while True:
        text = input("tú> ").strip()
        if text.lower() in {"salir", "exit", "quit"}:
            break
        if not text.lower().startswith("mariposa"):
            print("[ignorado] debe comenzar con 'mariposa'")
            continue
        phrase = text[len("mariposa"):].strip()
        if not phrase:
            print("[mosca] recibí el activador, pero falta una frase")
            continue
        result = brain.think(phrase)
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "text": phrase,
            "result": result,
        }
        with LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        print("mosca>", result)
        print(f"[guardado] {LOG}")


if __name__ == "__main__":
    main()
