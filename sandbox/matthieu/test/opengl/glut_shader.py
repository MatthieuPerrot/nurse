#!/usr/bin/env python

import sys
import PIL.Image
import numpy as np

path = [d for d in sys.path \
	if d.startswith('/home/mp210984/local/lib/python2.5/')]
path += [d for d in sys.path \
	if not d.startswith('/home/mp210984/local/lib/python2.5/')]
sys.path = path

import OpenGL.raw.GL.ARB.multitexture
import OpenGL.raw.GL.ARB.framebuffer_object
from OpenGL.raw.GL import *
from OpenGL.raw.GL import ARB
from OpenGL.raw.GL.constants import *
from OpenGL.GL import glBegin, glEnd
from OpenGL.GLUT import *
from OpenGL.GLU import *

ESCAPE = '\033'
window = 0

WIDTH, HEIGHT = 640, 480

pipeline_gw = None
pipeline_gaussian_h = None
pipeline_gaussian_v = None
pipeline_perlin = None

bg = sprite = None


image_backend = 'qt4'
#image_backend = 'pil'


class ImageBase(object):
	def __init__(self):
		self._raw = None

	def width(self):
		raise NotImplementedError

	def height(self):
		raise NotImplementedError

	def to_opengl(self):
		raise NotImplementedError


class ImageQtOpenGL(ImageBase):
	def __init__(self, fname):
		self._raw = QtGui.QImage()
		self._raw.load(fname)

	def width(self):
		return self._raw.width()

	def height(self):
		return self._raw.height()
	
	def to_opengl(self):
		self._raw_gl = QtOpenGL.QGLWidget.convertToGLFormat(self._raw)
		return ctypes.c_voidp(int(self._raw_gl.bits()))


class ImagePIL(ImageBase):
	def __init__(self, fname):
		self._raw = PIL.Image.open(fname)

	def width(self):
		return self._raw.size[0]

	def height(self):
		return self._raw.size[1]

	def to_opengl(self):
		self._raw_gl = np.array(np.array(self._raw)[::-1, :],
							copy='true')
		return self._raw_gl.ctypes


if image_backend == 'qt4':
	from PyQt4 import QtOpenGL, QtGui
	Image = ImageQtOpenGL

elif image_backend == 'pil':
	Image = ImagePIL

class Texture(object):
	def __init__(self):
		self._texture = ctypes.cast((GLuint * 1)(),
					ctypes.POINTER(GLuint)) 
		glGenTextures(1, self._texture)

class Texture1D(Texture):
	def __init__(self):
		Texture.__init__(self)

	def load_from_array(self, array):
		glBindTexture(GL_TEXTURE_1D, self._texture[0])
		glTexImage1D(GL_TEXTURE_1D, 0, GL_RGBA, len(array.ravel()),
					0, GL_RGBA, GL_UNSIGNED_BYTE, array)
		glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameterf(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_1D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		glBindTexture(GL_TEXTURE_1D, 0)

	def load_from_array(self, bits, width):
		glBindTexture(GL_TEXTURE_1D, self._texture[0])
		glTexImage1D(GL_TEXTURE_1D, 0, GL_RGBA, width,
					0, GL_RGBA, GL_UNSIGNED_BYTE, bits)
		glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameterf(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_1D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		glBindTexture(GL_TEXTURE_1D, 0)


class Texture2D(Texture):
	def __init__(self):
		Texture.__init__(self)

	def load_from_array(self, array):
		shape = array.shape
		glBindTexture(GL_TEXTURE_2D, self._texture[0])
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, shape[1], shape[0],
					0, GL_RGBA, GL_UNSIGNED_BYTE, array)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		glBindTexture(GL_TEXTURE_2D, 0)

	def load_from_bits(self, bits, width, height):
		glBindTexture(GL_TEXTURE_2D, self._texture[0])
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
				0, GL_RGBA, GL_UNSIGNED_BYTE, bits)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		glBindTexture(GL_TEXTURE_2D, 0)


