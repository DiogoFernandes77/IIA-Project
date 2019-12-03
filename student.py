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
        global safe
        global nearest_enemy
        global detonador
        global speed
        global last_dir
        global nearest_wall
        
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
        safe = True
        detonador = False
        speed = False
        last_dir = []
        ballom_test = -1
        check_stuck = 0
        prev_player_pos = (1,1)
        wrong_place = 0
        
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server
                lvl = state["level"]
                lives_count = state["lives"]
                if lvl >= 4: detonador = True
                
                if(lvl != level_number or lives_count != lives): # caso mude de nivel ou morre, tudo resetado
                    print("mudou de nivel")
                    k = 0
                    count = 0
                    prev = []
                    # prev_dir = [(0,0),(0,0),(0,0),(0,0),(0,0),(0,0)]
                    # danger_zone = []
                    check_count = 0
                    level_number = lvl
                    lives = lives_count
                    actions_in_queue.queue.clear()
                    safe = True
                    last_dir = []
                    ballom_test = -1
                    wrong_place = 0
                player_pos = state["bomberman"]
                player_pos = (player_pos[0],player_pos[1])
                wall_list = state["walls"]
                w_list = []
                for x in wall_list: w_list.append((x[0],x[1])) # conversao []->()
                wall_list = w_list
                mapa._walls = wall_list
                enemy_list = state["enemies"]
                saida = state["exit"]
                droped_powerups = state["powerups"]
                bombs  = state["bombs"]
                enemyPos = get_enemyPos()
                nearest_enemy = entity_finder(player_pos, enemyPos)

               
                if k == 0:
                    danger_zone = get_enemyPos()
                k+=1
                if prev_player_pos == player_pos:
                    check_stuck+=1

                prev_danger = danger_zone
                
                enemy_pos = get_enemyPos()
                dir = dir_ballon(enemy_pos)
                calc_danger(enemy_pos,dir)
                
                #print(enemyPos)
                danger_zone.extend(enemyPos)
                #print(danger_zone)

                if(wall_list != []):
                    nearest_wall = entity_finder(player_pos,wall_list)

        
                
                print("bombs->"+str(bombs))
                if bombs != []: 
                    
                    actions_in_queue.queue.clear()
                    for x in bombs:
                        b = Bomb(x[0],mapa,x[2])
                        p = dodge3(x[0],b)
                       
                        coord2dir(p)
                        if not b.in_range(player_pos): 
                            actions_in_queue.queue.clear()
                            if detonador:
                                actions_in_queue.put("A") # detonar
                
                
                if bombs == [] and actions_in_queue.empty(): 
                    if droped_powerups != []: #powerup do 2 n interessa para ja
                        actions_in_queue.queue.clear()
                        get_power()
                    elif detonador and enemy_list != [] and lvl == 3: #ja apanhou o detonador
                        kill(nearest_enemy, nearest_wall)
                    elif speed and enemy_list != []:
                        print("matar cm speed")
                        kill(nearest_enemy, nearest_wall)
                    elif lvl > 4 and enemy_list != []:
                        kill(nearest_enemy, nearest_wall)
                    elif (lvl >=2 and lvl < 4 and wall_list != [] and enemy_list != []): kill(nearest_enemy, nearest_wall) 
                    
                    else: 
                        if get_enemyName("Oneal") != [] and not detonador: # a partir do nivel 3 vai buscar 1º o power up
                            nearest_oneal = entity_finder(player_pos, get_enemyName("Oneal"))
                            kill(nearest_oneal, nearest_wall) 
                        elif(actions_in_queue.empty()):
                            
                            if saida != [] and len(enemy_list) == 0:# ir para a saida, se os monstros estiverem todos mortos
                                actions_in_queue.queue.clear()
                                print("Saida")
                                # print("aquiiii")
                                saida = (saida[0],saida[1])
                                to_exit(player_pos, saida ,mapa)
                                
                            else:
                                # ver como vamos chamar para matar o balao(ex qnd apanharmos um powerup ou quando tiver dentro do range)
                                
                                

                                if(wall_list == []):
                                    
                                    if(ballom_test ==  -1 or wrong_place >= 500):
                                        tmp = enemyPos[0]
                                        ballom_test = side_step(tmp)
                                        wrong_place = 0
                                        
                                    else:
                                        print("posiçao a ir" + str(ballom_test))
                                        m2 = mover(player_pos,ballom_test)
                                        m2.append(tmp)
                                        print("caminho da mover" + str(m2))
                                        coord2dir(m2)

                                else:
                                    if(nearest_wall != []):
                                        print("destruir parede")
                                        if near_wall(player_pos,nearest_wall):
                                            plant_bomb()
                                        else: go2wall(player_pos, nearest_wall,mapa)       
                    
                if(not actions_in_queue.empty()):
                    # print("aqui 1")
                    key = actions_in_queue.get()
                    
                else:
                    key = "A"
                
                if in_danger(player_pos,key) and bombs == []:
                    get_out()
                    key = actions_in_queue.get()
                if check_stuck == 30:
                    actions_in_queue.queue.clear()
                    actions_in_queue.put("B")
                    actions_in_queue.put("A")
                wrong_place += 1
                print(trocavel)
                prev_player_pos = player_pos
                print("key:"+str(key))
                
                
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
    global detonador
    global speed
    for pos,poder in droped_powerups:
        if(poder == "Flames"):
            bomb_radius += 1
            
        if(poder == "Detonator"):
            print("tnttt")
            detonador = True
        
        if(poder == "Speed"):
            print("speed")
            speed = True
        
        pos = (pos[0], pos[1]) # conversao [] -> ()
        coord2dir(mover(player_pos,pos))

