"""Puente entre frases y el simulador real de flybrain."""
import hashlib


class FlyBrainAdapter:
    def __init__(self):
        self.backend = None
        self.brain = None
        self.input_cells = None
        self.output_cells = None

    def load(self):
        from flybrain import FlyBrain
        self.brain = FlyBrain(device="cpu")
        # LC10a: seguimiento de objetivos; LPLC1: detección de objetos.
        self.input_cells = [
            (self.brain.cells(["LC10a"], side="L"), 0.8),
            (self.brain.cells(["LPLC1"], side="L"), 0.4),
        ]
        self.output_cells = {
            "escape": set(self.brain.cells(["DNp01"], side="L")),
            "forward": set(self.brain.cells(["DNg100"], side="L")),
            "steer": set(self.brain.cells(["DNa02"], side="L")),
            "backward": set(self.brain.cells(["MDN"], side="L")),
        }

    @staticmethod
    def encode_phrase(phrase: str) -> list[float]:
        digest = hashlib.sha256(phrase.encode("utf-8")).digest()
        return [round(byte / 255, 3) for byte in digest[:8]]

    def think(self, phrase: str) -> dict:
        if self.brain is None:
            self.load()
        signals = self.encode_phrase(phrase)
        # Variamos la intensidad con la frase, pero la decisión la produce
        # la actividad de la red, no una respuesta prefabricada.
        injection = [(cells, max(0.1, signals[index])) for index, (cells, _) in enumerate(self.input_cells)]
        fired = set()
        for _ in range(10):
            fired.update(self.brain.step(inject=injection))
        actions = [name for name, cells in self.output_cells.items() if cells & fired]
        return {
            "modo": "flybrain-cpu",
            "mensaje": phrase,
            "neuronas_activadas": len(fired),
            "acciones_detectadas": actions or ["sin_comando_detectado"],
            "nota": "actividad de la red; aún no es lenguaje español generado por la mosca",
        }

    def decide(self, features):
        return {"action": "UNKNOWN", "confidence": 0.0, "features": features}
