import openai
import io
import time

token_use = 0

def wrapper(func, args):
    return func(*args)

def generate_prompt(job, parameters):
    file = open("prompts/" + job + ".txt",mode='r')
    template = file.read()
    file.close()
    return wrapper(template.format, parameters)

# So far all calls to openai should work with the same parameters so why repeat code?
def call_openai(prompt, max_tokens = 256, model = "text-davinci-003"):
    global token_use
    print("\n\nPrompt:\n" + prompt)
    response = None
    while response is None:
        try:
            openai_response = openai.Completion.create(
                model=model,
                temperature=0.7,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0.1,
                presence_penalty=0,
                prompt=prompt)
            completion = openai_response
            response = completion["choices"][0]["text"].strip()
            tokens = completion['usage']['total_tokens']
            token_use += tokens
        except Exception as err:
            print("\nException: " + str(err))
            time.sleep(1)

    print("\nUsage:" + str(token_use))
    print("\n\nResponse:\n" + response)
    return response

def generate_image(prompt, size = "256x256"):
    url = openai.Image.create(prompt=prompt, size=size)['data'][0]['url']
    return url
