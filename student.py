import sys
import json
import asyncio
import websockets
import getpass
import os
import math
import queue
import time
import random
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
        global check_dodge
        global plant_finished
        global droped_powerups
        global bomb_radius
        global lives
        global player_lives
        global bombs_count
        global bombs
        global prev_danger

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])
        bombs_count = 1 #nº de bombas
        bomb_radius = 3 #para o power up
        danger_zone = []
        level_number = 1
        k = 0
        count = 0
        prev = []
        prev_dir = [(0,0),(0,0),(0,0),(0,0),(0,0),(0,0)]
        check_count = 0
        check_dodge = True
        cnt  = 0
        plant_finished = 0
        lives = 3
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server
                lvl = state["level"]
                lives_count = state["lives"]
                if(lvl != level_number or lives != lives_count): # caso mude de nivel ou morre tudo resetado
                    k = 0
                    count = 0
                    prev = []
                    prev_dir = [(0,0),(0,0),(0,0),(0,0),(0,0),(0,0)]
                    check_count = 0
                    level_number = lvl
                    lives = lives_count
                    actions_in_queue.queue.clear()
                
                player_pos = state["bomberman"]
                player_pos = (player_pos[0],player_pos[1])
                wall_list = state["walls"]
                mapa._walls = wall_list
                enemy_list = state["enemies"]
                exit = state["exit"]
                droped_powerups = state["powerups"]
                player_lives = state["lives"]
                bombs  = state["bombs"]
                print("bombs: "+str(bombs))
                if bombs != []:

                    print("pos bomb:" + str(bombs[0][0]))
                #print("plat_finished:" + str(plant_finished))
                
                
                if k == 0:
                    danger_zone = get_enemyPos()
                k+=1

                prev_danger = danger_zone
                # if bombs != []:
                #     bomb = Bomb(bombs[0][0],mapa,bombs[0][1])
                #     dodge2(bombs[0][0],bomb,mapa)

                if get_enemyName("Doll") == []:
                    dir_ballon(get_enemyName("Balloom")) # make danger zone only balloom, lvl 1 and 2
                else:
                    lst1 = get_enemyName("Balloom")  # lvl 3
                    lst2 = get_enemyName("Doll")
                    #print(lst1 + lst2)
                    dir_ballon(lst1 + lst2)
                
                
                if(wall_list != []):
                    nearest_wall = entity_finder(player_pos,wall_list)
                else:
                    nearest_wall = []
                
                if get_enemyName("Oneal") != []:
                    nearest_oneal = entity_finder(player_pos, get_enemyName("Oneal"))
                    kill(nearest_oneal, nearest_wall, "Oneal")
                
                # elif get_enemyName("Balloom") != [] and lvl != 1:
                #     nearest_Ballom = entity_finder(player_pos, get_enemyName("Balloom"))
                #     kill(nearest_Ballom, nearest_wall,"Balloom")

                elif(actions_in_queue.empty()):
                    if exit != [] and len(enemy_list) == 0:# ir para a saida, se os monstros estiverem todos mortos
                        if lvl == 1:
                            get_power()#para já chamo só aqui
                        print("pppppppppppppppppppppppp")
                        saida = (exit[0],exit[1])
                        to_exit(player_pos, exit ,mapa)
                    
                        
                    else:
                        # ver como vamos chamar para matar o balao(ex qnd apanharmos um powerup ou quando tiver dentro do range)
                        
                        enemyPos = get_enemyPos

                        if(wall_list == []):
                            
                            m2 = mover(player_pos,(10,1))
                            coord2dir(m2)
                            
                        else:
                            if(nearest_wall != []):
                                go2wall(player_pos, nearest_wall,mapa)
                            
                                if near_wall(player_pos,nearest_wall):
                                    plant_bomb()
                                    plant_finished = 0
               
                
                if(not actions_in_queue.empty()):
                    key = actions_in_queue.get()
                    
                else:
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
            
