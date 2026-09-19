"""Puente Universal de Mapeo Semántico y Neurobiológico para FlyBrain."""
import hashlib
import json
import re
import sys


class FlyBrainAdapter:
    def __init__(self):
        self.brain = None
        self.input_cells = None
        self.output_cells = None

    def load(self):
        try:
            from flybrain import FlyBrain
            self.brain = FlyBrain(device="cpu")
            
            self.input_cells = {
                "vision_objetos": self.brain.cells(["LC10a"], side="L"),
                "vision_movimiento": self.brain.cells(["LPLC1"], side="L"),
                "cuerpos_hongo": self.brain.cells(["MBON"], side="L"),
            }
            
            self.output_cells = {
                "escape": set(self.brain.cells(["DNp01"], side="L")),
                "forward": set(self.brain.cells(["DNg100"], side="L")),
                "steer": set(self.brain.cells(["DNa02"], side="L")),
                "backward": set(self.brain.cells(["MDN"], side="L")),
            }
        except Exception as err:
            print(f"[FlyBrain Warning] Modo simulación fallback activo: {err}", file=sys.stderr)
            self.brain = None

    def map_text_to_neural_signals(self, text: str) -> dict:
        has_numbers = bool(re.search(r'\d', text))
        has_letters = bool(re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', text))
        has_symbols = bool(re.search(r'[^\w\s]', text))
        
        sha = hashlib.sha256(text.encode("utf-8")).digest()
        
        stim_vision = round(sha[0] / 255.0, 3)
        stim_memory = round(sha[1] / 255.0, 3)
        stim_motion = round(sha[2] / 255.0, 3)

        return {
            "has_numbers": has_numbers,
            "has_letters": has_letters,
            "has_symbols": has_symbols,
            "length": len(text),
            "signals": {
                "vision": max(0.1, stim_vision),
                "memory": max(0.1, stim_memory),
                "motion": max(0.1, stim_motion)
            }
        }

    def think(self, phrase: str) -> dict:
        if self.brain is None:
            self.load()

        mapping = self.map_text_to_neural_signals(phrase)
        signals = mapping["signals"]

        if self.brain is None:
            return self._fallback_think(phrase, mapping)

        injection = [
            (self.input_cells["vision_objetos"], signals["vision"]),
            (self.input_cells["vision_movimiento"], signals["motion"]),
            (self.input_cells["cuerpos_hongo"], signals["memory"]),
        ]

        fired_total = set()
        output_totals = {name: 0 for name in self.output_cells}
        output_steps = {name: [] for name in self.output_cells}
        peak_activity = 0

        for step_number in range(10):
            try:
                fired = set(self.brain.step(inject=injection))
            except Exception:
                fired = set()

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

        actions = [name for name, count in output_totals.items() if count]

        return {
            "modo": "flybrain-mapped",
            "mensaje": phrase,
            "analisis_texto": mapping,
            "neuronas_activadas": len(fired_total),
            "acciones_detectadas": actions or ["sin_comando_detectado"],
            "decoder_experimental": self.decode_activity(
                actions or ["sin_comando_detectado"],
                len(fired_total),
                output_totals,
                output_steps,
                peak_activity,
            )
        }

    def _fallback_think(self, phrase: str, mapping: dict) -> dict:
        sig = mapping["signals"]
        neuronas = int((sig["vision"] + sig["memory"] + sig["motion"]) * 5000)
        
        actions = []
        # Corregido: la velocidad o el movimiento activan avance o giro, no pánico automático
        if sig["motion"] > 0.6:
            actions.append("steer")
        if sig["memory"] > 0.4:
            actions.append("forward")

        return {
            "modo": "flybrain-simulated-mapping",
            "mensaje": phrase,
            "analisis_texto": mapping,
            "neuronas_activadas": neuronas,
            "acciones_detectadas": actions or ["sin_comando_detectado"],
            "decoder_experimental": self.decode_activity(
                actions or ["sin_comando_detectado"],
                neuronas,
                {a: 5 for a in actions},
                {},
                neuronas // 2
            )
        }

    @staticmethod
    def decode_activity(
        actions: list[str],
        neurons_activated: int,
        output_totals: dict[str, int],
        output_steps: dict[str, list[int]],
        peak_activity: int,
    ) -> dict:
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
        else:
            state = "actividad_baja_sin_salida"

        return {
            "estado": state,
            "nivel_actividad": "alto" if peak_activity > 5000 else "medio",
            "pico_neuronas_por_paso": peak_activity,
            "salidas_totales": output_totals,
        }
