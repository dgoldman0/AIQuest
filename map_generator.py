import openai

#location = "The realm of Kaltan is a steampunk-inspired world, with an industrial society powered by steam. Technology is advanced enough to allow for airships, advanced weaponry, and magitech machines. The realm is inhabited by a variety of humanoid species, some of which possess the ability to wield elemental magic. The air is polluted from the many factories, and the rich and powerful live in lavish sky-cities. The lower classes toil away in the mines and factories, struggling to make ends meet. Despite this, Kaltan is a vibrant world, filled with opportunity, excitement, and danger."
prompt = "The Hall of Clockwork Wonders is a steampunk-inspired marvel located in the city of Kaltron. It is filled with a variety of exhibits, from automatons to flying machines to steam-powered robots. Two of the magical artifacts have gone missing from their display cases, and Rikon has ventured inside to retrieve them. The warehouse is filled with darkness and cobwebs, and Rikon soon finds himself confronted by a group of thugs and a hooded figure. He draws his sword and must now face whatever lies ahead in order to save his home and his people. The Hall of Clockwork Wonders is filled with marvels such as automatons, steam-powered robots, flying machines, clockwork tables, magical artifacts, steam-powered generators, clockwork clocks, magical mirrors, automaton workshops, and steam-powered elevators."

url = openai.Image.create(
  prompt=prompt,
  size="1024x1024"
)['data'][0]['url']

print(url)
