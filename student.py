import sys
import json
import asyncio
import websockets
import getpass
import os
import math
import queue
import time
from mapa import Map
from game import Bomb

# Next 2 lines are not needed for AI agent
import pygame

pygame.init()

actions_in_queue = queue.Queue(100)

dodge_stack = []
async def agent_loop(server_address="localhost:8000", agent_name="89221"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        global mapa
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
        k = 0

        while True:
            try:
                print("tempo "+str(time.time()))
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server
                player_pos = state["bomberman"]
                wall_list = state["walls"]
                mapa._walls = wall_list
                
                enemy_pos = []

                size = 5
                # for i in range (size):
                #     try:
                #         if(len(state["enemies"][i + 1]['pos']==[])) < size): # resolve index error
                #             size -=1
                #         if(state["enemies"][i]['pos']==[]):
                #             continue
                #         enemy_pos.append(state["enemies"][i]['pos'])
                #     except IndexError:
                #         print("erro id " +i+ "eliminado")

               
               
                #print("p"+str(enemy_pos))
                exit = state["exit"]
                
                #print(exit)
                nearest_wall = entity_finder(player_pos,wall_list)
                
                key = "" 
        
                if(actions_in_queue.empty()):
                    
                    #if exit != []:# ir para a saida
                     #   print("pppppppppppppppppppppppp")
                      #  path = to_exit(player_pos, exit ,mapa)
                       # wait(100)
                    
            
                    #if(enemy_pos != []): 
                        #kill_ballon(mapa, player_pos, enemy_pos,wall_list)   
                    # ver como vamos chamar para matar o balao(ex qnd apanharmos um powerup ou quando tiver dentro do range)

                    go2wall(player_pos, nearest_wall,mapa)
                    
                    if near_wall(player_pos,nearest_wall):
                        plant_bomb()
                        bomb = Bomb(player_pos, mapa, 3)
                        p = dodge2(player_pos, bomb, mapa, wall_list)
                        print(p)
                        m1 = mover(player_pos, p)
                        print(m1)
                        coord2dir(m1)
                        wait(5)
                        #go2wall(player_pos,(3,3),mapa)
                    
                key = actions_in_queue.get()
                dodge_stack.append(key)

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

def nearest_enemy(minha_pos,enemies_list):
    distancia = 1000
    
    for x in range(5):
        distancia_tmp = distancia_calculation(minha_pos,enemies_list[x]["pos"])
        if(distancia_tmp < distancia):
            distancia = distancia_tmp
            pos = enemies_list[x]["pos"]
    return pos
def entity_finder(minha_pos,obj_pos): # funçao para encontrar o objeto mais proximo
    distancia= 1000 # valor alto so para fa step_pos = side_step(nearest_wall)
    for pos in obj_pos:
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


class Node():
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __str__(self):
        return str(self.position)

    def __eq__(self, other):
        return self.position == other.position


def mover(player_pos, dst_pos):
    """Returns a list of tuples as a path from the given start to the given end in the given maze"""
    global mapa
    maze = mapa.map
    # Create start and end node
    start_node = Node(None, player_pos)
    #print(start_node)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, dst_pos)
   # print(end_node)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Add the start node
    open_list.append(start_node)

    # Loop until you find the end
    while len(open_list) > 0:

        # Get the current node
        current_node = open_list[0]
        #print(current_node)
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open list, add to closed list
        open_list.pop(current_index)
        closed_list.append(current_node)

        # Found the goal
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:

                path.append(current.position)
                current = current.parent
            return path[::-1] # Return reversed path

        # Generate children
        children = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]: # Adjacent squares adsw

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure within range
            if node_position[0] > (len(maze) - 1) or node_position[0] < 0 or node_position[1] > (len(maze[len(maze)-1]) -1) or node_position[1] < 0:
                continue
            
            # Make sure walkable terrain
            if mapa.is_blocked((node_position[0],node_position[1])): #maze[node_position[0]][node_position[1]] != 0:
                #print("stone")
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:

            # Child is on the closed list
            for closed_child in closed_list:
                if child == closed_child:
                    continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            # Add the child to the open list
            #print(child)
            open_list.append(child) 

def coord2dir(lista):
    print("lista de entrada"+str(lista))
    anterior = lista[0]

    for elem in lista[1:]:
        x = elem[0] - anterior[0]
        y = elem[1] - anterior[1]
        anterior = elem
        res = x,y
        if(res == (0,1)):
            actions_in_queue.put("s")
        
        if(res == (0,-1)):
            actions_in_queue.put("w")

        if(res == (1,0)):
            actions_in_queue.put("d")

        if(res == (-1,0)):
            actions_in_queue.put("a")
    

def go2wall(player_pos, wall ,mapa):
    
    step_pos = side_step(wall)
    if(player_pos[0] == step_pos[0] and player_pos[1] == step_pos[1]): # resolve o problema de mandar para ele proprio
        return
    #print("aqui")
    p = mover(player_pos, step_pos)
    print("aastar"+ str(p))
    coord2dir(p) 
    return p

def dodge2(bomb_pos, bomb, mapa, wall_list):
    next_pos = queue.Queue(100)
    next_pos.put(bomb_pos)
    print(bomb_pos)
    while(1):
        p1 = next_pos.get()
        for pos in [(0,1),(0,-1),(1,0),(-1,0)]:
            new_pos = (p1[0] + pos[0], p1[1] + pos[1])
            if(mapa.is_blocked(new_pos) or isWall(new_pos, wall_list)):
                print("1")
            else:
                if(not bomb.in_range(new_pos)):
                    print(new_pos)
                    return new_pos
                next_pos.put(new_pos)

def plant_bomb():
     
    actions_in_queue.put("B")
 
def wait(wait_time):
    for x in range(wait_time): # w8
        actions_in_queue.put("")
def side_step(pos):
    if even_number(pos[0]):
        pos = pos[0]-1, pos[1]

    elif even_number(pos[1]):
        pos = pos[0], pos[1]-1

    else:
        pos = pos[0], pos[1]-1
    
    return pos
def isWall(pos, wall_list):
    for x in wall_list:
        if pos[0] == x[0] and pos[1] == x[1]:
            return True
    return False

def to_exit(player_pos, exit ,mapa): # ver dps
    step_pos = side_step(exit)
    path = mover(player_pos, step_pos)
    path.append(exit)
    print(path)
    coord2dir(path)
    #return path

def kill_ballon(mapa, player_pos, enemy_pos, wall_list): 
    b_pos = entity_finder(player_pos, enemy_pos)
    
    

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
