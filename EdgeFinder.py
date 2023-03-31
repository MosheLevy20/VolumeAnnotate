import cv2
import numpy as np
from Annotations import point as Point
import numpy as np
import copy

def findEdges(initialEdge, filenameList):
    """
    Given an initial edge in the form of a list of points and a list of filenames, returns a modified list of edge points for each image that lies on the edge.

    Args:
        initialEdge (list): A list of points representing the edge in the first 2D image.
        filenameList (list): A list of filenames of 2D images.

    Returns:
        list: A list of lists, where each sublist contains the edge points for each image in the filenameList.
    """
    # Initialize the list of edge points with the initial edge
    allEdges = [initialEdge]

    for i in range(1, len(filenameList)):
        print(f"Processing image {i+1} of {len(filenameList)}")
        currentFilename = filenameList[i]

        # Load the current image
        currentImage = cv2.imread(currentFilename, cv2.IMREAD_GRAYSCALE)

        # Apply Canny edge detection to the current image
        edges = cv2.Canny(currentImage, 100, 200)

        # Find the intersection of the edges with the previous edge
        prevEdge = allEdges[-1]
        print(prevEdge)
        print(f"prevEdge length: {len(prevEdge)}")
        currentEdge = []
        #currentEdge = copy.deepcopy(prevEdge)
        
        for point in prevEdge:
            x, y = int(point.x*currentImage.shape[1]), int(point.y*currentImage.shape[0])
            #print(f"point({x}, {y}), {point.x}, {point.y}")
            # Check if the point is within the bounds of the current image
            if x >= 0 and x < edges.shape[1] and y >= 0 and y < edges.shape[0]:
                # Check if the point lies on an edge in the current image
                if edges[y, x] == 255:
                    currentEdge.append(point)
                else:
                    # Find the closest edge point to the left of the current point
                    leftX = max(x-1, 0)
                    while leftX >= 0 and edges[y, leftX] != 255:
                        leftX -= 1

                    # Find the closest edge point to the right of the current point
                    rightX = min(x+1, edges.shape[1]-1)
                    while rightX < edges.shape[1] and edges[y, rightX] != 255:
                        rightX += 1

                    # Use the closest edge point if one was found, otherwise use the original point
                    if leftX >= 0 and rightX < edges.shape[1]:
                        if abs(x - leftX) <= abs(rightX - x):
                            currentEdge.append(Point(leftX/edges.shape[1], y/edges.shape[0]))
                        else:
                            currentEdge.append(Point(rightX/edges.shape[1], y/edges.shape[0]))
                    elif leftX >= 0:
                        currentEdge.append(Point(leftX/edges.shape[1], y/edges.shape[0]))
                    elif rightX < edges.shape[1]:
                        currentEdge.append(Point(rightX/edges.shape[1], y/edges.shape[0]))
                    else:
                        currentEdge.append(point)

            else:
                # Place the edge at the same location in the previous slice
                currentEdge.append(point)

        r = int(len(currentEdge)/len(prevEdge))
        last = currentEdge[-1]
        print(f"r1 = {r}")
        bez = interpolatePoints(currentEdge[::r], currentImage.shape[1])
        r = len(bez)/len(prevEdge)
        print(f"r2 = {r}")
        #ceiling function
        r = int(r) + (r > int(r))
        # Store the current edge in the list of edges
        allEdges.append(bez[::r].append(last))

        #allEdges.append(currentEdge[::r])

    return allEdges

def interpolatePoints(points, display_width):
    points = [[i.x, i.y] for i in points]
    #use bezier curves to interpolate between points in the annotation list
    #first find the total length of the curve
    dists = np.array([(points[i+1][0]-points[i][0])**2 + (points[i+1][1]-points[i][1])**2 for i in range(len(points)-1)])
    dists = np.sqrt(dists)
    totalDist = np.sum(dists)*display_width
    dt = 1/totalDist
    # print("total dist", totalDist, dt)
    bezier = []
    t = 0
    while t <=1:
        newPoints = [i for i in points]
        while len(newPoints) > 1:
            temp = newPoints
            newPoints = []
            for index, i in enumerate(temp[:-1]):
                newPoints.append(getInterpolated(temp[index:index+2], t))
        bezier.append(Point(newPoints[0][0], newPoints[0][1],1))
        t += dt
    print(len(bezier), len(points), len(points)/dt)
    return bezier

def getInterpolated(points, t):
    points = np.array(points)
    return points[0]*(1-t) + points[1]*t