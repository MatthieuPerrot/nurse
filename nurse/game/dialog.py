from nurse.base import Object
from nurse.events import Event
from nurse.backends import KeyBoardDevice
from nurse.state_machine import State
from nurse.config import Config
from nurse.sprite import Dialog, UniformLayer, Text, StaticSprite
from nurse.context import Context
import numpy as np

class DialogState(State):
	
	def _parse_lines(self):
		import string
		words = string.split(self._text, ' ')
		current_text = words[0]
		lines = [ current_text ]	
		
		for word in words[1:] :
			current_text = string.join([current_text, word], ' ')
			repr = Config.get_graphic_engine().load_text(\
				current_text, self.font, self.font_size,
				0,0)
			if repr.content_width > self.max_width:
				current_text = word
				lines.append(word)
			else:
				lines[-1] = current_text
		return lines
			
	
	def __init__(self, name='text', text='...', font='Times New Roman',
			font_size=20, text_area=None, perso=None, char_per_sec=5.,
			typing_machine_mode=True):
		State.__init__(self,name)
		self._text = text
		self.font = font
		self.font_size = font_size
		self.max_width = text_area[1][0]
		self._lines = self._parse_lines()
		self.max_lines = 5
		self.perso = perso
		if typing_machine_mode:
			self.char_delay = 1000. / char_per_sec
		else:	self.char_delay = 0
		self.typing_machine_mode = typing_machine_mode
		self.list_backend_repr = []
		self._current_time = 0
		self._current_indice = 0
		self._current_text = ''
		self._current_line = 0
		self._current_height = 0
		self._has_terminated = False
	
	def _update_chars(self, n):
		max_ind = len(self._lines[self._current_line])
		ind = self._current_indice
		if ind == max_ind: 
			if self._current_line == len(self._lines) - 1:
				if not self._has_terminated :
					self._has_terminated = True
					self.emit('dialog_state_terminated')
				return
			ind = 0
			self._current_text = ''
			self._current_line += 1
			self._current_height += (self._current_line % self.max_lines) * self.list_backend_repr[-1].content_height

		new_ind = ind + n
		if new_ind > max_ind: new_ind = max_ind
		new_text = self._lines[self._current_line][ind:new_ind]
		self._current_text += new_text
		self._current_indice = new_ind
		anchor_x, anchor_y = self._fsm.get_location()
		repr = Config.get_graphic_engine().load_text(\
				self._current_text, self.font, self.font_size,
				anchor_x, anchor_y + self._current_height)
		if len(self.list_backend_repr) == 0:
			self.list_backend_repr.append(repr)
		else:	self.list_backend_repr[-1] = repr
		if len(self._current_text) == len(self._lines[self._current_line]):
			self.list_backend_repr.append(repr)
				
	def update(self, dt):
		self._current_time += dt	
		if self._current_time >= self.char_delay:
			if self.char_delay == 0:
				n = len(self._text)
			else:	n = int(self._current_time / self.char_delay)
			self._update_chars(n)
			self._current_time -= n * self.char_delay

	def on_entered(self):
		self.emit('dialog_state_started')

class DialogListener(Object):
	def __init__(self):
		Object.__init__(self, 'default_name')
		self.current_state = 0

	def on_dialog_start(self, event):
		signal = (Event.KEYBOARD, (KeyBoardDevice.constants.KEYDOWN,
					KeyBoardDevice.constants.K_SPACE))
		self.context.set_visible (self.next, False)
		self.context.connect(signal, self, 'on_fast_forward')

	def on_dialog_finish(self, event):
		if self.current_state == len(self.states) - 1:
			return
		signal = (Event.KEYBOARD, (KeyBoardDevice.constants.KEYDOWN,
					KeyBoardDevice.constants.K_SPACE))
		self.context.disconnect(signal, self, 'on_fast_forward')
		self.states[self.current_state].add_transition(self.context,
				signal, self.states[self.current_state + 1])
		self.current_state += 1
		try:
			self.context.set_visible (self.next, True)
		except NameError:
			pass

	def on_fast_forward(self, event):
		self.states[self.current_state].typing_machine_mode = False
		self.states[self.current_state].char_delay = 0
		

class DialogContext(Context):
	 def __init__(self, name, msg, text_area_mode="auto", is_visible=True, is_active=True,
			 _is_receiving_events=True):
		Context.__init__(self, name, is_visible, is_active, _is_receiving_events)

		screen = Config.get_graphic_engine().get_screen()
		ws, hs = screen.get_width(), screen.get_height()
		uniform = UniformLayer('dark', self, layer=0,
					color=(0, 0, 0), alpha=128)
		uniform.start()
	
		dialog_bg = StaticSprite('dialog_bg', self, layer=4)
		dialog_bg.load_from_filename(imgname='dialog.png',
					center_location='top_left')
		_, _, width, height = dialog_bg.bounding_box()
		x, y = (ws - width) / 2., hs - height 
		area = (x, y), (width, height)

		dialog_bg.set_location([x,y])
		dialog_bg.start()

		if text_area_mode is "color_area":
			black_area = dialog_bg.get_frame_infos()[0].find_color_area(color='black')
			text_area = ((x+black_area[0][0], y+black_area[0][1]), (black_area[1][0]-black_area[0][0], black_area[1][1]-black_area[0][1]))
		elif text_area_mode is "auto":
			text_area = (area[0][0] + 100, area[0][1] + 30), (area[1][0] - 130, area[1][1] + 60) 

		dialog = Dialog('dialog', self, layer=4)
		
		states = []
		for i, (perso, txt, typing_machine_mode) in enumerate(msg):
			state = DialogState('state_%d' % i, txt, 'Times New Roman', 13,
					text_area, perso, 20., typing_machine_mode)
			dialog.add_state(state)
			states.append(state)

		dialog.set_initial_state(states[0])
		dialog.set_location(text_area[0])
		dialog.start()
		next = Text('text', self, 4, '...', 'Times New Roman', 40)
		next.set_location([x+width-80,y+height-80])
		next.start()	
		self.set_visible(next, False)
		sprite = StaticSprite('sprite', self, layer=4)
		sprite.load_from_filename(imgname='perso.png')
		sprite.set_location([x + 60, y + height / 2])
		sprite.start() # FIXME
		dialog.dl = DialogListener()
		dialog.dl.states = states
		dialog.dl.context = self
		dialog.dl.next = next

		signal = (Event.KEYBOARD, (KeyBoardDevice.constants.KEYDOWN,
			KeyBoardDevice.constants.K_SPACE))
		self.connect(signal, dialog.dl, 'on_fast_forward')
		for state in states:
			state.connect('dialog_state_terminated', dialog.dl, 'on_dialog_finish')
			state.connect('dialog_state_started', dialog.dl, 'on_dialog_start')


