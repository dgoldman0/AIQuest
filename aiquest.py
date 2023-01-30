import asyncio
import data
import server
import maps
import realms
import characters
import players

async def main():
    server.inject_data(data)
    maps.inject_data(data)
    realms.inject_data(data)
    characters.inject_data(data)
    players.inject_data(data)
    data.init()
    print("Starting server...")
    await server.listen()

asyncio.run(main())
