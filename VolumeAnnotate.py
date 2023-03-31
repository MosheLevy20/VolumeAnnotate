from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os
from mImage import mImage
import numpy as np
from Annotations import point
import copy
import pickle
import cv2
import time
from EdgeFinder import findEdges

#TODO:
#filter that takes the high contrast image and adds it to the original image (makes ink pop out while also being able to see the paper)
#also summing in the z axis will probably help signal pop out, seems that way from inspection, but needs to be along edge, not straight z axis
#fix bug with higher resolution images (ink detection is not working)
#add ability to change color of annotation, drop down menu (helpful for discovering which features matter)
#add ability to change size of annotation
#undo/redo, ability to delete points
#need to use processed image for ink detection, refactor processing to be a function
#slider for radius of ink detection
#add measuring tool
#fix only allow clicks on image

#less important aesthetic things
#resolution, i.e. interpolation density
#dropdowns instead of cluttered buttons
#sprites on the buttons
#instructions
#panning via mouse drag, option for mousemode
#another option for mousemode is do nothing
#zooming via mouse wheel
#slider for pan speed 



#unique session id includingtimestamp
sessionId = time.strftime("%Y%m%d-%H%M%S")+"autosave.pkl"

def load_tif(path):
    tif = []
    for filename in os.listdir(path):
        if filename.endswith(".tif"):
            tif.append(path+filename)
    #sort the list by the number in the filename
    tif.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
    #tif = sorted(tif)
    print(tif)
    return tif
