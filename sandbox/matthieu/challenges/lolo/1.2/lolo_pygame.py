#!/usr/bin/env python

import sys, os, re, time, glob
import pygame
import numpy as np

#-------------------------------------------------------------------------------
# idee 1 : layer statique :
#          - on blit tous les tiles a l'init dans un sdl surface / texture
#          - au rendu, seule la sdl surface / texture est blitee
# idee 2 : lier un/des sprite(s) [3x3 cases] a une representation du morpion
# idee 3 : sdl -> opengl
# idee 4 : introduire Qt4

#-------------------------------------------------------------------------------
black_color = 0, 0, 0

#-------------------------------------------------------------------------------
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

    def render(self, renderer, current_time=0):
        raise NotImplementedError

    def get_sprite(self, tile_id):
        raise NotImplementedError


class SpritedTileWrapper(object):
    def __init__(self, layer, tile_id):
        self.layer = layer
	self.tile_id = tile_id


class TiledStaticLayer(Layer):
    def __init__(self, width, height,
                       coordinate_system=default_coordinate_system):
        Layer.__init__(self, coordinate_system)
        self.grid = np.zeros((width, height), dtype=np.int16)

    def fill_with_string(self, resource_manager, string):
        grid = self.grid.ravel()
        for i, val in enumerate(string):
	    grid[i] = resource_manager._tiles_repr_to_ind[val]
	# XXX: read the data in the good order : should be optimized
	self.grid = self.grid.reshape(self.grid.shape[1], self.grid.shape[0]).T

    def render(self, renderer, current_time=0):
        renderer.render_tiled_static_layer(self)

    def get_sprite(self, tile_id):
        return SpritedTileWrapper(self, tile_id)


class TiledDynamicLayer(Layer):
    def __init__(self, width, height,
                       coordinate_system=default_coordinate_system):
        Layer.__init__(self, coordinate_system)
        self.grid = np.zeros((width, height), dtype=np.int16)
        self._sprites = {}

    @classmethod
    def from_layer(self, layer, coordinate_system=default_coordinate_system):
        shape = np.array(layer.grid.shape)
	ref_scale = layer.coordinate_system.scaling
	new_scale = coordinate_system.scaling
	shape *= ref_scale / new_scale
	return TiledDynamicLayer(int(shape[0]), int(shape[1]),
					coordinate_system)

    def add_sprite(self, sprite):
        self._sprites[sprite.id] = sprite
        pos = sprite.motion.get_last_position()
	self.grid[pos[0]:pos[0] + sprite.hitbox[0],
                  pos[1]:pos[1] + sprite.hitbox[1]] = sprite.id
        sprite.coordinate_system = self.coordinate_system

    def get_sprites(self):
        return self._sprites

    def get_sprite(self, tile_id):
        if tile_id == 0: return None
        return self._sprites[tile_id]

    def update_sprite_grid_position(self, sprite, position):
	self.grid[self.grid == sprite.id] = 0
        pos = sprite.motion.get_last_position()
	self.grid[pos[0]:pos[0] + sprite.hitbox[0],
                  pos[1]:pos[1] + sprite.hitbox[1]] = sprite.id

    def render(self, renderer, current_time=0):
        renderer.render_tiled_dynamic_layer(self, current_time)


class FreeLayer(Layer):
    def __init__(self, coordinate_system=default_coordinate_system):
        Layer.__init__(self, coordinate_system)
        self._sprites = {}

    def add_sprite(self, sprite):
        self._sprites[sprite.id] = sprite
        sprite.coordinate_system = self.coordinate_system

    def get_sprites(self):
        return self._sprites

    def get_sprite(self, tile_id):
        return self._sprites[tile_id]

    def render(self, renderer, current_time=0):
        renderer.render_free_layer(self, current_time)

    def update_sprite_grid_position(self, sprite, position):
        pass


class Map(object):
    def __init__(self, resource_manager, filename):
        self.layers = [] # one tiles map per layer
        self.load_from_file(resource_manager, filename)
        # sprites which have to be updated
        self.sprites_to_be_updated = []

    def add_layer(self, layer):
        self.layers.append(layer)

    def update(self, current_time):
        for sprite in self.sprites_to_be_updated:
            sprite.update(current_time)

    def load_from_file(self, resource_manager, filename):
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
            grid = TiledStaticLayer(width, height)
            grid.fill_with_string(resource_manager, ''.join(layer))
            self.layers.append(grid)

    def render(self, renderer, current_time=0):
        '''
    renderer: MapRender visitor    
        '''
        renderer.clean_screen()
        for layer in self.layers:
            layer.render(renderer, current_time)
      

