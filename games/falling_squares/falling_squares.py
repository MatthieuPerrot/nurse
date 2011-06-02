#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import numpy as np

from nurse.base import *
from nurse.config import Config
from nurse.sprite import *
from nurse.context import Context, ContextManager
from nurse.screen import *

import sys
sys.path.append(sys.path[0] + '/../../examples/')

from test_spatial_event import *


color_map = np.random.randint(0, 255, (10, 3))
#-------------------------------------------------------------------------------
# Notes :
# -------

#-------------------------------------------------------------------------------
class Game(Object):
	def __init__(self, name='game', context=None):
		Object.__init__(self, name)
		# XXX : this method should be renamed ?
		context.add_fsm(self)
		self.score_sprite = None
		self.score = 1000
		self.current_color = None
		self.speed = 100 # ms
		self.time_between_two_squares = 1000 # ms
		self.level = 1

	def select_current_color(self):
		n = len(color_map)
		self.current_color = color_map[np.random.randint(n)]

		#TODO : change current_color_sprite

	def collide(self, square):
		'''

		'''
		if square.color == self._current_color:
			self.score += self.speed * self.level
		else:
			factor = (((self.level + 2) / 2.6) ** 2).astype('i')
			self.score -= self.speed * factor
		self.score_sprite.text = str(self.score)

	def update(self, dt):
		print dt


class MultiStaticSprite(Sprite):
	def __init__(self, name='multistatic_sprite', context=None, layer=1):
		Sprite.__init__(self, name, context, layer)

	def add_state(self, state):
		Sprite.add_state(self, state)

	def add_state_from_filename(self, state_name, filename):
		state = StaticSprite(state_name, None, self._layer)
		self.add_state(state)

	def add_state_from_color(self, state_name, size=None, shift=(0, 0),
			center_location=(0,0), color=(0, 0, 0), alpha=128):
		state = UniformLayer(state_name, None, self._layer, size,
				shift, center_location, color, alpha)
		self.add_state(state)

	def get_frame_infos(self, time):
		return self._current_state.get_frame_infos(time)

#	def on_state_changed(


class FallingMotion(Motion):
	def __init__(self, name='falling_motion', context=None, speed=100.):
		Motion.__init__(self, name, context, speed)


#-------------------------------------------------------------------------------

def random_square_generator(context, game):
	size = (20, 20)
	shift = (np.random.randint(game.resolution[0] - size[0]), 0)
	color = color_map[np.random.randint(len(color_map))]
	fsm = UniformLayer('square', context, layer=0, size=size, shift=shift,
			center_location='centered', color=color, alpha=255)
	fsm.set_motion(FallingMotion(speed=120.))
	fsm.start()
	return ChangeScoreOnCollision(fsm, color, game)


#-------------------------------------------------------------------------------
class ChangeScoreOnCollision(ObjectProxy):
	def __init__(self, receiver, color, game):
		ObjectProxy.__init__(self, receiver)
		self.color = color
		self._game = game

	def on_collision(self, event):
		self._game.collide(self)
		pass # FIXME


#-------------------------------------------------------------------------------
# FIXME : il faudrait un player qui ne se déplace que de gauche à droite
#         et seulement entre 2 bornes le long de cet axe

def create_player(context, layer):
	fsm = AnimatedSprite("player", context, layer=layer)
	fsm.set_motion(KeyboardLeftRightArrowsMotion(speed=120.))
	fsm.load_frames_from_filenames('__default__', ['perso.png'],
						'centered_bottom', 1)
	fsm.set_location((400, 550))
	fsm.start()
	return fsm

#-------------------------------------------------------------------------------
def main():
	# config
	Config.backend = 'pyglet'
	Config.init()

	# init
	context_manager = ContextManager()
	universe.context_manager = context_manager
	resolution = Config.resolution
	context = Context("context")

	# game
	game = Game('game', context)

	# layers
	bg_layer, player_layer, fg_layer, text_layer = range(4)

	# bg
	# FIXME add bg

	# player
	player = create_player(context, player_layer)

	# fg
	fg_color = (64, 64, 64)
	height = 40
	width = 40
	UniformLayer('fg_bottom', context, fg_layer,
		(resolution[0], height), (0, resolution[1] - height),
		'top_left', fg_color, 255)

	UniformLayer('fg_right', context, fg_layer,
		(width, resolution[1]), (resolution[0] - width, 0),
		'top_left', fg_color, 255)

	UniformLayer('fg_top', context, fg_layer,
		(resolution[0], height / 2), (0, 0),
		'top_left', fg_color, 255)

	# text
	# FIXME : had a shift to center text
	score_label = Text('text', context, text_layer,
			'Scores:', 'Times New Roman', 10)
	score_label.set_location((20, 0))
	score_label.start()
	score_label = Text('text', context, text_layer,
			'??????', 'Times New Roman', 10)
	score_label.set_location((80, 0))
	score_label.start()
	game.score_sprite = score_label

	strings = ['Hit spacebar to catch squares. You earn points when its color is the same than the active one. ',
	'You loose points if colors are different and lose more points when you miss a square.']
	for i, string in enumerate(strings):
		instr = Text('text', context, text_layer,
				string, 'Times New Roman', 10)
		instr.set_location((100, 560 + i * 15))
		instr.start()


	current_color_sprite = MultiStaticSprite('current_color',
					context, text_layer)

	white_color = (255, 255, 255)
	size = np.array([20, 20])
	for i, color in enumerate(color_map):
		shift = np.array([resolution[0] - width + size[0] / 2,
							100 + i * 40])
		UniformLayer('square', context, text_layer,
			size + 2, shift - 1, 'top_left', white_color, 255)
		UniformLayer('square', context, text_layer,
			(20, 20), shift, 'top_left', color, 255)

		shift[1] = 100
		current_color_sprite.add_state_from_color('color_' + str(i),
				(20, 20), shift, 'top_left', color, 255)
	current_color_sprite.start()
	

	# collider manager
	collider_manager = CollisionManager()
	collider_manager.add_collidable_ref_sprite(player)
	# collider_manager.add_collidable_sprites(squares)

	signal = (KeyBoardDevice.constants.KEYDOWN,
			KeyBoardDevice.constants.K_SPACE)
	context.connect(signal, collider_manager,
			"on_collision", asynchronous=False)

	# context
	geometry = (0, 0, resolution[0], resolution[1])
	screen = VirtualScreenRealCoordinates('screen', geometry)
	context.add_screen(screen)
	context_manager.add_state(context)
	context_manager.set_initial_state(context)
	context_manager.start()

	# start
	event_loop = Config.get_event_loop()
	event_loop.start()

if __name__ == "__main__" : main()
