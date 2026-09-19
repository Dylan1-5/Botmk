"""Capa cognitiva experimental sobre FlyBrain.

No afirma conciencia: conserva actividad del cerebro simulado y añade memoria,
estado interno, selección de respuestas y evaluación de acciones.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ModifiedMind:
    """Mente híbrida: actividad de flybrain + estado y memoria persistentes."""

    def __init__(self, brain: Any, state_path: str = "data/mind_state.json"):
        self.brain = brain
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        return {"turns": 0, "known_topics": [], "values": {"ayudar": 0.5, "no_dañar": 1.0}}

    def _save(self) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)

    @staticmethod
    def _topic(text: str) -> str:
        words = [w.strip("¿?¡!,.:;()[]").lower() for w in text.split()]
        return " ".join(words[:4]) or "silencio"

    def _choose_intent(self, text: str, state: str) -> str:
        """Elige entre respuestas candidatas; no usa una respuesta única fija."""
        candidates = {
            "direccion": ["orientarme", "observar", "explorar"],
            "avance": ["avanzar", "explorar", "acercarme"],
            "retroceso": ["retroceder", "esperar", "revisar"],
            "escape": ["alejarme", "protegerme", "esperar"],
        }.get(state, ["observar", "recordar", "esperar"])
        digest = hashlib.sha256(f"{self.state['turns']}:{text}".encode()).digest()
        return candidates[digest[0] % len(candidates)]

    def process(self, text: str) -> dict:
        result = self.brain.think(text)
        decoder = result.get("decoder_experimental", {})
        state = decoder.get("estado", "desconocido")
        topic = self._topic(text)
        if topic not in self.state["known_topics"]:
            self.state["known_topics"].append(topic)
        self.state["turns"] += 1
        intent = self._choose_intent(text, state)
        evaluation = "aceptable" if intent not in {"alejarme", "protegerme"} else "precaución"
        self._save()
        return {
            "brain_result": result,
            "mind": {
                "estado_interno": state,
                "intencion_elegida": intent,
                "evaluacion": evaluation,
                "memoria_turnos": self.state["turns"],
                "memoria_temas": len(self.state["known_topics"]),
                "tipo": "mente_hibrida_experimental_sin_prueba_de_conciencia",
            },
        }

    @staticmethod
    def verbalize(packet: dict) -> str:
        mind = packet["mind"]
        state = mind["estado_interno"]
        intent = mind["intencion_elegida"]
        evaluation = mind["evaluacion"]
        return f"Mi actividad indica {state}. Elegí {intent}; lo considero {evaluation}."
