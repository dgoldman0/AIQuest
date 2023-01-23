from generation import generate_prompt
from generation import call_openai
import characters

data = None

def inject_data(_data):
    global data
    data = _data

# Create a new realm.
def create_realm():
    print("Creating Realm")
    prompt = generate_prompt("realms/create_realm")
    setting = call_openai(prompt, 512)
    prompt = generate_prompt("realms/name_realm", (setting, ))
    name = call_openai(prompt, 256)
    prompt = generate_prompt("realms/generate_history", (name, setting, ))
    history = call_openai(prompt, 1024)
    print("Realm name: " + name)
    print("\nRealm Setting:\n" + setting)
    print("\nRealm History:\n" + history)
    realm_id = data.add_realm(name, setting, history)
    characters.generate_clans(realm_id, name, setting, history)
