"""Puente entre texto y el simulador de la mosca.

El backend real se conecta cuando sus APIs estén instaladas y validadas. El
modo diagnóstico permite ejecutar el prototipo en Termux sin dependencias
pesadas y muestra las señales que recibiría el cerebro.
"""
import hashlib


class FlyBrainAdapter:
    def __init__(self):
        self.backend = None

    def load(self):
        try:
            import flybrain  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Backend flybrain no instalado") from exc
        self.backend = flybrain

    @staticmethod
    def encode_phrase(phrase: str) -> list[float]:
        digest = hashlib.sha256(phrase.encode("utf-8")).digest()
        return [round(byte / 255, 3) for byte in digest[:8]]

    def think(self, phrase: str) -> dict:
        features = self.encode_phrase(phrase)
        if self.backend is None:
            return {
                "modo": "diagnóstico",
                "mensaje": phrase,
                "señales": features,
                "nota": "flybrain aún no está instalado; todavía no es una respuesta neuronal real",
            }
        raise NotImplementedError("Falta definir el encoder/decoder del backend flybrain")

    def decide(self, features: list[float]) -> dict:
        if self.backend is None:
            return {"action": "UNKNOWN", "confidence": 0.0, "features": features}
        raise NotImplementedError("Falta definir el encoder/decoder del experimento")
