#!/usr/bin/env python

import sys
import numpy as np
from PyQt4 import QtGui, QtOpenGL

path = [d for d in sys.path \
	if d.startswith('/home/mp210984/local/lib/python2.5/')]
path += [d for d in sys.path \
	if not d.startswith('/home/mp210984/local/lib/python2.5/')]
sys.path = path

import OpenGL.raw.GL.ARB.multitexture
from OpenGL.raw.GL import *
from OpenGL.raw.GL import ARB
from OpenGL.raw.GL.constants import *
from OpenGL.GL import glBegin, glEnd
#from OpenGL.GL import shaders
from OpenGL.GLUT import *
from OpenGL.GLU import *

ESCAPE = '\033'
window = 0


class Sprite(object):
	def __init__(self, name, id=0):
		self._image = QtGui.QImage()
		self._location = np.array([0., 0., 0.])
		self._textures = (GLuint * 1)()
		self._id = 0
		textures_ptr = ctypes.cast(self._textures,
				ctypes.POINTER(GLuint)) 
		glGenTextures(1, textures_ptr);
		self._image.load(name)
		self._image2 = QtOpenGL.QGLWidget.convertToGLFormat(self._image)

	def draw(self):
		glBindTexture(GL_TEXTURE_2D, self._textures[0])
		bits = ctypes.c_voidp(int(self._image2.bits()))
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
			self._image2.width(), self._image2.height(),
			0, GL_RGBA, GL_UNSIGNED_BYTE, bits)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)

		glPushMatrix()
		glLoadIdentity()
		glTranslatef(*self._location)
		s = 1./100.
		glScalef(s, s, s)
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
		glPopMatrix()

	def set_location(self, x, y, z):
		self._location[:] = (x, y, z)

	def shift_x(self, dx):
		self._location[0] += dx

	def shift_y(self, dy):
		self._location[1] += dy


bg = Sprite("../../../../data/pix/hopital.png")
bg.set_location(-3, -2, 0)
sprite = Sprite("../../../../data/pix/perso.png")
sprite.set_location(0, 0, 1)


def check_extensions():
	extensions = ctypes.cast(glGetString(GL_EXTENSIONS),
			ctypes.c_char_p).value.split(' ')
	error = False
	for ext in ['GL_ARB_shading_language_100',
		'GL_ARB_shader_objects', 'GL_ARB_vertex_shader',
		'GL_ARB_fragment_shader']:
		if ext not in extensions:
			print "error: missing extension: %s" % ext
			error = True
	#if error: sys.exit(1)


def load_pyopengl_shader(filename):
	fd = open(filename)
	code = ''.join(fd.readlines())

	GL.glEnable(GL.GL_VERTEX_PROGRAM_ARB)
	GL.glEnable(GL.GL_FRAGMENT_PROGRAM_ARB)

	v_shader = shaders.compileShader("""
	void main() {
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
	}""", shaders.GL_VERTEX_SHADER)

	f_shader = shaders.compileShader(code, shaders.GL_FRAGMENT_SHADER)
	pgm = shaders.compileProgram(v_shader, f_shader)
	shaders.glUseProgram(pgm)


def load_ctypesgl_shader(filename):
	fd = open(filename)

	v_code = """
	varying vec2 texture_coordinate; 
	void main() {
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
	gl_FrontColor = gl_BackColor = gl_Color;
	texture_coordinate = vec2(gl_MultiTexCoord0);
	}"""
	v_ccode = ctypes.byref(ctypes.c_char_p(v_code))
	f_code = ''.join(fd.readlines())
	f_ccode = ctypes.byref(ctypes.c_char_p(f_code))
	
	v_shader = ARB.shader_objects.glCreateShaderObjectARB(\
					GL_VERTEX_SHADER)
	f_shader = ARB.shader_objects.glCreateShaderObjectARB(\
					GL_FRAGMENT_SHADER)
	length = ctypes.c_int(-1)
	a = ARB.shader_objects.glShaderSourceARB.argtypes
	
	ARB.shader_objects.glShaderSourceARB.argtypes = (a[0],
		a[1], ctypes.POINTER(ctypes.c_char_p), a[3])
	ARB.shader_objects.glShaderSourceARB(v_shader, 1,
					v_ccode, ctypes.byref(length))
	ARB.shader_objects.glShaderSourceARB(f_shader, 1,
					f_ccode, ctypes.byref(length))

	ARB.shader_objects.glCompileShaderARB(v_shader)
	ARB.shader_objects.glCompileShaderARB(f_shader)

	compiled = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
	ARB.shader_objects.glGetObjectParameterivARB(f_shader,
					GL_COMPILE_STATUS, compiled)
	if not compiled[0]:
		blen = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
		slen = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
		ARB.shader_objects.glGetObjectParameterivARB(f_shader,
			GL_INFO_LOG_LENGTH , blen)
		log = ctypes.create_string_buffer(blen[0])
		if blen[0] > 1:
			ARB.shader_objects.glGetInfoLogARB(\
					f_shader, blen[0], slen, log)
			print "log = \n", log[:blen[0]]
		sys.exit(1)

	pgm = ARB.shader_objects.glCreateProgramObjectARB()
	ARB.shader_objects.glAttachObjectARB(pgm, v_shader)
	ARB.shader_objects.glAttachObjectARB(pgm, f_shader)
	ARB.shader_objects.glLinkProgramARB(pgm)

	linked = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
	ARB.shader_objects.glGetObjectParameterivARB(pgm,
			GL_LINK_STATUS, linked)
	if not linked[0]:
		print "error: link"
		sys.exit(1)
	ARB.shader_objects.glUseProgramObjectARB(pgm)	

	#ind = 0
	#my_sampler_uniform_location = \
	#	ARB.shader_objects.glGetUniformLocationARB(pgm,
	#				"sampler")
	#ARB.multitexture.glActiveTextureARB(GL_TEXTURE0 + ind)
	#ARB.shader_objects.glUniform1iARB(my_sampler_uniform_location, ind)



