#!/usr/bin/env python

import sys, os, re, time
import pygame
import numpy as np

#-------------------------------------------------------------------------------
# step 1 : lecture de la map
# step 2 : affichage de la map (layers + tiles)
# step 3 : affichage du perso (free layer)
# step 4 : controle clavier du perso
# step 5 : prendre et poser les coeurs sur le morpion
# step 6 : jouer au morpion
# step 7 : obstacles
#
#-------------------------------------------------------------------------------
# idee 1 : layer statique :
#          - on blit tous les tiles a l'init dans un sdl surface / texture
#          - au rendu, seule la sdl surface / texture est blitee
# idee 2 : lier un/des sprite(s) [3x3 cases] a une representation du morpion
# idee 3 : sdl -> opengl
# idee 4 : introduire Qt4

#-------------------------------------------------------------------------------
black_color = 0, 0, 0
prefix = "../common_data/"

#-------------------------------------------------------------------------------
tiles_img_files = {\
    ':' : 'background.jpg',
    '=' : 'wall.jpg',
    'o' : 'stone.png',
    '+' : 'tree.png',
    'A' : 'door.png',
    'f' : 'frontwall.png',
    'C' : 'heart.png',
    'X' : 'box.png',
    '_' : 'black.png',
#   '.' represents an invisible tile
}

tiles_repr_to_ind = {'.' : -1}
tiles_sdl_img = {}


def load_tiles():
    for i, (k, filename) in enumerate(tiles_img_files.items()):
        tiles_sdl_img[i] = pygame.image.load(prefix + filename).convert_alpha()
        tiles_repr_to_ind[k] = i


class BasicCoordinateSystem(object):
    def __init__(self, offset=(0, 0), scaling=(1, 1)):
        '''
    offset:  offset from object to screen (in object coordinate metric)
    scaling: scaling factor from object to screen
        '''
        self.offset = np.asarray(offset)
        self.scaling = np.asarray(scaling)

    def to_screen(self, position):
        return (position + self.offset) * self.scaling

default_coordinate_system = BasicCoordinateSystem()


class Layer(object):
    def __init__(self, coordinate_system=default_coordinate_system):
        self.coordinate_system = coordinate_system
        self.is_actionnable = False

    def render(self, renderer):
        raise NotImplementedError


class TiledStaticLayer(Layer):
    def __init__(self, width, height,
                       coordinate_system=default_coordinate_system):
        Layer.__init__(self, coordinate_system)
        self.tiles_map = np.zeros((height, width), dtype=np.int16)

    def fill_with_string(self, string):
        for i, val in enumerate(string):
            self.tiles_map.ravel()[i] = tiles_repr_to_ind[val]

    def render(self, renderer):
        renderer.render_tiled_static_layer(self)


class TiledDynamicLayer(Layer):
    def __init__(self, width, height,
                       coordinate_system=default_coordinate_system):
        Layer.__init__(self, coordinate_system)
        self.tiles_map = np.zeros((height, width), dtype=np.int16)
        self._sprites = []

    def add_sprite(self, sprite):
        self._sprites.append(sprite)
        sprite.coordinate_system = self.coordinate_system

    def get_sprites(self):
        return self._sprites

    def move(self, sprite, dst):
        sprite.set_ 

    def render(self, renderer):
        renderer.render_tiled_dynamic_layer(self)


class FreeLayer(Layer):
    def __init__(self, coordinate_system=default_coordinate_system):
        Layer.__init__(self, coordinate_system)
        self._sprites = []

    def add_sprite(self, sprite):
        self._sprites.append(sprite)
        sprite.coordinate_system = self.coordinate_system

    def get_sprites(self):
        return self._sprites

    def render(self, renderer):
        renderer.render_free_layer(self)

    def move(self, sprite, dst):
        sprite.set_ 


