from core import GameAPI
from constants import Sprite as sp, GRID_SIZE
import random as rnd
import math
################################################################################################################################
TEAMS = {
        "GREEN" : 0,
        "RED" : 1
}

TEAM_NAMES = {
        "GREEN" : "Royal Navy",
        "RED" : "Kaiserliche Marine"
}

COORDINATES_X = { 
        sp.GREEN_TEAM : 0, 
        sp.RED_TEAM: 6 }

X_LETTER_COORDINATES = {
        0 : "A", 1 : "B", 2 : "C", 3 : "D", 4 : "E", 5 : "F", 6 : "G"
}

CRUISER_AND_DESTROYERS_DAMAGE_DECREASE_DISTANCE = 2
BATTLESHIP_DAMAGE_IGNORE = 10
COORDINATES_Y = ( 1, 3, 5 )
SHIP_NAMES = {
        "GREEN" : {
                "DESTROYER" : "Medea",
                "CRUISER" : "Weymouth",
                "BATTLESHIP" : "Iron Duke"
        },
        "RED" : {
                "DESTROYER" : "G-101",
                "CRUISER" : "Kolberg",
                "BATTLESHIP" : "Koening"
        }
}

MAX_OBJECTS_COUNT = 15
OBJECT_SPAWN_PROBABILITY = ( MAX_OBJECTS_COUNT /  ( math.pow( GRID_SIZE, 2) - ( 2 * len(COORDINATES_Y)))) * 100

SHIP_PARAMS = {
        "DESTROYER" : {
                "damage" : 30,
                "speed" : 4,
                "max_health" : 15
        },

         "CRUISER" : {
                "damage" : 15,
                "speed" : 3,
                "max_health" : 30
        },

         "BATTLESHIP" : {
                "damage" : 20,
                "speed" : 2,
                "max_health" : 50
        }
}
################################################################################################################################
obstacles = []
################################################################################################################################
class Game(object):
        last_object = None
        last_node = None
        field = None
        current_team = "GREEN"
#------------------------------------------------------------------------------------------------------------------------------#
        def start(self, api: GameAPI) -> None:
                api.addMessage('start!')
                api.addMessage(f'[----------{TEAM_NAMES[self.current_team]}----------]')
                self.field = Field(api)
#------------------------------------------------------------------------------------------------------------------------------#
        def click(self, api: GameAPI, x: int, y: int) -> None:
                node = self.field.get_node(x, y)
                
                object = node.get_object_from_node()
                if not object == None and object.type == "SHIP" and object.team == self.current_team:
                        if not self.last_object == None and not self.last_object == object:
                                self.last_object.unmark()
                                object.try_mark()
                                self.last_object = object
                                self.last_node = node
                        else:
                                object.try_mark()
                                self.last_object = object
                                self.last_node = node

                elif self.last_object:
                        moved = self.last_object.try_to_move(node)
                        if moved : 
                                node.place_object(self.last_object)
                                self.last_node.clear_node()
                                self.last_node = None
                                self.last_object = None
                                self.change_current_team(api)

                        self.field.update_game_state()
#------------------------------------------------------------------------------------------------------------------------------#         
        def change_current_team(self, api) -> None:
                if self.current_team == "GREEN": 
                        self.current_team = "RED" 
                        self.field.try_enemies_attack("RED")
                else : 
                        self.current_team = "GREEN"
                        self.field.try_enemies_attack("GREEN")

                api.addMessage(f'[----------{TEAM_NAMES[self.current_team]}----------]')
################################################################################################################################
class GameObject(object):
        type = None
#------------------------------------------------------------------------------------------------------------------------------# 
        def __init__(self, type):
                self.type = type
################################################################################################################################
class Ship(GameObject):
        damage = 0
        speed = 0
        name = None
        max_health = 0
        current_health = 0
        sprite = None
        marked = False
        api = None
        type = "SHIP"
        marker = None
        team = None
        is_alive = True
