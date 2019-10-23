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



actions_in_queue = queue.Queue(100)


async def agent_loop(server_address="localhost:8000", agent_name="89221"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        global mapa
        global enemy_list
        global last_2
        global wall_list
        global bombs_list
        global check_count
        global timeout
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])
    
        k = 0
        last_2 = []
        enemy2hunt = []
        check_count = 0
        bombs_list = []
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server
                player_pos = state["bomberman"]
                wall_list = state["walls"]
                mapa._walls = wall_list
                
                enemy_list = state["enemies"]
                
                # b_pos = entity_finder(player_pos, get_enemyPos()) #ememy mais proximo
                # last_2.append(b_pos)
                
                # last_2 = last_2[-2:] #ultimos 2
                
                
                exit = state["exit"]
                
                #print(exit)
                if(wall_list != []):
                    nearest_wall = entity_finder(player_pos,wall_list)
                
                key = "" 
                
                if(actions_in_queue.empty()):
                    
                    if exit != [] and len(enemy_list) == 0:# ir para a saida, se os monstros estiverem todos mortos
                            print("pppppppppppppppppppppppp")
                            to_exit(player_pos, exit ,mapa)
                            wait(100)
                        
                    if(wall_list == []):
                        print("sem paredes")

    
                    else:  
                     # ver como vamos chamar para matar o balao(ex qnd apanharmos um powerup ou quando tiver dentro do range)
                    
                        go2wall(player_pos, nearest_wall,mapa)
                    
                        if near_wall(player_pos,nearest_wall):
                            if(distancia_calculation(player_pos, entity_finder(player_pos,get_enemyPos())) >= 3):
                                plant_bomb()
                                
                                
                                bomb = Bomb(player_pos, mapa, 3)
                                p = dodge2(player_pos, bomb, mapa)
                                m1 = mover(player_pos, p)
                                coord2dir(m1)
                                wait(7)
                                
                            else:
                                wait(10)
                
                in_danger(player_pos)
                    
                print(check_count)
                            
               
                    
                
                if(not actions_in_queue.empty()):
                    key = actions_in_queue.get()
                else:
                    print("queue vazia")
                    key = ""
                
                
                
                

                await websocket.send(
                            json.dumps({"cmd": "key", "key": key})
                        )  # send key command to server - you must implement this send in the AI agent
                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return


def in_danger(player_pos):
    global mapa
    global check_count
    if(check_count == 0):
        for pos in get_enemyPos():
            if(distancia_calculation(player_pos,pos) <= 2):
                actions_in_queue.queue.clear()
                plant_bomb()
                bomb = Bomb(player_pos,mapa,3)
                p = dodge2(player_pos, bomb, mapa)
                m1 = mover(player_pos, p)
                check_count = len(m1) +8
                coord2dir(m1)
                wait(7)
    else:
        check_count -= 1
    

def near_wall(bomberman,next_move): # diz se o playes esta colado a uma parede
    if distancia_calculation(bomberman,next_move) == 1:
        return True
    return False
    
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
    global enemy_list
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
            if mapa.is_blocked((node_position[0],node_position[1]) or isObs(node_position, enemy_list)): #maze[node_position[0]][node_position[1]] != 0:
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
    coord2dir(p)

def dodge2(bomb_pos, bomb, mapa):
    global wall_list
    global bombs_list
    global bombs_list
    
    
    next_pos = queue.Queue(100)
    next_pos.put(bomb_pos)
    
    while(1):
        p1 = next_pos.get()
        for pos in [(0,1),(0,-1),(1,0),(-1,0)]:
            new_pos = (p1[0] + pos[0], p1[1] + pos[1])
            if(mapa.is_blocked(new_pos) or isObs(new_pos, wall_list) or isObs(new_pos,get_enemyPos())):
                print("") # n faz nada / salta a frente
            else:
                if(not bomb.in_range(new_pos)):
                    print("encontrei")
                    return new_pos
                next_pos.put(new_pos)

def plant_bomb():
     
    actions_in_queue.put("B")
 
def wait(wait_time): #fazer w8 para time out da bomba
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

def isObs(pos, list): # itera a lista e ve se algum objeto interfere com a posição final
    for x in list:
        if pos[0] == x[0] and pos[1] == x[1]:
            return True
    return False

def get_enemyPos():
    global enemy_list
    pos = []
    for x in enemy_list:
        pos.append(x["pos"])
    return pos
def to_exit(player_pos, exit ,mapa): # ver dps
    step_pos = side_step(exit)
    path = mover(player_pos, step_pos)
    path.append(exit)
    coord2dir(path)

def kill_ballon(player_pos, b_pos): 
    global mapa
    global wall_list
    
    pos = kill_pos(b_pos, 2)
    p = mover(player_pos, pos)
    coord2dir(p)
    plant_bomb()
    
    bomb = Bomb(player_pos, mapa, 3)
    p1 = dodge2(player_pos, bomb, mapa)
    coord2dir(mover(player_pos,p1))
    wait(7)

def kill_pos(b_pos,range):
    global last_2

    
    prev = last_2[0]
    next = last_2[1]

    x = prev[0] - next[0]
    y = prev[1] - next[1]
    res = x,y
    if(res == (0,1)):
        return (b_pos[0], b_pos[1]+ range)
    if(res == (0,-1)):
        return (b_pos[0], b_pos[1] - range)
    if(res == (1,0)):
        return (b_pos[0] + range, b_pos[1])
    if(res == (-1,0)):
        return (b_pos[0] - range, b_pos[1])
    else:
        return (b_pos[0] - range, b_pos[1])

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
