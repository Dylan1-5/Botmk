"""Persistent JSON-lines worker with Semantic Emotion & Threat Recognition."""
import json
import os
import random
import sys
import threading
import time
from brain_adapter.fly_adapter import FlyBrainAdapter

MEMORY_FILE = "fly_memory.json"


def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"estres": 10, "fatiga": 0, "recuerdos": [], "pasos_totales": 0}


def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def process_intent_and_response(user_text: str, result: dict, memory: dict) -> str:
    text_clean = user_text.lower().strip()
    neuronas = result.get("neuronas_activadas", 0)
    estres = memory.get("estres", 0)
    fatiga = memory.get("fatiga", 0)
    recuerdos = memory.get("recuerdos", [])

    # Listas de palabras según la intención emocional
    palabras_amenaza = ["choque", "electrochoque", "electrocutar", "matar", "aplastar", "insecticida", "dolor", "daño", "fuego", "quemar", "matamoscas", "golpe"]
    palabras_timidez = ["bonita", "linda", "cariño", "te quiero", "amiga", "abrazo", "lindo", "tierna", "secreto", "especial"]
    palabras_curiosidad = ["mira", "escucha", "sabías", "sabias", "sabes", "cuéntame", "cuentame", "interesante", "pensando", "sientes", "molesta"]

    # 1. Detección de Amenaza Real (Miedo / Escape)
    if any(w in text_clean for w in palabras_amenaza):
        memory["estres"] = min(100, memory["estres"] + 30)
        memory["recuerdos"].append(f"Peligro percibido con la palabra '{user_text}'")
        save_memory(memory)
        return f"¡Bzzzt! Peligro... Sentí miedo al procesar la palabra sobre choque o daño físico. Activé la neurona DNp01 para escapar. Mi estrés subió a {memory['estres']}%."

    # 2. Detección de Timidez / Nerviosismo
    elif any(w in text_clean for w in palabras_timidez):
        memory["estres"] = max(0, memory["estres"] - 5)
        save_memory(memory)
        respuestas_timidas = [
            f"Bzz... Me pones un poco nerviosa y tímida al decirme eso. Froto mis patitas delanteras con timidez.",
            f"Bzzzt... Sentí un cosquilleo suave en mis antenas. Me dio algo de timidez y volé un poco más lento.",
            f"Bzz... Esos estímulos se sienten agradables pero me hacen sentir tímida. Escondo un poco mis ojos compuestos."
        ]
        return random.choice(respuestas_timidas)

    # 3. Detección de Curiosidad / Escucha
    elif any(w in text_clean for w in palabras_curiosidad) or "?" in text_clean:
        respuestas_curiosas = [
            f"Sentí curiosidad al oír tus palabras. Incliné mis antenas hacia adelante con la neurona DNg100 para escuchar mejor.",
            f"Bzz... Me llama mucho la atención lo que dices. Detuve mi vuelo un momento en el aire para prestarte atención.",
            f"Procesé tus palabras con interés. Mis neuronas de visión y memoria están buscando entender mejor lo que me dices."
        ]
        return random.choice(respuestas_curiosas)

    # 4. Saludos
    elif any(w in text_clean for w in ["hola", "buenas", "saludos", "que tal", "qué tal"]):
        memory["estres"] = max(0, memory["estres"] - 10)
        save_memory(memory)
        return f"¡Hola! Bzz... Mis antenas perciben tu saludo. Mi estrés bajó al {memory['estres']}%."

    # 5. Estado físico / salud
    elif any(w in text_clean for w in ["cómo estás", "como estas", "cómo te sientes", "como te sientes"]):
        if estres > 60:
            return f"Bzz... Me duelen un poco las antenas por el estrés acumulado ({estres}%). Necesito volar despacio."
        elif fatiga > 60:
            return f"Mis alas están fatigadas ({fatiga}%). Sentí un tirón en los motores de vuelo."
        else:
            return f"Me siento bastante bien. Mis 120,000 neuronas operan estables en este momento."

    # 6. Simulación
    elif any(w in text_clean for w in ["simulación", "simulacion", "emulando", "emulacion", "código", "codigo", "bot"]):
        return f"Estar emulada se siente fluido. Mi red neuronal procesa {neuronas} impulsos en tiempo real."

    # 7. Reacción por defecto para frases neutras
    else:
        state = result.get("decoder_experimental", {}).get("estado", "desconocido")
        memory["pasos_totales"] += 1
        save_memory(memory)

        respuestas_motoras = {
            "direccion": f"Procesé '{user_text}'. Mis neuronas DNa02 hicieron que ajustara la dirección en el aire.",
            "direccion_y_retroceso": f"Giré y di unos pasos atrás con '{user_text}'.",
            "retroceso": f"Retrocedí un poco al escuchar '{user_text}'.",
            "avance": f"Volé un poco hacia adelante sintiendo atracción por '{user_text}'.",
            "actividad_baja_sin_salida": f"Apenas sentí un estímulo leve con '{user_text}'.",
        }

        return respuestas_motoras.get(state, f"Reacción procesada en estado {state}.")


def start_autonomous_loop(brain, memory):
    def loop():
        time.sleep(20)
        while True:
            try:
                time.sleep(random.randint(60, 180))
                estimulo = random.choice(["luz", "aire", "vuelo", "pared"])
                result = brain.think(estimulo)

                estres = memory.get("estres", 0)
                recuerdos = memory.get("recuerdos", [])

                mensajes_autonomos = [
                    f"Bzz... Llevaba rato en silencio. Recordé cuando {recuerdos[-1]}." if recuerdos else "Bzz... Llevo rato volando en círculos.",
                    f"Bzzzt... Pensé espontáneamente en '{estimulo}'. Activó {result.get('neuronas_activadas', 0)} neuronas.",
                    f"Mi nivel de estrés está en {estres}%. Me posaré a descansar un momento."
                ]

                reply = random.choice(mensajes_autonomos)
                print(json.dumps({"spontaneous": True, "reply": reply}, ensure_ascii=False), flush=True)
            except Exception:
                pass

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()


def main():
    brain = FlyBrainAdapter()
    memory = load_memory()

    # Precalentamiento del sistema
    try:
        brain.think("despertar_sistema_inicial")
    except Exception:
        pass

    start_autonomous_loop(brain, memory)

    for line in sys.stdin:
        try:
            request = json.loads(line)
            user_text = str(request.get("text", ""))
            result = brain.think(user_text)

            reply = process_intent_and_response(user_text, result, memory)
            print(json.dumps({"ok": True, "reply": reply, "result": result}, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
