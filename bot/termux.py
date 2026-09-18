"""Consola para probar Botmk en Termux.

Solo procesa mensajes que comienzan con 'mariposa'.
"""
from brain_adapter.fly_adapter import FlyBrainAdapter


def main():
    brain = FlyBrainAdapter()
    print("Botmk · modo Termux")
    print("Escribe 'mariposa ' seguido de una frase. 'salir' termina.")
    while True:
        text = input("tú> ").strip()
        if text.lower() in {"salir", "exit", "quit"}:
            break
        if not text.lower().startswith("mariposa"):
            print("[ignorado] debe comenzar con 'mariposa'")
            continue
        phrase = text[len("mariposa"):].strip()
        if not phrase:
            print("[mosca] recibí el activador, pero falta una frase")
            continue
        print("mosca>", brain.think(phrase))


if __name__ == "__main__":
    main()
