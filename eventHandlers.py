from helpers import *
import os
def on_mouse_mode(app, id):
    if id == 0:
        app.mouseMode = "Outline Fragment"
    elif id == 1:
        app.mouseMode = "Label Ink"
    elif id == 2:
        app.mouseMode = "Move Points"
    #print(app.mouseMode)

def on_zoom_in(app, event):
    app.image.zoom(1/1.1)
    app._update_image()

def on_zoom_out(app, event):
    app.image.zoom(1.1)
    app._update_image()

def on_reset(app, event):
    app.image.reset()
    app._update_image()

def on_next_frame(app, event):
    app._frame_index = (app._frame_index + 1) % app._frame_count
    app._update_frame()

def on_previous_frame(app, event):
    app._frame_index = (app._frame_index - 1) % app._frame_count
    app._update_frame()

# def on_interpolate(app, event):
#     app.image.interpolate()
#     app._update_image()

def on_copy(app, event):
    #copy previous frame annotations
    app.image.annotations[app._frame_index] = copy.deepcopy(app.image.annotations[app._frame_index-1])
    app.image.interpolated[app._frame_index] = interpolatePoints(app.image.annotations[app._frame_index], app.image.img.shape)
    app._update_image()
    with open(app.sessionId, 'wb') as f:
        pickle.dump(app.image.annotations, f)
        pickle.dump(app.image.interpolated, f)
        pickle.dump(app.image.img.shape, f)

def on_save(app, event):
    #save annotations to file using pickle, pop up window to ask for file name
    filename = QFileDialog.getSaveFileName(app, 'Save File', os.getcwd(), "Pickle Files (*.pkl)")
    if filename[0] != '':
        with open(filename[0], 'wb') as f:
            pickle.dump(app.image.annotations, f)
            pickle.dump(app.image.interpolated, f)
            pickle.dump(app.image.img.shape, f)

def on_load(app, event):
    #load annotations from file using pickle, pop up window to ask for file name
    filename = QFileDialog.getOpenFileName(app, 'Open File', os.getcwd(), "Pickle Files (*.pkl)")
    if filename[0] != '':
        with open(filename[0], 'rb') as f:
            app.image.annotations = pickle.load(f)
            app.image.interpolated = pickle.load(f)
            app.image.imgShape = pickle.load(f)
            app._update_image()

def on_save_2D(app, event):
    image2D = app.image.get2DImage()
    filename = QFileDialog.getSaveFileName(app, 'Save File', os.getcwd(), "PNG Files (*.png)")
    if filename[0] != '':
        #use cv2 to save image
        cv2.imwrite(filename[0], image2D)
        
def on_ink(app, event):
    app.update_ink()
    app._update_image()



def on_slider_change(app, event):
    app.inkThreshold = app.slider.value()
    app.update_ink()
    app._update_image()

def on_show_annotations(app, event):
    app.show_annotations = not app.show_annotations
    #change the text of the button to reflect the current state
    if app.show_annotations:
        app.button_show_annotations.setText("Hide Annotations")
    else:
        app.button_show_annotations.setText("Show Annotations")
    app._update_image()

def on_slider_ink_radius_change(app, event):
    app.inkRadius = app.slider_ink_radius.value()
    app.update_ink()
    app._update_image()

def on_slider_annotation_radius_change(app, event):
    app.image.annotationRadius = app.slider_annotation_radius.value()
    app._update_image()
            
def on_slider_contrast_change(app, event):
    app.image.contrast = app.slider_contrast.value()
    app._update_image()



def on_edge(app, event):
    #get the list of image names
    imageNames = app._frame_list[app._frame_index:app._frame_index+app.edgeDepth]
    #use findEdges to get the list of edges
    edges = findEdges(app.image.interpolated[app._frame_index], imageNames)
    print(len(edges), app.edgeDepth)
    #add the edges as the annotations for the next edgeDepth frames
    for i in range(1,app.edgeDepth):
        #print(edges[i])
        print([j.x,j.y] for j in edges[i])
        #annotations is every n'th entry in interpolated, use slice notation
        app.image.annotations[app._frame_index+i] = edges[i][::5]
        app.image.interpolated[app._frame_index+i] = interpolatePoints(edges[i][::5], app.image.img.shape)
        print("updating ink")
    for i in range(1,app.edgeDepth):   
        app.update_ink(app._frame_index+i)
    #run ink detection on the new annotations
    
    app._update_image()

def on_slider_edge_change(app, event):
    app.edgeDepth = app.slider_edge.value()
    #app.label_edge.setText(f"Edge Depth: {app.edgeDepth}")


