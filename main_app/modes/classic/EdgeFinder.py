import cv2
import numpy as np
from main_app.helpers import Point

def find_and_discard_small_edges(image, min_edge_length=100):
	imNoZeros = image[image != 0]
	mu = np.mean(imNoZeros)
	sigma = np.std(imNoZeros)
	
	image= np.where(image > mu, 255, 0)
	image = np.array(image, dtype=np.uint8)
	# Apply Gaussian blur to reduce noise
	image = cv2.GaussianBlur(image, (3, 3), 0)

	# Apply Canny edge detection
	edges = cv2.Canny(image, mu, mu+sigma)

	# # Find contours from the edges
	contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

	# # Filter contours by length
	filtered_contours = [contour for contour in contours if cv2.arcLength(contour, True) > min_edge_length]

	# # Create a black image to draw filtered contours
	result_image = np.zeros_like(image)

	# # Draw the filtered contours on the result image
	cv2.drawContours(result_image, filtered_contours, -1, (255, 255, 255), 1)

	return result_image


def findEdges(initialEdge, imageIndices, radius, loader):
	# Initialize the list of edge points with the initial edge
	allEdges = [initialEdge]

	for idx, i in enumerate(imageIndices):
		print(f"Processing image {idx+1} of {len(imageIndices)}")
		# Load the current image - note this loads in as a grayscale array of
		# uint16s.
		#get bounding box arround annotation points in initialEdge, which is max in each dimension
		xs = [j.x for j in initialEdge]
		ys = [j.y for j in initialEdge]
		bounds = [np.min(xs)*loader.shape[2], np.max(xs)*loader.shape[2], np.min(ys)*loader.shape[1], np.max(ys)*loader.shape[1]]
		#find the center of the bounding box
		center = [(bounds[1]+bounds[0])/2, (bounds[3]+bounds[2])/2]
		relBounds = [bounds[0]-center[0], bounds[1]-center[0], bounds[2]-center[1], bounds[3]-center[1]]
		#set the new bounding box to be 2x the size of the original
		newBounds = [center[0]+relBounds[0]*3//2, center[0]+relBounds[1]*3//2, center[1]+relBounds[2]*3//2, center[1]+relBounds[3]*3//2]

		currentImage = loader[i, int(newBounds[2]):int(newBounds[3]), int(newBounds[0]):int(newBounds[1])]

		# Increase contrast
		if type(currentImage[0,0]) == np.uint16:
			print("Converting to uint8")
			f = (np.iinfo(np.uint16).max / np.iinfo(np.uint8).max)
		else:
			f = 1


		currentImage = cv2.convertScaleAbs(
			(currentImage / f).astype(np.uint8), 
			alpha=1.5, 
			beta=0
		)
	
		edges = find_and_discard_small_edges(currentImage, 50)

		# Find the intersection of the edges with the previous edge
		prevEdge = allEdges[-1]
		currentEdge = []

		for point in prevEdge:
			x, y = int(point.x * loader.shape[2] - newBounds[0]), int(point.y * loader.shape[1] - newBounds[2])

			# Check if the point is within the bounds of the current image
			if x >= 0 and x < edges.shape[1] and y >= 0 and y < edges.shape[0]:
				# Check if the point lies on an edge in the current image
				if edges[y, x] == 255:
					currentEdge.append(point)
				else:
					min_distance = float('inf')
					new_point = None

					# Loop through all neighboring points within the specified radius
					for i in range(-radius, radius+1):
						for j in range(-radius, radius+1):
							new_x = x + i
							new_y = y + j

							# Check if the new point is within the bounds of the current image
							if new_x >= 0 and new_x < edges.shape[1] and new_y >= 0 and new_y < edges.shape[0]:
								# Check if the new point lies on an edge in the current image
								if edges[new_y, new_x] == 255:
									distance = abs(i) + abs(j)

									if distance < min_distance:
										min_distance = distance
										new_x += newBounds[0]
										new_y += newBounds[2]
										new_x /= loader.shape[2]
										new_y /= loader.shape[1]

										new_point = Point(new_x, new_y)

					if new_point is not None:
						currentEdge.append(new_point)
					else:
						currentEdge.append(point)

			else:
				# Place the edge at the same location in the previous slice
				currentEdge.append(point)

		allEdges.append(currentEdge)
	return allEdges