class Map(object):
    def __init__(self, filename):
        self.layers = [] # one tiles map per layer
        self.load_from_file(filename)
        # sprites which have to be updated
        self.sprites_to_be_updated = []

    def add_layer(self, layer):
        self.layers.append(layer)

    def update(self, current_time):
        for sprite in self.sprites_to_be_updated:
            sprite.update(current_time)

    def load_from_file(self, filename):
        fd = open(filename)
        lines = fd.readlines()
        for i, line in enumerate(lines):
            if line[-1] == '\n':
                lines[i] = line[:-1]
        lines.append('')

        # split layers
        ind = []
        for i, line in enumerate(lines):
            if re.match("<layer.*>", line):
                ind.append(i)
        ind.append(-1)
        layers = []
        for i in range(len(ind) - 1):
            layers.append(lines[ind[i]:ind[i + 1]])

        # clean layers
        for layer in layers:
            while 1:
                try:
                    layer.remove("")
                except ValueError:
                    break
            del layer[0] # remove layer header

        # check layers format
        width = len(layers[0][0])
        height = len(layers[0])
        for layer in layers:
            for i, row in enumerate(layer):
                if width != len(row):
                    raise ValueError("incorrect map file: " + \
                                     "width mismatch (row %d)" % i)
            if len(layer) != height:
                raise ValueError("incorrect map file: height mismatch")

        # convert layers
        self.layers = []
        for layer in layers:
            tiles_map = TiledStaticLayer(width, height)
            tiles_map.fill_with_string(''.join(layer))
            self.layers.append(tiles_map)

    def render(self, renderer):
        '''
    renderer: MapRender visitor    
        '''
        renderer.clean_screen()
        for layer in self.layers:
            layer.render(renderer)
      

class ObstacleHandler(object):
    pass

class NoObstacleHandler(object):
    def __init__(self):
        ObstacleHandler.__init__(self)

    def sprite_can_move_to_dst(self, dst):
        return True

default_obstacle_handler = NoObstacleHandler()

class ObstacleHandlerFromLayer(ObstacleHandler):
    def __init__(self, layer, free_tiles=[]):
        ObstacleHandler.__init__(self)
        self.layer = layer
        self.free_tiles = free_tiles
    
    def sprite_can_move_to_dst(self, dst):
        tiles_map = self.layer.tiles_map
        return tiles_map[dst[1], dst[0]] in self.free_tiles

#-------------------------------------------------------------------------------
class TicTacToe(object):
    def __init__(self):
        self.board = np.zeros((3, 3), dtype=np.int16)
        self.end = False

    def player_play(self, player_ind, pos):
        if self.end: return None
        self.board[tuple(pos)] = player_ind
        return pos

    def ia_play(self, player_ind):
        '''
    ia play randomly
        '''
        if self.end: return None
        T = np.argwhere(self.board == 0)
        pos = tuple(T[np.random.randint(len(T))])
        self.board[pos] = player_ind
        return pos

    def check(self, player_ind):
        T = (self.board == player_ind)
        r = (T.sum(axis=0) == 3).sum()      # row
        c = (T.sum(axis=1) == 3).sum()      # col
        d1 = (np.diag(T).sum() == 3)       # first diag
        d2 = (np.diag(T[::-1]).sum() == 3) # second diag
        if (r + c + d1 + d2) > 0:
            self.end = True
            return True
        return False


class Quest(object):
    def __init__(self):
        self.move_n = 0
        self.tictactoe = TicTacToe()
        self.end = False
    

class Game(object):
    def __init__(self):
        self.quest = None

game = Game()

