from mImage import mImage
from helpers import *
from eventHandlers import *


# unique session id including timestamp, for autosaving progress
sessionId0 = time.strftime("%Y%m%d%H%M%S") 
sessionId = sessionId0 + "autosave.pkl"



class App(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.EH = EventHandler(self)

        self.sessionId = sessionId
        self.sessionId0 = sessionId0
        # set to full screen
        # self.showFullScreen()
        print(folder)
        #self.volpkg = Volpkg(folder, sessionId0)
        #self.loader = Loader(self.volpkg.img_array, max_mem_gb=3)
        img_array, _ = load_tif(folder)
        self.loader = Loader(img_array, max_mem_gb=3)

        # set grid layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self._frame_index = 0
        self._frame_count = img_array.shape[0]
        # add text for frame number, non editable
        self.frame_number = QLabel(self)
        self.frame_number.setText(f"Frame {self._frame_index+1}/{self._frame_count}")

        # add text for frame number, editable
        self.frame_edit_display = QLineEdit()
        self.frame_edit_display.setFocusPolicy(Qt.ClickFocus)
        self.frame_edit_display.setText(str(self._frame_index + 1))
        self.frame_edit_display.setValidator(QIntValidator(1, self._frame_count + 1))
        # self.frame_edit_display.editingFinished.connect(self.on_frame_edited())

        print("Initializing image")
        self.label = QLabel(self)
        self.image = mImage(self._frame_count, self.loader)
        print("Image initialized")

        ########################################################################
        ###################### Buttons and other widgets #######################
        ########################################################################

        self.button_frame_change = QPushButton("Go to Frame", self)
        self.button_frame_change.clicked.connect(self.EH.on_frame_change)

        self.button_zoom_in = QPushButton("Zoom In (\u2191)", self)
        self.button_zoom_in.clicked.connect(self.EH.on_zoom_in)

        self.button_zoom_out = QPushButton("Zoom Out (\u2193)", self)
        self.button_zoom_out.clicked.connect(self.EH.on_zoom_out)

        self.button_next_frame = QPushButton("Next Frame (\u2192)", self)
        # self.button_next_frame.clicked.connect(on_next_frame)
        self.button_next_frame.clicked.connect(self.EH.on_next_frame)

        self.button_previous_frame = QPushButton("Previous Frame (\u2190)", self)
        self.button_previous_frame.clicked.connect(self.EH.on_previous_frame)

        # copy previous frame annotations
        self.button_copy = QPushButton("Copy Prev. Frame", self)
        self.button_copy.clicked.connect(self.EH.on_copy)

        # save annotations
        self.button_save = QPushButton("Save To volpkg", self)
        self.button_save.clicked.connect(self.EH.on_save)
        # load annotations
        self.button_load = QPushButton("Load Annotations (.pkl)", self)
        self.button_load.clicked.connect(self.EH.on_load)

        # save as 2d mask
        self.button_save_2D = QPushButton("Save 2D Projection", self)
        self.button_save_2D.clicked.connect(self.EH.on_save_2D)

        #Show 3d preview
        # self.button_show_3D = QPushButton("Show 3D Preview", self)
        # self.button_show_3D.clicked.connect(self.EH.on_show_3D)

        # button that finds ink based on threshold
        self.button_ink = QPushButton("Find Ink (This Frame)", self)
        self.button_ink.clicked.connect(self.EH.on_ink)

        self.button_ink_all = QPushButton("Find Ink (All Frames)", self)
        self.button_ink_all.clicked.connect(self.EH.on_ink_all)

        # slider for threshold
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setValue(50)
        # set self.inkThreshold to the value of the slider
        self.slider.valueChanged.connect(self.EH.on_slider_change)
        self.inkThreshold = 50

        # toggle for whether to show annotations
        self.button_show_annotations = QPushButton("Hide Annotations", self)
        self.button_show_annotations.clicked.connect(self.EH.on_show_annotations)
        self.show_annotations = True

        # display mouse coordinates
        # self.mouse_coordinates = QLabel(self)
        # self.mouse_coordinates.setText("Mouse Coordinates: ")

        # slider for radius of ink detection
        self.slider_ink_radius = QSlider(Qt.Horizontal, self)
        self.slider_ink_radius.setMinimum(0)
        self.slider_ink_radius.setMaximum(30)
        self.slider_ink_radius.setValue(3)
        # set self.inkThreshold to the value of the slider
        self.slider_ink_radius.valueChanged.connect(self.EH.on_slider_ink_radius_change)
        # annotation radius slider
        self.slider_annotation_radius = QSlider(Qt.Horizontal, self)
        self.slider_annotation_radius.setMinimum(0)
        self.slider_annotation_radius.setMaximum(30)
        self.slider_annotation_radius.setValue(5)
        # change annotation radius when slider is changed
        self.slider_annotation_radius.valueChanged.connect(
            self.EH.on_slider_annotation_radius_change
        )

        # slider for contrast
        self.slider_contrast = QSlider(Qt.Horizontal, self)
        self.slider_contrast.setMinimum(0)
        self.slider_contrast.setMaximum(10)
        self.slider_contrast.setValue(3)
        # change contrast when slider is changed
        self.slider_contrast.valueChanged.connect(self.EH.on_slider_contrast_change)

        # button to invert image
        self.button_invert = QPushButton("Invert Image", self)
        self.button_invert.clicked.connect(self.EH.on_invert)

        # edge detection for the next n frames
        self.button_edge = QPushButton("Edge Detection", self)
        self.button_edge.clicked.connect(self.EH.on_edge)
        # slider for edge detection number of frames
        self.slider_edge = QSlider(Qt.Horizontal, self)
        self.slider_edge.setMinimum(0)
        self.slider_edge.setMaximum(100)
        self.slider_edge.setValue(10)
        self.slider_edge.valueChanged.connect(self.EH.on_slider_edge_change)
        self.edgeDepth = 10
        self.edgeDepthTxt = QLabel(
            f"Edge Detection: Number of Frames = {self.edgeDepth}"
        )

        # create menu for mouse modes
        self.mouseModeGroup = QButtonGroup()
        self.mouseModeGroup.setExclusive(True)
        self.mouseModeGroup.buttonClicked[int].connect(self.EH.on_mouse_mode)
        self.mouseModeWidget = QWidget()
        self.mouseModeLayout = QVBoxLayout()
        self.mouseModeWidget.setLayout(self.mouseModeLayout)
        self.mouseModeLayout.addWidget(QRadioButton("Pan (WASD)"))
        self.mouseModeLayout.addWidget(QRadioButton("Outline Fragment"))
        self.mouseModeLayout.addWidget(QRadioButton("Move Points"))
        self.mouseModeLayout.addWidget(QRadioButton("Delete Points"))
        self.mouseModeLayout.addWidget(QRadioButton("Annotate"))

        self.mouseModeGroup.addButton(self.mouseModeLayout.itemAt(0).widget(), 0)
        self.mouseModeGroup.addButton(self.mouseModeLayout.itemAt(1).widget(), 1)
        self.mouseModeGroup.addButton(self.mouseModeLayout.itemAt(2).widget(), 2)
        self.mouseModeGroup.addButton(self.mouseModeLayout.itemAt(3).widget(), 3)
        self.mouseModeGroup.addButton(self.mouseModeLayout.itemAt(4).widget(), 4)
        self.mouseModeGroup.button(0).setChecked(True)
        self.mouseMode = "Pan"

        # create menu for unwrap style
        self.unwrapStyleGroup = QButtonGroup()
        self.unwrapStyleGroup.setExclusive(True)
        self.unwrapStyleGroup.buttonClicked[int].connect(self.EH.on_unwrap_style)
        self.unwrapStyleWidget = QWidget()
        self.unwrapStyleLayout = QVBoxLayout()
        self.unwrapStyleWidget.setLayout(self.unwrapStyleLayout)
        self.unwrapStyleLayout.addWidget(QRadioButton("Annotations"))
        self.unwrapStyleLayout.addWidget(QRadioButton("Pure Projection"))

        self.unwrapStyleGroup.addButton(self.unwrapStyleLayout.itemAt(0).widget(), 0)
        self.unwrapStyleGroup.addButton(self.unwrapStyleLayout.itemAt(1).widget(), 1)

        self.unwrapStyleGroup.button(0).setChecked(True)
        self.unwrapStyle = "Annotate"

        # create dropdown menu for annotation color using a QComboBox
        self.annotationColorMenu = QComboBox(self)

        # add options to the dropdown menu [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
        self.annotationColorMenu.addItem("Red", QColor(255, 0, 0))
        self.annotationColorMenu.addItem("Green", QColor(0, 255, 0))
        self.annotationColorMenu.addItem("Blue", QColor(0, 0, 255))
        self.annotationColorMenu.addItem("Yellow", QColor(255, 255, 0))
        self.annotationColorMenu.addItem("Magenta", QColor(255, 0, 255))
        self.annotationColorMenu.addItem("Cyan", QColor(0, 255, 255))
        self.annotationColorMenu.currentIndexChanged[int].connect(
            self.EH.on_annotation_color_change
        )
        self.annotationColorIdx = 1
        # set initial color to green
        self.annotationColorMenu.setCurrentIndex(1)

        ########################################################################
        ############################### Layout #################################
        ########################################################################

        print("Setting pixmap")
        self.label.setPixmap(self.image.getImg(0))
        print("Finished pixmap")
        # self.layout.rowStretch(2)#didn't work, try:
        self.layout.addWidget(self.label, 0, 0, 30, 1)
        self.layout.addWidget(self.button_zoom_in, 4, 2, Qt.AlignRight)
        # the parameters are: row, column, rowspan, colspan, alignment
        self.layout.addWidget(self.button_zoom_out, 4, 1, Qt.AlignLeft)
        self.layout.addWidget(self.button_next_frame, 1, 2, Qt.AlignRight)
        self.layout.addWidget(self.button_previous_frame, 1, 1, Qt.AlignLeft)

        self.layout.addWidget(self.frame_number, 2, 1, 1, 2, Qt.AlignCenter)
        self.layout.addWidget(self.frame_edit_display, 3, 1, 1, 1, Qt.AlignLeft)
        self.layout.addWidget(self.button_frame_change, 3, 1, 1, 2, Qt.AlignRight)

        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        self.layout.addWidget(hline, 5, 1, 1, 3)

        self.layout.addWidget(self.mouseModeWidget, 5, 1, 6, 1)
        self.layout.addWidget(self.button_show_annotations, 6, 2, 1, 1)

        self.layout.addWidget(QLabel("Annotation Color:"), 7, 2, Qt.AlignCenter)
        self.layout.addWidget(self.annotationColorMenu, 8, 2, 1, 1)

        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        self.layout.addWidget(hline, 10, 1, 1, 3)

        self.layout.addWidget(QLabel("Ink Threshold"), 11, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider, 11, 2, 1, 1)

        self.layout.addWidget(QLabel("Ink Radius"), 12, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_ink_radius, 12, 2, 1, 1)
        self.inkRadius = 3

        self.layout.addWidget(QLabel("Annotation Radius"), 13, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_annotation_radius, 13, 2, 1, 1)

        self.layout.addWidget(QLabel("Contrast"), 14, 1, Qt.AlignRight)
        self.layout.addWidget(self.slider_contrast, 14, 2, 1, 1)

        self.layout.addWidget(self.button_ink, 15, 1, 1, 1)
        self.layout.addWidget(self.button_ink_all, 15, 2, 1, 1)

        self.layout.addWidget(self.button_invert, 16, 1, Qt.AlignTop)
        self.layout.addWidget(self.button_copy, 16, 2, Qt.AlignTop)

        self.layout.addWidget(self.button_edge, 19, 1, 1, 2, Qt.AlignTop)

        self.layout.addWidget(self.edgeDepthTxt, 17, 1, 1, 2, Qt.AlignCenter)
        self.layout.addWidget(self.slider_edge, 18, 1, 1, 2)

        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        self.layout.addWidget(hline, 20, 1, 1, 3)

        self.layout.addWidget(self.button_save, 22, 1, 1, 2, Qt.AlignCenter)
        self.layout.addWidget(self.button_load, 23, 1, 1, 2, Qt.AlignCenter)

        self.layout.addWidget(QLabel("Projection Style:"), 24, 1, 1, 2, Qt.AlignCenter)
        self.layout.addWidget(self.unwrapStyleWidget, 25, 1, 1, 2, Qt.AlignCenter)
        self.layout.addWidget(self.button_save_2D, 26, 1, 1, 2, Qt.AlignCenter)

        #self.layout.addWidget(self.button_show_3D, 27, 1, 1, 2, Qt.AlignCenter)
        
        if self.image.img is None:
            print("trace")
            self.image.getImg(self._frame_index)
        self.panLen = self.image.img.width() / 5

        self.pixelSize0 = (
            self.image.shape[0] / self.image.img.height()
        )
        self.pixelSize1 = (
            self.image.shape[1] / self.image.img.width()
        )

        self.show()

        self.dragging = False
        self.draggingIndex = -1
        self.draggingPoint = None
        self.draggingOffset = None

        self.panning = False

        self.clickState = 0

    def update_ink(self, index=None):
        if index is None:
            index = self._frame_index

        n = self.inkRadius
        # get the image

        img = self.image.normalize_image(index=index)
        # get the interpolated points
        points = self.image.interpolated[index]
        # loop through all points
        for i in range(len(points)):
            # get the x and y coordinates of the point
            x = points[i].x * img.shape[0]
            y = points[i].y * img.shape[1]

            # get the average value of the image in a nxn window around the point
            region = img[int(y - n) : int(y + n), int(x - n) : int(x + n)]
            # get the 90th percentile of the region
            if region.size == 0:
                val = 0
            else:
                if self.image.invert:
                    val = np.min(region)
                else:
                    val = np.max(region)
            # if the average value is greater than the threshold, then it's ink
            inkIdx = 1
            if self.image.invert:
                inkIdx = 0
            if val > self.inkThreshold:
                points[i].updateColor(inkIdx)
            else:
                points[i].updateColor(1 - inkIdx)

    def _update_frame(self):
        # self.image.setImg(self._frame_index)
        self.frame_number.setText(f"Frame: {self._frame_index+1}/{self._frame_count}")
        self._update_image()

    def _update_image(self):
        pmap = self.image.getImg(self._frame_index, self.show_annotations)
        self.label.setPixmap(pmap)

    def keyPressEvent(self, event):
        return self.EH.keyPressEvent(event)

    def mousePressEvent(self, event):
        return self.EH.mousePressEvent(event)

    def mouseMoveEvent(self, event):
        return self.EH.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        return self.EH.mouseReleaseEvent(event)
    






app = QApplication([])
# on startup request folder
folder = QFileDialog.getExistingDirectory(None, "Select Directory")
win = App(folder=folder)
print("App initialized")
app.exec()
