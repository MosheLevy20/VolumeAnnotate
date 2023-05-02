from helpers import *
import os
from EdgeFinder import findEdges


class EventHandler(object):
    def __init__(self, app):
        self.app = app

    def on_mouse_mode(self, id):
        print(f"mouse mode: {id}")
        if id == 0:
            self.app.mouseMode = "Pan"
        elif id == 1:
            self.app.mouseMode = "Outline Fragment"
        elif id == 2:
            self.app.mouseMode = "Move Points"
        elif id == 3:
            self.app.mouseMode = "Delete Points"
        elif id == 4:
            self.app.mouseMode = "Label Ink"
        else:
            print("Warning: invalid mouse mode")

    def on_unwrap_style(self, id):
        if id == 0:
            self.app.unwrapStyle = "Annotate"
        elif id == 1:
            self.app.unwrapStyle = "Project"
        else:
            print("Warning: invalid unwrap style")

    def on_annotation_color_change(self, id):
        self.app.annotationColorIdx = id
        self.app._update_image()

    def on_frame_change(self, event):
        input = self.app.frame_edit_display.text()
        input = (int(input) - 1) % self.app._frame_count
        self.app._frame_index = input
        self.app._update_frame()

    def on_zoom_in(self, event):
        self.app.image.zoom(1 / 1.1)
        self.app._update_image()

    def on_zoom_out(self, event):
        self.app.image.zoom(1.1)
        self.app._update_image()

    def on_next_frame(self, event):
        self.app._frame_index = min(self.app._frame_index + 1, self.app._frame_count - 10)
        self.app._update_frame()

    def on_previous_frame(self, event):
        self.app._frame_index = max(self.app._frame_index - 1, 0)
        self.app._update_frame()

    def on_copy(self, event):
        # copy previous frame annotations
        self.app.image.annotations[self.app._frame_index] = copy.deepcopy(
            self.app.image.annotations[self.app._frame_index - 1]
        )
        self.app.image.interpolated[self.app._frame_index] = interpolatePoints(
            self.app.image.annotations[self.app._frame_index], self.app.image.imshape
        )
        self.app._update_image()
        autoSave(self.app)

    def on_save(self, event):
        # save annotations to file using pickle, pop up window to ask for file name
        filename = QFileDialog.getSaveFileName(
            self.app, "Save File", os.getcwd(), "Pickle Files (*.pkl)"
        )
        if filename[0] != "":
            autoSave(self.app, filename[0])

    def on_load(self, event):
        # load annotations from file using pickle, pop up window to ask for file name
        filename = QFileDialog.getOpenFileName(
            self.app, "Open File", os.getcwd(), "Pickle Files (*.pkl)"
        )
        if filename[0] != "":
            with open(filename[0], "rb") as f:
                self.app.image.annotations = pickle.load(f)
                self.app.image.interpolated = pickle.load(f)
                self.app.image.imgShape = pickle.load(f)

    def on_save_2D(self, event):
        image2D = self.app.image.get2DImage(self.app)
        filename = QFileDialog.getSaveFileName(
            self.app, "Save File", os.getcwd(), "PNG Files (*.png)"
        )
        if filename[0] != "":
            # use cv2 to save image
            cv2.imwrite(filename[0], image2D)
    
    # def on_show_3D(self, event):
    #     #check if there are any annotations in any of the rows
    #     lens = [len(i) for i in self.app.image.interpolated]
    #     if sum(lens) == 0:
    #         return
    #     #get 3D voxel data
    #     #create empty np array whose size is the boudning box of the interpolated
    #     #loop through all interpolated and set the corresponding voxels to 1
    #     imshape = self.app.image.imshape
    #     #zmin, zmax, xmin, xmax, ymin, ymax = getBoundingBox(self.app.image.interpolated, imshape)
    #     voxels = np.zeros((len(self.app.image.interpolated), imshape[0], imshape[1]))
    #     for i in range(len(self.app.image.interpolated)):
    #         img = cv2.imread(self.app._frame_list[i], cv2.IMREAD_GRAYSCALE)
    #         for j in range(len(self.app.image.interpolated[i])):
    #             #get voxel value
        
    #             x = int(self.app.image.interpolated[i][j].x*imshape[0])
    #             y = int(self.app.image.interpolated[i][j].y*imshape[1])
    #             # value = img[x][y]
    #             # print(value)
    #             # print(i, x, y)
    #             # #print(zmin, zmax, xmin, xmax, ymin, ymax)
    #             # print(voxels.shape)
    #             # voxels[i][x][y] = value
    #             #for x,y and all its neighbors, set voxel to value
    #             r = 10
    #             for x1 in range(x-10, x+11):
    #                 for y1 in range(y-10, y+11):
    #                     if x1 >= 0 and x1 < imshape[0] and y1 >= 0 and y1 < imshape[1]:
    #                         #equal mean of neighbors out to radius
    #                         voxels[i][x1][y1] = img[x-r:x+r+1, y-r:y+r+1].mean()+np.random.randint(1,255)
            
    #     #pad the region around nonzero values with the average of their neighbors
        

    #     #crop voxels to region with nonzero values
    #     nonzero_z, nonzero_x, nonzero_y = np.nonzero(voxels)

    #     # Find the min and max indices along each axis
    #     z_min, z_max = np.min(nonzero_z), np.max(nonzero_z)
    #     y_min, y_max = np.min(nonzero_y), np.max(nonzero_y)
    #     x_min, x_max = np.min(nonzero_x), np.max(nonzero_x)

    #     # Slice the array using these indices
    #     voxels = voxels[z_min:z_max+1, x_min:x_max+1, y_min:y_max+1]*255

    #     #swap x and z axes
    #     voxels = np.swapaxes(voxels, 1, 0)


    #     #create popup window with VoxVis object
    #     self.app.voxVis = VoxelViewer(self.app, data=voxels)
    #     self.app.voxVis.show()

    def on_ink(self, event):
        self.app.update_ink()

    def on_ink_all(self, event):
        # loop through all frames and run ink detection
        for i in range(self.app._frame_count):
            self.app.update_ink(i)
        autoSave(self.app)

    def on_slider_change(self, event):
        self.app.inkThreshold = self.app.slider.value()
        self.app.update_ink()
        self.app._update_image()

    def on_show_annotations(self, event):
        self.app.show_annotations = not self.app.show_annotations
        # change the text of the button to reflect the current state
        if self.app.show_annotations:
            self.app.button_show_annotations.setText("Hide Annotations")
        else:
            self.app.button_show_annotations.setText("Show Annotations")
        self.app._update_image()

    def on_slider_ink_radius_change(self, event):
        self.app.inkRadius = self.app.slider_ink_radius.value()
        self.app.update_ink()

    def on_slider_annotation_radius_change(self, event):
        self.app.image.annotationRadius = self.app.slider_annotation_radius.value()
        self.app._update_image()

    def on_slider_contrast_change(self, event):
        self.app.image.contrast = self.app.slider_contrast.value()
        self.app._update_image()
    
    def on_slider_highlights_change(self, event):
        self.app.image.highlights = self.app.slider_highlights.value()
        self.app._update_image()
    
    def on_slider_midtones_change(self, event):
        self.app.image.midtones = self.app.slider_midtones.value()
        self.app._update_image()

    def on_slider_shadows_change(self, event):
        self.app.image.shadows = self.app.slider_shadows.value()
        self.app._update_image()

    def on_invert(self, event):
        self.app.image.invert = not self.app.image.invert
        self.app._update_image()

    def on_edge(self, event):
        # get the list of image names
        # imageNames = self.app._frame_list[
        #     self.app._frame_index : min(
        #         self.app._frame_index + self.app.edgeDepth, self.app._frame_count
        #     )
        # ]
        currentEdge = self.app.image.annotations[self.app._frame_index]
        if len(currentEdge) == 0:
            return
        imageIndices = list(range(
            self.app._frame_index, min(
            self.app._frame_index + self.app.edgeDepth, self.app._frame_count-1
        )))
        # use findEdges to get the list of edges
        edges = findEdges(
            currentEdge,
            imageIndices,
            self.app.inkRadius,
            self.app.loader 
        )

        # add the edges as the annotations for the next edgeDepth frames
        for i in range(1, len(edges)):
            # annotations is every n'th entry in interpolated, use slice notation
            self.app.image.annotations[self.app._frame_index + i] = edges[i]
            self.app.image.interpolated[self.app._frame_index + i] = interpolatePoints(
                edges[i], self.app.image.imshape
            )

        # run ink detection on the new annotations
        for i in range(1, len(edges)):
            self.app.update_ink(self.app._frame_index + i)

        autoSave(self.app)

    def on_slider_edge_change(self, event):
        self.app.edgeDepth = self.app.slider_edge.value()
        self.app.edgeDepthTxt.setText(
            f"Edge Detection: Number of Frames = {self.app.edgeDepth}"
        )
        # self.app.label_edge.setText(f"Edge Depth: {self.app.edgeDepth}")

    def keyPressEvent(self, event):
        #print(event.key())
        if event.key() == Qt.Key_Right:
            self.app._frame_index = min(self.app._frame_index + 1, self.app._frame_count - 10)
            self.app._update_frame()
            return
        elif event.key() == Qt.Key_Left:
            self.app._frame_index = max(self.app._frame_index - 1, 0)
            self.app._update_frame()
            return
        elif event.key() == Qt.Key_Up:
            if self.app.image.scale < 0.11:
                return
            self.app.image.zoom(1 / 1.1)
            self.app._update_image()
        elif event.key() == Qt.Key_Down:
            if self.app.image.scale > 10:
                return
            self.app.image.zoom(1.1)
            self.app._update_image()
        # wasd for panning
        elif event.key() == Qt.Key_A:
            self.app.image.pan(np.array([0, -self.app.panLen]))
            self.app._update_image()
        elif event.key() == Qt.Key_D:
            self.app.image.pan(np.array([0, self.app.panLen]))
            self.app._update_image()
        elif event.key() == Qt.Key_W:
            self.app.image.pan(np.array([-self.app.panLen, 0]))
            self.app._update_image()
        elif event.key() == Qt.Key_S:
            self.app.image.pan(np.array([self.app.panLen, 0]))
            self.app._update_image()
        elif event.key() == Qt.Key_C:
            # copy previous frame annotations
            self.app.image.annotations[self.app._frame_index] = copy.deepcopy(
                self.app.image.annotations[self.app._frame_index - 1]
            )
            self.app.image.interpolated[self.app._frame_index] = interpolatePoints(
                self.app.image.annotations[self.app._frame_index],
                self.app.image.imshape,
            )
            #
            self.app._update_image()
            with open(self.app.sessionId, "wb") as f:
                pickle.dump(self.app.image.annotations, f)
                pickle.dump(self.app.image.interpolated, f)
                pickle.dump(self.app.image.imshape, f)
        else:
            print("Warning: Unrecognized key press")

    def mousePressEvent(self, event):
        self.app.frame_edit_display.clearFocus()
        self.app.clickState = 1

        x, y = getRelCoords(self.app, event.pos())
        # check if the mouse is out of the image
        xf, yf = getImFrameCoords(self.app, event.pos())
        if xf < 0 or yf < 0 or xf > 1 or yf > 1:
            return
        print(f"rel coords: {x}, {y}")
        print(f"frame coords: {xf}, {yf}")

        if self.app.mouseMode == "Outline Fragment":
            self.app.image.annotations[self.app._frame_index].append(Point(x, y))
            if len(self.app.image.annotations[self.app._frame_index]) > 1:
                interped = interpolatePoints(
                    self.app.image.annotations[self.app._frame_index][-2:],
                    self.app.image.imshape,
                )
                self.app.image.interpolated[self.app._frame_index].extend(interped)
            self.app._update_image()
        elif self.app.mouseMode == "Label Ink":
            if len(self.app.image.interpolated[self.app._frame_index]) == 0:
                return
            # find closest point
            closest = self.app.image.interpolated[self.app._frame_index][0]
            closestIndex = 0
            for p in self.app.image.interpolated[self.app._frame_index]:
                if np.linalg.norm(
                    np.array([p.x, p.y]) - np.array([x, y])
                ) < np.linalg.norm(np.array([closest.x, closest.y]) - np.array([x, y])):
                    closest = p
                    closestIndex = self.app.image.interpolated[
                        self.app._frame_index
                    ].index(p)
            # label ink
            closestDist = np.linalg.norm(
                np.array([closest.x, closest.y]) - np.array([x, y])
            )

            if closestDist < 0.01:
                self.app.image.interpolated[self.app._frame_index][
                    closestIndex
                ].updateColor(self.app.annotationColorIdx)

        elif self.app.mouseMode == "Move Points":
            if len(self.app.image.annotations[self.app._frame_index]) == 0:
                return
            # find closest point in annotations and start dragging
            closest = self.app.image.annotations[self.app._frame_index][0]
            closestIndex = 0
            for p in self.app.image.annotations[self.app._frame_index]:
                if np.linalg.norm(
                    np.array([p.x, p.y]) - np.array([x, y])
                ) < np.linalg.norm(np.array([closest.x, closest.y]) - np.array([x, y])):
                    closest = p
                    closestIndex = self.app.image.annotations[
                        self.app._frame_index
                    ].index(p)
            closestDist = np.linalg.norm(
                np.array([closest.x, closest.y]) - np.array([x, y])
            )

            if closestDist < 0.01:
                self.app.dragging = True
                self.app.draggingIndex = closestIndex
                self.app.draggingFrame = self.app._frame_index
                self.app.draggingOffset = np.array([x, y]) - np.array(
                    [closest.x, closest.y]
                )
            self.app._update_image()

        elif self.app.mouseMode == "Pan":
            self.app.panStart = getUnscaledRelCoords(self.app, event.pos())
            self.app.panStartCoords = self.app.image.offset
            self.app.panning = True

        elif self.app.mouseMode == "Delete Points":
            if len(self.app.image.annotations[self.app._frame_index]) == 0:
                return
            # find closest point in annotations and start dragging
            closest = self.app.image.annotations[self.app._frame_index][0]
            closestIndex = 0
            for p in self.app.image.annotations[self.app._frame_index]:
                if np.linalg.norm(
                    np.array([p.x, p.y]) - np.array([x, y])
                ) < np.linalg.norm(np.array([closest.x, closest.y]) - np.array([x, y])):
                    closest = p
                    closestIndex = self.app.image.annotations[
                        self.app._frame_index
                    ].index(p)
            closestDist = np.linalg.norm(
                np.array([closest.x, closest.y]) - np.array([x, y])
            )

            if closestDist < 0.01:
                self.app.image.annotations[self.app._frame_index].pop(closestIndex)
                self.app.image.interpolated[self.app._frame_index] = interpolatePoints(
                    self.app.image.annotations[self.app._frame_index],
                    self.app.image.imshape,
                )
            self.app._update_image()
        else:
            print(f"Warning: mouse mode not recognized: {self.app.mouseMode}")

    # on mouse release, stop dragging
    def mouseReleaseEvent(self, event):
        self.app.clickState = 0
        self.app.dragging = False
        self.app.panning = False

    def mouseMoveEvent(self, event):
        x, y = getRelCoords(self.app, event.pos())

        # self.app.mouse_coordinates.setText(f"Mouse Coordinates: {x:.3f}, {y:.3f}, event: {event.pos().x()}, {event.pos().y()}")
        if self.app.mouseMode == "Move Points":
            if self.app.dragging:
                self.app.image.annotations[self.app.draggingFrame][
                    self.app.draggingIndex
                ].x = (x - self.app.draggingOffset[0])
                self.app.image.annotations[self.app.draggingFrame][
                    self.app.draggingIndex
                ].y = (y - self.app.draggingOffset[1])
                self.app.image.interpolated[self.app.draggingFrame] = interpolatePoints(
                    self.app.image.annotations[self.app.draggingFrame],
                    self.app.image.imshape,
                )
            self.app._update_image()

        elif self.app.mouseMode == "Label Ink":
            if len(self.app.image.interpolated[self.app._frame_index]) == 0:
                return
            if self.app.clickState == 1:
                # find closest point
                closest = self.app.image.interpolated[self.app._frame_index][0]
                closestIndex = 0
                for p in self.app.image.interpolated[self.app._frame_index]:
                    if np.linalg.norm(
                        np.array([p.x, p.y]) - np.array([x, y])
                    ) < np.linalg.norm(
                        np.array([closest.x, closest.y]) - np.array([x, y])
                    ):
                        closest = p
                        closestIndex = self.app.image.interpolated[
                            self.app._frame_index
                        ].index(p)
                # label ink
                closestDist = np.linalg.norm(
                    np.array([closest.x, closest.y]) - np.array([x, y])
                )
                # print(closestDist, "closest dist")
                if closestDist < 0.01:
                    self.app.image.interpolated[self.app._frame_index][
                        closestIndex
                    ].updateColor(self.app.annotationColorIdx)
                self.app._update_image()

        elif self.app.mouseMode == "Pan":
            if self.app.panning:
                pos = getUnscaledRelCoords(self.app, event.pos())
                delta = self.app.panStart - pos
                self.app.image.pan(
                    np.array(
                        [
                            delta.y() * self.app.pixelSize1,
                            delta.x() * self.app.pixelSize0,
                        ]
                    )
                )
                self.app.panStart = pos
                self.app.panStartCoords = self.app.image.offset
                self.app._update_image()
        else:
            print(f"Warning: mouse mode not recognized {self.app.mouseMode}")
