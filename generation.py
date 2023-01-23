import openai
import io

def wrapper(func, args):
    return func(*args)

def generate_prompt(job, parameters):
    file = open("prompts/" + job + ".txt",mode='r')
    template = file.read()
    file.close()
    return wrapper(template.format, parameters)

# So far all calls to openai should work with the same parameters so why repeat code?
def call_openai(prompt, max_tokens = 256):
    openai_response = openai.Completion.create(
        model="text-davinci-003",
        temperature=0.7,
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0.1,
        presence_penalty=0,
        prompt=prompt)
    completion = openai_response["choices"][0]["text"].strip()
    return completion
