"""Persistent JSON-lines worker for the WhatsApp bridge."""
import json
import sys
from brain_adapter.fly_adapter import FlyBrainAdapter


def response_for(result: dict) -> str:
    state = result.get("decoder_experimental", {}).get("estado", "desconocido")
    messages = {
        "direccion": "Estoy detectando un cambio de dirección.",
        "direccion_y_retroceso": "Estoy cambiando de dirección y retrocediendo.",
        "retroceso": "Estoy retrocediendo.",
        "avance": "Estoy avanzando.",
        "escape": "Detecté una señal de escape.",
        "actividad_alta_sin_salida": "Tengo actividad alta, pero no detecté una acción definida.",
        "actividad_baja_sin_salida": "Tengo actividad baja y no detecté una acción definida.",
    }
    return messages.get(state, f"Mi estado experimental es: {state}.")


def main():
    brain = FlyBrainAdapter()
    for line in sys.stdin:
        try:
            request = json.loads(line)
            result = brain.think(str(request.get("text", "")))
            print(json.dumps({"ok": True, "reply": response_for(result), "result": result}, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
