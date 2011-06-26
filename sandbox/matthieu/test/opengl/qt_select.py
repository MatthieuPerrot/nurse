#!/usr/bin/env python

import sys
import ctypes

if sys.version_info < (2, 6):
	path = [dir for dir in sys.path \
		if dir.startswith('/home/mp210984/local/lib/python2.5/')]
	path += [dir for dir in sys.path \
		if not dir.startswith('/home/mp210984/local/lib/python2.5/')]
	sys.path = path

from PyQt4 import QtCore, QtGui, QtOpenGL
from PyQt4.QtOpenGL import *

# from OpenGL.GL import *
from pyglet.gl import *

ESCAPE = '\033'
window = 0

def draw_square(location, color, id=0):
	glTranslatef(location[0], location[1], location[2])
	glColor3f(*color)
	glPushName(id)
	glBegin(GL_QUADS)                   
	glVertex3f(-0.5, 0.5, 0.0)          
	glVertex3f(0.5, 0.5, 0.0)           
	glVertex3f(0.5, -0.5, 0.0)          
	glVertex3f(-0.5, -0.5, 0.0)         
	glEnd()                             
	glPopName()
	glTranslatef(-location[0], -location[1], -location[2])


#-------------------------------------------------------------------------------
class mainWidget(QtOpenGL.QGLWidget):
	def __init__(self, fmt, parent, width, height):
		QtOpenGL.QGLWidget.__init__(self, fmt, parent)
		self.setMinimumSize(width, height)
		self._width = width
		self._height = height

	def initializeGL(self):
		glClearColor(0.0, 0.0, 0.0, 0.0)
		glClearDepth(1.0)
		glDepthFunc(GL_LESS)
		glEnable(GL_DEPTH_TEST)
		glShadeModel(GL_SMOOTH)	

		glViewport(0, 0, self._width, self._height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		w = 3.0
		h = (w * self._height) / self._width
		glOrtho(-w, w, -h, h, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

	def resizeGL(self, width, height):
		if height == 0: height = 1
		glViewport(0, 0, width, height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		w = 3.0
		h = (w * height) / width
		glOrtho(-w, w, -h, h, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

	def paintGL(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()

		draw_square([-1.5, -1.5, 0.0], [1., 0., 0.], 0)
		draw_square([-1.5, 0.0, 0.0], [1., 0.5, 0.], 1)
		draw_square([-1.5, 1.5, 0.0], [1., 1., 0.], 2)
		draw_square([0.0, -1.5, 0.0], [0., 1., 0.], 3)
		draw_square([0.0, 0.0, 0.0], [0., 1., 0.5], 4)
		draw_square([0.0, 1.5, 0.0], [0., 1., 1.], 5)
		draw_square([1.5, -1.5, 0.0], [0., 0., 1.], 6)
		draw_square([1.5, 0.0, 0.0], [0.5, 0., 1.], 7)
		draw_square([1.5, 1.5, 0.0], [1., 0., 1.], 8)
		glFlush()

	def mousePressEvent(self, event):
		x, y = event.x(), event.y()

		glInitNames()
		# glSelectBuffer(100) # FIXME: how to fix the size ?
		buffer_size = 512
		buffer = ctypes.cast((gl.GLint * buffer_size)(),
					ctypes.POINTER(GLuint)) 
		glSelectBuffer(buffer_size, buffer)
		glRenderMode(GL_SELECT)

		# screen # FIXME: this info must be global ?
		#                 get it from opengl ?
		s_width = self.width()
		s_height = self.height()

		# viewport: 1x1
		glPushMatrix()
		v_left = x
		v_bottom = s_height - 1 - y
		v_width, v_height = 1, 1
		glViewport(v_left, v_bottom, v_width, v_height)

		# ortho
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		w = 3.0
		h = (w * s_height) / s_width

		# screen coordinates
		s_left, s_right = -w, w
		s_bottom, s_top = -h, h
		s_width_ratio = float(s_right - s_left) / s_width
		s_height_ratio = float(s_top - s_bottom) / s_height
		glOrtho(-w + v_left * s_width_ratio,
			-w + (v_left + v_width) * s_width_ratio,
			-h + v_bottom * s_height_ratio,
			-h + (v_bottom + v_height) * s_height_ratio, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

		# draw scene
		self.paintGL()

		# analyse select buffer
		n = glRenderMode(GL_RENDER)
		for i in range(n):
			min_depth = buffer[3 * i + 1]
			max_depth = buffer[3 * i + 2]
			names = buffer[3 * i + 3]
			print "->", names 

		# retrieve the defaut projection / view
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		glViewport(0, 0, s_width, s_height)

	def keyPressEvent(self, event):
		if event.key() in [QtCore.Qt.Key_Escape, QtCore.Qt.Key_Q]:
			sys.exit()
		elif event.key() == QtCore.Qt.Key_S:
			pix = self.renderPixmap(self.width(), self.height())
			pix.save('screenshot.png', 'png')


class Window(QtGui.QMainWindow):
	def __init__(self):
		QtGui.QMainWindow.__init__(self)
		fmt = QtOpenGL.QGLFormat()
		fmt.setDoubleBuffer(True)
		widget = mainWidget(fmt, self, 640, 480)
		# enable keyPressEvent
		widget.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.setCentralWidget(widget)
		

def main():
	app = QtGui.QApplication(['gl widget'])
	window = Window()
	window.show()
	app.exec_()

print "Hit ESC key to quit."
main()
