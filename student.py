import sys
import json
import asyncio
import websockets
import getpass
import os
import math
import queue
from mapa import Map

# Next 2 lines are not needed for AI agent
import pygame

pygame.init()

actions_in_queue = queue.Queue(100)
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
                key = "" 
                if not near_wall(player_pos,nearest_wall):
                    if(actions_in_queue.empty):
                        #senao estiver colado a parede vai ate la
                        action_moving(player_pos,nearest_wall)
                else:
                    actions_in_queue.put("B") #else chamas a funçao das bombas para plantar e fugir
                
                key = actions_in_queue.get()


                
                
                
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
def action_moving(bomberman, dest_pos):

        
        bx = bomberman[0]
        by = bomberman [1]
        nx= dest_pos[0]
        ny = dest_pos[1]
        
        
        if ( (even_number(bx) and not even_number(by)) and  (even_number(nx) and not even_number(ny))):  
            if nx > bx:
                actions_in_queue.put("d")
            else:
                actions_in_queue.put("a")
            if ny > by :
                for count in range(ny - by + 1): # mais 1 devido ao range parar uma casa antes
                    actions_in_queue.put("s")
            else:
                for count in range(by-ny+1):
                    actions_in_queue.put("w")
            if nx > bx:
                for count in range(nx-bx+1):
                    actions_in_queue.put("d")
            else:
                for count in range(bx-nx+1):
                    actions_in_queue.put("a")
        
        
        
        elif ( (even_number(by) and not even_number(bx)) and  (even_number(ny) and not even_number(nx))):
            if ny > by:
                actions_in_queue.put("s")
            else:
                actions_in_queue.put("w")
            if nx > bx :
                for count in range(nx-bx+1):
                    actions_in_queue.put("d")
            else:
                for count in range(bx-nx+1):
                    actions_in_queue.put("a")
            if ny > by:
                for count in range(ny-by+1):
                    actions_in_queue.put("s")
            else:
                for count in range(by-ny+1):
                    actions_in_queue.put("w")
            
        
        else :
            if (even_number(nx) and not even_number(ny)):
                if ny > by:
                    actions_in_queue.put("s")  
                elif ny < by:
                    actions_in_queue.put("w")
                elif nx > bx:
                    actions_in_queue.put("d")
                else:
                    actions_in_queue.put("a")
            else:
                if nx > bx:
                    actions_in_queue.put("d")
                elif nx < bx:
                    actions_in_queue.put("a")
                elif ny > by:
                    actions_in_queue.put("s")
                else:
                    actions_in_queue.put("w")
            
    

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
