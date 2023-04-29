import numpy as np
import copy
import pickle
import cv2
import time
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
# from pyvistaqt import BackgroundPlotter
# import pyvista as pv
import struct
import json
import tifffile

#TODO: figure out step size generally (including non square images)

#point annotation object
class Point(object):
	def __init__(self, x, y, colorIdx=0, size=3):
		self.colorIdx = colorIdx
		color = getColor(colorIdx)
		self.x = x
		self.y = y
	 
		self.color = color
		self.size = size
	
	def __add__(self, other):
		return Point(self.x+other.x, self.y+other.y)
	
	def __sub__(self, other):
		return Point(self.x-other.x, self.y-other.y)
	
	def __mul__(self, scalar):
		return Point(self.x*scalar, self.y*scalar)

	#subscripting
	def __getitem__(self, key):
		if key == 0:
			return self.x
		elif key == 1:
			return self.y
		else:
			raise IndexError("Point index out of range")
	
	def __setitem__(self, key, value):
		if key == 0:
			self.x = value
		elif key == 1:
			self.y = value
		else:
			raise IndexError("Point index out of range")


	def show(self, arr, size, node, x0,y0,scale):
		if node:
			size *= 2
		#draws point to copy of the current frame
		x = int((self.x*arr.shape[1])/scale)-x0
		y = int((self.y*arr.shape[0])/scale)-y0
		cv2.circle(arr, (x,y), size, self.color, -1)
	
	def updateColor(self, colorIdx):
		self.colorIdx = colorIdx
		self.color = getColor(colorIdx)

def load_tif(path):
	tif = []
	for filename in os.listdir(path):
		# check if digit in filename
		if (filename.endswith(".tif") or filename.endswith(".png")) and any(
			char.isdigit() for char in filename
		):
			tif.append(path + "/" + filename)
	# sort the list by the number in the filename
	tif.sort(key=lambda f: int("".join(filter(str.isdigit, f))))
	# tif = sorted(tif)
	print(tif)
	return tif