#-------------------------------------------------------------------------------
class MapRenderer(object):
    '''
    Object rendering a map onto a given screen

    Note: follow the visitor pattern
    '''
    def __init__(self, screen):
        '''
    screen : SDL surface on which the rendering is done
        '''
        self.screen = screen
        self.tiles_max_id = 0
        self._resources = {}

    def register(self, sprite_id, sprite_state, motion_state, resource):
        id = sprite_id, sprite_state, motion_state
        self._resources[id] = resource

    def clean_screen(self):
        self.screen.fill(black_color);

    def render_tiled_static_layer(self, layer):
        tiles_map = layer.tiles_map
        for j, row in enumerate(tiles_map):
            for i, value in enumerate(row):
                ind = tiles_map[j, i]
                if ind == -1: continue
                img = tiles_sdl_img[ind]
                pos = layer.coordinate_system.to_screen(np.array([i, j]))
                self.screen.blit(img, pos)

    def render_free_layer(self, layer):
        for sprite in layer.get_sprites():
            sprite.render(self)

    def render_tiled_dynamic_layer(self, layer):
        for sprite in layer.get_sprites():
            sprite.render(self)

    def render_sprite(self, sprite):
        # FIXME
        #resource = self._resources[sprite.get_imprint()]
        self.screen.blit(sprite.get_current_image(), #XXX
                         sprite.get_screen_position()) #XXX


class Motion(object):
    def __init__(self, speed=1.):
        '''
    speed: unit per second (according to the sprite coordinate system)
        '''
        self.speed = speed # tiles per seconds
        self.states_stack = []

    def init_from_sprite(self, sprite):
        raise NotImplementedError

    def update_sprite(self, sprite, dt):
        raise NotImplementedError

    def get_current_state(self):
        if len(self.states_stack) == 0:
            return 0
        else:
            return self.states_stack[0]


