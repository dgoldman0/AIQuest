# Change the map generation system so that smoothing is done by another function.

import openai
import io

data = None

def inject_data(_data):
    global data
    data = _data

def wrapper(func, args):
    return func(*args)

def generate_prompt(job, parameters = None):
    file = open("prompts/" + job + ".txt",mode='r')
    template = file.read()
    file.close()
    if parameters is None:
        return template
    else:
        return wrapper(template.format, parameters)

# So far all calls to openai should work with the same parameters so why repeat code?
def call_openai(prompt):
    openai_response = openai.Completion.create(
        model="text-davinci-003",
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        prompt=prompt)
    completion = openai_response["choices"][0]["text"].strip()
    return completion

def create_location(x = 10000000, y = 10000000):
    prompt = generate_prompt("maps/create_location", (data.get_setting(), "100m", "100m", ))
    details = call_openai(prompt)
    data.add_map(x, y, details)
    generate_location_items(x, y, details)

def generate_location_items(x, y, details):
    prompt = generate_prompt("maps/generate_location_items", (data.get_setting(), "100m", "100m", details, ))
    items = call_openai(prompt)
    data.update_map_items(x, y, items)
