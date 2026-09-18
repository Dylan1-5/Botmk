class FlyBrainAdapter:
    def __init__(self): self.backend = None
    def load(self):
        try: import flybrain
        except ImportError as exc: raise RuntimeError('Backend flybrain no instalado') from exc
        self.backend = flybrain
    def decide(self, features):
        if self.backend is None: return {'action': 'UNKNOWN', 'confidence': 0.0, 'features': features}
        raise NotImplementedError('Falta definir el encoder/decoder del experimento')
