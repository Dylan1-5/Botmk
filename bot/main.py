from brain_adapter.fly_adapter import FlyBrainAdapter
from language.intents import parse_message

def main():
    brain = FlyBrainAdapter()
    print("Botmk experimental. Escribe 'salir' para terminar.")
    while True:
        text = input('> ')
        if text.lower().strip() in {'salir', 'exit', 'quit'}: break
        intent = parse_message(text)
        print({'parsed': intent, 'brain': brain.decide([float(hash(intent['intent']) % 1000)])})

if __name__ == '__main__': main()
