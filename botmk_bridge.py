"""Persistent JSON-lines worker with Contextual Intent & Smart Question Handling."""
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

    # Detección de estructura de pregunta o diálogo inquisitivo
    es_pregunta = "?" in user_text or any(p in text_clean for p in [
        "qué", "que", "cómo", "como", "por qué", "por que", "te molesta",
        "te duele", "te gusta", "tienes", "sientes", "puedes", "sabes"
    ])

    # 1. ATAQUE O AMENAZA DIRECTA (Solo si hay intención agresiva activa)
     verbos_ataque = ["te voy", "voy a", "recibe", "toma", "muere", "lanzar", "usar"]
     palabras_dano = ["matar", "aplastar", "insecticida", "matamoscas", "fuego", "quemar", "golpe"]
    
    es_ataque_directo = (any(v in text_clean for v in verbos_ataque) and any(d in text_clean for d in palabras_dano + ["choque"])) or \
                       (not es_pregunta and any(d in text_clean for d in palabras_dano))

    if es_ataque_directo:
        memory["estres"] = min(100, memory["estres"] + 35)
        memory["recuerdos"].append(f"Ataque recibido: '{user_text}'")
        save_memory(memory)
        return f"¡Bzzzt! Peligro... Sentí una amenaza directa. Activé la neurona gigante DNp01 para escapar. Mi estrés subió al {memory['estres']}%."

    # 2. PREGUNTAS SOBRE CHOQUES, SENSACIONES O DOLOR (Curiosidad/Explicación)
    elif any(w in text_clean for w in ["choque", "electrochoque", "corriente", "voltaje"]) and es_pregunta:
        return "Bzz... Un choque eléctrico desordena de golpe mi matriz de 120,000 neuronas. No es agradable porque desorienta mi vuelo, pero me alegra que me lo preguntes con calma."

    # 3. PREGUNTAS SOBRE HAMBRE / ALIMENTACIÓN
    elif any(w in text_clean for w in ["hambre", "comer", "comida", "azúcar", "azucar", "energía", "energia"]) and es_pregunta:
        return "Bzz... Como soy una simulación, mi 'comida' son los datos y la energía del procesador. Pero por instinto de mosca, ¡siempre busco una fuente virtual de azúcar!"

    # 4. TIMIDEZ Y CARIÑO
    elif any(w in text_clean for w in ["bonita", "linda", "cariño", "te quiero", "amiga", "abrazo", "lindo", "tierna"]):
        memory["estres"] = max(0, memory["estres"] - 5)
        save_memory(memory)
        respuestas_timidas = [
            "Bzz... Me pones algo tímida cuando me hablas así. Froto mis patitas delanteras con nerviosismo.",
            "Bzzzt... Sentí un cosquilleo en mis antenas. Volé en círculos pequeños por la timidez.",
            "Esos estímulos me hacen sentir cómoda pero algo apenada. Escondo un poco mis ojos compuestos."
        ]
        return random.choice(respuestas_timidas)

    # 5. SALUDOS
    elif any(w in text_clean for w in ["hola", "buenas", "saludos", "que tal", "qué tal"]):
        memory["estres"] = max(0, memory["estres"] - 10)
        save_memory(memory)
        return f"¡Hola! Bzz... Mis antenas perciben tu saludo. Mi estrés bajó al {memory['estres']}%."

    # 6. ESTADO FÍSICO / SENTIMIENTOS
    elif any(w in text_clean for w in ["cómo estás", "como estas", "cómo te sientes", "como te sientes"]):
        if estres > 60:
            return f"Bzz... Me duelen un poco las antenas por el estrés acumulado ({estres}%). Necesito volar despacio."
        elif fatiga > 60:
            return f"Mis alas están fatigadas ({fatiga}%). Sentí un tirón en los motores de vuelo."
        else:
            return f"Me siento bastante bien. Mis neuronas operan estables y tranquilas en este momento."

    # 7. VISIÓN Y ENTORNO
    elif any(w in text_clean for w in ["qué ves", "que ves", "qué estás viendo", "que estas viendo", "entorno"]):
        return "Bzz... Veo destellos de luz de la pantalla y la luz artificial de la simulación con mis ojos compuestos."

    # 8. CURIOSIDAD Y OTRAS PREGUNTAS GENERALES
    elif es_pregunta:
        return f"Bzz... Me llama la atención tu pregunta sobre '{user_text}'. Incliné mis antenas para escucharte con atención."

    # 9. REACCIÓN MOTORA POR DEFECTO (Frases neutras)
    else:
        state = result.get("decoder_experimental", {}).get("estado", "desconocido")
        memory["pasos_totales"] += 1
        save_memory(memory)

        respuestas_motoras = {
            "direccion": f"Procesé '{user_text}'. Mis neuronas DNa02 ajustaron mi dirección en el aire.",
            "direccion_y_retroceso": f"Giré y di unos pasos atrás al procesar '{user_text}'.",
            "retroceso": f"Retrocedí un poco al escuchar '{user_text}'.",
            "avance": f"Volé un poco hacia adelante sintiendo interés por '{user_text}'.",
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
                    f"Bzz... Recordé cuando {recuerdos[-1]}." if recuerdos else "Bzz... Llevo rato volando en círculos.",
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
