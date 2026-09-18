# Botmk

Proyecto separado para experimentar con una interfaz en español sobre una simulación del cerebro de la mosca.

## Estado

Prototipo local: texto en español → intención → vector de características → adaptador del cerebro. El adaptador es deliberadamente una interfaz aislada; todavía no afirma que la simulación entienda lenguaje.

## Ejecutar

```bash
python -m bot.main
python -m pytest
```

## Estructura

- `language/`: interpretación inicial en español.
- `brain_adapter/`: interfaz aislada para el simulador.
- `bot/`: prueba de consola.
- `tests/`: pruebas reproducibles.

Este proyecto no modifica Sylphie ni comparte sus credenciales, sesiones o base de datos.