#------------------------------------------------------------------------------------------------------------------------------# 
        def __init__(self, type, name, api: GameAPI, team) -> None:
                self.damage = SHIP_PARAMS[ type ][ "damage" ]
                self.speed = SHIP_PARAMS[ type ][ "speed" ]
                self.max_health = SHIP_PARAMS[ type ][ "max_health" ]
                self.name = name
                self.api = api
                self.team = team
#------------------------------------------------------------------------------------------------------------------------------# 
        def try_to_move(self, target) -> bool:
                x = target.pos_x
                y = target.pos_y
                distance = abs(self.pos_x - x) + abs(self.pos_y - y)
                moved = False

                if distance <= self.speed:
                        target_obj = target.get_object_from_node()
                        if not target_obj:
                                self.marker.moveTo(x, y)
                                self.unmark()
                                moved = True
                                self.pos_x = x
                                self.pos_y = y
                                self.api.addMessage(str(f'{self.name} moved to {X_LETTER_COORDINATES[x]}:{y+1}!'))
                        elif not target_obj.type == "CLIFF" and not target_obj.type == "ISLAND" and not target_obj.type == "SHIP":
                                self.marker.moveTo(x, y)
                                self.unmark()
                                moved = True
                                self.pos_x = x
                                self.pos_y = y
                                self.api.addMessage(str(f'{self.name} moved to {x}:{y}!'))
                return moved
#------------------------------------------------------------------------------------------------------------------------------#         
        def try_mark(self) -> None:
                self.marked = not self.marked
                self.marker.setSelected(self.marked)
#------------------------------------------------------------------------------------------------------------------------------# 
        def unmark(self) -> None:        
                self.marked = False
                self.marker.setSelected(self.marked)
#------------------------------------------------------------------------------------------------------------------------------# 
        def try_attack(self, targets) -> None:
                if len(targets) == 0: return
                for target in targets:
                        target.take_damage(self.damage/len(targets), self)
#------------------------------------------------------------------------------------------------------------------------------# 
        def take_damage(self, damage) -> None:
                self.current_health -= damage
                if self.current_health <= 0 : 
                        self.destroy_ship()
                        return
                
                self.api.addMessage(str(f'{self.name} was hit by {damage}, current Health: {self.current_health}'))
                self.marker.setHealth(self.current_health/self.max_health)
#------------------------------------------------------------------------------------------------------------------------------# 
        def set_atributes(self, x, y, sprite) -> None:
                self.pos_x = x
                self.pos_y = y
                self.sprite = sprite
                self.current_health = self.max_health
                self.marker = self.api.addMarker(self.sprite, self.pos_x, self.pos_y)
#------------------------------------------------------------------------------------------------------------------------------#                 
        def destroy_ship(self) -> None:
                self.marker.remove()
                self.api.addMessage(str('---------------------------------------'))
                self.api.addMessage(str(f'Ship {self.name} was Destroyed!'))
                self.api.addMessage(str('---------------------------------------'))
                self.is_alive = False
################################################################################################################################
class Battleship(Ship):
#------------------------------------------------------------------------------------------------------------------------------# 
        def __init__(self, api,  team) -> None:
                type = "BATTLESHIP"
                name = SHIP_NAMES[team][type]
                super().__init__(type, name, api, team)
#------------------------------------------------------------------------------------------------------------------------------# 
        def perform_observing(self, enemy_ships) -> None:
                attackable = []

                for ship in enemy_ships:
                        if ship.is_alive:
                                if ship.pos_x == self.pos_x:
                                        step = 1 if self.pos_y < ship.pos_y else - 1
                                        is_clear = True
                                        for y in range(self.pos_y, ship.pos_y + step, step):
                                               if (self.pos_x, y) in obstacles:
                                                       is_clear = False
                                        if is_clear:
                                                 attackable.append(ship)
                                if ship.pos_y == self.pos_y:                         
                                        is_clear = True
                                        step = 1 if self.pos_x < ship.pos_x else - 1
                                        for x in range(self.pos_x, ship.pos_x + step, step):
                                               if (x, self.pos_y) in obstacles:
                                                       is_clear = False
                                        if is_clear:
                                                 attackable.append(ship)

                self.try_attack(attackable)
