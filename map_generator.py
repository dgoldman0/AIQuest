import openai

#location = "The realm of Kaltan is a steampunk-inspired world, with an industrial society powered by steam. Technology is advanced enough to allow for airships, advanced weaponry, and magitech machines. The realm is inhabited by a variety of humanoid species, some of which possess the ability to wield elemental magic. The air is polluted from the many factories, and the rich and powerful live in lavish sky-cities. The lower classes toil away in the mines and factories, struggling to make ends meet. Despite this, Kaltan is a vibrant world, filled with opportunity, excitement, and danger."
prompt = "Rikon is left in awe when he enters the Hall of Clockwork Wonders. The towering spires and intricate clockwork mechanisms lining the walls fill the air with a faint hum of machinery. In the center of the room, a group of thugs huddle around a mysterious cloaked figure. Among the many exhibits in the hall, Rikon spots automatons, steam-powered robots, flying machines, a magical artifact, and a magical mirror. Tools and machinery, such as a steam-powered generator, a clockwork table, an automaton workshop, and a steam-powered elevator, can also be seen scattered around the hall. The entire complex is illuminated in a soft golden light, giving it an ethereal feel."

url = openai.Image.create(
  prompt=prompt,
  size="256x256"
)['data'][0]['url']

print(url)
