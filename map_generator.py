import openai

location = "The realm of Kaltan is a steampunk-inspired world, with an industrial society powered by steam. Technology is advanced enough to allow for airships, advanced weaponry, and magitech machines. The realm is inhabited by a variety of humanoid species, some of which possess the ability to wield elemental magic. The air is polluted from the many factories, and the rich and powerful live in lavish sky-cities. The lower classes toil away in the mines and factories, struggling to make ends meet. Despite this, Kaltan is a vibrant world, filled with opportunity, excitement, and danger."

url = openai.Image.create(
  prompt=location,
  size="1024x1024"
)['data'][0]['url']

print(url)
