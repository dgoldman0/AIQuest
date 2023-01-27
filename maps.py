from generation import generate_prompt
from generation import call_openai

data = None

def inject_data(_data):
    global data
    data = _data

# Does not check to see if surrounding locations are already filled in. Will be fixed in time.
def create_location(realm_id, x = 100, y = 100):
    print("Creating new location...")
    realm = data.get_realm(realm_id)
    prompt = generate_prompt("maps/create_location", (realm[1], realm[2], "1000m", "1000m", ))
    details = call_openai(prompt, 512)
    print("Details: " + details)
    data.add_map(realm_id, x, y, details)
    generate_location_items(realm_id, x, y, realm[1], details)

def generate_location_items(realm_id, x, y, setting, details):
    print("Creating location items...")
    prompt = generate_prompt("maps/generate_location_features", (setting, 10, "1000m", "1000m", details, ))
    items = call_openai(prompt, 1024)
    data.update_map_items(realm_id, x, y, items)
