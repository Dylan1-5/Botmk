from language.intents import parse_message

def test_balance(): assert parse_message('cuánto dinero tengo')['intent'] == 'BALANCE'
def test_slot_amount(): assert parse_message('juguemos slot 500') == {'intent': 'SLOT', 'slots': {'amount': 500}}