def get_power():
    global droped_powerups
    global bomb_radius
    global player_pos
    global bombs_count
    for pos,poder in droped_powerups:
        if(poder == "Flames"):
            bomb_radius += 1
            pos = (pos[0], pos[1]) # conversao [] -> ()
            coord2dir(mover(player_pos,pos))
        if(poder == "Bombs"):
            bombs_count += 1
            pos = (pos[0], pos[1]) # conversao [] -> ()
            coord2dir(mover(player_pos,pos))
        else:
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
    global wall_list
    maze = mapa.map

    start_node = Node(None, player_pos)
    #print(start_node)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, dst_pos)
    #print(end_node)
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
    global wall_list

    if(lista == []):
        return
    anterior = lista[0]

    for elem in lista[1:]:
        x = elem[0] - anterior[0]
        y = elem[1] - anterior[1]
        if isObs(elem, wall_list): # se mandar p uma parede
            return "parede"
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
    #print("wall->" + str(wall))
    step_pos = side_step(wall)
    #print("step_pos_wall->" + str(step_pos))
    p = mover(player_pos, step_pos)
    coord2dir(p)


def dodge2(bomb_pos, bomb, mapa):
    global danger_zone
    global wall_list
    global check_dodge 
    check_dodge = True
    next_pos = queue.Queue(100)
    next_pos.put(bomb_pos)

    #print(bomb_pos)
    while(1):
        i = 0
        p1 = next_pos.get()
        lst = [(0,1),(0,-1),(1,0),(-1,0)]
        random.shuffle(lst)
        for pos in lst:
            new_pos = (p1[0] + pos[0], p1[1] + pos[1])
            if(mapa.is_blocked(new_pos) or isObs(new_pos, wall_list) or isObs(new_pos,get_enemyPos()) or isObs(new_pos, danger_zone)):
                i+=1
                print(i)
                if i == 4: #n tem hipoteses
                    check_dodge = False
                    return new_pos
                continue# n faz nada / salta a frente     
            else:
                if(not bomb.in_range(new_pos)):
                    #print(new_pos)
                    return new_pos
                next_pos.put(new_pos)

def plant_bomb():
    global player_pos
    global plant_finished
    global bomb_radius
    plant_finished = 0
    bomb = Bomb(player_pos, mapa, bomb_radius) #verifica primeiro
    p1 = dodge2(player_pos, bomb, mapa)
    if check_dodge:
        actions_in_queue.put("B")
        m1 = mover(player_pos, p1)
        coord2dir(m1)
        wait(7)
        plant_finished = 8 + len(m1)
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
        if(mapa.is_blocked(new_pos) or isObs(new_pos, wall_list)):
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