class Volpkg(object):
	def __init__(self, folder, sessionId0):
		if folder.endswith(".volpkg") or os.path.exists(folder+".volpkg"):
			self.basepath = folder if folder.endswith(".volpkg") else folder+".volpkg"
			#get all volumes in the folder
			volumes = os.listdir(f"{self.basepath}/volumes")
			#remove hidden files
			volumes = [i for i in volumes if not i.startswith(".")]
			volume = volumes[0] #should switch to a dialog to select volume
			self.volume = volume
			self.tifstack = load_tif(f"{self.basepath}/volumes/{volume}")
			self.segmentations = None #TODO
			#pass
		else:
			self.basepath = folder+".volpkg"
			#make volpkg folder
			os.mkdir(self.basepath)
			self.tifstack = load_tif(folder)
			#copy tifstack to volumes folder
			os.mkdir(f"{self.basepath}/volumes")
			#volume name
			os.mkdir(f"{self.basepath}/volumes/{sessionId0}")
			for i, tif in enumerate(self.tifstack):
				#use cp command
				os.system(f"cp {tif} {self.basepath}/volumes/{sessionId0}/{i}.tif")
			
			

			self.segmentations = None
			
	def saveVCPS(self, file_name, annotations, imshape, ordered=True, point_type='float', encoding='utf-8'):
		annotations = self.stripAnnoatation(annotations, imshape)
		#check if paths directory exists
		if not os.path.exists(self.basepath+"/paths"):
			os.mkdir(self.basepath+"/paths")
		#check if file_name directory exists
		if not os.path.exists(self.basepath+"/paths/"+file_name):
			os.mkdir(self.basepath+"/paths/"+file_name)
		file_path = f"{self.basepath}/paths/{file_name}/pointset.vcps"
		height, width, dim = annotations.shape
		header = {
			'width': width,
			'height': height,
			'dim': dim,
			'ordered': 'true' if ordered else 'false',
			'type': point_type,
			'version': '1'
		}

		with open(file_path, 'wb') as file:
			# Write header
			for key, value in header.items():
				file.write(f"{key}: {value}\n".encode(encoding))
			file.write("<>\n".encode(encoding))

			# Write data
			format_str = 'd' if point_type == 'double' else 'f'
			for i in range(height):
				for j in range(width):
					point = annotations[i, j]
					for value in point:
						file.write(struct.pack(format_str, value))
		
		#write meta.json {"name":"20230426114804","type":"seg","uuid":"20230426114804","vcps":"pointset.vcps","volume":"20230210143520"}
		meta = {
			"name": file_name,
			"type": "seg",
			"uuid": file_name,
			"vcps": "pointset.vcps",
			"volume": self.volume
		}
		with open(f"{self.basepath}/paths/{file_name}/meta.json", 'w') as file:
			json.dump(meta, file)

		


	def stripAnnoatation(self, annotationsRaw, imshape):
		interpolated = [i for i in annotationsRaw if len(i) > 0]

		H = len(interpolated)
		W = max([len(i) for i in interpolated])
		im = np.zeros((H, W*2, 3), dtype=np.float64)
		#replace all 0's with nan
		im[im == 0] = np.nan

		cy = H//2

		Center = interpolated[cy][len(interpolated[cy])//2]
		for i in range(len(interpolated)):
			if len(interpolated[i]) > 0:
				#find the center of the slice by finding the point with min distance from true center
				center = interpolated[i][0]
				centerIndex = 0
				for jindex, j in enumerate(interpolated[i]):
					if np.sqrt((j.x-Center.x)**2 + (j.y-Center.y)**2) < np.sqrt((center.x-Center.x)**2 + (center.y-Center.y)**2):
						center = j
						centerIndex = jindex
				#populate the image with the interpolated to the left and right of the center
				
				for jindex, j in enumerate(interpolated[i]):

					x,y = interpolated[i][jindex].x, interpolated[i][jindex].y
					x *= imshape[0]
					y *= imshape[1]
			
					
					im[i, W - (centerIndex-jindex)] = [x,y,i]
			
	
			
		return im



class Loader:
	def __init__(self, tifStack):
		self.mappings = []
		self.tifStack = tifStack
		for f in sorted(tifStack):
			self.mappings.append(tifffile.memmap(f, mode='r'))

	#overload index operator
	def __getitem__(self, slice):
		s = slice[0]
		return self.mappings[s][slice[1:]]

	def getFrame(self, f):
		return self[f,:,:]




#under development
# class VoxelViewer(QMainWindow):

# 	def __init__(self, parent=None, data=None):
# 		QMainWindow.__init__(self, parent)

# 		# Create the main window
# 		self.setWindowTitle("Voxel Viewer")
# 		self.resize(800, 600)

# 		# Create a PyVista background plotter
# 		self.plotter = BackgroundPlotter()
# 		self.plotter.allow_quit_keypress = False
# 		self.setCentralWidget(self.plotter.app_window)
# 		print(data)
# 		data = data
# 		print(data)
# 		#quit()
# 		# Convert voxel data to mesh and reduce resolution if needed
# 		self.voxel_mesh = self.create_mesh(data, min_value=0.5)
# 		self.plotter.add_mesh(self.voxel_mesh, opacity=0.5)

# 	def create_mesh(self, data, min_value=1e-5):
# 		# Convert the voxel data to a 3D volume
# 		volume = pv.wrap(data)

# 		# Create a mesh by thresholding the volume based on the min_value
# 		mesh = volume.threshold(value=(min_value, data.max()))

# 		# Convert the UnstructuredGrid to a PolyData object, with brightness val
# 		polydata = mesh.extract_geometry()

# 		return polydata



def getColor(colorIdx):
	colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
	return colors[colorIdx]


def interpolatePoints(points, imShape):
	#use linear interpolation to interpolate between points in the annotation list
	pixels = [[i.x*imShape[1], i.y*imShape[0]] for i in points]
	interp = []
	for i in range(len(pixels)-1):
		#find the distance between the two points
		dist = np.sqrt((pixels[i+1][0]-pixels[i][0])**2 + (pixels[i+1][1]-pixels[i][1])**2)
		#find the number of pixels to interpolate between them
		n = int(dist)#TODO
		if n == 0:
			continue
		#find the step size
		step = 1/n
		#interpolate between the two pixels
		for j in np.arange(0,n,1):
			x = pixels[i][0] + (pixels[i+1][0]-pixels[i][0])*j*step
			y = pixels[i][1] + (pixels[i+1][1]-pixels[i][1])*j*step
			interp.append(Point(x/imShape[1], y/imShape[0],0,2))
	return interp



#get the coordinates of the mouse relative to the image frame
def getImFrameCoords(app, pos):
	pos = getUnscaledRelCoords(app, pos)
	image_rect = app.label.pixmap().rect()
	x = pos.x()/image_rect.width()
	y = pos.y()/image_rect.height()
	return x,y

#get the coordinates of the mouse relative to the full image
def getRelCoords(app, pos):
	pos = getUnscaledRelCoords(app, pos)
	image_rect = app.label.pixmap().rect()
	x = pos.x()*app.image.scale+app.image.offset[1]/app.pixelSize1
	y = pos.y()*app.image.scale+app.image.offset[0]/app.pixelSize0
	x /= image_rect.width()
	y /= image_rect.height()
	return x,y

#get the coordinates of the mouse, shifting the origin to the top left corner of the image
def getUnscaledRelCoords(app, pos):
	label_pos = app.label.pos()
	image_rect = app.label.pixmap().rect()
	image_pos = QPoint(int(label_pos.x() + (app.label.width() - image_rect.width()) / 2),int(label_pos.y() + (app.label.height() - image_rect.height()) / 2))
	#get pos relative to image 
	pos = pos - image_pos
	return pos

#get pixel coordinates from relative coordinates
def getPixelCoords(imShape, x, y):
	x = int(x*imShape[1])
	y = int(y*imShape[0])
	return x,y


	

def autoSave(app, file_name=None):
	if file_name == None:
		file_name = app.sessionId0
	#save annotations to file
	with open(f"{file_name}.pkl", 'wb') as f:
		pickle.dump(app.image.annotations, f)
		pickle.dump(app.image.interpolated, f)
		pickle.dump(app.image.img.shape, f)
	#save annotations to vcp file
	app.volpkg.saveVCPS(app.sessionId0, app.image.interpolated, app.image.img.shape)