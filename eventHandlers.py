from helpers import *
import os
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
            
        #print(self.app.mouseMode)

    def on_zoom_in(self, event):
        self.app.image.zoom(1/1.1)
        

    def on_zoom_out(self, event):
        self.app.image.zoom(1.1)
        

    def on_reset(self, event):
        self.app.image.reset()
        

    def on_next_frame(self, event):
        self.app._frame_index = (self.app._frame_index + 1) % self.app._frame_count
        self.app._update_frame()

    def on_previous_frame(self, event):
        self.app._frame_index = (self.app._frame_index - 1) % self.app._frame_count
        self.app._update_frame()


    def on_copy(self, event):
        #copy previous frame annotations
        self.app.image.annotations[self.app._frame_index] = copy.deepcopy(self.app.image.annotations[self.app._frame_index-1])
        self.app.image.interpolated[self.app._frame_index] = interpolatePoints(self.app.image.annotations[self.app._frame_index], self.app.image.img.shape)
        
        with open(self.app.sessionId, 'wb') as f:
            pickle.dump(self.app.image.annotations, f)
            pickle.dump(self.app.image.interpolated, f)
            pickle.dump(self.app.image.img.shape, f)

    def on_save(self, event):
        #save annotations to file using pickle, pop up window to ask for file name
        filename = QFileDialog.getSaveFileName(self.app, 'Save File', os.getcwd(), "Pickle Files (*.pkl)")
        if filename[0] != '':
            with open(filename[0], 'wb') as f:
                pickle.dump(self.app.image.annotations, f)
                pickle.dump(self.app.image.interpolated, f)
                pickle.dump(self.app.image.img.shape, f)

    def on_load(self, event):
        #load annotations from file using pickle, pop up window to ask for file name
        filename = QFileDialog.getOpenFileName(self.app, 'Open File', os.getcwd(), "Pickle Files (*.pkl)")
        if filename[0] != '':
            with open(filename[0], 'rb') as f:
                self.app.image.annotations = pickle.load(f)
                self.app.image.interpolated = pickle.load(f)
                self.app.image.imgShape = pickle.load(f)
                

    def on_save_2D(self, event):
        image2D = self.app.image.get2DImage()
        filename = QFileDialog.getSaveFileName(self.app, 'Save File', os.getcwd(), "PNG Files (*.png)")
        if filename[0] != '':
            #use cv2 to save image
            cv2.imwrite(filename[0], image2D)
            
    def on_ink(self, event):
        self.app.update_ink()
        


    def on_slider_change(self, event):
        self.app.inkThreshold = self.app.slider.value()
        self.app.update_ink()
        

    def on_show_annotations(self, event):
        self.app.show_annotations = not self.app.show_annotations
        #change the text of the button to reflect the current state
        if self.app.show_annotations:
            self.app.button_show_annotations.setText("Hide Annotations")
        else:
            self.app.button_show_annotations.setText("Show Annotations")
        

    def on_slider_ink_radius_change(self, event):
        self.app.inkRadius = self.app.slider_ink_radius.value()
        self.app.update_ink()
        

    def on_slider_annotation_radius_change(self, event):
        self.app.image.annotationRadius = self.app.slider_annotation_radius.value()
        
                
    def on_slider_contrast_change(self, event):
        self.app.image.contrast = self.app.slider_contrast.value()
        



    def on_edge(self, event):
        #get the list of image names
        imageNames = self.app._frame_list[self.app._frame_index:self.app._frame_index+self.app.edgeDepth]
        #use findEdges to get the list of edges
        edges = findEdges(self.app.image.interpolated[self.app._frame_index], imageNames)
        print(len(edges), self.app.edgeDepth)
        #add the edges as the annotations for the next edgeDepth frames
        for i in range(1,self.app.edgeDepth):
            #print(edges[i])
            print([j.x,j.y] for j in edges[i])
            #annotations is every n'th entry in interpolated, use slice notation
            self.app.image.annotations[self.app._frame_index+i] = edges[i][::5]
            self.app.image.interpolated[self.app._frame_index+i] = interpolatePoints(edges[i][::5], self.app.image.img.shape)
            print("updating ink")
        for i in range(1,self.app.edgeDepth):   
            self.app.update_ink(self.app._frame_index+i)
        #run ink detection on the new annotations
        
        

    def on_slider_edge_change(self, event):
        self.app.edgeDepth = self.app.slider_edge.value()
        #self.app.label_edge.setText(f"Edge Depth: {self.app.edgeDepth}")


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.app._frame_index = (self.app._frame_index + 1) % self.app._frame_count
            self.app._update_frame()
            return
        elif event.key() == Qt.Key_Left:
            self.app._frame_index = (self.app._frame_index - 1) % self.app._frame_count
            self.app._update_frame()
            return
        elif event.key() == Qt.Key_Up:
            if self.app.image.scale < 0.11:
                return
            self.app.image.zoom(1/1.1)
        elif event.key() == Qt.Key_Down:
            if self.app.image.scale > 10:
                return
            self.app.image.zoom(1.1)
        #wasd for panning
        elif event.key() == Qt.Key_A:
            self.app.image.pan(np.array([0, -self.app.panLen]))
        elif event.key() == Qt.Key_D:
            self.app.image.pan(np.array([0, self.app.panLen]))
        elif event.key() == Qt.Key_W:
            self.app.image.pan(np.array([-self.app.panLen, 0]))
        elif event.key() == Qt.Key_S:
            self.app.image.pan(np.array([self.app.panLen, 0]))
        elif event.key() == Qt.Key_C:
            #copy previous frame annotations
            self.app.image.annotations[self.app._frame_index] = copy.deepcopy(self.app.image.annotations[self.app._frame_index-1])
            self.app.image.interpolated[self.app._frame_index] = interpolatePoints(self.app.image.annotations[self.app._frame_index], self.app.image.img.shape)
            #
            with open(sessionId, 'wb') as f:
                pickle.dump(self.app.image.annotations, f)
                pickle.dump(self.app.image.interpolated, f)
                pickle.dump(self.app.image.img.shape, f)

        

    def mousePressEvent(self, event):
        #check if the mouse is out of the image
        # if event.pos().x() > self.app.image.img.shape[1]*self.app.image.scale or event.pos().y() > self.app.image.img.shape[0]*self.app.image.scale:
        #     return

        self.app.clickState = 1
        print(f"mouse pressed at {event.pos().x()}, {event.pos().y()}")

        x,y = getRelCoords(self.app,event.pos())
        if x < 0 or y < 0 or x > 1 or y > 1:
            return
        print(f"rel coords: {x}, {y}")
        #print image coordinates
        print(f"image coords: {x*self.app.image.img.shape[1]}, {y*self.app.image.img.shape[0]}")

        if self.app.mouseMode == "Outline Fragment":
            self.app.image.annotations[self.app._frame_index].append(Point(x,y))
            if len(self.app.image.annotations[self.app._frame_index]) > 1:
                interped = interpolatePoints(self.app.image.annotations[self.app._frame_index][-2:], self.app.image.img.shape)
                self.app.image.interpolated[self.app._frame_index].extend(interped)
        elif self.app.mouseMode == "Label Ink":
            if len(self.app.image.interpolated[self.app._frame_index]) == 0:
                return
            #find closest point
            closest = self.app.image.interpolated[self.app._frame_index][0]
            closestIndex = 0
            for p in self.app.image.interpolated[self.app._frame_index]:
                if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                    closest = p
                    closestIndex = self.app.image.interpolated[self.app._frame_index].index(p)
            #label ink
            closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
            #print(closestDist, "closest dist")
            if closestDist < 0.01:
                self.app.image.interpolated[self.app._frame_index][closestIndex].updateColor(self.app.labelingColorIdx)

        elif self.app.mouseMode == "Move Points":
            if len(self.app.image.annotations[self.app._frame_index]) == 0:
                return
            #find closest point in annotations and start dragging
            closest = self.app.image.annotations[self.app._frame_index][0]
            closestIndex = 0
            for p in self.app.image.annotations[self.app._frame_index]:
                if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                    closest = p
                    closestIndex = self.app.image.annotations[self.app._frame_index].index(p)
            closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
            #print(closestDist, "closest dist")
            if closestDist < 0.01:
                self.app.dragging = True
                self.app.draggingIndex = closestIndex
                self.app.draggingFrame = self.app._frame_index
                self.app.draggingOffset = np.array([x,y])-np.array([closest.x,closest.y])
        
        elif self.app.mouseMode == "Pan":
            self.app.panStart = getUnscaledRelCoords(self.app, event.pos())
            self.app.panStartCoords = self.app.image.offset
            self.app.panning = True
        
        elif self.app.mouseMode == "Delete Points":
            if len(self.app.image.annotations[self.app._frame_index]) == 0:
                return
            #find closest point in annotations and start dragging
            closest = self.app.image.annotations[self.app._frame_index][0]
            closestIndex = 0
            for p in self.app.image.annotations[self.app._frame_index]:
                if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                    closest = p
                    closestIndex = self.app.image.annotations[self.app._frame_index].index(p)
            closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
            #print(closestDist, "closest dist")
            if closestDist < 0.01:
                self.app.image.annotations[self.app._frame_index].pop(closestIndex)
                self.app.image.interpolated[self.app._frame_index] = interpolatePoints(self.app.image.annotations[self.app._frame_index], self.app.image.img.shape)

            
            
        

    #on mouse release, stop dragging
    def mouseReleaseEvent(self, event):
        self.app.clickState = 0
        self.app.dragging = False
        self.app.panning = False
        

    def mouseMoveEvent(self, event):
        
        #print pos of pixmap


        x,y = getRelCoords(self.app, event.pos())
        
        self.app.mouse_coordinates.setText(f"Mouse Coordinates: {x:.3f}, {y:.3f}, event: {event.pos().x()}, {event.pos().y()}")
        if self.app.mouseMode == "Move Points":
            if self.app.dragging:
                self.app.image.annotations[self.app.draggingFrame][self.app.draggingIndex].x = x-self.app.draggingOffset[0]
                self.app.image.annotations[self.app.draggingFrame][self.app.draggingIndex].y = y-self.app.draggingOffset[1]
                self.app.image.interpolated[self.app.draggingFrame] = interpolatePoints(self.app.image.annotations[self.app.draggingFrame], self.app.image.img.shape)
            

        elif self.app.mouseMode == "Label Ink":
            if len(self.app.image.interpolated[self.app._frame_index]) == 0:
                return
            if self.app.clickState == 1:
                #find closest point
                closest = self.app.image.interpolated[self.app._frame_index][0]
                closestIndex = 0
                for p in self.app.image.interpolated[self.app._frame_index]:
                    if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                        closest = p
                        closestIndex = self.app.image.interpolated[self.app._frame_index].index(p)
                #label ink
                closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
                #print(closestDist, "closest dist")
                if closestDist < 0.01:
                    self.app.image.interpolated[self.app._frame_index][closestIndex].updateColor(self.app.labelingColorIdx)
        
        elif self.app.mouseMode == "Pan":
            if self.app.panning:
                #self.app.image.offset should be updated
                x,y = self.app.panStart.x(), self.app.panStart.y()
                # X,Y = getRelCoords(self.app, event.pos())
                # X *= self.app.image.img.shape[1]
                # Y *= self.app.image.img.shape[0]
                pos = getUnscaledRelCoords(self.app, event.pos())
                X,Y = pos.x(), pos.y()
                deltax = (x - X)
                deltay = (y - Y)
                self.app.image.offset = (deltay+self.app.panStartCoords[0], deltax+self.app.panStartCoords[1])
