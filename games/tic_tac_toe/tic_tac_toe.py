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
# - use a timer to generate squares could be better


#-------------------------------------------------------------------------------
# TODO: to be moved to sprite.py

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

	def add_state_from_sprite(self, sprite):
		self.add_state(sprite)

	def get_frame_infos(self, time):
		return self._current_state.get_frame_infos(time)


#-------------------------------------------------------------------------------
class ChangeTextOnCollision(ObjectProxy):
	def __init__(self, sprite_receiver, text_sprite, text_str):
		ObjectProxy.__init__(self, sprite_receiver)
		self._text_sprite = text_sprite
		self._text_str = text_str

	def on_collision(self, event):
		self._text_sprite.text = self._text_str


def create_bg_left(context, text, resolution):
	shift = (0, 0)
	size = (resolution[0] / 2, resolution[1])
	fsm = UniformLayer('left', context, layer=0, size=size, shift=shift,
				color=(64, 32, 32), alpha=255)
	fsm.start()
	return ChangeTextOnCollision(fsm, text, 'left')


def create_frame(context, location):
	frame = StaticSprite("frame", None, layer=2)
	frame.load_from_filename('frame.png')
	frame.start()

	cross = StaticSprite("cross", None, layer=2)
	cross.load_from_filename('cross.png')
	cross.start()

	circle = StaticSprite("circle", None, layer=2)
	circle.load_from_filename('circle.png')
	circle.start()

	signal = (Event.MOUSE, MouseDevice.constants.PRESS)
	frame.add_transition(context, signal, cross)

	multi = MultiStaticSprite("multi", context, layer=2)
	multi.add_state_from_sprite(frame)
	multi.add_state_from_sprite(cross)
	multi.add_state_from_sprite(circle)
	multi.set_initial_state(frame)
	multi.set_location(location)
	multi.start()
	
	return multi


#-------------------------------------------------------------------------------
def main():
	# config
	width = 200
	spacing = 20
	Config.backend = 'pyglet'
	Config.resolution = [width * 3 + 4 * spacing] * 2
	Config.init()

	# init
	context_manager = ContextManager()
	universe.context_manager = context_manager
	resolution = Config.resolution
	context = Context("context")

	# Game
	for i in range(3):
		for j in range(3):
			location = np.array((i * (width + spacing) + spacing,
					j * (width + spacing) + spacing))
			create_frame(context, location)

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
