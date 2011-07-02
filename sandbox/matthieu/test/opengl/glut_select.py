#!/usr/bin/env python

import sys
path = [dir for dir in sys.path \
	if dir.startswith('/home/mp210984/local/lib/python2.5/')]
path += [dir for dir in sys.path \
	if not dir.startswith('/home/mp210984/local/lib/python2.5/')]
sys.path = path

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
# from pyglet.gl import *

ESCAPE = '\033'
window = 0

def InitGL(width, height):
	glClearColor(0.0, 0.0, 0.0, 0.0)
	glClearDepth(1.0)
	glDepthFunc(GL_LESS)
	glEnable(GL_DEPTH_TEST)
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

	draw_square([-1.5, -1.5, 0.0], [1., 0., 0.], 0)
	draw_square([-1.5, 0.0, 0.0], [1., 0.5, 0.], 1)
	draw_square([-1.5, 1.5, 0.0], [1., 1., 0.], 2)
	draw_square([0.0, -1.5, 0.0], [0., 1., 0.], 3)
	draw_square([0.0, 0.0, 0.0], [0., 1., 0.5], 4)
	draw_square([0.0, 1.5, 0.0], [0., 1., 1.], 5)
	draw_square([1.5, -1.5, 0.0], [0., 0., 1.], 6)
	draw_square([1.5, 0.0, 0.0], [0.5, 0., 1.], 7)
	draw_square([1.5, 1.5, 0.0], [1., 0., 1.], 8)
	glutSwapBuffers()


def keyPressed(*args):
	if args[0] == ESCAPE or args[0] == 'q':
		glutDestroyWindow(window)
		sys.exit()


def mousePressed(*args):
	button, type, x, y = args
	if type == 1: return # resolved click right now !

	glInitNames()
	glSelectBuffer(100) # FIXME: how to fix the size ?
	glRenderMode(GL_SELECT)

	# screen # FIXME: this info must be global ?
	#                 get it from opengl ?
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
	buffer = glRenderMode(GL_RENDER)
	for hit_record in buffer:
		min_depth, max_depth, names = hit_record
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
	s_width, s_height = 640, 480
	
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
    	