def keyPressEvent(app, event):
    if event.key() == Qt.Key_Right:
        app._frame_index = (app._frame_index + 1) % app._frame_count
        app._update_frame()
        return
    elif event.key() == Qt.Key_Left:
        app._frame_index = (app._frame_index - 1) % app._frame_count
        app._update_frame()
        return
    elif event.key() == Qt.Key_Up:
        if app.image.scale < 0.11:
            return
        app.image.zoom(1/1.1)
    elif event.key() == Qt.Key_Down:
        if app.image.scale > 10:
            return
        app.image.zoom(1.1)
    #wasd for panning
    elif event.key() == Qt.Key_A:
        app.image.pan(np.array([0, -app.panLen]))
    elif event.key() == Qt.Key_D:
        app.image.pan(np.array([0, app.panLen]))
    elif event.key() == Qt.Key_W:
        app.image.pan(np.array([-app.panLen, 0]))
    elif event.key() == Qt.Key_S:
        app.image.pan(np.array([app.panLen, 0]))
    elif event.key() == Qt.Key_C:
        #copy previous frame annotations
        app.image.annotations[app._frame_index] = copy.deepcopy(app.image.annotations[app._frame_index-1])
        app.image.interpolated[app._frame_index] = interpolatePoints(app.image.annotations[app._frame_index], app.image.img.shape)
        #app._update_image()
        with open(sessionId, 'wb') as f:
            pickle.dump(app.image.annotations, f)
            pickle.dump(app.image.interpolated, f)
            pickle.dump(app.image.img.shape, f)

    app._update_image()

def mousePressEvent(app, event):
    #check if the mouse is out of the image
    # if event.pos().x() > app.image.img.shape[1]*app.image.scale or event.pos().y() > app.image.img.shape[0]*app.image.scale:
    #     return

    app.clickState = 1
    print(f"mouse pressed at {event.pos().x()}, {event.pos().y()}")

    x,y = app.getRelCoords(event.pos())
    print(f"rel coords: {x}, {y}")
    #print image coordinates
    print(f"image coords: {x*app.image.img.shape[1]}, {y*app.image.img.shape[0]}")

    if app.mouseMode == "Outline Fragment":
        app.image.annotations[app._frame_index].append(Point(x,y))
        if len(app.image.annotations[app._frame_index]) > 1:
            interped = interpolatePoints(app.image.annotations[app._frame_index][-2:], app.image.img.shape)
            app.image.interpolated[app._frame_index].extend(interped)
    elif app.mouseMode == "Label Ink":
        if len(app.image.interpolated[app._frame_index]) == 0:
            return
        #find closest point
        closest = app.image.interpolated[app._frame_index][0]
        closestIndex = 0
        for p in app.image.interpolated[app._frame_index]:
            if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                closest = p
                closestIndex = app.image.interpolated[app._frame_index].index(p)
        #label ink
        closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
        #print(closestDist, "closest dist")
        if closestDist < 0.01:
            app.image.interpolated[app._frame_index][closestIndex].updateColor(app.labelingColorIdx)

    elif app.mouseMode == "Move Points":
        if len(app.image.annotations[app._frame_index]) == 0:
            return
        #find closest point in annotations and start dragging
        closest = app.image.annotations[app._frame_index][0]
        closestIndex = 0
        for p in app.image.annotations[app._frame_index]:
            if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                closest = p
                closestIndex = app.image.annotations[app._frame_index].index(p)
        closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
        #print(closestDist, "closest dist")
        if closestDist < 0.01:
            app.dragging = True
            app.draggingIndex = closestIndex
            app.draggingFrame = app._frame_index
            app.draggingOffset = np.array([x,y])-np.array([closest.x,closest.y])
        
        
    app._update_image()

#on mouse release, stop dragging
def mouseReleaseEvent(app, event):
    app.clickState = 0
    app.dragging = False
    app._update_image()

def mouseMoveEvent(app, event):
    
    #print pos of pixmap


    x,y = app.getRelCoords(event.pos())
    
    app.mouse_coordinates.setText(f"Mouse Coordinates: {x:.3f}, {y:.3f}, event: {event.pos().x()}, {event.pos().y()}")
    if app.mouseMode == "Move Points":
        if app.dragging:
            app.image.annotations[app.draggingFrame][app.draggingIndex].x = x-app.draggingOffset[0]
            app.image.annotations[app.draggingFrame][app.draggingIndex].y = y-app.draggingOffset[1]
            app.image.interpolated[app.draggingFrame] = interpolatePoints(app.image.annotations[app.draggingFrame], app.image.img.shape)
        

    elif app.mouseMode == "Label Ink":
        if len(app.image.interpolated[app._frame_index]) == 0:
            return
        if app.clickState == 1:
            #find closest point
            closest = app.image.interpolated[app._frame_index][0]
            closestIndex = 0
            for p in app.image.interpolated[app._frame_index]:
                if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                    closest = p
                    closestIndex = app.image.interpolated[app._frame_index].index(p)
            #label ink
            closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
            #print(closestDist, "closest dist")
            if closestDist < 0.01:
                app.image.interpolated[app._frame_index][closestIndex].updateColor(app.labelingColorIdx)
    app._update_image()

