from main_app.helpers import *
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QSizePolicy

def getLayoutItems(app):
    #returns dict of layout, widgets - name and object
    #app.layout = QGridLayout()
    addItems(app)
    createLayout(app)
    

def find_variable_name(variable):
    for name, value in globals().items():
        if value is variable:
            return name
    return None

def addItems(app):
    app.button_frame_change = QPushButton("Go to Frame", app)
    app.button_frame_change.clicked.connect(app.EH.on_frame_change)

    app.button_zoom_in = QPushButton("Zoom In (\u2191)", app)
    app.button_zoom_in.clicked.connect(app.EH.on_zoom_in)

    app.button_zoom_out = QPushButton("Zoom Out (\u2193)", app)
    app.button_zoom_out.clicked.connect(app.EH.on_zoom_out)

    app.button_next_frame = QPushButton("Next Frame (\u2192)", app)
    # app.button_next_frame.clicked.connect(on_next_frame)
    app.button_next_frame.clicked.connect(app.EH.on_next_frame)

    app.button_previous_frame = QPushButton("Previous Frame (\u2190)", app)
    app.button_previous_frame.clicked.connect(app.EH.on_previous_frame)

    # copy previous frame annotations
    app.button_copy = QPushButton("Copy Prev. Frame", app)
    app.button_copy.clicked.connect(app.EH.on_copy)

    # save annotations
    app.button_save = QPushButton("Save Segment (.pkl)", app)
    app.button_save.clicked.connect(app.EH.on_save)
    # load annotations
    app.button_load = QPushButton("Load Segment (.pkl)", app)
    app.button_load.clicked.connect(app.EH.on_load)

    # save as 2d mask
    app.button_save_2D = QPushButton("Save 2D Projection", app)
    app.button_save_2D.clicked.connect(app.EH.on_save_2D)

    app.button_export_obj = QPushButton("Export .OBJ", app)
    app.button_export_obj.clicked.connect(app.EH.on_export_obj)

    app.button_export_volpkg = QPushButton("Export .volpkg", app)
    app.button_export_volpkg.clicked.connect(app.EH.on_export_to_volpkg)
    #Show 3d preview
    #app.button_show_3D = QPushButton("Show 3D Preview", app)
    #app.button_show_3D.clicked.connect(app.EH.on_show_3D)

    # button that finds ink based on threshold
    # app.button_ink = QPushButton("Find Ink (This Frame)", app)
    # app.button_ink.clicked.connect(app.EH.on_ink)

    # app.button_ink_all = QPushButton("Find Ink (All Frames)", app)
    # app.button_ink_all.clicked.connect(app.EH.on_ink_all)

    # slider for threshold
    # app.slider = QSlider(Qt.Horizontal, app)
    # app.slider.setMinimum(0)
    # app.slider.setMaximum(255)
    # app.slider.setValue(50)
    # # set app.inkThreshold to the value of the slider
    # app.slider.valueChanged.connect(app.EH.on_slider_change)
    # app.inkThreshold = 50

    # toggle for whether to show annotations
    app.button_show_annotations = QPushButton("Hide Annotations", app)
    app.button_show_annotations.clicked.connect(app.EH.on_show_annotations)
    app.show_annotations = True

    # display mouse coordinates
    # app.mouse_coordinates = QLabel(app)
    # app.mouse_coordinates.setText("Mouse Coordinates: ")

    # slider for radius of ink detection
    # app.slider_ink_radius = QSlider(Qt.Horizontal, app)
    # app.slider_ink_radius.setMinimum(0)
    # app.slider_ink_radius.setMaximum(30)
    # app.slider_ink_radius.setValue(3)
    # # set app.inkThreshold to the value of the slider
    # app.slider_ink_radius.valueChanged.connect(app.EH.on_slider_ink_radius_change)
    # annotation radius slider
    app.slider_annotation_radius = QSlider(Qt.Horizontal, app)
    app.slider_annotation_radius.setMinimum(0)
    app.slider_annotation_radius.setMaximum(30)
    app.slider_annotation_radius.setValue(5)
    # change annotation radius when slider is changed
    app.slider_annotation_radius.valueChanged.connect(
        app.EH.on_slider_annotation_radius_change
    )

    # slider for contrast
    # app.slider_contrast = QSlider(Qt.Horizontal, app)
    # app.slider_contrast.setMinimum(0)
    # app.slider_contrast.setMaximum(10)
    # app.slider_contrast.setValue(3)
    # # change contrast when slider is changed
    # app.slider_contrast.valueChanged.connect(app.EH.on_slider_contrast_change)
    app.slider_highlights = QSlider(Qt.Horizontal, app)
    app.slider_highlights.setMinimum(1)
    app.slider_highlights.setMaximum(200)
    app.slider_highlights.setValue(50)
    #change highlights when slider is changed
    app.slider_highlights.valueChanged.connect(app.EH.on_slider_highlights_change)

    #slider for midtones
    app.slider_midtones = QSlider(Qt.Horizontal, app)
    app.slider_midtones.setMinimum(1)
    app.slider_midtones.setMaximum(200)
    app.slider_midtones.setValue(50)
    #change midtones when slider is changed
    app.slider_midtones.valueChanged.connect(app.EH.on_slider_midtones_change)

    #slider for shadows
    app.slider_shadows = QSlider(Qt.Horizontal, app)
    app.slider_shadows.setMinimum(1)
    app.slider_shadows.setMaximum(200)
    app.slider_shadows.setValue(50)
    #change shadows when slider is changed
    app.slider_shadows.valueChanged.connect(app.EH.on_slider_shadows_change)


    # button to invert image
    app.button_invert = QPushButton("Invert Image", app)
    app.button_invert.clicked.connect(app.EH.on_invert)

    # edge detection for the next n frames
    app.button_edge = QPushButton("Edge Detection", app)
    app.button_edge.clicked.connect(app.EH.on_edge)
    # slider for edge detection number of frames
    app.slider_edge = QSlider(Qt.Horizontal, app)
    app.slider_edge.setMinimum(0)
    app.slider_edge.setMaximum(100)
    app.slider_edge.setValue(10)
    app.slider_edge.valueChanged.connect(app.EH.on_slider_edge_change)
    app.edgeDepth = 10
    app.edgeDepthTxt = QLabel(
        f"Edge Detection: Number of Frames = {app.edgeDepth}"
    )

    # create menu for mouse modes
    app.mouseModeGroup = QButtonGroup()
    app.mouseModeGroup.setExclusive(True)
    app.mouseModeGroup.buttonClicked[int].connect(app.EH.on_mouse_mode)
    app.mouseModeWidget = QWidget()
    app.mouseModeLayout = QVBoxLayout()
    app.mouseModeWidget.setLayout(app.mouseModeLayout)
    app.mouseModeLayout.addWidget(QRadioButton("Pan (WASD)"))
    app.mouseModeLayout.addWidget(QRadioButton("Outline Fragment"))
    app.mouseModeLayout.addWidget(QRadioButton("Move Points"))
    app.mouseModeLayout.addWidget(QRadioButton("Delete Points"))
    app.mouseModeLayout.addWidget(QRadioButton("Annotate"))

    app.mouseModeGroup.addButton(app.mouseModeLayout.itemAt(0).widget(), 0)
    app.mouseModeGroup.addButton(app.mouseModeLayout.itemAt(1).widget(), 1)
    app.mouseModeGroup.addButton(app.mouseModeLayout.itemAt(2).widget(), 2)
    app.mouseModeGroup.addButton(app.mouseModeLayout.itemAt(3).widget(), 3)
    app.mouseModeGroup.addButton(app.mouseModeLayout.itemAt(4).widget(), 4)
    app.mouseModeGroup.button(0).setChecked(True)
    app.mouseMode = "Pan"

    # create menu for unwrap style
    app.unwrapStyleGroup = QButtonGroup()
    app.unwrapStyleGroup.setExclusive(True)
    app.unwrapStyleGroup.buttonClicked[int].connect(app.EH.on_unwrap_style)
    app.unwrapStyleWidget = QWidget()
    app.unwrapStyleLayout = QVBoxLayout()
    app.unwrapStyleWidget.setLayout(app.unwrapStyleLayout)
    app.unwrapStyleLayout.addWidget(QRadioButton("Annotations"))
    app.unwrapStyleLayout.addWidget(QRadioButton("Pure Projection"))

    app.unwrapStyleGroup.addButton(app.unwrapStyleLayout.itemAt(0).widget(), 0)
    app.unwrapStyleGroup.addButton(app.unwrapStyleLayout.itemAt(1).widget(), 1)

    app.unwrapStyleGroup.button(0).setChecked(True)
    app.unwrapStyle = "Annotate"

    # create dropdown menu for annotation color using a QComboBox
    app.annotationColorMenu = QComboBox(app)

    # add options to the dropdown menu [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
    app.annotationColorMenu.addItem("Red", QColor(255, 0, 0))
    app.annotationColorMenu.addItem("Green", QColor(0, 255, 0))
    app.annotationColorMenu.addItem("Blue", QColor(0, 0, 255))
    app.annotationColorMenu.addItem("Yellow", QColor(255, 255, 0))
    app.annotationColorMenu.addItem("Magenta", QColor(255, 0, 255))
    app.annotationColorMenu.addItem("Cyan", QColor(0, 255, 255))
    app.annotationColorMenu.currentIndexChanged[int].connect(
        app.EH.on_annotation_color_change
    )
    app.annotationColorIdx = 1
    # set initial color to green
    app.annotationColorMenu.setCurrentIndex(1)


    app.frame_number = QLabel(app)

    app.frame_number.setText(f"Frame {app._frame_index+1}/{app._frame_count}")

    # add text for frame number, editable
    app.frame_edit_display = QLineEdit()
    app.frame_edit_display.setFocusPolicy(Qt.ClickFocus)
    app.frame_edit_display.setText(str(app._frame_index + 1))
    app.frame_edit_display.setValidator(QIntValidator(1, app._frame_count + 1))

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout

