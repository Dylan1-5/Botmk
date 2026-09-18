# Botmk

Proyecto separado para experimentar con una interfaz en español sobre una simulación del cerebro de la mosca.

## Probar en Termux

```bash
pkg install python git
cd Botmk
python -m bot.termux
```

Solo se procesan mensajes que comienzan con `mariposa`:

```text
mariposa hola, ¿cómo estás?
```

Todo lo demás se ignora. El modo actual es diagnóstico: convierte la frase en señales reproducibles y muestra qué recibiría el adaptador. No se presenta como una respuesta neuronal real hasta conectar y validar el backend `fly.ai`.

## Estructura

- `language/`: interpretación inicial en español.
- `brain_adapter/`: interfaz y encoder aislado para el simulador.
- `bot/termux.py`: consola de prueba.
- `tests/`: pruebas reproducibles.

Este proyecto no modifica Sylphie ni comparte sus credenciales, sesiones o base de datos.