class GridKeyboardFullArrowsMotion(Motion):
    states = {0 : 'none', 1 : 'up', 2 : 'down', 3 : 'left', 4 : 'right' }
    state_from_direction_dict = {(0, 0) : 0, (0, -1) : 1, (0, 1) : 2,
                                 (-1, 0) : 3, (1, 0) : 4 }

    def __init__(self, speed=1.):
        '''
    speed: unit per second (according to the sprite coordinate system)
        '''
        Motion.__init__(self, speed)
        self.last_position = None
        self.slice_delta_time = 1. / self.speed
        self.last_time_point = None
        self.move_actions = []
        self.used_directions_stack = []
        self.true_directions_stack = []

    def state_from_direction(self, direction):
	try:
            new_state = self.state_from_direction_dict[tuple(direction)]
        except KeyError:
            new_state = self.states_stack[0]
	return new_state

    def init_from_sprite(self, sprite):
        self.last_position = sprite.position

    def update_sprite(self, sprite, current_time):
        '''
    handle current actions and update position/logic
        '''
        if 0: print "====== update ======="
	if 0: print "3c)", self.true_directions_stack, self.used_directions_stack, self.states_stack
        if len(self.used_directions_stack) == 0: return
        delta_time = current_time - self.last_time_point 
        used_direction = self.used_directions_stack[0]
        norm_used_direction = np.sqrt((used_direction ** 2).sum())
	if norm_used_direction == 0: return
        norm_time = delta_time * self.speed / norm_used_direction
        if 0:
            print "-----------"
            print "tdir = ", self.true_directions_stack
            print "udir = ", self.used_directions_stack
        if 0:
            print "p0 = ", self.last_position
            print "t0 = ", self.last_time_point
        if 0:
            print "t = ", current_time
            print "dt = ", delta_time
            print "nt = ", norm_time
        while norm_time > 1: # we go beyond the checkpoint
            if 0: print "!!!!!!!!!!!!"
            self.last_position += self.used_directions_stack[0]
            n = len(self.used_directions_stack)
            if n == 2: # use the following motion or use the only one available
                del self.true_directions_stack[0]
                del self.used_directions_stack[0]
                del self.states_stack[0]
            delta_time -= self.slice_delta_time * norm_used_direction
            self.last_time_point += self.slice_delta_time * norm_used_direction
            new_pos = self.last_position + self.true_directions_stack[0]
            if not sprite.obstacle_handler.sprite_can_move_to_dst(new_pos):
                self.used_directions_stack[0] = np.array([0., 0.])
                self.states_stack[0] = 0
            used_direction = self.used_directions_stack[0]
            norm_used_direction = np.sqrt((used_direction ** 2).sum())
            if not norm_used_direction: norm_used_direction = 1
            norm_time = delta_time * self.speed / norm_used_direction
            if 0:
                print "tdir = ", self.true_directions_stack
                print "udir = ", self.used_directions_stack
            if 0:
                print "p0 = ", self.last_position
                print "t0 = ", self.last_time_point
            if 0:
                print "t = ", current_time
                print "dt = ", delta_time
                print "nt = ", norm_time
        delta_position = norm_time * self.used_directions_stack[0]
        sprite.position = self.last_position + delta_position
        if len(self.true_directions_stack):
            current_dir_norm = (self.true_directions_stack[0] ** 2).sum()
            if current_dir_norm == 0:
                del self.true_directions_stack[0]
                del self.used_directions_stack[0]
                del self.states_stack[0]
        if 0:
            print "p = ", sprite.position
	if 0: print "3b)", self.true_directions_stack, self.used_directions_stack, self.states_stack
	print self.states_stack

    def add_move_action(self, sprite, direction):
        if 0: print "====== action =======", direction
	if 0: print "1a)", self.true_directions_stack, self.used_directions_stack, self.states_stack
        n = len(self.used_directions_stack)
        if n: # combining motions 
            current_dir_norm = (self.used_directions_stack[0] ** 2).sum()
            if n == 2 and current_dir_norm == 0:
                self.last_time_point = time.time()
                del self.true_directions_stack[0]
                del self.used_directions_stack[0]
                del self.states_stack[0]
                n -= 1
            last_used_direction = self.used_directions_stack[0]
            next_true_direction = self.true_directions_stack[-1]
            next_used_direction = self.used_directions_stack[-1]
            new_true_direction  = next_true_direction + direction
            for new_dir in [new_true_direction, direction, next_used_direction]:
                new_pos = self.last_position + last_used_direction + new_dir
                if sprite.obstacle_handler.sprite_can_move_to_dst(new_pos):
                    new_used_direction = new_dir
                    break
                else:
                    new_used_direction = np.array([0., 0.])
            if n == 1: # new motion to be combined with the last one
                self.true_directions_stack.append(new_true_direction)
                self.used_directions_stack.append(new_used_direction)
                new_state = self.state_from_direction(new_used_direction)
                self.states_stack.append(new_state)
            else: # replace last added motion to a combination by a new on
                self.true_directions_stack[1] = new_true_direction
                self.used_directions_stack[1] = new_used_direction
                new_state = self.state_from_direction(new_used_direction)
                self.states_stack[1] = new_state
        else: # new motion from zero
            self.last_time_point = time.time()
            new_pos = self.last_position + direction
            if sprite.obstacle_handler.sprite_can_move_to_dst(new_pos):
                new_used_direction = direction
            else:
                new_used_direction = np.array([0., 0.])
            self.true_directions_stack.append(direction)
            self.used_directions_stack.append(new_used_direction)
            new_state = self.state_from_direction(new_used_direction)
            self.states_stack.append(new_state)
	if 0: print "1b)", self.true_directions_stack, self.used_directions_stack, self.states_stack
        if len(self.true_directions_stack):
            current_dir_norm = (self.true_directions_stack[0] ** 2).sum()
            if current_dir_norm == 0:
                del self.true_directions_stack[0]
                del self.used_directions_stack[0]
                del self.states_stack[0]
	if 0: print "1c)", self.true_directions_stack, self.used_directions_stack, self.states_stack
                
    def remove_move_action(self, sprite, direction):
        if 0: print "====== remove action =======", direction
	if 0: print "2a)", self.true_directions_stack, self.used_directions_stack, self.states_stack
        n = len(self.used_directions_stack)
        if n == 0:
            self.last_time_point = time.time()
            self.used_directions_stack.append(np.array([0., 0.]))
            self.true_directions_stack.append(np.array([0., 0.]))
            self.states_stack.append(0)
            n = 1
        current_dir_norm = (self.used_directions_stack[0] ** 2).sum()
        if n == 2 and current_dir_norm == 0:
            self.last_time_point = time.time()
            del self.true_directions_stack[0]
            del self.used_directions_stack[0]
            del self.states_stack[0]
            n -= 1
        last_used_direction = self.used_directions_stack[0]
        next_used_direction = self.used_directions_stack[-1]
        next_true_direction = self.true_directions_stack[-1]
        new_true_direction = next_true_direction - direction
        new_pos = self.last_position + last_used_direction + new_true_direction
        if n == 1 and current_dir_norm == 0:
            self.last_time_point = time.time()
            del self.true_directions_stack[0]
            del self.used_directions_stack[0]
            del self.states_stack[0]
            n -= 1
        if sprite.obstacle_handler.sprite_can_move_to_dst(new_pos):
            new_used_direction = new_true_direction
        else:
            new_used_direction = np.array([0., 0.])
        # next motion is no motion or simplify/decombine motion
        if n <= 1: # add next motion 
            self.true_directions_stack.append(new_true_direction)
            self.used_directions_stack.append(new_used_direction)
            new_state = self.state_from_direction(new_used_direction)
            self.states_stack.append(new_state)
        else: # n = 2 : modify next motion
            self.true_directions_stack[1] = new_true_direction
            self.used_directions_stack[1] = new_used_direction
            new_state = self.state_from_direction(new_used_direction)
            self.states_stack[1] = new_state
	if 0: print "2b)", self.true_directions_stack, self.used_directions_stack, self.states_stack
        if len(self.true_directions_stack):
            current_dir_norm = (self.true_directions_stack[0] ** 2).sum()
            if current_dir_norm == 0:
                del self.true_directions_stack[0]
                del self.used_directions_stack[0]
                del self.states_stack[0]
	if 0: print "2c)", self.true_directions_stack, self.used_directions_stack, self.states_stack


    def add_move_up(self, sprite):
        self.add_move_action(sprite, np.array([0., -1.]))

    def add_move_down(self, sprite):
        self.add_move_action(sprite, np.array([0., 1.]))

    def add_move_left(self, sprite):
        self.add_move_action(sprite, np.array([-1., 0.]))

    def add_move_right(self, sprite):
        self.add_move_action(sprite, np.array([1., 0.]))

    def remove_move_up(self, sprite):
        self.remove_move_action(sprite, np.array([0., -1.]))

    def remove_move_down(self, sprite):
        self.remove_move_action(sprite, np.array([0., 1.]))

    def remove_move_left(self, sprite):
        self.remove_move_action(sprite, np.array([-1., 0.]))

    def remove_move_right(self, sprite):
        self.remove_move_action(sprite, np.array([1., 0.]))