class Sprite(Texture2D):
	def __init__(self, id=0):
		Texture2D.__init__(self)
		self._location = np.array([0., 0., 0.])
		self._id = id

	def new_empty(self, width, height, id=0):
		self._width = width
		self._height = height
		glBindTexture(GL_TEXTURE_2D, self._texture[0])
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		null = ctypes.c_voidp(0)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0,
					     GL_RGBA, GL_UNSIGNED_BYTE, null)
		glBindTexture(GL_TEXTURE_2D, 0)

	def load_from_name(self, fname):
		img = Image(fname)
		self._width = img.width()
		self._height = img.height()
		self.load_from_bits(img.to_opengl(), self._width, self._height)

	def draw(self):
		glBindTexture(GL_TEXTURE_2D, self._texture[0])
		glPushMatrix()
		glLoadIdentity()
		glTranslatef(*self._location)
		if self._id: glPushName(self._id)
		glBegin(GL_QUADS)                   
		glTexCoord2f(0.0, 0.0)
		glVertex3f(0.0, 0.0, 0.0)          
		glTexCoord2f(1.0, 0.0)
		glVertex3f(self._width, 0.0, 0.0)         
		glTexCoord2f(1.0, 1.0)
		glVertex3f(self._width, self._height, 0.0)          
		glTexCoord2f(0.0, 1.0)
		glVertex3f(0.0, self._height, 0.0)
		glEnd()                             
		if self._id: glPopName()
		glPopMatrix()
		glBindTexture(GL_TEXTURE_2D, 0)

	def set_location(self, x, y, z):
		self._location[:] = (x, y, z)

	def shift_x(self, dx):
		self._location[0] += dx

	def shift_y(self, dy):
		self._location[1] += dy


def create_fbo(s_width, s_height):
	# create texture object
	fbo_sprite = Sprite()
	fbo_sprite.new_empty(s_width, s_height)
	fbo_tex = fbo_sprite._texture

	# render buffer
	rbo = ctypes.cast((GLuint * 1)(), ctypes.POINTER(GLuint)) 
	ARB.framebuffer_object.glGenRenderbuffers(1, rbo)
	ARB.framebuffer_object.glBindRenderbuffer(\
		ARB.framebuffer_object.GL_RENDERBUFFER, rbo[0])
	ARB.framebuffer_object.glRenderbufferStorage(\
		ARB.framebuffer_object.GL_RENDERBUFFER,
		GL_DEPTH_COMPONENT, s_width, s_height)

	# frame buffer
	fbo = ctypes.cast((GLuint * 1)(), ctypes.POINTER(GLuint)) 
	ARB.framebuffer_object.glGenFramebuffers(1, fbo)
	ARB.framebuffer_object.glBindFramebuffer(\
		ARB.framebuffer_object.GL_FRAMEBUFFER, fbo[0])
	
	# attach the texture to FBO color attachment point
	ARB.framebuffer_object.glFramebufferTexture2D(\
		ARB.framebuffer_object.GL_FRAMEBUFFER,
		ARB.framebuffer_object.GL_COLOR_ATTACHMENT0,
		GL_TEXTURE_2D, fbo_tex[0], 0)

	# attach the renderbuffer to depth attachment point
	ARB.framebuffer_object.glFramebufferRenderbuffer(\
		ARB.framebuffer_object.GL_FRAMEBUFFER,
		ARB.framebuffer_object.GL_DEPTH_ATTACHMENT,
		ARB.framebuffer_object.GL_RENDERBUFFER, rbo[0]);

	# check FBO status
	status = ARB.framebuffer_object.glCheckFramebufferStatus(\
			ARB.framebuffer_object.GL_FRAMEBUFFER)
	if (status != ARB.framebuffer_object.GL_FRAMEBUFFER_COMPLETE):
		print "error: with FBO check"
		sys.exit(1)

	# switch back to window-system-provided framebuffer
	ARB.framebuffer_object.glBindFramebuffer(\
		ARB.framebuffer_object.GL_FRAMEBUFFER, 0)
	ARB.framebuffer_object.glBindRenderbuffer(\
		ARB.framebuffer_object.GL_RENDERBUFFER, 0);

	return fbo, fbo_sprite


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
	if error: sys.exit(1)


#-------------------------------------------------------------------------------
a = ARB.shader_objects.glShaderSourceARB.argtypes
ARB.shader_objects.glShaderSourceARB.argtypes = (a[0],
	a[1], ctypes.POINTER(ctypes.c_char_p), a[3])


