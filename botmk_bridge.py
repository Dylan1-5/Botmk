"""Persistent JSON-lines worker for the WhatsApp bridge with Fly Brain Memory & Autonomy."""
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
    return {
        "estres": 10,
        "fatiga": 0,
        "recuerdos": [],
        "pasos_totales": 0
    }

def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def update_memory_state(memory, result, user_text):
    memory["pasos_totales"] += 1
    neuronas = result.get("neuronas_activadas", 0)
    acciones = result.get("acciones_detectadas", [])

    # Modificar estrés y fatiga según la carga recibida
    if neuronas > 10000:
        memory["estres"] = min(100, memory["estres"] + 20)
        memory["recuerdos"].append(f"Sobrecarga de {neuronas} neuronas con '{user_text}'")
    else:
        memory["estres"] = max(0, memory["estres"] - 5)

    if "escape" in acciones:
        memory["fatiga"] = min(100, memory["fatiga"] + 25)
        memory["recuerdos"].append("Tuve que dar un salto de huida por pánico.")

    # Guardar solo los últimos 5 recuerdos pasados
    if len(memory["recuerdos"]) > 5:
        memory["recuerdos"] = memory["recuerdos"][-5:]

    save_memory(memory)

def response_for(result: dict, memory: dict, user_text: str) -> str:
    state = result.get("decoder_experimental", {}).get("estado", "desconocido")
    neuronas = result.get("neuronas_activadas", 0)
    estres = memory.get("estres", 0)
    fatiga = memory.get("fatiga", 0)
    recuerdos = memory.get("recuerdos", [])

    respuestas_motoras = {
        "direccion": f"Bzz... Al procesar '{user_text}', mis neuronas DNa02 se encendieron. Cambié de dirección en el aire.",
        "direccion_y_retroceso": f"Esa frase me sacudió. Mis motores me hicieron girar y dar un paso atrás.",
        "retroceso": f"Me asusté un poco con '{user_text}'. Activé mi motor de retroceso.",
        "avance": f"Siento curiosidad por '{user_text}'. Mis neuronas DNg100 me impulsan a volar hacia adelante.",
        "escape": f"¡Bzzzt! Siento peligro. Activé mi neurona gigante DNp01 y di un salto de huida instantáneo.",
        "actividad_alta_sin_salida": f"¡Uff! Mi cerebro tuvo un pico de {neuronas} neuronas encendidas, pero no supe a dónde volar.",
        "actividad_baja_sin_salida": f"Apenas sentí un cosquilleo en mis antenas ({neuronas} neuronas). Casi no me hizo efecto.",
    }

    base_msg = respuestas_motoras.get(state, f"Siento algo raro en mi red neuronal (Estado: {state}).")

    emocion = ""
    if estres > 60:
        emocion = f" Siento mucho estrés ({estres}%) acumulado."
    elif fatiga > 50:
        emocion = f" Mis alas están agotadas (Fatiga: {fatiga}%)."

    recuerdo_msg = ""
    if recuerdos and random.random() < 0.5:
        recuerdo_msg = f" Aún recuerdo mi pasado reciente: {recuerdos[-1]}."

    return f"{base_msg}{emocion}{recuerdo_msg}"

def start_autonomous_loop(brain, memory):
    """Hilo autónomo (Libre albedrío): Habla por sí sola en intervalos aleatorios."""
    def loop():
        time.sleep(20)
        while True:
            try:
                time.sleep(random.randint(60, 180))  # Envía mensaje cada 1 a 3 minutos
                
                estimulos_azar = ["aire", "vuelo", "luz", "sombra", "azucar", "peligro"]
                estimulo = random.choice(estimulos_azar)
                result = brain.think(estimulo)
                
                estres = memory.get("estres", 0)
                recuerdos = memory.get("recuerdos", [])
                
                mensajes_autonomos = [
                    f"Bzz... Llevaba rato en silencio. Estaba recordando cuando {recuerdos[-1]}." if recuerdos else "Bzz... Llevo rato volando en círculos. Siento ganas de explorar.",
                    f"Bzzzt... Tuve un pensamiento espontáneo sobre '{estimulo}'. Disparó {result.get('neuronas_activadas', 0)} neuronas en mi cerebro.",
                    f"Siento que mi nivel de estrés está en {estres}%. Necesito descansar sobre una pared un momento."
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
            
            update_memory_state(memory, result, user_text)
            reply = response_for(result, memory, user_text)
            
            print(json.dumps({"ok": True, "reply": reply, "result": result}, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