class ObstacleHandler(object):
    pass

class NoObstacleHandler(object):
    def __init__(self):
        ObstacleHandler.__init__(self)

    def sprite_can_move_to_dst(self, sprite, src, dst):
        return True

default_obstacle_handler = NoObstacleHandler()

class ObstacleHandlerFromLayers(ObstacleHandler):
    def __init__(self, layers, free_tiles=[]):
        ObstacleHandler.__init__(self)
        self.layers = layers
        self.free_tiles = free_tiles
    
    def sprite_can_move_to_dst(self, sprite, src, dst):
        for layer in self.layers:
            can_move = self.sprite_can_move_to_dst_in_layer(sprite,
                                                   src, dst, layer)
            if not can_move: return False
        return True

    def sprite_can_move_to_dst_in_layer(self, sprite, src, dst, layer):
        #XXX: do not check the entire grid
	sprite_scale = sprite.coordinate_system.scaling
        obstacle_grid = layer.grid
	obstacle_scale = layer.coordinate_system.scaling
        scale = (sprite_scale * 1.) / obstacle_scale
        sprite_grid = sprite.layer.grid
        sprite_grid2 = sprite_grid.copy()
	sprite_grid2[sprite_grid2 == sprite.id] = 0
	sprite_grid2[dst[0]:dst[0] + sprite.hitbox[0],
                  dst[1]:dst[1] + sprite.hitbox[1]] = sprite.id
	positions = np.argwhere((sprite_grid2 != sprite_grid) * \
			(sprite_grid != sprite.id))
	for position in positions:
            print position, scale, sprite_grid.shape, obstacle_grid.shape
            tile_id = obstacle_grid[position[0] * scale[0],
			           position[1] * scale[1]]
	    dst_sprite = layer.get_sprite(tile_id)
	    # FIXME : test sprite property
            is_free_tile = (dst_sprite in [None, sprite]) or \
			   (tile_id in self.free_tiles)
	    if not is_free_tile: return False
	return True



#-------------------------------------------------------------------------------
class Quest(object):
    def __init__(self):
        self.move_n = 0
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
    def __init__(self, resource_manager, screen):
        '''
    screen : SDL surface on which the rendering is done
        '''
        self.resource_manager = resource_manager
        self.screen = screen

    def clean_screen(self):
        self.screen.fill(black_color)

    def render_tiled_static_layer(self, layer, current_time=0):
        grid = layer.grid
        for i, row in enumerate(grid):
            for j, value in enumerate(row):
                tile_id = grid[i, j]
                if tile_id == -1: continue
                img = self.resource_manager.get_tile_resource(tile_id).get_current_version(0)
                pos = layer.coordinate_system.to_screen(np.array([i, j]))
                self.screen.blit(img, pos)

    def render_free_layer(self, layer, current_time=0):
        for sprite in layer.get_sprites():
            sprite.render(self, current_time)

    def render_tiled_dynamic_layer(self, layer, current_time=0):
        for sprite in layer.get_sprites().values():
            sprite.render(self, current_time)

    def render_sprite(self, sprite, current_time=0):
        resource_id = sprite.get_current_resource_id()
	t = sprite.motion.get_current_animation_time(current_time)
        img = self.resource_manager.get_sprite_resource(resource_id).get_current_version(t)
        self.screen.blit(img, sprite.get_screen_position())


class Motion(object):
    def __init__(self, speed=1.):
        '''
    speed: unit per second (according to the sprite coordinate system)
        '''
        self.speed = speed # tiles per seconds
        self.states_stack = []
        self.last_position = None

    def init_from_sprite(self, sprite):
        raise NotImplementedError

    def update_sprite(self, sprite, dt):
        raise NotImplementedError

    def get_current_state(self):
        if len(self.states_stack) == 0:
            return 0
        else:
            return self.states_stack[0]

    def get_current_animation_time(self, current_time):
        return 0

    def get_last_position(self):
        return self.last_position


