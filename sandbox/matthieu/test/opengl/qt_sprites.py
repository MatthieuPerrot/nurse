#!/usr/bin/env python

import sys
import ctypes
import numpy as np

if sys.version_info < (2, 6):
	path = [dir for dir in sys.path \
		if dir.startswith('/home/mp210984/local/lib/python2.5/')]
	path += [dir for dir in sys.path \
		if not dir.startswith('/home/mp210984/local/lib/python2.5/')]
	sys.path = path

from PyQt4 import QtCore, QtGui, QtOpenGL
from pyglet.gl import *

ESCAPE = '\033'
window = 0

class Sprite(object):
	def __init__(self, name, id=0):
		self._image = QtGui.QImage()
		self._location = np.array([0., 0., 0.])
		self._textures = (gl.GLuint * 1)()
		self._id = 0
		textures_ptr = ctypes.cast(self._textures,
				ctypes.POINTER(GLuint)) 
		glGenTextures(1, textures_ptr);
		self._image.load(name)
		self._image2 = QtOpenGL.QGLWidget.convertToGLFormat(self._image)

	def draw(self):
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glBindTexture(GL_TEXTURE_2D, self._textures[0])
		bits = ctypes.c_voidp(int(self._image2.bits()))
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
			self._image2.width(), self._image2.height(),
			0, GL_RGBA, GL_UNSIGNED_BYTE, bits)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)

		glTranslatef(*self._location)
		glPushName(self._id)
		glBegin(GL_QUADS)                   
		glTexCoord2f(0.0, 0.0)
		glVertex3f(0.0, 0.0, 0.0)          
		glTexCoord2f(1.0, 0.0)
		glVertex3f(self._image.width(), 0.0, 0.0)         
		glTexCoord2f(1.0, 1.0)
		glVertex3f(self._image.width(), self._image.height(), 0.0)          
		glTexCoord2f(0.0, 1.0)
		glVertex3f(0.0, self._image.height(), 0.0)
		glEnd()                             
		glPopName()
		glTranslatef(*(-self._location))

	def set_location(self, x, y, z):
		self._location[:] = (x, y, z)

	def shift_x(self, dx):
		self._location[0] += dx

	def shift_y(self, dy):
		self._location[1] += dy
		

#-------------------------------------------------------------------------------
class mainWidget(QtOpenGL.QGLWidget):
	def __init__(self, fmt, parent, width, height):
		QtOpenGL.QGLWidget.__init__(self, fmt, parent)
		self.setMinimumSize(width, height)
		self._width = width
		self._height = height
		self._shift_x = 0
		self._shift_y = 0
		self._bg = Sprite("../../../../data/pix/hopital.png")
		self._sprite = Sprite("../../../../data/pix/perso.png")
		self._sprite.set_location(self._width / 2, self._height / 2, 1)

	def initializeGL(self):
		glClearColor(0.0, 0.0, 0.0, 0.0)
		glClearDepth(1.0)
		glDepthFunc(GL_LESS)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_TEXTURE_2D)
		glShadeModel(GL_SMOOTH)	

		glViewport(0, 0, self._width, self._height)
		#glMatrixMode(GL_PROJECTION)
		#glLoadIdentity()
		#glOrtho(0, self._width, 0, self._height, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		

	def resizeGL(self, width, height):
		if height == 0: height = 1
		self._width = width
		self._height = height
		glViewport(0, 0, width, height)
		#glMatrixMode(GL_PROJECTION)
		#glLoadIdentity()
		#glOrtho(0, self._width, 0, self._height, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

	def paintGL(self):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		#glOrtho(0, self._width, 0, self._height, -1, 1)
		ratio = float(self._width) / self._height
		if ratio <= 1.3333:
			glOrtho(0, 640.,
			0, self._height * 480 / (self._width * 3. / 4), -1, 1)
		else:	glOrtho(0, self._width * 640 / (self._height * 4. / 3), 
						0, 480., -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()

		glEnable(GL_BLEND)
		self._bg.draw()
		self._sprite.draw()

		glDisable(GL_BLEND)
		glFlush()

	def mousePressEvent(self, event):
		x, y = event.x(), event.y()
		print "mouse event"
		print (x, y)

	def keyPressEvent(self, event):
		delta = 10
		key = event.key()
		if key in [QtCore.Qt.Key_Escape, QtCore.Qt.Key_Q]:
			sys.exit()
		elif key == QtCore.Qt.Key_Left:
			self._sprite.shift_x(-delta)
		elif key == QtCore.Qt.Key_Right:
			self._sprite.shift_x(delta)
		elif key == QtCore.Qt.Key_Up:
			self._sprite.shift_y(delta)
		elif key == QtCore.Qt.Key_Down:
			self._sprite.shift_y(-delta)
		self.updateGL()


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
