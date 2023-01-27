import openai

#location = "The realm of Kaltan is a steampunk-inspired world, with an industrial society powered by steam. Technology is advanced enough to allow for airships, advanced weaponry, and magitech machines. The realm is inhabited by a variety of humanoid species, some of which possess the ability to wield elemental magic. The air is polluted from the many factories, and the rich and powerful live in lavish sky-cities. The lower classes toil away in the mines and factories, struggling to make ends meet. Despite this, Kaltan is a vibrant world, filled with opportunity, excitement, and danger."
prompt = "Kamiko is tall and imposing, with red skin and two horns protruding from her forehead. Her eyes are a deep yellow, and her expression is usually fierce and intimidating. She wears a dark red cloak and carries a katana at her side. Her body is toned and muscular, and her movements are swift and precise. Her hair is black and is usually kept in a tight bun or braid. She is intimidating to behold, and is a formidable opponent in battle."

url = openai.Image.create(
  prompt=prompt,
  size="1024x1024"
)['data'][0]['url']

print(url)