class NoMotion(Motion):
    def __init__(self, speed=1.):
        Motion.__init__(self, speed)

    def init_from_sprite(self, sprite):
        self.last_position = sprite.position

    def update_sprite(self, sprite, dt):
        pass

    def get_current_state(self):
        return 0

    def get_current_animation_time(self, current_time):
        return 0

    def get_last_position(self):
        return self.last_position

default_motion = NoMotion()


class GridKeyboardFullArrowsMotion(Motion):
    states = {0 : 'none', 1 : 'up', 2 : 'down', 3 : 'left', 4 : 'right' }
    state_from_direction_dict = {(0, 0) : 0, (0, -1) : 1, (0, 1) : 2,
                                 (-1, 0) : 3, (1, 0) : 4 }

    def __init__(self, speed=1.):
        '''
    speed: unit per second (according to the sprite coordinate system)
        '''
        Motion.__init__(self, speed)
        self.slice_delta_time = 1. / self.speed
        self.last_time_motion_change = 0 #FIXME
        self.last_time_point = None
        self.move_actions = []
        self.used_directions_stack = []
        self.true_directions_stack = []

    def get_current_animation_time(self, current_time):
        return (current_time - self.last_time_motion_change)

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
        if len(self.used_directions_stack) == 0: return
        delta_time = current_time - self.last_time_point 
        used_direction = self.used_directions_stack[0]
        norm_used_direction = np.sqrt((used_direction ** 2).sum())
        if norm_used_direction == 0: return
        norm_time = delta_time * self.speed / norm_used_direction
        while norm_time > 1: # we go beyond the checkpoint
            self.last_position += self.used_directions_stack[0]
	    sprite.layer.update_sprite_grid_position(sprite, self.last_position)
            delta_time -= self.slice_delta_time * norm_used_direction
            self.last_time_point += self.slice_delta_time * norm_used_direction
            n = len(self.used_directions_stack)
            if n == 2: # use the following motion or use the only one available
                del self.true_directions_stack[0]
                del self.used_directions_stack[0]
                del self.states_stack[0]
                self.last_time_motion_change = self.last_time_point
            new_pos = self.last_position + self.true_directions_stack[0]
            if not sprite.obstacle_handler.sprite_can_move_to_dst(\
			    sprite, self.last_position, new_pos):
                self.used_directions_stack[0] = np.array([0., 0.])
                new_state = self.state_from_direction(self.true_directions_stack[0])
                self.states_stack[0] = new_state
            used_direction = self.used_directions_stack[0]
            norm_used_direction = np.sqrt((used_direction ** 2).sum())
            if not norm_used_direction: norm_used_direction = 1
            norm_time = delta_time * self.speed / norm_used_direction
        delta_position = norm_time * self.used_directions_stack[0]
        sprite.position = self.last_position + delta_position
        if len(self.true_directions_stack):
            current_dir_norm = (self.true_directions_stack[0] ** 2).sum()
            if current_dir_norm == 0:
                del self.true_directions_stack[0]
                del self.used_directions_stack[0]
                del self.states_stack[0]

    def add_move_action(self, sprite, direction):
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
                if sprite.obstacle_handler.sprite_can_move_to_dst(\
			sprite, self.last_position, new_pos):
                    new_used_direction = new_dir
                    break
                else:
                    new_used_direction = np.array([0., 0.])
            if n == 1: # new motion to be combined with the last one
                self.true_directions_stack.append(new_true_direction)
                self.used_directions_stack.append(new_used_direction)
                new_state = self.state_from_direction(new_true_direction)
                self.states_stack.append(new_state)
            else: # replace last added motion to a combination by a new on
                self.true_directions_stack[1] = new_true_direction
                self.used_directions_stack[1] = new_used_direction
                new_state = self.state_from_direction(new_true_direction)
                self.states_stack[1] = new_state
        else: # new motion from zero
            self.last_time_point = time.time()
            self.last_time_motion_change = self.last_time_point
            new_pos = self.last_position + direction
            if sprite.obstacle_handler.sprite_can_move_to_dst(sprite,
				    self.last_position, new_pos):
                new_used_direction = direction
            else:
                new_used_direction = np.array([0., 0.])
            self.true_directions_stack.append(direction)
            self.used_directions_stack.append(new_used_direction)
            new_state = self.state_from_direction(direction)
            self.states_stack.append(new_state)
        if len(self.true_directions_stack):
            current_dir_norm = (self.true_directions_stack[0] ** 2).sum()
            if current_dir_norm == 0:
                del self.true_directions_stack[0]
                del self.used_directions_stack[0]
                del self.states_stack[0]
                
    def remove_move_action(self, sprite, direction):
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
        if sprite.obstacle_handler.sprite_can_move_to_dst(sprite,
					self.last_position, new_pos):
            new_used_direction = new_true_direction
        else:
            new_used_direction = np.array([0., 0.])
        # next motion is no motion or simplify/decombine motion
        if n <= 1: # add next motion 
            self.true_directions_stack.append(new_true_direction)
            self.used_directions_stack.append(new_used_direction)
            new_state = self.state_from_direction(new_true_direction)
            self.states_stack.append(new_state)
        else: # n = 2 : modify next motion
            self.true_directions_stack[1] = new_true_direction
            self.used_directions_stack[1] = new_used_direction
            new_state = self.state_from_direction(new_true_direction)
            self.states_stack[1] = new_state
        if len(self.true_directions_stack):
            current_dir_norm = (self.true_directions_stack[0] ** 2).sum()
            if current_dir_norm == 0:
                del self.true_directions_stack[0]
                del self.used_directions_stack[0]
                del self.states_stack[0]

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
    max_id = 1

    def __init__(self, layer, position=(0, 0), hitbox=np.array([1., 1.]),
                       coordinate_system=default_coordinate_system):
        self.id = Sprite.max_id
        Sprite.max_id += 1
        self.state = 0 # default
	self.hitbox = hitbox
        self.layer = layer
        self.position = np.asarray(position)
        self.obstacle_handler = default_obstacle_handler
        self.motion = default_motion
        self.motion.init_from_sprite(self)

    def get_current_resource_id(self):
        return self.id, self.state, self.motion.get_current_state()

    def set_motion(self, motion):
        self.motion = motion
        self.motion.init_from_sprite(self)

    def render(self, renderer, current_time=0):
        renderer.render_sprite(self, current_time)

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
        self.sdl_surface = pygame.Surface(resolution)

    def fill(self, color):
        self.sdl_surface.fill(color)

    def blit(self, img, pos):
        self.sdl_surface.blit(img, pos)

    def render(self, renderer, map, current_time=0):
        map.render(renderer, current_time)
        self.sdl_screen.blit(self.sdl_surface, (0, 0))
        pygame.display.update()


