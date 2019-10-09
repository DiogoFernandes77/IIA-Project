import sys
import json
import asyncio
import websockets
import getpass
import os
import math

from mapa import Map

# Next 2 lines are not needed for AI agent
import pygame

pygame.init()


async def agent_loop(server_address="localhost:8000", agent_name="89221"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])

        # Next 3 lines are not needed for AI agent
        SCREEN = pygame.display.set_mode((299, 123))
        SPRITES = pygame.image.load("data/pad.png").convert_alpha()
        SCREEN.blit(SPRITES, (0, 0))

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                nearest_wall = wall_finder(state["bomberman"],state["walls"]) #argumentos(pos do bomberman,lista das pos das paredes no mapa)
                print(nearest_wall)
                
                
                
                


                
                    
                await websocket.send(
                    json.dumps({"cmd": "key", "key": "d"})
                )

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

            # Next line is not needed for AI agent
            pygame.display.flip()

def wall_finder(minha_pos,walls_pos):
    distancia= 1000 # valor alto so para fazer a primeira comparaçao, pode ser alterado no futuro para uma melhor maneira
    for pos in walls_pos:
        distancia_tmp = math.sqrt( ((minha_pos[0] - pos[0])**2) +  ((minha_pos[1] - pos[1])** 2))
        if(distancia_tmp < distancia):
            distancia = distancia_tmp
            next_wall = pos
    return next_wall
        













# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
