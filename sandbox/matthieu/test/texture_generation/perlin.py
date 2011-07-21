import numpy as np
import pylab as pl
from scipy.misc import pilutil

np.random.seed(3523725)

# size of look-up tables (gradient, permutation)
n = 256
# gradients
G = np.random.uniform(-1., 1., (n, 2))
# pertutation table
P = np.arange(n)
np.random.shuffle(P)


# bibref for a recent enhancement of the method
bibref = '''
@inproceedings{perlin2002improving,
		title={Improving noise},
		author={Perlin, K.},
		booktitle={ACM Transactions on Graphics (TOG)},
		volume={21},
		number={3},
		pages={681--682},
		year={2002},
		organization={ACM}
		}
'''

def tangent_vec(x, y):
	v = np.array([x - 6, y - 6])
	s = np.sqrt((v ** 2).sum())
	if s != 0: v /= s
	return v

def circular_wave_derivative(x, y, w=1.):
	'''
    f(r, theta) = cos(r) # polar coordinates
	'''
	r = np.sqrt(x ** 2 + y ** 2)
	if r:
		p = np.array([x, y])
		return -np.sin(w * r) * 2 * w * p / r
	else:	return np.array([0., 0.])

def perlin_noise(x, y):
	qx0 = np.floor(x);
	qx1 = qx0 + 1
	qy0 = np.floor(y)
	qy1 = qy0 + 1

	#Permutate values to get indices to use with the gradient look-up tables
	q00 = P[(qy0 + P[qx0 % n]) % n]
	q01 = P[(qy0 + P[qx1 % n]) % n]
	q10 = P[(qy1 + P[qx0 % n]) % n]
	q11 = P[(qy1 + P[qx1 % n]) % n]

	# Computing vectors from the four points to the input point
	tx0 = x - np.floor(x)
	ty0 = y - np.floor(y)
	tx1 = tx0 - 1
	ty1 = ty0 - 1

	# Compute the dot-product between the vectors and the gradients
	#q00, q01, q10, q11 = 0, 1, 2, 3
	#G[0] = circular_wave_derivative(qx0, qy0)
	#G[1] = circular_wave_derivative(qx1, qy0)
	#G[2] = circular_wave_derivative(qx0, qy1)
	#G[3] = circular_wave_derivative(qx1, qy1)

	#q00, q01, q10, q11 = 0, 0, 0, 0
	#G[0, 0] = 1
	#G[0, 1] = -1
	#G[0, 0] = 1
	#G[0, 1] = 0
	#G[0] = tangent_vec(x, y)
	#G[1] = tangent_vec(x + 1, y)
	#G[2] = tangent_vec(x, y + 1)
	#G[3] = tangent_vec(x + 1, y + 1)
	v00 = G[q00, 0] * tx0 + G[q00, 1] * ty0
	v01 = G[q01, 0] * tx1 + G[q01, 1] * ty0
	v10 = G[q10, 0] * tx0 + G[q10, 1] * ty1
	v11 = G[q11, 0] * tx1 + G[q11, 1] * ty1

	# bi-cubic interpolation between v_0 and v_1 at x
	# v_x = v_0 - (3x^2 - 2x^3) * (v_0 - v_1).
	# x axis interpolation
	wx = (3 - 2 * tx0) * tx0 ** 2
	#wx = (10. + (6 * tx0 - 15) * tx0) * tx0 ** 3
	v0 = v00 - wx * (v00 - v01)
	v1 = v10 - wx * (v10 - v11)
	# y axis interpolation
	wy = (3 - 2 * ty0) * ty0 ** 2
	#wy = (10. + (6 * ty0 - 15) * ty0) * ty0 ** 3
	v = v0 - wy * (v0 - v1)

	return v


def map_perlin_noise(resolution, scaling = np.array([10., 10.])):
	V = np.zeros(resolution, dtype='f')
	factor = scaling / resolution
	for x in np.arange(resolution[0]):
		xs = x * factor[0]
		for y in np.arange(resolution[1]):
			ys = y * factor[1]
			V[x, y] = perlin_noise(xs, ys)
	return V

def map_fract(resolution, scaling = np.array([10., 10.]), iter_n=5):
	scaling = np.array([10., 10.])
	V = np.zeros(resolution, dtype='f')
	for i in range(iter_n):
		s = (2 ** i)
		V += map_perlin_noise(resolution, scaling * s) / s
	return V

def map_magma(resolution, scaling = np.array([10., 10.]), iter_n=5):
	V = np.zeros(resolution, dtype='f')
	for i in range(iter_n):
		s = (2 ** i)
		P = map_perlin_noise(resolution, scaling * s)
		V += np.abs(P) / s
	return V

def map_marble(resolution, scaling = np.array([10., 10.]), iter_n=5):
	V = np.zeros(resolution, dtype='f')
	X = np.repeat(np.linspace(0, 1., resolution[1])[None], resolution[0], 0)
	for i in range(iter_n):
		s = (2 ** i)
		P = map_perlin_noise(resolution, scaling * s)
		V += np.sin(X + np.abs(P) / s)
	return V

def map_image(filename, scaling = np.array([10., 10.]), amp=1.):
	img = pilutil.imread(filename)
	img2 = img.copy()
	resolution = img.shape[0], img.shape[1]
	s = 100.
	X = np.repeat(np.linspace(0, 1. / s, resolution[1])[None],
						resolution[0], 0)
	Y = np.repeat(np.linspace(0, 1. / s, resolution[0])[None],
						resolution[1], 0).T
	P = map_perlin_noise(resolution, scaling)
	Vx = (np.sin(X + amp * np.abs(P) / s)) * (resolution[1] - 2) * s
	Vy = (np.sin(Y + amp * np.abs(P) / s)) * (resolution[0] - 2) * s
	Vx = np.minimum(np.maximum(Vx, 0), resolution[1] - 2)
	Vy = np.minimum(np.maximum(Vy, 0), resolution[0] - 2)

	for i in range(resolution[0]):
		for j in range(resolution[1]):
			vy = Vy[i, j]
			vx = Vx[i, j]
			vy0 = np.floor(vy)
			vx0 = np.floor(vx)
			wy = vy - vy0
			vy1 = vy0 + 1
			wx = vx - vx0
			vx1 = vx0 + 1
			val0 = img[vy0, vx0] * (1 - wx) + img[vy0, vx1] * wx
			val1 = img[vy1, vx0] * (1 - wx) + img[vy1, vx1] * wx
			img2[i, j] = val0 * (1 - wy) + val1 * wy
	return img2

def draw_gradients(resolution, scaling = np.array([10., 10.]), size=1):
	V = np.zeros(resolution, dtype='f')
	factor = scaling / resolution
	for x in np.arange(scaling[0]):
		xs = x * resolution[0] / scaling[0]
		for y in np.arange(scaling[1]):
			ys = y * resolution[1] / scaling[1]
			g = circular_wave_derivative(x, y) * size
			pl.plot([xs, xs + g[0]], [ys, ys + g[1]], 'b-')


resolution = np.array([200., 200.])
V = map_perlin_noise(resolution, scaling=np.array([11., 11.]))
#V = map_fract(resolution, scaling=np.array([4., 4.]), iter_n=8)
#V = map_magma(resolution, scaling=np.array([4., 4.]), iter_n=8)
#V = map_marble(resolution, scaling=np.array([10., 10.]), iter_n=8)
#V = map_image('../../../../data/pix/hopital.png', np.array([20., 20.]), amp=0.5)

pl.hot()
pl.imshow(V, interpolation='nearest')
#draw_gradients(resolution, scaling=np.array([11., 11.]), size=5.)


pl.show()