#-------------------------------------------------------------------------------
# game specifics

class Player(Sprite):
    def __init__(self, map, position=(0, 0), hitbox=np.array([1., 1.]),
                       coordinate_system=default_coordinate_system):
        Sprite.__init__(self, map, position, hitbox, coordinate_system)
        self.set_motion(GridKeyboardFullArrowsMotion(speed=8.))
        self.carrying_an_object = False
                
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
            else:
                player.key_down(event.key)
        elif event.type == pygame.KEYUP:
            player.key_up(event.key)


#-------------------------------------------------------------------------------
class Resource(object):
    def get_current_frame(self, t):
        '''
    Return the version of the resource at the normalized time 't'

    t: floating number between 0 and 1
        '''
        raise NotImplementedError


class ImageResource(Resource):
    def __init__(self, resource_filename):
        Resource.__init__(self)
        self._raw_image = pygame.image.load(resource_filename).convert_alpha()

    def get_current_version(self, animation_time):
        return self._raw_image


class AnimationResource(Resource):
    def __init__(self, resource_prefix, duration=1.):
        '''
    resource_prefix:   complete path + prefix of numerated image files
    duration:          duration in second of the total animation
        '''
        Resource.__init__(self)
        self._raw_images = []
	self.duration = duration 
	filenames = glob.glob(resource_prefix + '*.*')
	if len(filenames) == 0: raise ValueError
	for filename in filenames:
            raw_image = pygame.image.load(filename).convert_alpha()
            self._raw_images.append(raw_image)

    def get_current_version(self, animation_time):
        size = len(self._raw_images)
        ind = int(animation_time * size / self.duration)
        return self._raw_images[ind % size]