class Shader(object):
	def _load_shader_from_filename(self, filename, shader):
		fd = open(filename)
		code = ''.join(fd.readlines())
		self._load_shader_from_str(code, shader)

	def _load_shader_from_str(self, code, shader):
		c_code = ctypes.byref(ctypes.c_char_p(code))
		length = ctypes.c_int(-1)
		ARB.shader_objects.glShaderSourceARB(shader, 1,
				c_code, ctypes.byref(length))
		ARB.shader_objects.glCompileShaderARB(shader)

		compiled = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
		ARB.shader_objects.glGetObjectParameterivARB(shader,
						GL_COMPILE_STATUS, compiled)
		if not compiled[0]:
			print "error: compiling shader:"
			blen = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
			slen = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
			ARB.shader_objects.glGetObjectParameterivARB(shader,
				GL_INFO_LOG_LENGTH , blen)
			log = ctypes.create_string_buffer(blen[0])
			if blen[0] > 1:
				ARB.shader_objects.glGetInfoLogARB(\
						shader, blen[0], slen, log)
				print log[:blen[0]]
			raise RuntimeError

	def load_default(self):
		cls = self.__class__
		self._load_shader_from_str(cls.default_code, self._id)


class VertexShader(Shader):
	default_code = """
		varying vec2 texture_coordinate; 
		void main() {
		gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
		gl_FrontColor = gl_BackColor = gl_Color;
		texture_coordinate = vec2(gl_MultiTexCoord0);
		}"""

	def __init__(self):
		Shader.__init__(self)
		self._id = ARB.shader_objects.glCreateShaderObjectARB(\
							GL_VERTEX_SHADER)

	def load_from_file(self, fname):
		self._load_shader_from_filename(fname, self._id)


class FragmentShader(Shader):
	default_code = """
		varying vec2 texture_coordinate; 
		uniform sampler2D sampler;
		void main(void) {
		gl_FragColor = texture2D(sampler, texture_coordinate.xy);
		}"""

	def __init__(self):
		Shader.__init__(self)
		self._id = ARB.shader_objects.glCreateShaderObjectARB(\
						GL_FRAGMENT_SHADER)
	def load_from_file(self, fname):
		self._load_shader_from_filename(fname, self._id)


class OpenglPipeline(object):
	def __init__(self):
		self._vertex_shader = VertexShader()
		self._fragment_shader = FragmentShader()
		self._pgm = ARB.shader_objects.glCreateProgramObjectARB()

	def load_from_file(self, v_fname=None, f_fname=None):
		if v_fname is None:
			self._vertex_shader.load_default()
		else: self._vertex_shader.load_from_file(v_fname)
		if f_fname is None:
			self._fragment_shader.load_default()
		else: self._fragment_shader.load_from_file(f_fname)
		
		ARB.shader_objects.glAttachObjectARB(self._pgm,
					self._vertex_shader._id)
		ARB.shader_objects.glAttachObjectARB(self._pgm,
					self._fragment_shader._id)
		ARB.shader_objects.glLinkProgramARB(self._pgm)

		linked = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
		ARB.shader_objects.glGetObjectParameterivARB(self._pgm,
						GL_LINK_STATUS, linked)
		if linked[0] == GL_FALSE:
			print "error: linking shaders:"
			blen = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
			slen = ctypes.cast((GLint * 1)(), ctypes.POINTER(GLint))
			ARB.shader_objects.glGetObjectParameterivARB(self._pgm,
				GL_INFO_LOG_LENGTH , blen)
			log = ctypes.create_string_buffer(blen[0])
			if blen[0] > 1:
				ARB.shader_objects.glGetInfoLogARB(\
					self._pgm, blen[0], slen, log)
				print log[:blen[0]]
			raise RuntimeError

	def select(self):
		ARB.shader_objects.glUseProgramObjectARB(self._pgm)

	@classmethod
	def select_default(cls):
		ARB.shader_objects.glUseProgramObjectARB(0)


#-------------------------------------------------------------------------------
def load_pipeline(filename):
	gl_pipeline = OpenglPipeline()
	gl_pipeline.load_from_file(None, filename)
	return gl_pipeline


fbo_sprite = None
fbo_sprite2 = None
fbo = None
fbo2 = None

