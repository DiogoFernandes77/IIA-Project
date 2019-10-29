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
        global player_pos
        global count
        global prev
        global danger_zone
        global prev_dir
        global check_count
        global level_number
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])
        danger_zone = []
        level_number = 1
        k = 0
        count = 0
        prev = []
        prev_dir = [(0,0),(0,0),(0,0),(0,0),(0,0),(0,0)]
        check_count = 0
        
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server
                key = "" 
                lvl = state["level"]
                if(lvl != level_number):
                    k = 0
                    count = 0
                    prev = []
                    prev_dir = [(0,0),(0,0),(0,0),(0,0),(0,0),(0,0)]
                    check_count = 0
                    level_number = lvl
                
                player_pos = state["bomberman"]
                wall_list = state["walls"]
                mapa._walls = wall_list
                enemy_list = state["enemies"]
                exit = state["exit"]
                if k == 0:
                    danger_zone = get_enemyPos()
                k+=1
                dir_ballon(get_enemyPos())


                if(wall_list != []):
                    nearest_wall = entity_finder(player_pos,wall_list)
                else:
                    nearest_wall = []
                
                
                if(actions_in_queue.empty()):
                    flag  = 0
                    if exit != [] and len(enemy_list) == 0:# ir para a saida, se os monstros estiverem todos mortos
                            print("pppppppppppppppppppppppp")
                            saida = (exit[0],exit[1])
                            to_exit(player_pos, exit ,mapa)
                    
                        
                    else:
                        # ver como vamos chamar para matar o balao(ex qnd apanharmos um powerup ou quando tiver dentro do range)
                        if(wall_list == []):
                            
                            m2 = mover(player_pos,(10,1))
                            coord2dir(m2)
                            
                        else:
                            if(nearest_wall != []):
                                go2wall(player_pos, nearest_wall,mapa)
                            
                                if near_wall(player_pos,nearest_wall):
                                    plant_bomb()
                 
                if(not actions_in_queue.empty()):
                    key = actions_in_queue.get()
                else:
                    print("queue vazia")
                    key = ""
                if in_danger(player_pos,key):
                    get_out()
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
    global danger_zone
    maze = mapa.map
    if(player_pos[0] == dst_pos[0] and player_pos[1] == dst_pos[1]):
        return []
    # Create start and end node
    start_node = Node(None, player_pos)
    print(start_node)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, dst_pos)
    print(end_node)
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
    if(lista == []):
        return
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
    # if(player_pos[0] == step_pos[0] and player_pos[1] == step_pos[1]): # resolve o problema de mandar para ele proprio
    #     return
    #print("aqui")
    p = mover(player_pos, step_pos)
    coord2dir(p)

def canDodge(pos, r):
    global mapa
    b = Bomb(pos, mapa, r)
    if dodge2(pos,b,mapa) == False:
        return False
    else:
        return True

def dodge2(bomb_pos, bomb, mapa):
    global danger_zone
    global wall_list
    next_pos = queue.Queue(100)
    next_pos.put(bomb_pos)
    #print(bomb_pos)
    while(1):
        i = 0
        p1 = next_pos.get()
        for pos in [(0,1),(0,-1),(1,0),(-1,0)]:
            new_pos = (p1[0] + pos[0], p1[1] + pos[1])
            if(mapa.is_blocked(new_pos) or isObs(new_pos, wall_list) or isObs(new_pos,get_enemyPos()) or isObs(new_pos, danger_zone)):
                i+=1
                print(i)
                if i == 4: #n tem hipoteses
                    return False
                continue# n faz nada / salta a frente     
            else:
                if(not bomb.in_range(new_pos)):
                    #print(new_pos)
                    return new_pos
                next_pos.put(new_pos)

def plant_bomb():
    global player_pos
    if canDodge(player_pos,3):
        actions_in_queue.put("B")
        bomb = Bomb(player_pos, mapa, 3)
        p1 = dodge2(player_pos, bomb, mapa)
        m1 = mover(player_pos, p1)
        coord2dir(m1)
        wait(7)
    else: wait(1)
 
def wait(wait_time): #fazer w8 para time out da bomba
    for x in range(wait_time): # w8
        actions_in_queue.put("")
def side_step(pos):
    global mapa
    global wall_list
    global danger_zone
    for x in [(0,1),(0,-1),(1,0),(-1,0)]:
        new_pos = (x[0] + pos[0], x[1] + pos[1])
        if(mapa.is_blocked(new_pos) or isObs(new_pos, wall_list) or isObs(new_pos,get_enemyPos()) or isObs(new_pos,danger_zone)):
            continue
        else: return new_pos
def isObs(pos, list): # itera a lista e ve se algum objeto interfere com a posição final
    for x in list:
        if pos[0] == x[0] and pos[1] == x[1]:
            return True
    return False