#------------------------------------------------------------------------------------------------------------------------------# 
        def take_damage(self, damage, enemy) -> None:
                damage = 0 if damage < BATTLESHIP_DAMAGE_IGNORE else damage
                return super().take_damage(damage)
################################################################################################################################                
class Cruiser(Ship):
#------------------------------------------------------------------------------------------------------------------------------# 
        def __init__(self,  api,  team) -> None:
                type = "CRUISER"
                name = SHIP_NAMES[team][type]
                super().__init__(type, name, api,  team)
#------------------------------------------------------------------------------------------------------------------------------# 
        def perform_observing(self, enemy_ships) -> None:
                attackable = []
                for ship in enemy_ships:
                        if ship.is_alive:
                                if ship.pos_x == self.pos_x:
                                        step = 1 if self.pos_y < ship.pos_y else - 1
                                        is_clear = True
                                        for y in range(self.pos_y, ship.pos_y + step, step):
                                               if (self.pos_x, y) in obstacles:
                                                       is_clear = False
                                        if is_clear:
                                                 attackable.append(ship)
                                if ship.pos_y == self.pos_y:                         
                                        is_clear = True
                                        step = 1 if self.pos_x < ship.pos_x else - 1
                                        for x in range(self.pos_x, ship.pos_x + step, step):
                                               if (x, self.pos_y) in obstacles:
                                                       is_clear = False
                                        if is_clear:
                                                 attackable.append(ship)

                self.try_attack(attackable)
#------------------------------------------------------------------------------------------------------------------------------# 
        def take_damage(self, damage, enemy) -> None:
                distance = abs(self.pos_x - enemy.pos_x) + abs(self.pos_y - enemy.pos_y)
                if distance > CRUISER_AND_DESTROYERS_DAMAGE_DECREASE_DISTANCE:
                        damage = math.floor(damage/2)
                return super().take_damage(damage)
################################################################################################################################
class Destroyer(Ship):
        def __init__(self,   api,  team) -> None:
                type = "DESTROYER"
                name = SHIP_NAMES[team][type]
                super().__init__(type, name, api,  team)
#------------------------------------------------------------------------------------------------------------------------------# 
        def perform_observing(self, enemy_ships) -> None:
                attackable = []

                for ship in enemy_ships:
                        if abs(ship.pos_x - self.pos_x) <=1 and abs(ship.pos_y - self.pos_y) <=1 and ship.is_alive:
                                attackable.append(ship)
                
                self.try_attack(attackable)
#------------------------------------------------------------------------------------------------------------------------------# 
        def take_damage(self, damage, enemy) -> None:
                distance = abs(self.pos_x - enemy.pos_x) + abs(self.pos_y - enemy.pos_y)
                if distance > CRUISER_AND_DESTROYERS_DAMAGE_DECREASE_DISTANCE:
                        damage = math.floor(damage/2)
                return super().take_damage(damage)
################################################################################################################################
class Node(object):
        field = None
        pos_x = 0
        pos_y = 0
        object = None
#------------------------------------------------------------------------------------------------------------------------------# 
        def __init__(self, pos_x, pos_y, field):
                self.pos_x = pos_x
                self.pos_y = pos_y
                self.field = field
#------------------------------------------------------------------------------------------------------------------------------# 
        def place_object(self, object)-> None:
                self.object = object
#------------------------------------------------------------------------------------------------------------------------------# 
        def get_object_from_node(self) -> GameObject:
                return self.object        
#------------------------------------------------------------------------------------------------------------------------------#       
        def clear_node(self) -> None:
                self.object = None
################################################################################################################################
class Field(object):
        object_cache = []
        ships_cache = []
        api = None
#------------------------------------------------------------------------------------------------------------------------------# 
        def __init__(self, api) -> None:
                self.init_nodes()
                self.api = api
                self.place_ships(api)
                self.place_objects(api)
