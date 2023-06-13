import numpy as np
import copy
import pickle
import cv2
import time
import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import trimesh
import json
import struct
# from matplotlib.tri._triangulation import Triangulation

# import matplotlib.pyplot as plt


#point annotation object
class Point(object):
	def __init__(self, x, y, colorIdx=0, size=3):
		self.colorIdx = colorIdx
		color = getColor(colorIdx)
		# These points are generated using getRelCoords, meaning
		# that x and y are measured as fractions of the whole image from
		# the upper left corner (0, 0) of the image.
		self.x = x
		self.y = y
	 
		self.color = color
		self.size = size
	
	def __repr__(self):
		return f"X {self.x} Y {self.y} S {self.size}"

	def __add__(self, other):
		return Point(self.x+other.x, self.y+other.y)
	
	def __sub__(self, other):
		return Point(self.x-other.x, self.y-other.y)
	
	def __mul__(self, scalar):
		return Point(self.x*scalar, self.y*scalar)

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

	def show(self, arr, img_shape, size, node, offset, scale):
		x0, y0 = offset
		if node:
			size *= 2
		#draws point to copy of the current frame
		local_x = int(self.x * img_shape[1]) - y0 
		local_y = int(self.y * img_shape[0]) - x0
		cv2.circle(arr, (local_x, local_y), size, self.color, -1)
	
	def updateColor(self, colorIdx):
		self.colorIdx = colorIdx
		self.color = getColor(colorIdx)




def getColor(colorIdx):
	colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
	return colors[colorIdx]



def adjust_color(image, shadows, midtones, highlights):
	# Normalize input values to a range between 0 and 1
	shadows = (shadows-50) / 50
	midtones = (midtones-50) / 50
	highlights = (highlights-50) / 50

	# Convert the image to a floating-point format
	image_float = image.astype(np.float32) / 255.0

	# Adjust shadows
	image_float = np.where(image_float < 0.5, image_float * (1 + shadows), image_float)

	# Adjust midtones (gamma correction)
	image_float = np.power(image_float, 1 / (1 + midtones))

	# Adjust highlights
	image_float = np.where(image_float > 0.5, image_float * (1 - highlights) + highlights, image_float)

	# Clip the values to the range [0, 1] and convert back to the original data type
	adjusted_image = np.clip(image_float * 255, 0, 255).astype(np.uint8)

	return adjusted_image


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


