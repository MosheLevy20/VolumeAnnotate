import os
from mImage import mImage
from EdgeFinder import findEdges
from helpers import *
from eventHandlers import *

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



class App(QWidget):

    def __init__(self, *args):
        super().__init__(*args)

        self.sessionId = sessionId
        #set to full screen
        #self.showFullScreen()

        self._frame_list = load_tif("../../campfire/rec/")
        #self._frame_list = load_tif("../../scroll1-1cm/")
        #self._frame_list = load_tif("../../scroll1-1cm-cropped/")
        #self._frame_list = load_tif("zIntImages/")
        #set grid layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self._frame_index = 0
        self._frame_count = len(self._frame_list)
        #add text for frame number, non editable
        self.frame_number = QLabel(self)
        self.frame_number.setText(f"Slice {self._frame_index+1}/{self._frame_count}")
  
        self.image = mImage(self._frame_list[0], len(self._frame_list))



        ########################################################################
        ###################### Buttons and other widgets #######################
        ########################################################################

        self.button_reset = QPushButton('Reset', self)
    
        self.button_reset.clicked.connect(lambda: on_reset(self, None))

        self.button_zoom_in = QPushButton('Zoom In (Up Key)', self)
        self.button_zoom_in.clicked.connect(lambda: on_zoom_in(self, None))

        self.button_zoom_out = QPushButton('Zoom Out (Down Key)', self) 
        self.button_zoom_out.clicked.connect(lambda: on_zoom_out(self, None))

        self.button_next_frame = QPushButton('Next Frame (Right Key)', self) 
        #self.button_next_frame.clicked.connect(on_next_frame)
        self.button_next_frame.clicked.connect(lambda: on_next_frame(self, None))
        

        self.button_previous_frame = QPushButton('Previous Frame (Left Key)', self)
        self.button_previous_frame.clicked.connect(lambda: on_previous_frame(self, None))

        #copy previous frame annotations
        self.button_copy = QPushButton('Copy Previous Frame', self)
        self.button_copy.clicked.connect(lambda: on_copy(self, None))

        #save annotations
        self.button_save = QPushButton('Save Annotations', self)
        self.button_save.clicked.connect(lambda: on_save(self, None))
        #load annotations
        self.button_load = QPushButton('Load Annotations', self)
        self.button_load.clicked.connect(lambda: on_load(self, None))

        #save as 2d mask
        self.button_save_2D = QPushButton('Save 2D', self)
        self.button_save_2D.clicked.connect(lambda: on_save_2D(self, None))

        #button that finds ink based on threshold
        self.button_ink = QPushButton('Find Ink', self)
        self.button_ink.clicked.connect(lambda: on_ink(self, None))

        #slider for threshold
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setValue(50)
        #set self.inkThreshold to the value of the slider
        self.slider.valueChanged.connect(lambda: on_slider_change(self, None))
        self.inkThreshold = 50

        #toggle for whether to show annotations
        self.button_show_annotations = QPushButton('Hide Annotations', self)
        self.button_show_annotations.clicked.connect(lambda: on_show_annotations(self, None))
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
        self.slider_ink_radius.valueChanged.connect(lambda: on_slider_ink_radius_change(self, None))
        #annotation radius slider
        self.slider_annotation_radius = QSlider(Qt.Horizontal, self)
        self.slider_annotation_radius.setMinimum(0)
        self.slider_annotation_radius.setMaximum(30)
        self.slider_annotation_radius.setValue(5)
        #change annotation radius when slider is changed
        self.slider_annotation_radius.valueChanged.connect(lambda: on_slider_annotation_radius_change(self, None))

        #slider for contrast
        self.slider_contrast = QSlider(Qt.Horizontal, self)
        self.slider_contrast.setMinimum(0)
        self.slider_contrast.setMaximum(30)
        self.slider_contrast.setValue(5)
        
        #change contrast when slider is changed
        self.slider_contrast.valueChanged.connect(lambda: on_slider_contrast_change(self, None))

        #edge detection for the next n frames
        self.button_edge = QPushButton('Edge Detection', self)
        self.button_edge.clicked.connect(lambda: on_edge(self, None))
        #slider for edge detection number of frames
        self.slider_edge = QSlider(Qt.Horizontal, self)
        self.slider_edge.setMinimum(0)
        self.slider_edge.setMaximum(100)
        self.slider_edge.setValue(10)
        self.slider_edge.valueChanged.connect(lambda: on_slider_edge_change(self, None))
        self.edgeDepth = 10

        #create menu for mouse modes
        self.mouseModeGroup = QButtonGroup()
        self.mouseModeGroup.setExclusive(True)
        self.mouseModeGroup.buttonClicked[int].connect(lambda: on_mouse_mode(self, None))
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



        ########################################################################
        ############################### Layout #################################
        ########################################################################
    
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


        self.layout.addWidget(QLabel("Ink Radius"), 15, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_ink_radius, 16, 1, 1, 2)
        self.inkRadius = 3

        self.layout.addWidget(QLabel("Annotation Radius"), 17, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_annotation_radius, 18, 1, 1, 2)

        self.layout.addWidget(QLabel("Contrast"), 19, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_contrast, 20, 1, 1, 2)

        self.layout.addWidget(self.button_edge, 21, 2, Qt.AlignTop)

        self.layout.addWidget(QLabel("Edge Threshold"), 21, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_edge, 22, 1, 1, 2)

        self.labelingColorIdx = 1

        self.panLen = self.image.getImg(self._frame_index).width()/5

        self.pixelSize0 = self.image.img.shape[0]/self.image.getImg(self._frame_index).height()
        self.pixelSize1 = self.image.img.shape[1]/self.image.getImg(self._frame_index).width()


        self.show()

        self.dragging = False
        self.draggingIndex = -1
        self.draggingPoint = None
        self.draggingOffset = None
        
        self.clickState = 0
    

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

            
    def _update_frame(self):
        self.image.setImg(self._frame_list[self._frame_index])
        self.frame_number.setText(f"Slice {self._frame_index+1}/{self._frame_count}")
        self._update_image()
        
    def _update_image(self):
        pmap = self.image.getImg(self._frame_index, self.show_annotations)
        #self.image.showAnnotations(pmap, self._frame_index)
        self.label.setPixmap(pmap)

    
    def keyPressEvent(self, event):
        return keyPressEvent(self, event)

    def mousePressEvent(self, event):
        return mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        return mouseMoveEvent(self, event)
    
    def mouseReleaseEvent(self, event):
        return mouseReleaseEvent(self, event)
    


    
#default to full screen

app = QApplication([])
win = App()
#app.setStyle('Fusion')
#app.setStyle('Windows')
#app.setStyle('WindowsVista')
#app.setStyle('Fusion')
#other styles: Windows, WindowsVista, Macintosh, Fusion, Breeze, WindowsXP, WindowsVista, Windows
app.exec()