#------------------------------------------------------------------------------------------------------------------------------# 
        def init_nodes(self) -> None:
                for x in range(0, GRID_SIZE, 1):
                        row = []
                        for y in range(0, GRID_SIZE, 1):                        
                                node = Node(x,y, self)
                                row.append(node)
                        self.object_cache.append(row)     
#------------------------------------------------------------------------------------------------------------------------------# 
        def place_ships(self, api) -> None:
                team_green = [Destroyer(api, "GREEN"), Cruiser(api, "GREEN"), Battleship(api, "GREEN")]
                team_red = [Destroyer(api, "RED"), Cruiser(api, "RED"), Battleship(api, "RED")]

                for ship in sp.GREEN_TEAM:
                        x = COORDINATES_X[sp.GREEN_TEAM]
                        y = COORDINATES_Y[sp.GREEN_TEAM.index(ship)]
                        team_green[sp.GREEN_TEAM.index(ship)].set_atributes(x, y, ship)
                        node = self.get_node(x, y)
                        node.place_object(team_green[sp.GREEN_TEAM.index(ship)])
                        
                for ship in sp.RED_TEAM:
                         x = COORDINATES_X[sp.RED_TEAM]
                         y = COORDINATES_Y[sp.RED_TEAM.index(ship)]
                         team_red[sp.RED_TEAM.index(ship)].set_atributes(x, y, ship)
                         node = self.get_node(x, y)
                         node.place_object(team_red[sp.RED_TEAM.index(ship)])

                self.ships_cache.append(team_green)
                self.ships_cache.append(team_red)
#------------------------------------------------------------------------------------------------------------------------------# 
        def place_objects(self, api) -> None:
                object_counter = 0
                for x in range(0, GRID_SIZE, 1):
                        for y in range(0, GRID_SIZE, 1):
                                node = self.get_node(x, y)
                                if(x in COORDINATES_X.values() and y in COORDINATES_Y):
                                        continue
                                else:
                                        is_placing = True if rnd.randrange(0, 100) < OBJECT_SPAWN_PROBABILITY and object_counter < 15 else False

                                        if is_placing:
                                                object = "ISLAND" if rnd.randrange(0, 2) == 1 else "CLIFF"
                                                object_to_place = sp.ISLAND if object == "ISLAND" else sp.CLIFF
                                                api.addImage(object_to_place, x, y)
                                                new_object = GameObject(object)
                                                node.place_object(new_object)
                                                object_counter += 1
                                                if object == "CLIFF":
                                                        obstacles.append((x, y))
#------------------------------------------------------------------------------------------------------------------------------# 
        def get_node(self, x, y) -> Node:
                return self.object_cache[x][y]
#------------------------------------------------------------------------------------------------------------------------------# 
        def try_enemies_attack(self, team) -> None:    
                enemy = "RED" if team == "GREEN" else "GREEN"
                for ship in self.ships_cache[TEAMS[team]]:
                        if ship.is_alive :
                                ship.perform_observing(self.ships_cache[TEAMS[enemy]])                      
#------------------------------------------------------------------------------------------------------------------------------#  
        def update_game_state(self) -> None:               
                for i in range (0, len(TEAMS), 1):
                        for ship in self.ships_cache[i]:
                                if not ship.is_alive:
                                        node = self.get_node(ship.pos_x, ship.pos_y)
                                        node.clear_node()
                                        self.ships_cache[i].remove(ship)
                   
                if len(self.ships_cache[TEAMS["GREEN"]]) == 0:
                        self.api.addMessage(str(f'No ships in Team - Royal Navy! Game is Ended!'))
                        self.api.addMessage(str('###############################################################'))
                elif len(self.ships_cache[TEAMS["RED"]]) == 0:
                        self.api.addMessage(str(f'No ships in Team - Kaiserliche Marine! Game is Ended!'))
                        self.api.addMessage(str('###############################################################'))
################################################################################################################################