#first point: 2590.7200000000003, 2267.4397076735686
#
class App(QWidget):

    def __init__(self, *args):
        super().__init__(*args)
        #set to full screen
        #self.showFullScreen()
        self._frame_list = load_tif("../../campfire/rec/")
        #self._frame_list = load_tif("../../scroll1-1cm/")
        #self._frame_list = load_tif("../../scroll1-1cm-cropped/")
        #self._frame_list = load_tif("zIntImages/")
        #set grid layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.button_reset = QPushButton('Reset', self)
        self.button_reset.clicked.connect(self.on_reset)

        self.button_zoom_in = QPushButton('Zoom In (Up Key)', self)
        self.button_zoom_in.clicked.connect(self.on_zoom_in)

        self.button_zoom_out = QPushButton('Zoom Out (Down Key)', self) 
        self.button_zoom_out.clicked.connect(self.on_zoom_out)

        self.button_next_frame = QPushButton('Next Frame (Right Key)', self) 
        self.button_next_frame.clicked.connect(self.on_next_frame)

        self.button_previous_frame = QPushButton('Previous Frame (Left Key)', self)
        self.button_previous_frame.clicked.connect(self.on_previous_frame)

        #copy previous frame annotations
        self.button_copy = QPushButton('Copy Previous Frame', self)
        self.button_copy.clicked.connect(self.on_copy)

        #save annotations
        self.button_save = QPushButton('Save Annotations', self)
        self.button_save.clicked.connect(self.on_save)
        #load annotations
        self.button_load = QPushButton('Load Annotations', self)
        self.button_load.clicked.connect(self.on_load)

        #save as 2d mask
        self.button_save_2D = QPushButton('Save 2D', self)
        self.button_save_2D.clicked.connect(self.on_save_2D)

        #button that finds ink based on threshold
        self.button_ink = QPushButton('Find Ink', self)
        self.button_ink.clicked.connect(self.on_ink)

        #slider for threshold
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setValue(50)
        #set self.inkThreshold to the value of the slider
        self.slider.valueChanged.connect(self.on_slider_change)
        self.inkThreshold = 50

        #toggle for whether to show annotations
        self.button_show_annotations = QPushButton('Hide Annotations', self)
        self.button_show_annotations.clicked.connect(self.on_show_annotations)
        self.show_annotations = True

        #display mouse coordinates
        self.mouse_coordinates = QLabel(self)
        self.mouse_coordinates.setText("Mouse Coordinates: ")

        #slider for radius of ink detection
        self.slider_ink_radius = QSlider(Qt.Horizontal, self)
        self.slider_ink_radius.setMinimum(0)
        self.slider_ink_radius.setMaximum(30)
        self.slider_ink_radius.setValue(3)
        #set self.inkThreshold to the value of the slider
        self.slider_ink_radius.valueChanged.connect(self.on_slider_ink_radius_change)
        #annotation radius slider
        self.slider_annotation_radius = QSlider(Qt.Horizontal, self)
        self.slider_annotation_radius.setMinimum(0)
        self.slider_annotation_radius.setMaximum(30)
        self.slider_annotation_radius.setValue(5)
        #change annotation radius when slider is changed
        self.slider_annotation_radius.valueChanged.connect(self.on_slider_annotation_radius_change)

        #slider for contrast
        self.slider_contrast = QSlider(Qt.Horizontal, self)
        self.slider_contrast.setMinimum(0)
        self.slider_contrast.setMaximum(30)
        self.slider_contrast.setValue(5)
        
        #change contrast when slider is changed
        self.slider_contrast.valueChanged.connect(self.on_slider_contrast_change)

        #edge detection for the next n frames
        self.button_edge = QPushButton('Edge Detection', self)
        self.button_edge.clicked.connect(self.on_edge)
        #slider for edge detection number of frames
        self.slider_edge = QSlider(Qt.Horizontal, self)
        self.slider_edge.setMinimum(0)
        self.slider_edge.setMaximum(100)
        self.slider_edge.setValue(10)
        self.slider_edge.valueChanged.connect(self.on_slider_edge_change)
        self.edgeDepth = 10

        
        



        
    




        #interpolate fragment
        # self.button_interpolate = QPushButton('Interpolate Fragment', self)
        # self.button_interpolate.clicked.connect(self.on_interpolate)

        #create menu for mouse modes
        self.mouseModeGroup = QButtonGroup()
        self.mouseModeGroup.setExclusive(True)
        self.mouseModeGroup.buttonClicked[int].connect(self.on_mouse_mode)
        self.mouseModeWidget = QWidget()
        self.mouseModeLayout = QVBoxLayout()
        self.mouseModeWidget.setLayout(self.mouseModeLayout)
        self.mouseModeLayout.addWidget(QRadioButton("Outline Fragment"))
        self.mouseModeLayout.addWidget(QRadioButton("Label Ink"))
        self.mouseModeLayout.addWidget(QRadioButton("Move Points"))
        self.mouseModeGroup.addButton(self.mouseModeLayout.itemAt(0).widget(), 0)
        self.mouseModeGroup.addButton(self.mouseModeLayout.itemAt(1).widget(), 1)
        self.mouseModeGroup.addButton(self.mouseModeLayout.itemAt(2).widget(), 2)
        self.mouseModeGroup.button(0).setChecked(True)
        self.mouseMode = "Outline Fragment"


        
        #print(type(self.mouseModeGroup))
        #quit()
        self._frame_index = 0
        self._frame_count = len(self._frame_list)
        #add text for frame number, non editable
        self.frame_number = QLabel(self)
        self.frame_number.setText(f"Slice {self._frame_index+1}/{self._frame_count}")
  
        self.image = mImage(self._frame_list[0], len(self._frame_list))
        #self.pixmap = QPixmap(self._frame_list[0])
    
        self.label = QLabel(self)
        self.label.setPixmap(self.image.getImg(0))
        #self.layout.rowStretch(2)#didn't work, try: 
        self.layout.addWidget(self.label, 0, 0, 30,1)
        self.layout.addWidget(self.button_zoom_in, 2, 2, Qt.AlignTop)
        #the parameters are: row, column, rowspan, colspan, alignment
        self.layout.addWidget(self.button_zoom_out, 2, 1, Qt.AlignTop)
        self.layout.addWidget(self.button_next_frame, 1, 2, Qt.AlignTop)
        self.layout.addWidget(self.button_previous_frame, 1, 1, Qt.AlignTop)
        self.layout.addWidget(self.button_reset, 5,2, Qt.AlignTop)
        self.layout.addWidget(self.frame_number, 3, 2, Qt.AlignTop)
        #add black horizontal line
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        self.layout.addWidget(hline, 4, 1, 1, 3)
        #self.layout.addWidget(, 4, 1, 1, 2)


        #self.layout.addWidget(self.button_interpolate, 6, 2, Qt.AlignTop)
        self.layout.addWidget(self.button_copy, 7, 2, Qt.AlignTop)

        self.layout.addWidget(self.mouseModeWidget, 5, 1, 3,1)

        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        self.layout.addWidget(hline, 8, 1, 1, 3)

        self.layout.addWidget(self.button_save, 9, 2, Qt.AlignTop)
        self.layout.addWidget(self.button_load, 9, 1, Qt.AlignTop)
        self.layout.addWidget(self.button_save_2D, 10, 2, Qt.AlignTop)
        self.layout.addWidget(self.button_ink, 10, 1, Qt.AlignTop)

        self.layout.addWidget(QLabel("Ink Threshold"), 11, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider, 12, 1, 1, 2)
        self.layout.addWidget(self.button_show_annotations, 13, 1, 1, 2)
        self.layout.addWidget(self.mouse_coordinates, 14, 1, 1, 2)

        #add text describing slider
        
        self.layout.addWidget(QLabel("Ink Radius"), 15, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_ink_radius, 16, 1, 1, 2)
        self.inkRadius = 3

        self.layout.addWidget(QLabel("Annotation Radius"), 17, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_annotation_radius, 18, 1, 1, 2)

        self.layout.addWidget(QLabel("Contrast"), 19, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_contrast, 20, 1, 1, 2)

        #button_edge = QPushButton('Edge Threshold', self)
        self.layout.addWidget(self.button_edge, 21, 2, Qt.AlignTop)

        self.layout.addWidget(QLabel("Edge Threshold"), 21, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_edge, 22, 1, 1, 2)



        self.labelingColorIdx = 1
        #self.layout.addWidget(self.mouseModeWidget, 4, 1, Qt.AlignTop)
        
       
        #self.layout.addWidget(self.mouseModeWidget, 4, 1, Qt.AlignTop)
        
        self.panLen = self.image.getImg(self._frame_index).width()/5

        self.pixelSize0 = self.image.img.shape[0]/self.image.getImg(self._frame_index).height()
        self.pixelSize1 = self.image.img.shape[1]/self.image.getImg(self._frame_index).width()
        self.show()


        self.dragging = False
        self.draggingIndex = -1
        self.draggingPoint = None
        self.draggingOffset = None
        
        self.clickState = 0


    def on_mouse_mode(self, id):
        if id == 0:
            self.mouseMode = "Outline Fragment"
        elif id == 1:
            self.mouseMode = "Label Ink"
        elif id == 2:
            self.mouseMode = "Move Points"
        #print(self.mouseMode)

    def on_zoom_in(self, event):
        self.image.zoom(1/1.1)
        self._update_image()

    def on_zoom_out(self, event):
        self.image.zoom(1.1)
        self._update_image()
    
    def on_reset(self, event):
        self.image.reset()
        self._update_image()
    
    def on_next_frame(self, event):
        self._frame_index = (self._frame_index + 1) % self._frame_count
        self._update_frame()
    
    def on_previous_frame(self, event):
        self._frame_index = (self._frame_index - 1) % self._frame_count
        self._update_frame()
    
    # def on_interpolate(self, event):
    #     self.image.interpolate()
    #     self._update_image()
    
    def on_copy(self, event):
        #copy previous frame annotations
        self.image.annotations[self._frame_index] = copy.deepcopy(self.image.annotations[self._frame_index-1])
        self.image.interpolated[self._frame_index] = self.image.interpolatePoints(self.image.annotations[self._frame_index])
        self._update_image()
        with open(sessionId, 'wb') as f:
            pickle.dump(self.image.annotations, f)
            pickle.dump(self.image.interpolated, f)
            pickle.dump(self.image.img.shape, f)
    
    def on_save(self, event):
        #save annotations to file using pickle, pop up window to ask for file name
        filename = QFileDialog.getSaveFileName(self, 'Save File', os.getcwd(), "Pickle Files (*.pkl)")
        if filename[0] != '':
            with open(filename[0], 'wb') as f:
                pickle.dump(self.image.annotations, f)
                pickle.dump(self.image.interpolated, f)
                pickle.dump(self.image.img.shape, f)
    
    def on_load(self, event):
        #load annotations from file using pickle, pop up window to ask for file name
        filename = QFileDialog.getOpenFileName(self, 'Open File', os.getcwd(), "Pickle Files (*.pkl)")
        if filename[0] != '':
            with open(filename[0], 'rb') as f:
                self.image.annotations = pickle.load(f)
                self.image.interpolated = pickle.load(f)
                self.image.imgShape = pickle.load(f)
                self._update_image()
    
    def on_save_2D(self, event):
        image2D = self.image.get2DImage()
        filename = QFileDialog.getSaveFileName(self, 'Save File', os.getcwd(), "PNG Files (*.png)")
        if filename[0] != '':
            #use cv2 to save image
            cv2.imwrite(filename[0], image2D)
            
    def on_ink(self, event):
        self.update_ink()
        self._update_image()
    
    def update_ink(self, index = None):
        if index is None:
            index = self._frame_index
        print(self._frame_list[index], index,'this')
        
        #iterate through all interpolated points and find the average value of the image in a nxn window around the point
        #if the average value is greater than the threshold, then it's ink
        n = self.inkRadius
        #get the image
       
        img = self.image.getProcImg(self._frame_list[index])
        #get the interpolated points
        points = self.image.interpolated[index]
        #loop through all points
        for i in range(len(points)):
            #get the x and y coordinates of the point
            x = points[i].x*img.shape[1]
            y = points[i].y*img.shape[0]
            if i == 0:
                print(f"first point: {x}, {y}")
            #get the average value of the image in a nxn window around the point
            region = img[int(y-n):int(y+n), int(x-n):int(x+n)]
            #get the 90th percentile of the region
            if region.size == 0:
                avg = 0
            else:
                #avg = np.percentile(region, 10)
                avg = np.min(region)
            #print(avg, self.inkThreshold)
            #if the average value is greater than the threshold, then it's ink
            if avg < self.inkThreshold:
                points[i].updateColor(1)
            else:
                points[i].updateColor(0)


    def on_slider_change(self, event):
        self.inkThreshold = self.slider.value()
        self.update_ink()
        self._update_image()

    def on_show_annotations(self, event):
        self.show_annotations = not self.show_annotations
        #change the text of the button to reflect the current state
        if self.show_annotations:
            self.button_show_annotations.setText("Hide Annotations")
        else:
            self.button_show_annotations.setText("Show Annotations")
        self._update_image()

    def on_slider_ink_radius_change(self, event):
        self.inkRadius = self.slider_ink_radius.value()
        self.update_ink()
        self._update_image()
    
    def on_slider_annotation_radius_change(self, event):
        self.image.annotationRadius = self.slider_annotation_radius.value()
        self._update_image()
                
    def on_slider_contrast_change(self, event):
        self.image.contrast = self.slider_contrast.value()
        self._update_image()



    def on_edge(self, event):
        #get the list of image names
        imageNames = self._frame_list[self._frame_index:self._frame_index+self.edgeDepth]
        #use findEdges to get the list of edges
        edges = findEdges(self.image.interpolated[self._frame_index], imageNames)
        print(len(edges), self.edgeDepth)
        #add the edges as the annotations for the next edgeDepth frames
        for i in range(1,self.edgeDepth):
            #print(edges[i])
            print([j.x,j.y] for j in edges[i])
            #annotations is every n'th entry in interpolated, use slice notation
            self.image.annotations[self._frame_index+i] = edges[i][::5]
            self.image.interpolated[self._frame_index+i] = self.image.interpolatePoints(edges[i][::5])
            print("updating ink")
        for i in range(1,self.edgeDepth):   
            self.update_ink(self._frame_index+i)
        #run ink detection on the new annotations
        
        self._update_image()

    def on_slider_edge_change(self, event):
        self.edgeDepth = self.slider_edge.value()
        #self.label_edge.setText(f"Edge Depth: {self.edgeDepth}")


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self._frame_index = (self._frame_index + 1) % self._frame_count
            self._update_frame()
            return
        elif event.key() == Qt.Key_Left:
            self._frame_index = (self._frame_index - 1) % self._frame_count
            self._update_frame()
            return
        elif event.key() == Qt.Key_Up:
            if self.image.scale < 0.11:
                return
            self.image.zoom(1/1.1)
        elif event.key() == Qt.Key_Down:
            if self.image.scale > 10:
                return
            self.image.zoom(1.1)
        #wasd for panning
        elif event.key() == Qt.Key_A:
            self.image.pan(np.array([0, -self.panLen]))
        elif event.key() == Qt.Key_D:
            self.image.pan(np.array([0, self.panLen]))
        elif event.key() == Qt.Key_W:
            self.image.pan(np.array([-self.panLen, 0]))
        elif event.key() == Qt.Key_S:
            self.image.pan(np.array([self.panLen, 0]))
        elif event.key() == Qt.Key_C:
            #copy previous frame annotations
            self.image.annotations[self._frame_index] = copy.deepcopy(self.image.annotations[self._frame_index-1])
            self.image.interpolated[self._frame_index] = self.image.interpolatePoints(self.image.annotations[self._frame_index])
            #self._update_image()
            with open(sessionId, 'wb') as f:
                pickle.dump(self.image.annotations, f)
                pickle.dump(self.image.interpolated, f)
                pickle.dump(self.image.img.shape, f)
   
        self._update_image()
    
    def mousePressEvent(self, event):
        #check if the mouse is out of the image
        # if event.pos().x() > self.image.img.shape[1]*self.image.scale or event.pos().y() > self.image.img.shape[0]*self.image.scale:
        #     return

        self.clickState = 1
        print(f"mouse pressed at {event.pos().x()}, {event.pos().y()}")

        x,y = self.getRelCoords(event.pos())
        print(f"rel coords: {x}, {y}")
        #print image coordinates
        print(f"image coords: {x*self.image.img.shape[1]}, {y*self.image.img.shape[0]}")

        if self.mouseMode == "Outline Fragment":
            self.image.annotations[self._frame_index].append(point(x,y))
            if len(self.image.annotations[self._frame_index]) > 1:
                interped = self.image.interpolatePoints(self.image.annotations[self._frame_index][-2:])
                self.image.interpolated[self._frame_index].extend(interped)
        elif self.mouseMode == "Label Ink":
            if len(self.image.interpolated[self._frame_index]) == 0:
                return
            #find closest point
            closest = self.image.interpolated[self._frame_index][0]
            closestIndex = 0
            for p in self.image.interpolated[self._frame_index]:
                if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                    closest = p
                    closestIndex = self.image.interpolated[self._frame_index].index(p)
            #label ink
            closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
            #print(closestDist, "closest dist")
            if closestDist < 0.01:
                self.image.interpolated[self._frame_index][closestIndex].updateColor(self.labelingColorIdx)

        elif self.mouseMode == "Move Points":
            if len(self.image.annotations[self._frame_index]) == 0:
                return
            #find closest point in annotations and start dragging
            closest = self.image.annotations[self._frame_index][0]
            closestIndex = 0
            for p in self.image.annotations[self._frame_index]:
                if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                    closest = p
                    closestIndex = self.image.annotations[self._frame_index].index(p)
            closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
            #print(closestDist, "closest dist")
            if closestDist < 0.01:
                self.dragging = True
                self.draggingIndex = closestIndex
                self.draggingFrame = self._frame_index
                self.draggingOffset = np.array([x,y])-np.array([closest.x,closest.y])
            
            
        self._update_image()
    
    #on mouse release, stop dragging
    def mouseReleaseEvent(self, event):
        self.clickState = 0
        self.dragging = False
        self._update_image()

    def mouseMoveEvent(self, event):
        
        #print pos of pixmap
   

        x,y = self.getRelCoords(event.pos())
        
        self.mouse_coordinates.setText(f"Mouse Coordinates: {x:.3f}, {y:.3f}, event: {event.pos().x()}, {event.pos().y()}")
        if self.mouseMode == "Move Points":
            if self.dragging:
                self.image.annotations[self.draggingFrame][self.draggingIndex].x = x-self.draggingOffset[0]
                self.image.annotations[self.draggingFrame][self.draggingIndex].y = y-self.draggingOffset[1]
                self.image.interpolated[self.draggingFrame] = self.image.interpolatePoints(self.image.annotations[self.draggingFrame])
            

        elif self.mouseMode == "Label Ink":
            if len(self.image.interpolated[self._frame_index]) == 0:
                return
            if self.clickState == 1:
                #find closest point
                closest = self.image.interpolated[self._frame_index][0]
                closestIndex = 0
                for p in self.image.interpolated[self._frame_index]:
                    if np.linalg.norm(np.array([p.x,p.y])-np.array([x,y])) < np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y])):
                        closest = p
                        closestIndex = self.image.interpolated[self._frame_index].index(p)
                #label ink
                closestDist = np.linalg.norm(np.array([closest.x,closest.y])-np.array([x,y]))
                #print(closestDist, "closest dist")
                if closestDist < 0.01:
                    self.image.interpolated[self._frame_index][closestIndex].updateColor(self.labelingColorIdx)
        self._update_image()
    
    #on resize move label to 20,20
    def resizeEvent(self, event):
        print("resize")
        #move label to 20,20
        self._update_image()
    
    def getRelCoords(self, pos):
        label_pos = self.label.pos()
        image_rect = self.label.pixmap().rect()
        image_pos = QPoint(int(label_pos.x() + (self.label.width() - image_rect.width()) / 2),int(label_pos.y() + (self.label.height() - image_rect.height()) / 2))
        print(f"image pos: {image_pos.x()}, {image_pos.y()}")
        #get pos relative to image 
        pos = pos - image_pos

        x = pos.x()*self.image.scale+self.image.offset[1]/self.pixelSize1
        y = pos.y()*self.image.scale+self.image.offset[0]/self.pixelSize0
        x /= image_rect.height()
        y /= image_rect.width()
        return x,y
            
    def _update_frame(self):
        self.image.setImg(self._frame_list[self._frame_index])
        self.frame_number.setText(f"Slice {self._frame_index+1}/{self._frame_count}")
        self._update_image()
        
    def _update_image(self):
        pmap = self.image.getImg(self._frame_index, self.show_annotations)
        #self.image.showAnnotations(pmap, self._frame_index)
        self.label.setPixmap(pmap)
    


    
#default to full screen

app = QApplication([])
win = App()
#app.setStyle('Fusion')
#app.setStyle('Windows')
#app.setStyle('WindowsVista')
#app.setStyle('Fusion')
#other styles: Windows, WindowsVista, Macintosh, Fusion, Breeze, WindowsXP, WindowsVista, Windows
app.exec()