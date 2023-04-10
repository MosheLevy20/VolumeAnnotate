import cv2
import numpy as np
from helpers import Point


def find_and_discard_small_edges(image, min_edge_length=100):
    mu = np.mean(image)
    sigma = np.std(image)
    
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

def findEdges(initialEdge, filenameList, radius):
    # Initialize the list of edge points with the initial edge
    allEdges = [initialEdge]

    for i in range(1, len(filenameList)):
        print(f"Processing image {i+1} of {len(filenameList)}")
        currentFilename = filenameList[i]

        # Load the current image
        currentImage = cv2.imread(currentFilename, cv2.IMREAD_GRAYSCALE)
        # Increase contrast
        currentImage = cv2.convertScaleAbs(currentImage, alpha=2.5, beta=0)

        edges = find_and_discard_small_edges(currentImage, 50)
 
        # Find the intersection of the edges with the previous edge
        prevEdge = allEdges[-1]
        currentEdge = []

        for point in prevEdge:
            x, y = int(point.x * currentImage.shape[1]), int(point.y * currentImage.shape[0])

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
                                        new_point = Point(new_x / edges.shape[1], new_y / edges.shape[0])

                    if new_point is not None:
                        currentEdge.append(new_point)
                    else:
                        currentEdge.append(point)

            else:
                # Place the edge at the same location in the previous slice
                currentEdge.append(point)

        allEdges.append(currentEdge)
    return allEdges

