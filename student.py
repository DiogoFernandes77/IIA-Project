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
                player_pos = state["bomberman"]
                wall_list = state["walls"]
                nearest_wall = entity_finder(player_pos,wall_list) #argumentos(pos do bomberman,lista das pos das paredes no mapa)
                
                print(nearest_wall)
                if not near_wall(player_pos,nearest_wall): #senao estiver colado a parede vai ate la
                    key = action_moving(player_pos,nearest_wall)
                #else chamas a funçao das bombas para plantar e fugir
                
                
                
                
                await websocket.send(
                            json.dumps({"cmd": "key", "key": key})
                        )  # send key command to server - you must implement this send in the AI agent
                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return
def near_wall(bomberman,next_move): # diz se o playes esta colado a uma parede
    if distancia_calculation(bomberman,next_move) == 1:
        return True
    return False
def action_moving(bomberman, next_move):

        
        bx = bomberman[0]
        by = bomberman [1]

        nx= next_move[0]
        ny = next_move[1]

        
        if nx > bx:
            key = "d"
        elif nx < bx:
            key = "a"
        elif ny > by:
            key = "s"
        else:
            key = "w"
        
        return key

def entity_finder(minha_pos,walls_pos): # funçao para encontrar o objeto mais proximo
    distancia= 1000 # valor alto so para fazer a primeira comparaçao, pode ser alterado no futuro para uma melhor maneira
    for pos in walls_pos:
        distancia_tmp = distancia_calculation(minha_pos,pos)
        if(distancia_tmp < distancia):
            distancia = distancia_tmp
            next_wall = pos
    return next_wall
def distancia_calculation(coord1,coord2):
    return math.sqrt( ((coord1[0] - coord2[0])**2) +  ((coord1[1] - coord2[1])** 2))



def even_number(number): 
    if (number % 2 == 0):
        return True
    return False    

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
