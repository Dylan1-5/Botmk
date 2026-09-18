"""Puente entre frases y el simulador real de flybrain."""
import hashlib
import json


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
        # La decisión la produce la actividad de la red, no una respuesta prefabricada.
        injection = [(cells, max(0.1, signals[index]))
                     for index, (cells, _) in enumerate(self.input_cells)]
        fired_total = set()
        activity_by_step = []
        output_totals = {name: 0 for name in self.output_cells}
        output_steps = {name: [] for name in self.output_cells}
        peak_activity = 0

        for step_number in range(10):
            fired = set(self.brain.step(inject=injection))
            fired_total.update(fired)
            output_counts = {
                name: len(cells & fired)
                for name, cells in self.output_cells.items()
            }
            peak_activity = max(peak_activity, len(fired))
            for name, count in output_counts.items():
                output_totals[name] += count
                if count:
                    output_steps[name].append(step_number + 1)
            # Firma compacta: permite comparar patrones sin guardar miles de IDs.
            fired_ids = sorted(int(index) for index in fired)
            spike_hash = hashlib.sha256(
                json.dumps(fired_ids, separators=(",", ":")).encode("ascii")
            ).hexdigest()[:16]
            activity_by_step.append({
                "paso": step_number + 1,
                "neuronas_con_spike": len(fired),
                "salidas_con_spike": output_counts,
                "firma_spikes": spike_hash,
                "muestra_spikes": fired_ids[:16],
            })

        actions = [name for name, count in output_totals.items() if count]
        return {
            "modo": "flybrain-cpu",
            "mensaje": phrase,
            "neuronas_activadas": len(fired_total),
            "acciones_detectadas": actions or ["sin_comando_detectado"],
            "decoder_experimental": self.decode_activity(
                actions or ["sin_comando_detectado"],
                len(fired_total),
                output_totals,
                output_steps,
                peak_activity,
            ),
            "actividad_detallada": {
                "pasos": activity_by_step,
                "salidas_totales": output_totals,
            },
            "nota": "actividad de la red; aún no es lenguaje español generado por la mosca",
        }

    @staticmethod
    def decode_activity(
        actions: list[str],
        neurons_activated: int,
        output_totals: dict[str, int],
        output_steps: dict[str, list[int]],
        peak_activity: int,
    ) -> dict:
        """Decoder interpretable; no pretende ser español aprendido."""
        action_set = set(actions)
        if "escape" in action_set:
            state = "escape"
        elif "steer" in action_set and "backward" in action_set:
            state = "direccion_y_retroceso"
        elif "steer" in action_set:
            state = "direccion"
        elif "backward" in action_set:
            state = "retroceso"
        elif "forward" in action_set:
            state = "avance"
        elif neurons_activated >= 10000:
            state = "actividad_alta_sin_salida"
        else:
            state = "actividad_baja_sin_salida"
        if peak_activity < 1000:
            nivel = "bajo"
        elif peak_activity < 10000:
            nivel = "medio"
        else:
            nivel = "alto"
        return {
            "estado": state,
            "tipo": "decoder_experimental_reglas",
            "nivel_actividad": nivel,
            "pico_neuronas_por_paso": peak_activity,
            "salidas_totales": output_totals,
            "pasos_de_salida": output_steps,
        }

    def decide(self, features):
        return {"action": "UNKNOWN", "confidence": 0.0, "features": features}
