import openai

#location = "The realm of Kaltan is a steampunk-inspired world, with an industrial society powered by steam. Technology is advanced enough to allow for airships, advanced weaponry, and magitech machines. The realm is inhabited by a variety of humanoid species, some of which possess the ability to wield elemental magic. The air is polluted from the many factories, and the rich and powerful live in lavish sky-cities. The lower classes toil away in the mines and factories, struggling to make ends meet. Despite this, Kaltan is a vibrant world, filled with opportunity, excitement, and danger."
prompt = "The Hall of Clockwork Wonders is a 100m by 100m complex located in the middle of the city of Kaltron. It is a marvel of steampunk technology, consisting of towering spires, intricate clockwork mechanisms, and magical artifacts. It is filled with a variety of exhibits, from automatons to flying machines to steam-powered robots. Two of the magical artifacts have gone missing from their display cases, and Rikon is determined to find out who is behind this sinister plot and retrieve the artifacts. The warehouse is filled with darkness, and the only light comes from a few flickering lamps. The walls are lined with dust and old machinery, and the floor is littered with broken crates and debris. In the middle of the warehouse is a small group of thugs and a mysterious figure wearing a hooded cloak."

url = openai.Image.create(
  prompt=prompt,
  size="1024x1024"
)['data'][0]['url']

print(url)
