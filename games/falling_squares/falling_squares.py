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


#-------------------------------------------------------------------------------
class Game(Object):
	def __init__(self, name='game'):
		Object.__init__(self, name)
	pass # FIXME

game = Game()

#-------------------------------------------------------------------------------
color_map = np.random.randint(0, 255, (10, 3))

def random_square_generator(context, game):
	size = (20, 20)
	shift = (np.random.randint(game.resolution[0] - size[0]), 0)
	color = color_map[np.random.randint(len(color_map))]
	fsm = UniformLayer('square', context, layer=0, size=size, shift=shift,
			center_location='centered', color=color, alpha=255)
	fsm.start()
	return ChangeScoreOnCollision(fsm, game)


#-------------------------------------------------------------------------------
class ChangeScoreOnCollision(ObjectProxy):
	def __init__(self, receiver, game):
		ObjectProxy.__init__(self, receiver)
		self._game = game

	def on_collision(self, event):
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

	strings = ['Hit spacebar to catch squares. You earn points when its color is the same than the active one. ',
	'You loose points if colors are different and lose more points when you miss a square.']
	for i, str in enumerate(strings):
		instr = Text('text', context, text_layer,
				str, 'Times New Roman', 10)
		instr.set_location((100, 560 + i * 15))
		instr.start()

	white_color = (255, 255, 255)
	size = np.array([20, 20])
	for i, color in enumerate(color_map):
		shift = np.array([resolution[0] - width + size[0] / 2,
							100 + i * 40])
		UniformLayer('square', context, text_layer,
			size + 2, shift - 1, 'top_left', white_color, 255)
		UniformLayer('square', context, text_layer,
			(20, 20), shift, 'top_left', color, 255)
	

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