load_shader = load_ctypesgl_shader


def InitGL(width, height):
	check_extensions()
	load_shader('fragment.fs')
	glClearColor(0.0, 0.0, 0.0, 0.0)
	glClearDepth(1.0)
	glDepthFunc(GL_LESS)
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_TEXTURE_2D)
	glShadeModel(GL_SMOOTH)	


	glViewport(0, 0, width, height)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	w = 3.0
	h = (w * height) / width
	glOrtho(-w, w, -h, h, -1, 1)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()


def ReSizeGLScene(width, height):
	if height == 0: height = 1
	glViewport(0, 0, width, height)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	w = 3.0
	h = (w * height) / width
	glOrtho(-w, w, -h, h, -1, 1)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()


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

def DrawGLScene():
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glLoadIdentity()

	if 0:
		draw_square([-1.5, -1.5, 0.0], [1., 0., 0.], 0)
		draw_square([-1.5, 0.0, 0.0], [1., 0.5, 0.], 1)
		draw_square([-1.5, 1.5, 0.0], [1., 1., 0.], 2)
		draw_square([0.0, -1.5, 0.0], [0., 1., 0.], 3)
		draw_square([0.0, 0.0, 0.0], [0., 1., 0.5], 4)
		draw_square([0.0, 1.5, 0.0], [0., 1., 1.], 5)
		draw_square([1.5, -1.5, 0.0], [0., 0., 1.], 6)
		draw_square([1.5, 0.0, 0.0], [0.5, 0., 1.], 7)
		draw_square([1.5, 1.5, 0.0], [1., 0., 1.], 8)

	glDisable(GL_BLEND)
	bg.draw()
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	sprite.draw()

	glutSwapBuffers()


def keyPressed(*args):
	delta = 0.1
	if args[0] == ESCAPE or args[0] == 'q':
		glutDestroyWindow(window)
		sys.exit()
	if args[0] == 'k':
		sprite.shift_y(-delta)
	elif args[0] == 'i':
		sprite.shift_y(delta)
	elif args[0] == 'j':
		sprite.shift_x(-delta)
	elif args[0] == 'l':
		sprite.shift_x(delta)


def mousePressed(*args):
	button, type, x, y = args
	if type == 1: return # resolved click right now !

	glInitNames()
	# glSelectBuffer(100) # FIXME: how to fix the size ?
	buffer_size = 512
	buffer = ctypes.cast((GLint * buffer_size)(),
				ctypes.POINTER(GLuint)) 
	glSelectBuffer(buffer_size, buffer)
	glRenderMode(GL_SELECT)

	s_width = glutGet(GLUT_WINDOW_WIDTH)
	s_height = glutGet(GLUT_WINDOW_HEIGHT)

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
	DrawGLScene()

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


def main():
	global window
	glutInit("")

	glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
	#s_width, s_height = 640, 480
	s_width, s_height = 800, 600
	
	glutInitWindowSize(s_width, s_height)
	glutInitWindowPosition(0, 0)
	
	window = glutCreateWindow("title")

	glutDisplayFunc(DrawGLScene)
	glutIdleFunc(DrawGLScene)
	glutReshapeFunc(ReSizeGLScene)
	glutKeyboardFunc(keyPressed)
	glutMouseFunc(mousePressed)

	InitGL(s_width, s_height)

	glutMainLoop()

print "Hit ESC key to quit."
main()
    	