class Sprite(object):
    def __init__(self, layer, position=(0, 0),
                       coordinate_system=default_coordinate_system):
        self.id = None # no_id
        self.state = 0 # default
        self.motion = None
        self.layer = layer
        self.position = np.asarray(position)
        self.sdl_img = None #XXX
        self.obstacle_handler = default_obstacle_handler

    def get_imprint(self):
        return self.id, self.state, self.motion.get_current_state()

    def set_motion(self, motion):
        self.motion = motion
        self.motion.init_from_sprite(self)

    def load_from_file(self, filename): #XXX
        self.sdl_img = pygame.image.load(filename).convert_alpha() #XXX
    def get_current_image(self): #XXX
        return self.sdl_img #XXX

    def render(self, renderer):
        renderer.render_sprite(self)

    def get_screen_position(self):
        return self.layer.coordinate_system.to_screen(self.position)

    def set_position(self, position):
        self.position = np.asarray(position)

    def update(self, current_time):
        self.motion.update_sprite(self, current_time)


class Screen(object):
    def __init__(self, resolution):
        self.resolution = resolution
        self.sdl_screen = pygame.display.set_mode(resolution)
        self.sdl_surface = pygame.Surface(resolution);
        self.renderer = MapRenderer(self.sdl_surface)

    def render(self, map):
        map.render(self.renderer)
        self.sdl_screen.blit(self.sdl_surface, (0, 0));
        pygame.display.update();