def get_enemyPos():
    global enemy_list
    #print(enemy_list)
    pos = []
    for x in enemy_list:
        pos.append(x["pos"])
    #print(pos)
    return pos
def to_exit(player_pos, exit ,mapa): # ver dps
    print("Print exit" + str(exit))
    step_pos = side_step(exit)
    print("Exit com step_pos"+str(step_pos))
    path = mover(player_pos, step_pos)
    path.append(exit)
    coord2dir(path)

def kill_ballon(player_pos, b_pos): 
    global danger_zone
    global wall_list
    global mapa
    
    lista = mover(player_pos,(20,1))
    coord2dir(lista)
    

def dir_ballon(enemy_pos):
    global prev
    global count
    global wall_list
    global mapa
    global prev_dir
    global danger_zone
    final_dir = []
    
    count +=1
    
    #print(" pos -> "+str(enemy_pos[0]))
    
    if count == 1:
        prev = enemy_pos
        

   # print("prev ->"+ str(prev))
    #print("enemy_pos->" + str(enemy_pos))
    for index in range(len(enemy_pos)):
        
        c1 = enemy_pos[index][0]-prev[index][0]
        c2 = enemy_pos[index][1]-prev[index][1]

        future = (enemy_pos[index][0] + c1, enemy_pos[index][1] +c2)
        if(mapa.is_blocked(future) or isObs(future, wall_list)):
            if c1 == 1: 
                for x in [(0,-1),(-1,0),(0,1)]:
                    future = future[0] + x[0] , future[1] + x[1]
                    if(mapa.is_blocked(future) or isObs(future, wall_list)):
                        continue
                    final_dir.append(x)
                    break
            elif c1 == -1:
                for x in [(0,1),(1,0),(0,-1)]:
                    future = future[0] + x[0] , future[1] + x[1]
                    if(mapa.is_blocked(future) or isObs(future, wall_list)):
                        continue
                    final_dir.append(x)
                    break
            elif c2 == 1:
                for x in [(1,0),(0,-1),(-1,0)]:
                    future = future[0] + x[0] , future[1] + x[1]
                    if(mapa.is_blocked(future) or isObs(future, wall_list)):
                        continue
                    final_dir.append(x)
                    break
            elif c2 == -1:
                for x in [(-1,0),(0,1),(1,0)]:
                    future = future[0] + x[0] , future[1] + x[1]
                    if(mapa.is_blocked(future) or isObs(future, wall_list)):
                        continue
                    final_dir.append(x)
                    break
            else: final_dir.append((0,0))

        else : final_dir.append((c1, c2))
    
    #print(final_dir)
    prev = enemy_pos
    calc_danger(enemy_pos,final_dir)
    prev_dir = final_dir

def calc_danger(enemy_pos,list_diretions):
    global danger_zone
    dir = []
    size = len(enemy_pos)
    danger_zone = danger_zone[:size]
    for cnt in range(size):
        if list_diretions[cnt] == (0,0):
            danger_zone[cnt] = danger_zone[cnt][0] + list_diretions[cnt][0], danger_zone[cnt][1] + list_diretions[cnt][1]
        else: 
            danger_zone[cnt] = enemy_pos[cnt][0] + list_diretions[cnt][0], enemy_pos[cnt][1] + list_diretions[cnt][1]

    for i in range(size):
        dir.append((danger_zone[i][0] - enemy_pos[i][0], danger_zone[i][1] - enemy_pos[i][1]))
    
    for i in range(size):
        danger_zone.append((danger_zone[i][0] - 2*dir[i][0], danger_zone[i][1] - 2*dir[i][1])) # 1 atrás
        danger_zone.append((danger_zone[i][0] + dir[i][0], danger_zone[i][1] + dir[i][1])) #adiciona 2 à frente
    #print(danger_zone)

def in_danger(player_pos,key):
    global mapa
    global check_count
    global danger_zone
    global mapa
    movement = (0,0)
    if(key == "w"):
        movement = (0,-1)
    if(key == "s"):
        movement = (0,1)
    if(key == "a"):
        movement = (-1,0)
    if(key == "d"):
        movement = (1,0)
    
    next_pos = (player_pos[0] + movement[0], player_pos[1] + movement[1])
    
    if(isObs(next_pos,get_enemyPos()) or isObs(next_pos, danger_zone)):
        print("aquis")
        return True

def get_out():
    global player_pos
    actions_in_queue.queue.clear()
    b = Bomb(player_pos,mapa,2)
    p1 = dodge2(player_pos,b,mapa)
    m1 = mover(player_pos, p1)
    coord2dir(m1)
    wait(1)
# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