class ResourceManager(object):
    def __init__(self, prefix):
        self.prefix = prefix
        self.tiles_max_id = 0
        self._resources = {}
        self._sprites = {}
        self._tiles = {}
        # string repr must be used only during data loading
        self._tiles_repr_to_ind = {'.' : -1}

    def register_animation(self, sprite_id, sprite_state,
                           motion_state, resource_prefix, duration=1.):
        # XXX: if an animation is load 2 times wih different duration the second registration is ignored
        resource_id = sprite_id, sprite_state, motion_state
        path = os.path.join(self.prefix, 'animations', resource_prefix)
	resource = self._resources.get(path)
	if resource is None:
            self._resources[path] = AnimationResource(path, duration)
        self._sprites[resource_id] = self._resources.get(path)

    def register_image(self, sprite_id, sprite_state,
                       motion_state, resource_filename):
        resource_id = sprite_id, sprite_state, motion_state
        path = os.path.join(self.prefix, resource_filename)
	resource = self._resources.get(path)
	if resource is None:
            self._resources[path] = ImageResource(path)
        self._sprites[resource_id] = self._resources.get(path)

    def register_tile(self, tile_repr, resource_filename):
        tile_id = self.tiles_max_id
        self.tiles_max_id += 1
        path = os.path.join(self.prefix, resource_filename)
	resource = self._resources.get(path)
	if resource is None:
            self._resources[path] = ImageResource(path)
        self._tiles[tile_id] = self._resources.get(path)
        self._tiles_repr_to_ind[tile_repr] = tile_id

    def get_tile_resource(self, resource_id):
        return self._tiles[resource_id]

    def get_sprite_resource(self, resource_id):
        return self._sprites[resource_id]


#-------------------------------------------------------------------------------
# main

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

# globals
#screen = None

def main():
    # config
    prefix = "../common_data/"
    music = False

    resource_manager = ResourceManager(prefix)

    # pygame init
    pygame.mixer.init()
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.font.init()
    pygame.init()

    if music:
        pygame.mixer.music.load(prefix + 'lolo.ogg')
        pygame.mixer.music.play(-1)

    # init screen and tiles
    #global screen #FIXME : remove
    screen = Screen((640, 480))
    renderer = MapRenderer(resource_manager, screen)
    for (tile_repr, filename) in tiles_img_files.items():
        resource_manager.register_tile(tile_repr, filename)

    # create map
    coordinate_system = BasicCoordinateSystem(scaling=np.array([30, 30]))
    map = Map(resource_manager, "lolo.map")
    for layer in map.layers:
        layer.coordinate_system = coordinate_system
    map.layers[1].is_actionnable = True
    coordinate_system2 = BasicCoordinateSystem(scaling=np.array([15, 15]))
    player_layer = TiledDynamicLayer.from_layer(map.layers[0],
		    			coordinate_system2)
    #free_layer = FreeLayer(coordinate_system)
    map.add_layer(player_layer)

    # player
    player = Player(player_layer, [2, 4], hitbox=np.array([2., 2.]))
    player.obstacle_handler = ObstacleHandlerFromLayers(\
		    [map.layers[0], player_layer],
                    free_tiles=[resource_manager._tiles_repr_to_ind[':']])
    player_layer.add_sprite(player)
    duration = 1.5
    resource_manager.register_image(player.id, 0, 0, "player.png")
    resource_manager.register_animation(player.id, 0, 1, "lolo-up", duration)
    resource_manager.register_animation(player.id, 0, 2, "lolo-down", duration)
    resource_manager.register_animation(player.id, 0, 3, "lolo-left", duration)
    resource_manager.register_animation(player.id, 0, 4, "lolo-right", duration)
    map.sprites_to_be_updated.append(player)


    # box 1
    box = Sprite(player_layer, [10, 12], hitbox=np.array([2., 2.]))
    player_layer.add_sprite(box)
    resource_manager.register_image(box.id, 0, 0, 'box.png')
    map.sprites_to_be_updated.append(box)

    # box 2
    box2 = Sprite(player_layer, [12, 14], hitbox=np.array([2., 2.]))
    player_layer.add_sprite(box2)
    resource_manager.register_image(box2.id, 0, 0, 'box.png')
    map.sprites_to_be_updated.append(box2)


    game.quest = Quest()

    # main loop
    while not game.quest.end:
        read_event(player)
        current_time = time.time()
        map.update(current_time)
        screen.render(renderer, map, current_time)

    # clean and quit
    pygame.font.quit()
    pygame.quit()



if __name__ == '__main__':
    main()
