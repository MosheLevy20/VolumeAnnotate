import numpy as np
import copy
import pickle
import cv2
import time
import os
import tifffile
import zarr
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
# from pyvistaqt import BackgroundPlotter
# import pyvista as pv
import struct
import json

#TODO: figure out step size generally (including non square images)

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

	def show(self, arr, img_shape, size, node, x0, y0, scale):
		if node:
			size *= 2
		#draws point to copy of the current frame
		local_x = int(self.x * img_shape[1]) - y0 
		local_y = int(self.y * img_shape[0]) - x0
		cv2.circle(arr, (local_x, local_y), size, self.color, -1)
	
	def updateColor(self, colorIdx):
		self.colorIdx = colorIdx
		self.color = getColor(colorIdx)

def load_tif(path):
	"""This function will take a path to a folder that contains a stack of .tif
	files and returns a concatenated 3D zarr array that will allow access to an
	arbitrary region of the stack.

	We support two different styles of .tif stacks.  The first are simply
	numbered filenames, e.g., 00.tif, 01.tif, 02.tif, etc.  In this case, the
	numbers are taken as the index into the zstack, and we assume that the zslices
	are fully continuous.

	The second follows @spelufo's reprocessing, and are not 2D images but 3D cells
	of the data.  These should be labeled

	cell_yxz_YINDEX_XINDEX_ZINDEX

	where these provide the position in the Y, X, and Z grid of cuboids that make
	up the image data.
	"""
	# Get a list of .tif files
	tiffs = [filename for filename in os.listdir(path) if filename.endswith(".tif")]
	if all([filename[:-4].isnumeric() for filename in tiffs]):
		# This looks like a set of z-level images
		tiffs.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
		paths = [os.path.join(path, filename) for filename in tiffs]
		store = tifffile.imread(paths, aszarr=True)
	elif all([filename.startswith("cell_yxz_") for filename in tiffs]):
		# This looks like a set of cell cuboid images
		images = tifffile.TiffSequence(os.path.join(path, "*.tif"), pattern=r"cell_yxz_(\d+)_(\d+)_(\d+)")
		store = images.aszarr(axestiled={0: 1, 1: 2, 2: 0})
	stack_array = zarr.open(store, mode="r")
	return stack_array, tiffs


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
			self.img_array, self.tifstack = load_tif(f"{self.basepath}/volumes/{volume}")
			self.segmentations = None #TODO
		else:
			self.basepath = folder+".volpkg"
			#make volpkg folder
			os.mkdir(self.basepath)
			self.img_array, self.tifstack = load_tif(folder)
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
	"""Provides a cached interface to the data.
	
	When provided with z, x, and y slices, queries whether that
	data is available from any previously cached data.  If it
	is, returns the subslice of that cached data that contains
	the data we need.  
	
	If it isn't, then we:
	- clear out the oldest cached data if we need space
	- load the data we need, plus some padding
		- padding depends on the chunking of the zarr array and the
		  size of the data loaded
	- store that data in our cache, along with the access time.

	The cache is a dictionary, indexed by a namedtuple of
	slice objects (zslice, xslice, yslice), that provides a
	dict of 
	{"accesstime": last access time, "array": numpy array with data}
	"""

	def __init__(self, zarr_array, max_mem_gb=3):
		self.shape = zarr_array.shape
		print("Data array shape: ", self.shape)
		self.cache = {}
		self.zarr_array = zarr_array
		self.max_mem_gb = max_mem_gb
		chunk_shape = self.zarr_array.chunks
		if chunk_shape[0] == 1:
			self.chunk_type = "zstack"
		else:
			self.chunk_type = "cuboid"


	def _check_slices(self, cache_slice, new_slice, length):
		"""Queries whether a new slice's data is contained
		within an older slice.
		
		Note we don't handle strided slices.
		"""
		if isinstance(new_slice, int):
			new_start = new_slice
			new_stop = new_slice + 1
		else:
			new_start = 0 if new_slice.start is None else max(0, new_slice.start)
			new_stop = length if new_slice.stop is None else min(length, new_slice.stop)
		if isinstance(cache_slice, int):
			cache_start = cache_slice
			cache_stop = cache_slice + 1
		else:
			cache_start = 0 if cache_slice.start is None else cache_slice.start
			cache_stop = length if cache_slice.stop is None else cache_slice.stop
		if (new_start >= cache_start) and (new_stop <= cache_stop):
			# New slice should be the slice in the cached data that gives the request
			if isinstance(new_slice, int):
				return new_start - cache_start
			else:
				return slice(
					new_start - cache_start,
					new_stop - cache_start,
					None
				)
		else:
			return None

	def check_cache(self, zslice, xslice, yslice):
		"""Looks through the cache to see if any cached data
		can provide the data we need.
		"""
		for key in self.cache.keys():
			cache_zslice = hashable_to_slice(key[0])
			cache_xslice = hashable_to_slice(key[1])
			cache_yslice = hashable_to_slice(key[2])
			sub_zslice = self._check_slices(cache_zslice, zslice, self.shape[0])
			sub_xslice = self._check_slices(cache_xslice, xslice, self.shape[1])
			sub_yslice = self._check_slices(cache_yslice, yslice, self.shape[2])
			if sub_zslice is None or sub_xslice is None or sub_yslice is None:
				continue
			# At this point we have a valid slice to index into this subarray.
			# Update the access time and return the array.
			self.cache[key]["accesstime"] = time.time()
			return self.cache[key]["array"][sub_zslice, sub_xslice, sub_yslice]
		return None
	
	@property
	def cache_size(self):
		total_mem_gb = 0
		for _, data in self.cache.items():
			total_mem_gb += data["array"].nbytes / 1e9
		return total_mem_gb
	
	def empty_cache(self):
		"""Removes the oldest item in the cache to free up memory.
		"""
		if not self.cache:
			return
		oldest_time = None
		oldest_key = None
		for key, value in self.cache.items():
			if oldest_time is None or value["accesstime"] < oldest_time:
				oldest_time = value["accesstime"]
				oldest_key = key
		del self.cache[oldest_key]
	
	def estimate_slice_size(self, zslice, xslice, yslice):
		def slice_size(s, l):
			if isinstance(s, int):
				return 1
			elif isinstance(s, slice):
				s_start = 0 if s.start is None else s.start
				s_stop = l if s.stop is None else s.stop
				return s_stop - s_start
			raise ValueError("Invalid index")
		return (
			self.zarr_array.dtype.itemsize * 
			slice_size(zslice, self.shape[0]) *
			slice_size(xslice, self.shape[1]) * 
			slice_size(yslice, self.shape[2])
		) / 1e9

	def pad_request(self, zslice, xslice, yslice):
		"""Takes a requested slice that is not loaded in memory
		and pads it somewhat so that small movements around the
		requested area can be served from memory without hitting
		disk again.

		For zstack data, prefers padding in xy, while for cuboid
		data, prefers padding in z.
		"""
		def pad_slice(old_slice, length, int_add=1):
			if isinstance(old_slice, int):
				if length == 1:
					return old_slice
				return slice(
					max(0, old_slice - int_add),
					min(length, old_slice + int_add + 1),
					None
				)
			start = old_slice.start if old_slice.start is not None else 0
			stop = old_slice.stop if old_slice.stop is not None else length
			adj_width = (stop - start) // 2 + 1
			return slice(
				max(0, start - adj_width),
				min(length, stop + adj_width),
				None
			)
		est_size = self.estimate_slice_size(zslice, xslice, yslice)
		if (3 * est_size) >= self.max_mem_gb:
			# No padding; the array's already larger than the cache.
			return zslice, xslice, yslice
		if self.chunk_type == "zstack":
			# First pad in X and Y, then Z
			xslice = pad_slice(xslice, self.shape[1])
			est_size = self.estimate_slice_size(zslice, xslice, yslice)
			if (3 * est_size) >= self.max_mem_gb:
				return zslice, xslice, yslice
			yslice = pad_slice(yslice, self.shape[2])
			est_size = self.estimate_slice_size(zslice, xslice, yslice)
			if (3 * est_size) >= self.max_mem_gb:
				return zslice, xslice, yslice
			zslice = pad_slice(zslice, self.shape[0])
		elif self.chunk_type == "cuboid":
			# First pad in Z by 5 in each direction if we have space, then in XY
			zslice = pad_slice(
				zslice, 
				self.shape[0], 
				int_add=min(5, self.max_mem_gb // (2 * est_size))
			)
			est_size = self.estimate_slice_size(zslice, xslice, yslice)
			if (3 * est_size) >= self.max_mem_gb:
				return zslice, xslice, yslice
			xslice = pad_slice(xslice, self.shape[1])
			est_size = self.estimate_slice_size(zslice, xslice, yslice)
			if (3 * est_size) >= self.max_mem_gb:
				return zslice, xslice, yslice
			yslice = pad_slice(yslice, self.shape[2])
		return zslice, xslice, yslice

	def __getitem__(self, key):
		"""Overloads the slicing operator to get data with caching
		"""
		zslice, xslice, yslice = key
		for item in (zslice, xslice, yslice):
			if isinstance(item, slice) and item.step is not None:
				raise ValueError("Sorry, we don't support strided slices yet")
		# First check if we have the requested data already in memory
		result = self.check_cache(zslice, xslice, yslice)
		if result is not None:
			return result
		# Pad out the requested slice before we pull it from disk
		# so that we cache neighboring data in memory to avoid
		# repeatedly hammering the disk
		padded_zslice, padded_xslice, padded_yslice = self.pad_request(zslice, xslice, yslice)
		est_size = self.estimate_slice_size(padded_zslice, padded_xslice, padded_yslice)
		# Clear out enough space from the cache that we can fit the new
		# request within our memory limits.
		while self.cache and (self.cache_size + est_size) > self.max_mem_gb:
			self.empty_cache()
		self.cache[(
			slice_to_hashable(padded_zslice),
			slice_to_hashable(padded_xslice),
			slice_to_hashable(padded_yslice),
		)] = {
			"accesstime": time.time(),
			"array": self.zarr_array[padded_zslice, padded_xslice, padded_yslice],
		}
		result = self.check_cache(zslice, xslice, yslice)
		if result is None:
			# We shouldn't get cache misses!
			print("Unexpected cache miss")
			print(zslice, xslice, yslice)
			print(padded_zslice, padded_xslice, padded_yslice)
			raise ValueError("Cache miss after cache loading")
		return result

def slice_to_hashable(slice):
	return (slice.start, slice.stop)

def hashable_to_slice(item):
	return slice(item[0], item[1], None)

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
def getRelCoords(app, pos):
	"""Returns the coordinates of the mouse reported as a fraction
	of the way through the full image.

	Note that the full image may not be currently displayed, so we have
	to adjust the location appropriately.
	"""
	pos = getUnscaledRelCoords(app, pos)
	image_rect = app.label.pixmap().rect()
	x = pos.x()*app.image.scale+app.image.offset[1]/app.pixelSize1
	y = pos.y()*app.image.scale+app.image.offset[0]/app.pixelSize0
	x /= image_rect.width()
	y /= image_rect.height()
	return x,y


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
		file_name = app.sessionId0
	#save annotations to file
	with open(f"{file_name}.pkl", 'wb') as f:
		pickle.dump(app.image.annotations, f)
		pickle.dump(app.image.interpolated, f)
		pickle.dump(app.image.imshape, f)
	#save annotations to vcp file
	# TODO: resolve volpkg issues
	# app.volpkg.saveVCPS(app.sessionId0, app.image.interpolated, app.image.imshape)