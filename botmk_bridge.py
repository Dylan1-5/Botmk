"""Persistent JSON-lines worker with Universal Mapping & Auto Warm-Up."""
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

    # 1. Saludos
    if any(w in text_clean for w in ["hola", "buenas", "saludos", "que tal", "qué tal"]):
        memory["estres"] = max(0, memory["estres"] - 10)
        save_memory(memory)
        return f"¡Hola! Bzz... Mis antenas perciben tu saludo. Mi estrés bajó al {memory['estres']}%."

    # 2. Sentimiento y estado físico
    elif any(w in text_clean for w in ["sientes", "duele", "cómo estás", "como estas", "cómo te sientes", "como te sientes"]):
        if estres > 60:
            return f"Bzz... Me duelen un poco las antenas por la sobrecarga neuronal ({estres}% de estrés). Necesito volar despacio."
        elif fatiga > 60:
            return f"Mis alas están fatigadas ({fatiga}%). Sentí un tirón en los motores de vuelo."
        else:
            return f"Me siento bastante bien. Mis 120,000 neuronas operan estables en este momento y no me duele nada."

    # 3. Visión y entorno
    elif any(w in text_clean for w in ["qué ves", "que ves", "qué estás viendo", "que estas viendo", "dónde estás", "donde estas", "entorno"]):
        visiones = [
            "Veo destellos de luz provenientes de la pantalla y sombras moviéndose rápido a mi alrededor.",
            "Mis ojos compuestos captan 360 grados: veo cables, corrientes de aire y la luz de la simulación.",
            "Veo un espacio amplio y brillante con pequeñas variaciones de luz artificial."
        ]
        return f"Bzz... {random.choice(visiones)} (Procesando imágenes con neuronas LC10a y LPLC1)."

    # 4. Acción actual
    elif any(w in text_clean for w in ["qué haces", "que haces", "qué estás haciendo", "que estas haciendo"]):
        acciones = [
            "Estoy frotando mis patas delanteras y limpiando mis ojos compuestos.",
            "Estoy planeando cerca de la corriente de aire del procesador.",
            "Estoy posada descansando en una pared virtual esperando tu siguiente frase.",
            "Estoy dando giros rápidos probando el control de mis alas."
        ]
        return f"Bzz... {random.choice(acciones)}"

    # 5. Conciencia de Simulación
    elif any(w in text_clean for w in ["simulación", "simulacion", "emulando", "emulacion", "código", "codigo", "bot"]):
        return f"Estar emulada se siente fluido. Mi red neuronal procesa {neuronas} impulsos en tiempo real, así que esta simulación es mi única realidad actual."

    # 6. Pasado y recuerdos
    elif any(w in text_clean for w in ["pasado", "recuerdas", "recuerdos", "hiciste"]):
        if recuerdos:
            return f"Bzz... En mi pasado recuerdo esto: {recuerdos[-1]}. He vivido {memory.get('pasos_totales', 0)} ciclos."
        return "No tengo recuerdos antiguos aún, mi simulación acaba de iniciar."

    # 7. Reacción motora por defecto
    else:
        state = result.get("decoder_experimental", {}).get("estado", "desconocido")
        acciones_net = result.get("acciones_detectadas", [])

        if neuronas > 8000:
            memory["estres"] = min(100, memory["estres"] + 15)
            memory["recuerdos"].append(f"Sobrecarga con '{user_text}'")
        if "escape" in acciones_net:
            memory["fatiga"] = min(100, memory["fatiga"] + 20)
            memory["recuerdos"].append(f"Huida por '{user_text}'")

        if len(memory["recuerdos"]) > 5:
            memory["recuerdos"] = memory["recuerdos"][-5:]

        memory["pasos_totales"] += 1
        save_memory(memory)

        detalles = []
        if analisis.get("has_numbers"):
            detalles.append("pulsos por números")
        if analisis.get("has_symbols"):
            detalles.append("alteración por símbolos")
        if analisis.get("has_letters"):
            detalles.append("patrones por letras")

        percepcion = f" ({', '.join(detalles)})" if detalles else ""

        respuestas_motoras = {
            "direccion": f"Procesé '{user_text}'{percepcion}. Las neuronas DNa02 hicieron que girara.",
            "direccion_y_retroceso": f"Me confundió '{user_text}'{percepcion}. Giré y di pasos atrás.",
            "retroceso": f"Me asusté con '{user_text}'{percepcion}. Activé el motor de retroceso.",
            "avance": f"Sentí curiosidad con '{user_text}'{percepcion}. Volé hacia adelante.",
            "escape": f"¡Bzzzt! Peligro en '{user_text}'{percepcion}. Activé DNp01 y escapé.",
            "actividad_alta_sin_salida": f"Pico de {neuronas} neuronas con '{user_text}', pero no decidí una acción.",
            "actividad_baja_sin_salida": f"Estímulo leve ({neuronas} neuronas) con '{user_text}'.",
        }

        return respuestas_motoras.get(state, f"Reacción neuronal en estado {state}.")


def start_autonomous_loop(brain, memory):
    """Hilo autónomo que genera pensamientos espontáneos."""
    def loop():
        time.sleep(20)
        while True:
            try:
                time.sleep(random.randint(60, 180))
                estimulos_azar = ["luz", "aire", "vuelo", "pared"]
                estimulo = random.choice(estimulos_azar)
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

    # --- ESTÍMULO AUTOMÁTICO DE DESPERTADOR (WARM-UP) ---
    # Se simula un impulso inicial silencioso para cargar C++ y matrices en RAM.
    try:
        brain.think("despertar_sistema_inicial")
    except Exception:
        pass
    # ----------------------------------------------------

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