def InitGL(width, height):
	global pipeline_gw, pipeline_gaussian_h, pipeline_gaussian_v
	global pipeline_perlin
	global bg, sprite
	global fbo, fbo_sprite
	global fbo2, fbo_sprite2

	check_extensions()
	bg = Sprite(id=1)
	bg.load_from_name("../../../../data/pix/hopital.png")
	bg.set_location(-3, -2, 0)
	sprite = Sprite(id=2)
	sprite.load_from_name("../../../../data/pix/perso.png")
	sprite.set_location(0, 0, 1)
	pipeline_gw = load_pipeline('fragment.fs')
	#pipeline_perlin = load_pipeline('perlin.fs')
	pipeline_perlin = load_pipeline('gaussian_horizontal.fs')
	#pipeline_gaussian_v = load_pipeline('gaussian_vertical.fs')
	#pipeline_gaussian_h = load_pipeline('gaussian_horizontal.fs')
	#pipeline_gaussian_v = load_pipeline('gaussian_vertical_center.fs')
	#pipeline_gaussian_h = load_pipeline('gaussian_horizontal_center.fs')
	glClearColor(0.0, 0.0, 0.0, 0.0)
	glClearDepth(1.0)
	glDepthFunc(GL_LESS)
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_TEXTURE_2D)
	glShadeModel(GL_SMOOTH)	
	glViewport(0, 0, width, height)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()

	s_width = glutGet(GLUT_WINDOW_WIDTH)
	s_height = glutGet(GLUT_WINDOW_HEIGHT)
	fbo, fbo_sprite = create_fbo(s_width, s_height)
	fbo2, fbo_sprite2 = create_fbo(s_width, s_height)


def ReSizeGLScene(width, height):
	if height == 0: height = 1
	glViewport(0, 0, width, height)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	ratio = float(width) / height
	if ratio <= 1.3333:
		glOrtho(0, WIDTH,
			0, height * HEIGHT / (width * 3. / 4), -1, 1)
	else:	glOrtho(0, width * WIDTH / (height * 4. / 3), 0, HEIGHT, -1, 1)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()


def DrawGLScene():
	ARB.framebuffer_object.glBindFramebuffer(\
		ARB.framebuffer_object.GL_FRAMEBUFFER, fbo[0])

	glClearColor(0., 0., 0., 0.)
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

	pipeline_gw.select()
	glDisable(GL_BLEND)
	bg.draw()
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	sprite.draw()

	#ARB.framebuffer_object.glBindFramebuffer(\
	#	ARB.framebuffer_object.GL_FRAMEBUFFER, fbo2[0])
	#glClearColor(0., 0., 0., 0.)
	#glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	#pipeline_gaussian_h.select()
	#fbo_sprite.draw()

	ARB.framebuffer_object.glBindFramebuffer(\
		ARB.framebuffer_object.GL_FRAMEBUFFER, 0)
	glClearColor(0., 0., 0., 0.)
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	#pipeline_gaussian_v.select()
	pipeline_perlin.select()
	#fbo_sprite2.draw()
	fbo_sprite.draw()
	
	glutSwapBuffers()


def keyPressed(*args):
	delta = 10.
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
	elif args[0] == 's':
		ARB.shader_objects.glUseProgramObjectARB(0)
	elif args[0] == 't':
		ARB.shader_objects.glUseProgramObjectARB(pgm)


def mousePressed(*args):
	button, type, x, y = args
	if type == 1: return # resolved click right now !

	glInitNames()
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

	# screen coordinates
	ratio = float(s_width) / s_height
	if ratio <= 1.3333:
		s_left, s_right = 0, WIDTH
		s_bottom, s_top = 0, s_height * HEIGHT / (s_width * 3. / 4)
	else:
		s_left, s_right = 0, s_width * WIDTH / (s_height * 4. / 3)
		s_bottom, s_top = 0, HEIGHT
	s_width_ratio = float(s_right - s_left) / s_width
	s_height_ratio = float(s_top - s_bottom) / s_height
	glOrtho(v_left * s_width_ratio,
		(v_left + v_width) * s_width_ratio,
		v_bottom * s_height_ratio,
		(v_bottom + v_height) * s_height_ratio, -1, 1)

	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()

	# draw scene
	DrawGLScene()

	# analyse select buffer
	n = glRenderMode(GL_RENDER)
	argmin = -1
	min = np.inf
	for i in range(n):
		min_depth = buffer[3 * i + 1]
		max_depth = buffer[3 * i + 2]
		name = buffer[3 * i + 3]
		if min_depth < min:
			min = min_depth
			argmin = name

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
	
	glutInitWindowSize(WIDTH, HEIGHT)
	glutInitWindowPosition(0, 0)
	
	window = glutCreateWindow("title")

	glutDisplayFunc(DrawGLScene)
	glutIdleFunc(DrawGLScene)
	glutReshapeFunc(ReSizeGLScene)
	glutKeyboardFunc(keyPressed)
	glutMouseFunc(mousePressed)

	InitGL(WIDTH, HEIGHT)

	glutMainLoop()

print "Hit ESC key to quit."
main()
    	