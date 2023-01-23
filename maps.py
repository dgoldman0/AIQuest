from generation import generate_prompt
from generation import call_openai

data = None

def inject_data(_data):
    global data
    data = _data

# Does not check to see if surrounding locations are already filled in. Will be fixed in time.
def create_location(realm_id, x = 10000000, y = 10000000):
    print("Creating new location...")
    realm = data.get_realm(realm_id)
    prompt = generate_prompt("maps/create_location", (realm[1], realm[2], "100m", "100m", ))
    details = call_openai(prompt, 1024)
    print("Details: " + details)
    data.add_map(realm_id, x, y, details)
    generate_location_items(realm_id, x, y, realm[1], details)

def generate_location_items(realm_id, x, y, setting, details):
    print("Creating location items...")
    prompt = generate_prompt("maps/generate_location_items", (setting, 10, "100m", "100m", details, ))
    items = call_openai(prompt, 2048)
    data.update_map_items(realm_id, x, y, items)