class ImageLabel(QLabel):
	def __init__(self, pmap, app):
		super().__init__()
		self.original_pixmap = pmap
		self.setPixmap(self.original_pixmap)
		self.app = app

	def resizeEvent(self, event):
		self.update()
	def update(self):
		pmap = self.app.image.getImg(self.app._frame_index)
		if pmap.isNull(): 
			return

		scaled_pixmap = pmap.scaled(self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
		self.setPixmap(scaled_pixmap)


def getImFrameCoords(app, pos):
	"""Returns the coordinates of the mouse reported as a fraction
	of the way through the image frame.
	"""
	pos = getUnscaledRelCoords(app, pos)
	image_rect = app.label.pixmap().rect()
	x = pos.x() / image_rect.width()
	y = pos.y() / image_rect.height()
	return x,y

#get the coordinates of the mouse relative to the full image
# def getRelCoords(app, pos):
# 	"""Returns the coordinates of the mouse reported as a fraction
# 	of the way through the full image.

# 	Note that the full image may not be currently displayed, so we have
# 	to adjust the location appropriately.
# 	"""
# 	pos = getUnscaledRelCoords(app, pos)
# 	image_rect = app.label.pixmap().rect()
# 	x = pos.x()*app.image.scale+app.image.offset[1]/app.pixelSize1
# 	y = pos.y()*app.image.scale+app.image.offset[0]/app.pixelSize0
# 	x /= image_rect.width()
# 	y /= image_rect.height()
# 	return x,y
import copy
def getRelCoords(app, pos):
	# Get the position of the event relative to the image
	pos = app.label.mapFromGlobal(pos)
	
	offset = copy.deepcopy(app.image.offset)
	offset[0] /= app.pixelSize0/app.image.scale
	offset[1] /= app.pixelSize1/app.image.scale
	print(offset)
	# Get the size of the image
	image_size = app.label.size()
	image_rect = app.label.pixmap().rect()
	x = pos.x()*app.image.scale+offset[1]
	y = pos.y()*app.image.scale+offset[0]
	
	# Compute the relative position in the range [0, 1]
	rel_pos_x = x /image_rect.width()
	rel_pos_y = y / image_rect.height()

	return (rel_pos_x, rel_pos_y)

def getUnscaledRelCoords(app, pos):
	"""Takes the mouse position and returns the x, y coordinates represented
	as the pixel distance from the upper left corner of the image.
	"""
	label_pos = app.label.pos()
	image_rect = app.label.pixmap().rect()
	# image_pos here is the pixel position of the upper left corner of the image
	# inside the QT application
	image_pos = QPoint(
		int(label_pos.x() + (app.label.width() - image_rect.width()) / 2),
		int(label_pos.y() + (app.label.height() - image_rect.height()) / 2),
	)
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
		file_name = app.sessionId
	#save annotations to file
	with open(f"{file_name}", 'wb') as f:
		pickle.dump(app.image.annotations, f)
		pickle.dump(app.image.interpolated, f)
		pickle.dump(app.image.imshape, f)
	#save annotations to vcp file
	# TODO: resolve volpkg issues
	# app.volpkg.saveVCPS(app.sessionId0, app.image.interpolated, app.image.imshape)

def getPointsAndVoxels(app):
	lens = [len(i) for i in app.image.interpolated]
	if sum(lens) == 0:
		return
	print("showing 3D")

	imshape = app.image.imshape

	# Create lists to store the nodes and faces that make up the mesh
	nodes = []
	#rowlens = [len(i) for i in app.image.interpolated]
	# Iterate through the rows of interpolated
	for i in range(len(app.image.interpolated)):
		row = app.image.interpolated[i]
		if len(row) == 0:
			continue
		nrow = []
		# Add nodes to the nodes list
		for p in row:
			nrow.append((i,p.x * imshape[1], p.y * imshape[0]))
		nodes.append(nrow)



	# Retrieve the full_data array as in the original code
	noneEmptyZ = [index for index, i in enumerate(app.image.annotations) if len(i) > 0]
	zmin, zmax = min(noneEmptyZ), max(noneEmptyZ)
	xmin, xmax = int(min(p.x for row in app.image.annotations for p in row) * imshape[0]), \
				int(max(p.x for row in app.image.annotations for p in row) * imshape[0])
	ymin, ymax = int(min(p.y for row in app.image.annotations for p in row) * imshape[1]), \
				int(max(p.y for row in app.image.annotations for p in row) * imshape[1])
	full_data = app.loader[zmin:zmax + 1, xmin:xmax + 1, ymin:ymax + 1]

	return nodes, full_data, (zmin, xmin, ymin)


def exportToObj(app, fname):
	# points -= np.array(offset)
	points, voxel_data, offset = getPointsAndVoxels(app)
	mesh = getAnnMesh(points, voxel_data, offset=offset)
	print(f"saving to {fname}")
	mesh.export(fname, file_type='obj')

def getAnnMesh(points, voxel_data, offset=(0,0,0)):

	for index, i in enumerate(points):
		for jindex, j in enumerate(i):
			points[index][jindex] = (j[0]-offset[0], j[1]-offset[1], j[2]-offset[2])
	
	verts, im = strip(points, voxel_data)
	verts, faces = createAnnMesh(verts)
	
	mesh = create_trimesh_with_brightness(verts, faces, im.flatten())
		
	return mesh

def strip(points,voxel_data):
	H = len(points)
	W = max([len(i) for i in points])
	im = np.zeros((H, W*2))
	verts = np.zeros((H, W*2, 3))
	mask = np.zeros((H, W*2))
	cy = H//2
	Center = points[cy][len(points[cy])//2]
	for i in range(len(points)):
		if len(points[i]) > 0:
			#find the center of the slice by finding the point with min distance from true center
			center = points[i][0]
			centerIndex = 0
			for jindex, j in enumerate(points[i]):
				if np.sqrt((j[0]-Center[0])**2 + (j[1]-Center[1])**2) < np.sqrt((center[0]-Center[0])**2 + (center[1]-Center[1])**2):
					center = j
					centerIndex = jindex
			#populate the image with the points to the left and right of the center
			n=0
			for jindex, j in enumerate(points[i]):
				
				z,y,x = j
				
				region = voxel_data[i, int(y-n):int(y+n+1), int(x-n):int(x+n+1)]
				val = np.mean(region, axis=(0,1))
				im[i, W - (centerIndex-jindex)] = val
				verts[i, W - (centerIndex-jindex)] = np.array(j)
				mask[i, W - (centerIndex-jindex)] = 1
	#crop the arrays so that there are no zeros
	_, sliceArr = largest_non_zero_subarray(mask)
	im = im[sliceArr[0]:sliceArr[1], sliceArr[2]:sliceArr[3]]
	verts = verts[sliceArr[0]:sliceArr[1], sliceArr[2]:sliceArr[3]]
	#check for duplicates in verts 
	#first reshape verts to be 1d list of points
	return verts, im
	

def create_trimesh_with_brightness(verts, faces, brightnesses):
	"""
	Create a trimesh.Trimesh object with vertex brightness values.

	Args:
	verts (numpy.ndarray): An array of vertex coordinates with shape (N, 3).
	faces (numpy.ndarray): An array of face indices with shape (M, 3).
	brightnesses (numpy.ndarray): An array of brightness values with shape (N,).

	Returns:
	trimesh.Trimesh: A trimesh.Trimesh object with vertex brightness attributes.
	"""
	if len(verts) != len(brightnesses):
		raise ValueError("The length of 'verts' and 'brightnesses' must be the same.")

	mesh = trimesh.Trimesh(vertices=verts, faces=faces)
	brightnesses_normalized = (brightnesses - brightnesses.min()) / (brightnesses.max() - brightnesses.min())
	vertex_colors = np.zeros((len(verts), 4))
	vertex_colors[:, :3] = brightnesses_normalized[:, np.newaxis] * np.ones(3)  # Broadcast brightness to RGB channels
	vertex_colors[:, 3] = 1.0  # Set alpha channel to 1.0 (fully opaque)
	vertex_colors *= 255  # Scale the values to the range [0, 255]
	mesh.visual.vertex_colors = vertex_colors.astype(np.uint8)

	return mesh

def createAnnMesh(points_2d):
	# Get dimensions of the 2D array
	rows, cols = points_2d.shape[0], points_2d.shape[1]

	# Flatten the 2D array of points to a 1D array of vertices
	verts = points_2d.reshape(-1, 3)

	# Create an empty list to store the triangles
	triangles = []

	for r in range(rows - 1):
		for c in range(cols - 1):
			# Calculate the indices of the 4 points forming a square
			p1 = r * cols + c
			p2 = r * cols + c + 1
			p3 = (r + 1) * cols + c
			p4 = (r + 1) * cols + c + 1

			# Create two triangles to form a square by connecting neighboring points and a diagonal
			triangle1 = [p1, p2, p4]
			triangle2 = [p1, p4, p3]

			# Add the triangles to the list
			triangles.extend([triangle1, triangle2])

	return np.array(verts), np.array(triangles)




def largest_non_zero_subarray(arr):
	arr_np = np.array(arr, dtype=int)
	binary_matrix = (arr_np > 0).astype(int)

	rows, cols = binary_matrix.shape
	largest_area = 0
	largest_subarray = []
	largest_slice = (0, 0, 0, 0)
	dp = np.zeros((rows, cols), dtype=int)

	for i in range(rows):
		for j in range(cols):
			if i == 0:
				dp[i, j] = binary_matrix[i, j]
			elif binary_matrix[i, j] == 1:
				dp[i, j] = dp[i - 1, j] + 1

	for i in range(rows):
		stack = []
		left = np.zeros(cols, dtype=int)
		right = np.zeros(cols, dtype=int)

		for j in range(cols):
			while stack and dp[i, stack[-1]] > dp[i, j]:
				right[stack.pop()] = j
			left[j] = stack[-1] if stack else -1
			stack.append(j)

		while stack:
			right[stack.pop()] = cols

		for j in range(cols):
			area = (right[j] - left[j] - 1) * dp[i, j]
			if area > largest_area:
				largest_area = area
				largest_subarray = arr_np[i - dp[i, j] + 1:i + 1, left[j] + 1:right[j]]
				largest_slice = (i - dp[i, j] + 1, i + 1, left[j] + 1, right[j])

	return largest_subarray, largest_slice



#copy stripping from to obj
#pass in list of tiff files to put in volume, if volume doesn't exist already?
#TODO check if point coords ar normalized right
class Volpkg(object):
	def __init__(self, app, folder, saveTiffs=False):
		self.app = app
		self.sessionId0 = app.sessionId0
		#make spaces friendly e.g. by adding \ before spaces (does it depend on OS?)
		self.saveTiffs = saveTiffs

		#check if folder exists
		if os.path.exists(folder):
			if folder.endswith(".volpkg"):
				self.basepath = folder
				self.volume = os.listdir(f"{self.basepath}/volumes")[0]
				#get all volumes in the folder
			else:
				print("Folder must end with .volpkg")
		else:
			self.basepath = folder if folder.endswith(".volpkg") else folder+".volpkg"
			print(self.basepath)

			#make volpkg folder
			os.mkdir(self.basepath)
			self.tifstack = self.app.tiffs
			#copy tifstack to volumes folder
			os.mkdir(f"{self.basepath}/volumes")
			#volume name
			os.mkdir(f"{self.basepath}/volumes/{self.sessionId0}")
			self.volume = self.sessionId0
			if self.saveTiffs:
				for i, tif in enumerate(self.tifstack):
					#use cp command
					to = f"{self.basepath}/volumes/{self.sessionId0}/"
					#replace spaces with \
					tif = tif.replace(" ", "\\ ")
					to = to.replace(" ", "\\ ")
					#get tif name
					tifName = tif.split("/")[-1]
					#strip so it only has n digits, where n is int(log10(len(tifstack)))+1
					n = int(np.log10(len(self.tifstack)))+1
					tifName = tifName[n+1:]
					os.system(f'cp {tif} {to}/{tifName}')
			
			height,width = self.app.image.imshape
			#save meta.json in volume folder, form: {"height":560,"max":65535.0,"min":0.0,"name":"ca","slices":35,"type":"vol","uuid":"20230511123535","voxelsize":10.0,"width":560}
			meta = {"height":height,"max":65535.0,"min":0.0,"name":self.sessionId0,"slices":len(self.tifstack),"type":"vol","uuid":self.sessionId0,"voxelsize":10.0,"width":width}
			with open(f"{self.basepath}/volumes/{self.sessionId0}/meta.json", 'w') as f:
				json.dump(meta, f)

			#make paths folder
			os.mkdir(f"{self.basepath}/paths")
			#make renders folder
			os.mkdir(f"{self.basepath}/renders")

			#save config.json. EX: {"materialthickness":1000.0,"name":"campfire","version":6}
			name = folder.split("/")[-1].split(".")[0]
			config = {"materialthickness":1000.0,"name":name,"version":6}
			with open(f"{self.basepath}/config.json", 'w') as f:
				json.dump(config, f)

		#make our path
		pathToPath = f"{self.basepath}/paths/{self.sessionId0}"
		os.mkdir(pathToPath)

		self.saveVCPS(pathToPath)





		

	def saveVCPS(self, pathdir, ordered=True, point_type='double', encoding='utf-8'):
		print("saving vcps")
		annotations = self.stripAnnoatation(self.app)
		#reorder the last axis from 012 to 120
		Xs = annotations[:,:,0]
		Ys = annotations[:,:,1]
		Zs = annotations[:,:,2]
		annotations = np.stack((Ys, Zs, Xs), axis=2)
		height, width, dim = annotations.shape
		#flatten annotations
		#convert to float64
		annotations = annotations.astype(np.float64)
		
		# print(annotations.shape)
		# print(width, height, dim)
		file_path = f"{pathdir}/pointset.vcps"
		
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
			# for i in range(len(annotations)):
			# 	for j in range(len(annotations[i])):
			# 		for k in range(len(annotations[i, j])):
					
			# 			#quit()
			# 			point = annotations[i, j, k]
			# 			file.write(struct.pack('d', point))
			#save to binary file
			annotations.tofile(file)

				
		
		#filename is end of path
		file_name = self.sessionId0

		#write meta.json {"name":"20230426114804","type":"seg","uuid":"20230426114804","vcps":"pointset.vcps","volume":"20230210143520"}
		meta = {
			"name": file_name,
			"type": "seg",
			"uuid": file_name,
			"vcps": "pointset.vcps",
			"volume": self.volume
		}
		with open(f"{pathdir}/meta.json", 'w') as file:
			json.dump(meta, file)




	def stripAnnoatation(self, app):
		points, voxel_data, offset = getPointsAndVoxels(app)
		points, im = strip(points, voxel_data)
		return points




# def mplGetTriFromSimplex(*args, **kwargs):
# 	tri, args, kwargs = \
# 		Triangulation.get_from_args_and_kwargs(*args, **kwargs)

# 	triangles = tri.get_masked_triangles()
# 	return triangles

# def triangles_to_vertices_faces(triangles):
# 	vertices = []
# 	faces = []
# 	vertex_indices = {}

# 	for triangle in triangles:
# 		face = []
# 		for vertex in triangle:
# 			vertex_tuple = tuple(vertex)
# 			if vertex_tuple not in vertex_indices:
# 				vertex_indices[vertex_tuple] = len(vertices)
# 				vertices.append(vertex)

# 			index = vertex_indices[vertex_tuple]
# 			face.append(index)

# 		faces.append(face)

# 	return np.array(vertices), np.array(faces)