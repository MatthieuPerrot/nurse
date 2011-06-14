#FIXME : must delayed imports
import nurse.backends.sdl_backend
import nurse.backends.pyglet_backend
from nurse.backends.sdl_backend import SdlGraphicEngine, SdlEventLoop, \
					SdlKeyBoardDevice, SdlMouseDevice
from nurse.backends.pyglet_backend import PygletGraphicEngine, PygletEventLoop,\
					PygletKeyBoardDevice, PygletMouseDevice

import pygame # FIXME: remove



class Config(object):
	# config data values
	backend = 'sdl'
	resolution = 800, 600
	caption = 'nurse game engine'
	sdl_flags = pygame.constants.DOUBLEBUF | pygame.constants.HWSURFACE | \
				pygame.constants.HWACCEL # | pygame.FULLSCREEN  
	fps = 60

	# internal data
	default_context = None
	event_loop_backend_map = {'sdl' : SdlEventLoop,
				'pyglet' : PygletEventLoop}
	keyboard_backend_map = {'sdl' : SdlKeyBoardDevice,
				'pyglet' : PygletKeyBoardDevice}
	mouse_backend_map = {'sdl' : SdlMouseDevice,
				'pyglet' : PygletMouseDevice}
	graphic_backend_instance =  None
	event_loop_backend_instance = None
	keyboard_backend_instance = None
	mouse_backend_instance = None

	@classmethod
	def init(cls):
		# to avoid an import loop
		from context import Context
		cls.default_context = Context('default')
		cls.graphic_backend_map = {\
			'sdl' : (SdlGraphicEngine,
				(cls.resolution, cls.sdl_flags)),
			'pyglet' : (PygletGraphicEngine,
				(cls.resolution, cls.caption))}

		# instanciate backends
		Config.get_graphic_engine()
		Config.get_event_loop()
		Config.get_keyboard_device()
		Config.get_mouse_device()

	@classmethod
	def read_config_file(cls):
		pass # FIXME : read from file (configobj ?)

	@classmethod
	def get_default_context(cls):
		return Config.default_context

	@classmethod
	def get_graphic_engine(cls):
		if cls.graphic_backend_instance is None:
			c, args = cls.graphic_backend_map[cls.backend]
			cls.graphic_backend_instance = c(*args)
		return cls.graphic_backend_instance

	@classmethod
	def get_event_loop(cls):
		if cls.event_loop_backend_instance is None:
			c = cls.event_loop_backend_map[cls.backend]
			cls.event_loop_backend_instance = c(Config.fps)
			if cls.backend == 'pyglet':
				gfx = cls.get_graphic_engine()
				win = gfx.get_screen().get_raw_image()
				instance = cls.event_loop_backend_instance
				instance.on_draw = win.event(instance.on_draw)
		return cls.event_loop_backend_instance

	@classmethod
	def get_keyboard_device(cls):
		if cls.keyboard_backend_instance is None:
			c = cls.keyboard_backend_map[cls.backend]
			cls.keyboard_backend_instance = c()
			if cls.backend == 'pyglet':
				gfx = cls.get_graphic_engine()
				win = gfx.get_screen().get_raw_image()
				instance = cls.keyboard_backend_instance
				instance.attach_window(win)
		return cls.keyboard_backend_instance

	@classmethod
	def get_mouse_device(cls):
		if cls.mouse_backend_instance is None:
			c = cls.mouse_backend_map[cls.backend]
			cls.mouse_backend_instance = c()
			if cls.backend == 'pyglet':
				gfx = cls.get_graphic_engine()
				win = gfx.get_screen().get_raw_image()
				instance = cls.mouse_backend_instance
				instance.attach_window(win)
		return cls.mouse_backend_instance