screen = None

#-------------------------------------------------------------------------------
class Player(Sprite):
    def __init__(self, map, position=(0, 0),
                       coordinate_system=default_coordinate_system):
        Sprite.__init__(self, map, position, coordinate_system)
        self.set_motion(GridKeyboardFullArrowsMotion(speed=4.))
        self.carrying_an_object = False
                
    def take_or_put(self):
        '''
    try to take or put an object in the current tile
        '''
        box = tiles_repr_to_ind['X']
        heart = tiles_repr_to_ind['C']
        void = tiles_repr_to_ind['.']
        black = tiles_repr_to_ind['_']
        bg = tiles_repr_to_ind[':']
        tictactoe = game.quest.tictactoe
        for layer in self.map.layers:
            if not isinstance(layer, TiledStaticLayer): continue
            tiles_map = layer.tiles_map
            tiles_ind = tiles_map[self.position[1], self.position[0]]
            if not layer.is_actionnable: continue
            if game.quest.tictactoe.end: return
            if tiles_ind == heart and not self.carrying_an_object:
                self.carrying_an_object = True
                tiles_map[self.position[1], self.position[0]] = void
            if tiles_ind == black and self.carrying_an_object:
                self.carrying_an_object = False
                tiles_map[self.position[1], self.position[0]] = heart
                tictactoe.player_play(1, self.position - 10)
                if tictactoe.check(1):
                    self.map.layers[0].tiles_map[1, 17] = bg
                    print "you win !"
                    return
                pos = tictactoe.ia_play(2)
                if pos:
                    self.map.layers[1].tiles_map[pos[1] + 10, pos[0] + 10] = box
                if tictactoe.check(2):
                    print "you loose !"
                    return

    def key_down(self, key):
        if key == pygame.K_UP:
            self.motion.add_move_up(self)
        elif key == pygame.K_DOWN:
            self.motion.add_move_down(self)
        elif key == pygame.K_LEFT:
            self.motion.add_move_left(self)
        elif key == pygame.K_RIGHT:
            self.motion.add_move_right(self)

    def key_up(self, key):
        if key == pygame.K_UP:
            self.motion.remove_move_up(self)
        elif key == pygame.K_DOWN:
            self.motion.remove_move_down(self)
        elif key == pygame.K_LEFT:
            self.motion.remove_move_left(self)
        elif key == pygame.K_RIGHT:
            self.motion.remove_move_right(self)

def read_event(player):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                sys.exit(0)
            elif event.key == pygame.K_SPACE:
                player.take_or_put()
            else:
                player.key_down(event.key)
        elif event.type == pygame.KEYUP:
            player.key_up(event.key)

   
def main():
    # pygame init
    pygame.mixer.init()
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.font.init()
    pygame.init()

    #pygame.mixer.music.load(prefix + 'lolo.ogg')
    #pygame.mixer.music.play(-1)

    # init screen and tiles
    global screen
    screen = Screen((640, 480))
    load_tiles()

    # create map
    coordinate_system = BasicCoordinateSystem(scaling=np.array([30, 30]))
    map = Map("lolo.map")
    for layer in map.layers:
        layer.coordinate_system = coordinate_system
    map.layers[1].is_actionnable = True
    free_layer = FreeLayer(coordinate_system)
    map.add_layer(free_layer)
    player = Player(free_layer, [1, 2])
    player.map = map # tmp hack
    player.load_from_file(prefix + "player.png")
    player.obstacle_handler = ObstacleHandlerFromLayer(map.layers[0],
                    free_tiles=[tiles_repr_to_ind[':']])
    free_layer.add_sprite(player)

    map.sprites_to_be_updated.append(player)

    game.quest = Quest()

    # main loop
    while not game.quest.end:
        read_event(player)
        current_time = time.time()
        map.update(current_time)
        screen.render(map)

    # clean and quit
    pygame.font.quit()
    pygame.quit()



if __name__ == '__main__':
    main()