def kill(pos, w, enemy): 
    global danger_zone
    global wall_list
    global mapa
    global plant_finished
    global player_pos
    d = distancia_calculation(player_pos,w)
    alcance = 1
    print("DISTANCIA È:" + str(d))
    isNear = d == 1

    if enemy == "Balloom":
        alcance = 6

    print("range  "+ str(alcance))
    if plant_finished == 0:
        actions_in_queue.queue.clear()
        b = Bomb(pos,mapa,alcance)
        kill_pos = in_range(pos,b)
        p = mover(player_pos, kill_pos)
        #print(p)
        m1 = coord2dir(p)

        if player_pos == kill_pos:
            plant_bomb() #para matar
        
        if len(p) >= 2:
            for paredes in wall_list:
                if(p[1] == (paredes[0],paredes[1])):
                    plant_bomb()
                    break
        elif isNear:
            plant_bomb()
        

    else: plant_finished -= 1

    #print("player_pos: "+ str(player_pos))
    # i = get_Index(pos)
    # print("i:" + str(i))
    # print(danger_zone)
    # t = (danger_zone[i][0] - pos[0], danger_zone[i][1] - pos[1]) # direçao

    # print("dir:" +str(t))

    # kill_pos = (danger_zone[i][0]+ 2*t[0], danger_zone[i][1] + 2*t[1]) #3 pos á frente, conforme a direção
    # print(kill_pos)
    
    

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
    global prev_danger
    dir = []
    size = len(enemy_pos) # so os ballooms tem danger_zone
    danger_zone = danger_zone[:size]
    #print("LISTA DOS INMIGOS" + str(list_diretions))
    try:
        for cnt in range(size):
            if list_diretions[cnt] == (0,0):
                danger_zone[cnt] = danger_zone[cnt][0] + list_diretions[cnt][0], danger_zone[cnt][1] + list_diretions[cnt][1]
            else: 
                danger_zone[cnt] = enemy_pos[cnt][0] + list_diretions[cnt][0], enemy_pos[cnt][1] + list_diretions[cnt][1]
        
        for i in range(size):
            if list_diretions[i] == (0,0):
                danger_zone = prev_danger
                print("1")
            else:
                danger_zone.append((danger_zone[i][0] - 2*list_diretions[i][0], danger_zone[i][1] - 2*list_diretions[i][1])) # 1 atras
                danger_zone.append((danger_zone[i][0] + 2*list_diretions[i][0], danger_zone[i][1] + 2*list_diretions[i][1])) # 3 a frenteS
                #danger_zone.append((danger_zone[i][0] + 3*list_diretions[i][0], danger_zone[i][1] + 3*list_diretions[i][1])) # 4 a frenteS
                #danger_zone.append((danger_zone[i][0] + 4*dir[i][0], danger_zone[i][1] + 4*dir[i][1])) # 5 a frenteS
                danger_zone.append((danger_zone[i][0] + list_diretions[i][0], danger_zone[i][1] + list_diretions[i][1])) # 2 a frente  

    except IndexError:
        danger_zone = prev_danger
        print("----------------HOUVE ERRO DE INDEX NA DANGER_ZONE------------------")
        print("----------------HOUVE ERRO DE INDEX NA DANGER_ZONE------------------")
        print("----------------HOUVE ERRO DE INDEX NA DANGER_ZONE------------------")
        print("----------------HOUVE ERRO DE INDEX NA DANGER_ZONE------------------")
    print(enemy_pos)
    print("danger zone ->"+ str(danger_zone))

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
    global lives
    global player_lives
    global player_pos
    global plant_finished
    if player_lives == lives: #se morrer, foi inevitável morrer
        print("123")
        actions_in_queue.queue.clear()
        print("1234")
        plant_bomb()
        wait(1)
        plant_finished = 0
    else: return

def get_enemyName(name): #funçap que devolve posiçoes dos enimigos cm o nome passado como arg
    global enemy_list
    pos = []
    for x in enemy_list:
        if x["name"] == name:
            pos.append(x["pos"])
    return pos

def get_Index(pos):
    i = 0
    lst = get_enemyPos()
    for x in lst:
        if x[0] == pos[0] and x[1] == pos[1]:
            return i
        i+=1

def in_range(enemy, bomb):
    global danger_zone
    global wall_list
    global check_dodge 
    check_dodge = True
    lst = []
    next_pos = queue.Queue(100)
    next_pos.put(enemy)

    #print(bomb_pos)
    while(1):
        i = 0
        p1 = next_pos.get()
        lst = [(0,1),(0,-1),(1,0),(-1,0)] # para variar
        #random.shuffle(lst)
        for pos in lst:
            new_pos = (p1[0] + pos[0], p1[1] + pos[1])
            if(mapa.is_blocked(new_pos) or isObs(new_pos,get_enemyPos())):
                continue# n faz nada / salta a frente     
            else:
                if(not bomb.in_range(new_pos)):
                    #print(new_pos)
                    return new_pos
                next_pos.put(new_pos)

def get_Bomb(name):
    global bombs 
    for b in bombs:
       return b[name] 
# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
