from generation import generate_prompt
from generation import call_openai

data = None

def inject_data(_data):
    global data
    data = _data


# Initialize the first set of spells for the game.
def initialize_spells():
    for element in ["earth", "fire", "air", "water", "light", "shadow"]:
        generate_spell(element, "novice")

# Generate a spell, and generate a negation spell as well, as all spells come in pairs.
def generate_spell(elements, tier):
    print("Generating spell for " + elements + " @ " + tier + " tier.")
    prompt = generate_prompt("magic/creation", [elements, tier])
    completion = call_openai(prompt)
    print(completion)
    spell_id = data.add_spell(completion)
    generate_mishaps(spell_id, completion)
    generate_negation(completion)

# Generates the mishaps table for a spell.
def generate_mishaps(spell_id, spell):
    print("Generating mishaps for spell...")
    prompt = generate_prompt("magic/mishaps", [spell])
    completion = call_openai(prompt)
    print(completion)
    data.set_mishaps(spell_id, completion)
    return completion

# Generates the negation of a spell.
def generate_negation(spell):
    print("Generating negation for spell...")
    prompt = generate_prompt("magic/create_negation", [spell])
    completion = call_openai(prompt)
    print(completion)
    spell_id = data.add_spell(completion)
    generate_mishaps(spell_id, completion)
