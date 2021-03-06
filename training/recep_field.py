####################################################### README #########################################################

# This file consists of function that convolves an image with a receptive field so that imgut to the network is 
# close to the form perceived by our eyes. 

#########################################################################################################################


import numpy as np
import cv2
from parameters import param as par

def rf(img):
	"""
	画像の畳み込みを行う

	Parameters
	----------
	img : int list[28,28]
		畳み込みを行う画像のデータ。データは0~253で表現される

	Returns
	-------
	potential : float list[28,28]
		畳み込みで得られたデータ。
	"""
	sca1 =  0.625
	sca2 =  0.125
	sca3 = -0.125
	sca4 = -.5

	#Receptive field kernel
	w = [[	sca4, sca3, sca2, sca3, sca4],
	 	[	sca3, sca2, sca1, sca2, sca3],
	 	[ 	sca2, sca1,    1, sca1, sca2],
	 	[	sca3, sca2, sca1, sca2, sca3],
	 	[	sca4, sca3, sca2, sca3, sca4]]

	potential = np.zeros([par.kPixelX_, par.kPixelX_])
	ran = [-2, -1, 0, 1, 2]
	ox = 2
	oy = 2

	#Convolution
	for i in range(par.kPixelX_):
		for j in range(par.kPixelX_):
			summ = 0
			for m in ran:
				for n in ran:
					if (i+m) >= 0 and (i + m) <= par.kPixelX_ - 1 and (j + n) >= 0 and (j + n) <= par.kPixelX_ - 1:
						summ = summ + w[ox + m][oy + n] * img[i + m][j + n] / 255
			potential[i][j] = summ
	return potential		

if __name__ == '__main__':

	img = cv2.imread("mnist1/" + str(1) + ".png", 0)
	potential = rf(img)
	max_a = []
	min_a = []
	for i in potential:
		max_a.append(max(i))
		min_a.append(min(i))
	print("max" + str(max(max_a)))
	print("min" + str(min(min_a)))