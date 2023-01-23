from generation import generate_prompt
from generation import call_openai

data = None

def inject_data(_data):
    global data
    data = _data

def create_location(realm_id, x = 10000000, y = 10000000):
    prompt = generate_prompt("maps/create_location", (data.get_setting(realm_id), "100m", "100m", ))
    details = call_openai(prompt, 1024)
    data.add_map(realm_id, x, y, details)
    generate_location_items(realm_id, x, y, details)

def generate_location_items(realm_id, x, y, details):
    prompt = generate_prompt("maps/generate_location_items", (data.get_setting(realm_id), "100m", "100m", details, ))
    items = call_openai(prompt, 2048)
    data.update_map_items(x, y, items)