def createLayout(app):
    # Create main layout
    main_layout = QHBoxLayout()

    # Create control layout
    control_layout = QVBoxLayout()
    image_layout = QVBoxLayout()

    # Add widgets to control layout
    control_layout.addWidget(app.button_zoom_in)
    control_layout.addWidget(app.button_zoom_out)
    control_layout.addWidget(app.button_next_frame)
    control_layout.addWidget(app.button_previous_frame)

    #control_layout.addWidget(app.label)
    # control_layout.addWidget(app.frame_number)
    # control_layout.addWidget(app.frame_edit_display)
    # control_layout.addWidget(app.button_frame_change)

    # control_layout.addWidget(app.mouseModeWidget)
    # control_layout.addWidget(app.button_show_annotations)
    # control_layout.addWidget(app.annotationColorMenu)
    # control_layout.addWidget(app.slider_annotation_radius)

    # control_layout.addWidget(app.slider_shadows)
    # control_layout.addWidget(app.slider_midtones)
    # control_layout.addWidget(app.slider_highlights)

    # control_layout.addWidget(app.button_invert)
    # control_layout.addWidget(app.button_copy)

    # control_layout.addWidget(app.slider_edge)
    # control_layout.addWidget(app.button_edge)

    # control_layout.addWidget(app.button_export_obj)
    # control_layout.addWidget(app.button_export_volpkg)
    # control_layout.addWidget(app.button_save)
    # control_layout.addWidget(app.button_load)

    # control_layout.addWidget(app.unwrapStyleWidget)
    # control_layout.addWidget(app.button_save_2D)

    app.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    for i in range(control_layout.count()):
        widget = control_layout.itemAt(i).widget()
        if widget is not None:  # Skip layout spacers
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    # Add image to image layout
    image_layout.addWidget(app.label)
    # Add image layout to main layout
    main_layout.addLayout(image_layout)
    # Add control layout to main layout
    main_layout.addLayout(control_layout)

    

    # Set layout
    app.layout = main_layout
