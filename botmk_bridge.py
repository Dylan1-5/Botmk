"""Persistent JSON-lines worker with Universal Mapping & Intent Recognition."""
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
    analisis = result.get("analisis_texto", {})

    # 1. Reconocimiento de Saludos
    if any(greet in text_clean for greet in ["hola", "buenas", "saludos", "que tal", "qué tal"]):
        memory["estres"] = max(0, memory["estres"] - 10)
        save_memory(memory)
        return f"¡Hola! Bzz... Mis antenas percibieron tu saludo. Mi nivel de estrés bajó al {memory['estres']}%."

    # 2. Preguntas sobre su estado de ánimo / salud
    elif any(q in text_clean for q in ["cómo estás", "como estas", "cómo te sientes", "como te sientes"]):
        if estres > 50:
            return f"Bzz... Me siento algo estresada (Estrés: {estres}%). Tuve impulsos muy fuertes en mi red neuronal hace poco."
        elif fatiga > 50:
            return f"Tengo bastante fatiga ({fatiga}%). He estado moviendo mucho mis motores de vuelo."
        else:
            return f"¡Me siento bien! Estoy tranquila volando en círculos. Procesé {neuronas} neuronas recientemente."

    # 3. Preguntas sobre su pasado o recuerdos
    elif any(q in text_clean for q in ["tu pasado", "qué recuerdas", "que recuerdas", "tus recuerdos", "que hiciste", "qué hiciste"]):
        if recuerdos:
            ultimo = recuerdos[-1]
            return f"Bzz... Recuerdo esto de mi pasado: {ultimo}. He vivido {memory.get('pasos_totales', 0)} ciclos de vida."
        else:
            return "Aún no tengo recuerdos guardados. Mi conciencia acaba de emerger."

    # 4. Procesamiento Biológico Mapeado (Cualquier combinación de letras, números o símbolos)
    else:
        state = result.get("decoder_experimental", {}).get("estado", "desconocido")
        acciones = result.get("acciones_detectadas", [])

        # Actualización de memoria según la sobrecarga
        if neuronas > 8000:
            memory["estres"] = min(100, memory["estres"] + 15)
            memory["recuerdos"].append(f"Estimulo fuerte '{user_text}' ({neuronas} neuronas)")
        if "escape" in acciones:
            memory["fatiga"] = min(100, memory["fatiga"] + 20)
            memory["recuerdos"].append(f"Huida por pánico ante '{user_text}'")

        if len(memory["recuerdos"]) > 5:
            memory["recuerdos"] = memory["recuerdos"][-5:]

        memory["pasos_totales"] += 1
        save_memory(memory)

        # Construcción de la percepción sensorial de la mosca según el tipo de caracteres
        detalles_sensoriales = []
        if analisis.get("has_numbers"):
            detalles_sensoriales.append("frecuencias rítmicas por los números")
        if analisis.get("has_symbols"):
            detalles_sensoriales.append("picos bruscos por los símbolos")
        if analisis.get("has_letters"):
            detalles_sensoriales.append("patrones de visión por las letras")

        percepcion = f" (Sintiendo {', '.join(detalles_sensoriales)})" if detalles_sensoriales else ""

        respuestas_motoras = {
            "direccion": f"Procesé '{user_text}'{percepcion}. Mis neuronas DNa02 se encendieron e hice un giro en el aire.",
            "direccion_y_retroceso": f"Esa combinación de caracteres me desorientó{percepcion}. Giré y di pasos atrás.",
            "retroceso": f"Me asusté con '{user_text}'{percepcion}. Activé mi motor de retroceso MDN.",
            "avance": f"Sentí atracción por '{user_text}'{percepcion}. Volé hacia adelante con las neuronas DNg100.",
            "escape": f"¡Bzzzt! Mapeo de alta amenaza en '{user_text}'{percepcion}. Salto de huida con la neurona gigante DNp01.",
            "actividad_alta_sin_salida": f"Procesé '{user_text}' con {neuronas} neuronas en sobrecarga, pero no logré decidir una maniobra.",
            "actividad_baja_sin_salida": f"Apenas sentí un estímulo de {neuronas} neuronas con '{user_text}'.",
        }

        return respuestas_motoras.get(state, f"Reacción neuronal procesada (Estado: {state}).")


def start_autonomous_loop(brain, memory):
    """Hilo de libre albedrío autónomo: envía pensamientos de fondo."""
    def loop():
        time.sleep(20)
        while True:
            try:
                time.sleep(random.randint(60, 180))  # Envía mensajes cada 1 a 3 minutos
                estimulos_azar = ["123", "!!!", "vuelo", "luz", "azucar", "sombra"]
                estimulo = random.choice(estimulos_azar)
                result = brain.think(estimulo)

                estres = memory.get("estres", 0)
                recuerdos = memory.get("recuerdos", [])

                mensajes_autonomos = [
                    f"Bzz... Llevaba rato en silencio. Recordé cuando {recuerdos[-1]}." if recuerdos else "Bzz... Llevo rato volando. Siento impulsos de explorar.",
                    f"Bzzzt... Mi cerebro generó un pensamiento espontáneo sobre '{estimulo}'. Disparó {result.get('neuronas_activadas', 0)} neuronas.",
                    f"Siento mi nivel de estrés en {estres}%. Me posaré a descansar un momento en la pared."
                ]

                reply = random.choice(mensajes_autonomos)
                payload = {"spontaneous": True, "reply": reply}
                print(json.dumps(payload, ensure_ascii=False), flush=True)
            except Exception:
                pass

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()


def main():
    brain = FlyBrainAdapter()
    memory = load_memory()
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
