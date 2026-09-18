import re

def parse_message(text: str) -> dict:
    value = text.strip().lower()
    if any(w in value for w in ('hola', 'buenas', 'hey')): return {'intent': 'GREETING', 'slots': {}}
    if any(w in value for w in ('ayuda', 'help', 'comandos')): return {'intent': 'HELP', 'slots': {}}
    if any(w in value for w in ('saldo', 'dinero', 'balance', 'monedas')): return {'intent': 'BALANCE', 'slots': {}}
    match = re.search(r'(?:slot|apost(?:ar|emos)?).*?(\d[\d,.]*)', value)
    if match: return {'intent': 'SLOT', 'slots': {'amount': int(match.group(1).replace(',', '').replace('.', ''))}}
    if any(w in value for w in ('ranking', 'top', 'mejores')): return {'intent': 'RANKING', 'slots': {}}
    return {'intent': 'UNKNOWN', 'slots': {}}