def near_wall(bomberman,next_move): # diz se o playes esta colado a uma parede
    for w in wall_list:
        if distancia_calculation(bomberman,w) == 1:
            return True
    return False

def entity_finder(minha_pos,obj_pos): # funçao para encontrar o objeto mais proximo
    distancia= 1000 # valor alto so para fa step_pos = side_step(nearest_wall)
    next_wall = []
    for pos in obj_pos:
        distancia_tmp = distancia_calculation(minha_pos,pos)
        if(distancia_tmp < distancia) and can_side_step(pos):
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
def return_path(current_node):
    path = []
    current = current_node
    while current is not None:
        path.append(current.position)
        current = current.parent
    return path[::-1]  # Return reversed path

def mover(player_pos, dst_pos): 
    """Returns a list of tuples as a path from the given start to the given end in the given maze"""
    global mapa
    global enemy_list
    global danger_zone
    global wall_list
    global nearest_enemy
    global bombs
    maze = mapa.map
    nearest_wall = entity_finder(player_pos,wall_list)
    print("n"+str(nearest_wall))
    start_node = Node(None, player_pos)
    #print(start_node)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, dst_pos)
    #print(end_node)
    end_node.g = end_node.h = end_node.f = 0

    # Adding a stop condition
    outer_iterations = 0
    if wall_list != []and dst_pos == side_step(nearest_wall):
        max_iterations = len(maze) ** 2
    else :max_iterations = (len(maze) // 4) ** 2


    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Add the start node
    open_list.append(start_node)

    # Loop until you find the end
    while len(open_list) > 0:
        outer_iterations += 1
        # Get the current node
        current_node = open_list[0]
        if outer_iterations > max_iterations:
            outer_iterations = 0
            # if we hit this point return the path such as it is
            # it will not contain the destination
            if wall_list != []:
                print("return"+ str(nearest_wall))
                return mover(player_pos, side_step(nearest_wall))
            return [player_pos, side_step(player_pos)]
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
            
            # Get node positionnew_pos: tuple
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            if bombs != []:
                for x in bombs: 
                    if x[0][0] == node_position[0] and x[0][1] == node_position[1]:
                        continue
            #Make sure within range
            if node_position[0] > (len(maze) - 1) or node_position[0] < 0 or node_position[1] > (len(maze[len(maze)-1]) -1) or node_position[1] < 0:
                continue
            if Node(current_node, node_position) in closed_list:
                continue
            # Make sure walkable terrain
            if mapa.is_blocked((node_position[0],node_position[1])) or isObs(node_position, get_enemyPos()) :
                continue
          
            # Create new node
            # print("node"+str(node_position))
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:

            # Child is on the closed list
            for closed_child in closed_list:
                if child == closed_child:
                    break
            
            # Create the f, g, and h values
            child.g = current_node.g + 1
        
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
        
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g >= open_node.g:
                    break

            # Add the child to the open list
            #print(child)
            open_list.append(child) 
    return [player_pos, side_step(player_pos)]

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
    step_pos = side_step(wall)
    p = mover(player_pos, step_pos)
    coord2dir(p)
def get_path(node):
    if node.parent is None:
        return [node.position]
    path = get_path(node.parent)
    path += [node.position]
    return(path)

def dodge3(bomb_pos,bomb):#amnh
    global mapa
    global enemy_list
    global danger_zone
    global wall_list
    global nearest_enemy
    global bombs
    maze = mapa.map
    nearest_wall = entity_finder(player_pos,wall_list)
    #print("n"+str(nearest_wall))
    start_node = Node(None, player_pos)
    if bombs == []:
        bomb_pos = (bomb_pos[0],bomb_pos[1])
    open_list = []
    open_list.append(start_node)
    limite = 1000 # ver dps valor
    i = 0
    lst = [(0, -1), (0, 1), (-1, 0), (1, 0),(0,0)]
    # Loop until you find the end
    while len(open_list) > 0:
        i+=1
        
        node = open_list.pop(0)
        if (not bomb.in_range(node.position) and not isObs(node.position,danger_zone)):
            return get_path(node)
        lnewnodes = []
        
        random.shuffle(lst)
        for new_position in lst: # Adjacent squares adsw
            # Get node positionnew_pos: tuple
            node_position = (node.position[0] + new_position[0], node.position[1] + new_position[1])
            if node.position == player_pos:
                pai = player_pos
            else: pai = node.parent.position
            if nearest_enemy != [] and distancia_calculation(player_pos, nearest_enemy) <= 3:
                if distancia_calculation(node_position, nearest_enemy) < distancia_calculation(pai, nearest_enemy): #tem de se afastar
                    continue
            #Make sure within range
            if node_position[0] > (len(maze) - 1) or node_position[0] < 0 or node_position[1] > (len(maze[len(maze)-1]) -1) or node_position[1] < 0:
                continue
            # Make sure walkable terrain
            if mapa.is_blocked((node_position[0],node_position[1])) or isObs(node_position, danger_zone) or isObs(node_position,wall_list) or (node_position[0] == bomb_pos[0] and node_position[1] == bomb_pos[1]):
                continue
            
            # Create new node
            
            # Append
    
            if node_position not in get_path(node): #posso ver por pos?
                new_node = Node(node, node_position)
                lnewnodes.append(new_node)

            open_list.extend(lnewnodes)
   
    print("ultimo recurso")
    return mover(player_pos, dodge2(bomb_pos,bomb)) # ultimo recurso, para garantir tds os caminhos possiveis
       

def dodge2(bomb_pos, bomb):
    global danger_zone
    global wall_list
    global check_dodge
    global mapa 
    bomb_pos = (bomb_pos[0],bomb_pos[1])
    check_dodge = True
    next_pos = queue.Queue(100)
    next_pos.put(bomb_pos)
    #print(bomb_pos)
    while not next_pos.empty():
        p1 = next_pos.get()
        lst = [(0,1),(0,-1),(1,0),(-1,0)]
        for pos in lst:
            new_pos = (p1[0] + pos[0], p1[1] + pos[1])
            #print(new_pos)
            if(mapa.is_blocked(new_pos) or isObs(new_pos, wall_list) or isObs(new_pos, danger_zone) or new_pos == bomb_pos):                    
                continue# n faz nada / salta a frente     
            else:
                if(not bomb.in_range(new_pos)):
                    #print("dodge_pos "+str(new_pos))
                    return new_pos
                next_pos.put(new_pos)
    return side_step(player_pos)

def plant_bomb():
    global player_pos
    global bomb_radius
    global safe

    
    actions_in_queue.put("B")
    
    
    
 
def wait(wait_time): #fazer w8 para time out da bomba
    for x in range(wait_time): # w8
        actions_in_queue.put("")
def side_step(pos):
    global mapa
    global wall_list
    global danger_zone
    global player_pos
    
    lst = []
    for x in [(0,1),(1,0),(0,-1),(-1,0)]:
        new_pos = (x[0] + pos[0], x[1] + pos[1])
        if(mapa.is_blocked(new_pos) or isObs(new_pos, wall_list) or not can_side_step(new_pos) or isObs(new_pos,get_enemyPos())):
            continue
        lst.append(new_pos)
    
    return entity_finder(player_pos, lst) # para ir para o side_step mais perto
        
def can_side_step(pos):
    for x in [(0,1),(1,0),(0,-1),(-1,0)]:
        check_pos = (pos[0] + x[0], pos[1] + x[1])
        if(mapa.is_blocked(check_pos) or isObs(check_pos, wall_list) or isObs(check_pos,get_enemyPos())):
                continue
        else:
            return True
    return False

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

def to_exit(player_pos, saida ,mapa): # ver dps
   
    global nearest_wall
    if near_wall(player_pos,nearest_wall):
        plant_bomb()
    step_pos = side_step(saida)
    
    path = mover(player_pos, step_pos)
    path.append(saida)
    coord2dir(path)

def kill(pos, w): 
    global danger_zone
    global wall_list
    global mapa
    global detonador
    global player_pos
    global safe
    global bombs
    global prev_kill
    
    nearest_wall = entity_finder(player_pos,wall_list)

    if near_wall(player_pos,nearest_wall):
        actions_in_queue.queue.clear()
        plant_bomb()
        return

    d = distancia_calculation(player_pos,w)
    if detonador:
        alcance = 4
    else: alcance = 3
    isNear = d == 1
    #print("range  "+ str(alcance))
    
    b = Bomb(pos,mapa,alcance)
    kill_pos = in_range(pos,b)
    #print("kil_pos"+str(kill_pos))
    print("nearest wall kill"+str(nearest_wall))
    p = mover(player_pos, kill_pos)
    print("caminho para matar")
    
    if wall_list != [] and p[len(p) - 1] == side_step(nearest_wall):
        # actions_in_queue.queue.clear()
        print("Efeito")
        pass
    else: 
        actions_in_queue.queue.clear()
    print(actions_in_queue.empty())
    
    m1 = coord2dir(p)

    # print(safe)
    # print (detonador and safe and bombs != [])
    if player_pos == kill_pos:
        actions_in_queue.queue.clear()
        plant_bomb() #para matar
    
    #print("player_pos: "+ str(player_pos))
    # i = get_Index(pos)
    # print("i:" + str(i))
    #print(danger_zone)
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
        #print(1)
        c1 = enemy_pos[index][0]-prev[index][0]
        c2 = enemy_pos[index][1]-prev[index][1]

        future = (enemy_pos[index][0] + c1, enemy_pos[index][1] +c2)
        if(mapa.is_blocked(future) or isObs(future, wall_list)):
            if c1 == 1: 
                for x in [(0,-1),(-1,0),(0,1)]:
                    future = future[0] + x[0] , future[1] + x[1]
                    if(mapa.is_blocked(future) or isObs(future, wall_list)):
                        if x == (0,1): final_dir.append((0,0))
                        continue
                    final_dir.append(x)
                    break
            elif c1 == -1:
                for x in [(0,1),(1,0),(0,-1)]:
                    future = future[0] + x[0] , future[1] + x[1]
                    if(mapa.is_blocked(future) or isObs(future, wall_list)):
                        if x == (0,-1): final_dir.append((0,0))
                        continue
                    final_dir.append(x)
                    break
            elif c2 == 1:
                for x in [(-1,0),(0,1),(1,0)]:
                    future = future[0] + x[0] , future[1] + x[1]
                    if(mapa.is_blocked(future) or isObs(future, wall_list)):
                        if x == (-1,0): final_dir.append((0,0))
                        continue
                    final_dir.append(x)
                    break
            elif c2 == -1:
                for x in [(1,0),(0,-1),(-1,0)]:
                    future = future[0] + x[0] , future[1] + x[1]
                    if(mapa.is_blocked(future) or isObs(future, wall_list)):
                        if x == (1,0): final_dir.append((0,0))
                        continue
                    final_dir.append(x)
                    break
            else: final_dir.append((0,0))

        else : final_dir.append((c1, c2))

    prev = enemy_pos
    prev_dir = final_dir
    #print("dir"+str(final_dir))
    return final_dir

def calc_danger(enemy_pos,list_diretions): # para balloom e Doll
    global danger_zone
    global prev_danger
    size = len(enemy_pos) # so os ballooms tem danger_zone
    danger_zone = danger_zone[0:size]
    #print("LISTA DOS INMIGOS" + str(list_diretions))
    
    for cnt in range(size):
        # dir = (danger_zone[cnt][0] - enemy_pos[cnt][0], danger_zone[cnt][1] - enemy_pos[cnt][1])
        # print("dir"+str(dir))
        if list_diretions[cnt] == (0,0):
            danger_zone[cnt] = danger_zone[cnt][0]  , danger_zone[cnt][1] 
        else:
            
            danger_zone[cnt] = enemy_pos[cnt][0] + list_diretions[cnt][0], enemy_pos[cnt][1] + list_diretions[cnt][1]

def in_danger(player_pos,key):
    global mapa
    global check_count
    global danger_zone
    global prev_danger
    global mapa
    global wall_list

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
    next_pos1 = (player_pos[0] + 2 * movement[0], player_pos[1] + 2 * movement[1]) # danger_zone n funciona bem, soluçao
    n_left = (player_pos[0] -1, player_pos[1])
    n_right = (player_pos[0] + 1, player_pos[1])
    n_up = (player_pos[0] , player_pos[1] - 1)
    n_down = (player_pos[0] , player_pos[1] + 1)
    dig1 = (player_pos[0] + 1, player_pos[1] + 1)
    dig2 = (player_pos[0] -1 , player_pos[1] + 1)
    dig3 = (player_pos[0] - 1 , player_pos[1] - 1)
    dig4 = (player_pos[0] +1, player_pos[1] - 1)
    
    if(isObs(next_pos,danger_zone) or isObs(next_pos1,danger_zone) or isObs(player_pos,danger_zone) or isObs(n_up,danger_zone) or isObs(n_down,danger_zone) or isObs(n_left,danger_zone) or isObs(n_right,danger_zone)):
        #print("aquis")
        return True
    if(isObs(dig1 ,danger_zone) or isObs(dig2 ,danger_zone) or isObs(dig3,danger_zone) or isObs(dig4,danger_zone)):
       return True

def get_out():
    global lives
    global player_lives
    global player_pos
    global plant_finished
    global bombs
    
    
    actions_in_queue.queue.clear()
    
    plant_bomb()


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
    global player_pos 
    check_dodge = True
    lst = []
    flag = False

    if enemy == []:
        return player_pos
    next_pos = queue.Queue(100)
    next_pos.put(enemy)
    oneal_list = get_enemyName("Oneal")


    
    i = 0
    lst = [(0,1),(0,-1),(1,0),(-1,0)]
    #print(bomb_pos)
    while not next_pos.empty():
        print("calcular kill_ pos")
        
        p1 = next_pos.get()
       
        # random.shuffle(lst)
        for pos in lst:
            i+=1
            new_pos = (p1[0] + pos[0], p1[1] + pos[1])
            if(mapa.is_blocked(new_pos) or isObs(new_pos,danger_zone)):
                # if i == 8 and not detonador:
                #     print("ciclo") 
                #     return entity_finder(player_pos,wall_list) 
                
                # elif i == 12: 
                #     print("ciclo1")
                #     return entity_finder(player_pos,wall_list)

                # else: continue# n faz nada / salta a frente
                continue
                
            else:
                if(bomb.in_range(new_pos)):
                    print(new_pos)
                    return new_pos
                next_pos.put(new_pos)
    return entity_finder(player_pos,wall_list)

def isOneal(pos):
    list_pos = get_enemyName("Oneal")
    for p in list_pos:
        if p == pos:
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