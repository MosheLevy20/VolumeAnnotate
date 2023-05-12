from .mImage import mImage
from .helpers import *
from . import modes
from .loading import Loader, RemoteZarr, load_tif
import importlib
# unique session id including timestamp, for autosaving progress
sessionId0 = time.strftime("%Y%m%d%H%M%S") 
sessionId = sessionId0 + "autosave.pkl"

class App(QWidget):
	def __init__(self, *args, STREAM=False, scroll="scroll1", mode="classic", downpath=None, folder=None):
		super().__init__(*args)
		self.mode = importlib.import_module(f'{modes.__name__}.{mode}')

		self.EH = self.mode.eventHandlers.EventHandler(self)

		self.sessionId = sessionId
		self.sessionId0 = sessionId0

		t0 = time.time()
		if STREAM:
			urls = {"scroll1":"http://dl.ash2txt.org/full-scrolls/Scroll1.volpkg/volumes_masked/20230205180739/", 
			"scroll2":"http://dl.ash2txt.org/full-scrolls/Scroll2.volpkg/volumes_masked/20230210143520/",
			}
			urlsSmall = {"scroll1":"http://dl.ash2txt.org/full-scrolls/Scroll1.volpkg/volumes_small/20230205180739/",
						 "scroll2":"http://dl.ash2txt.org/full-scrolls/Scroll2.volpkg/volumes_small/20230210143520/",}

			username = "registeredusers"
			password = "only"
			self.scroll = scroll
			downpath = os.path.join(downpath, scroll+"_downloads")
			#check if downpath exists
			if not os.path.exists(downpath):
				os.makedirs(downpath)
			img_array = RemoteZarr(urls[scroll], username, password, downpath, max_storage_gb=20)
		else:
			print(folder)
			img_array, tiffs = load_tif(folder)
			self.tiffs = [folder + "/" + t for t in tiffs]
			print(f"img_array: {img_array.shape}")
		self.loader = Loader(img_array, STREAM, max_mem_gb=8)
		

		self._frame_index = 0
		if STREAM:
			self._frame_count = img_array.file_list.shape[0]
		else:
			self._frame_count = img_array.shape[0]
		# add text for frame number, non editable
		print("Initializing image")
		self.label = QLabel(self)
		self.image = mImage(self._frame_count, self.loader)
		print(self.loader.shape, "Lshape")
		print("Image initialized")
		print("Setting pixmap")
		self.label.setPixmap(self.image.getImg(0))
		print("Finished pixmap")
		
		
		if self.image.img is None:
			self.image.getImg(self._frame_index)
		self.panLen = self.image.img.width() / 5

		self.pixelSize0 = self.image.loaded_shape[0] / self.image.img.height()
		self.pixelSize1 = self.image.loaded_shape[1] / self.image.img.width()

		# set grid layout, and assign widgets to app attributes
		self.mode.layout.getLayoutItems(self)
		
		self.setLayout(self.layout)
		

		

		self.dragging = False
		self.draggingIndex = -1
		self.draggingPoint = None
		self.draggingOffset = None
		self.panning = False
		self.clickState = 0

		self.show()


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
	
	def wheelEvent(self, event):
		return self.EH.wheelEvent(event)
	





class StartupDialog(QDialog):
	def __init__(self, *args):
		super().__init__()
		self.app = args[0]
		#get list of all folders in modes
		modePath = os.path.dirname(modes.__file__)
		#get all folders in modes that contain __init__.py
		modeFolders = [f for f in os.listdir(modePath) if os.path.isdir(os.path.join(modePath, f)) and "__init__.py" in os.listdir(os.path.join(modePath, f))]
		self.setWindowTitle("Select data source")
		self.setWindowModality(Qt.ApplicationModal)
		self.resize(400, 200)
		
		# Set up the layout
		layout = QVBoxLayout()


		# Add a label
		layout.addWidget(QLabel("Select data source:"))

		# Add radio buttons for data source options
		#self.stream_data = QRadioButton("Stream data (Disabled for now)")
		layout.addWidget(QLabel("Stream data disabled for now"))
		self.local_data = QRadioButton("Load data from local directory")
		#layout.addWidget(self.stream_data)
		layout.addWidget(self.local_data)

		# Add a button to browse for a local directory (disabled by default)
		#add text for directory selection
		layout.addWidget(QLabel("Select local directory:"))
		self.browse_button = QPushButton("Browse")
		self.browse_button.setEnabled(True)
		layout.addWidget(self.browse_button)

		# Add a line edit to display the selected local directory path
		self.directory_path = QLineEdit()
		self.directory_path.setEnabled(False)
		layout.addWidget(self.directory_path)

		#add a mode selection dropdown
		self.modeSelect = QComboBox()
		self.modeSelect.addItems(modeFolders)
		#add text for mode selection
		layout.addWidget(QLabel("Select mode:"))
		layout.addWidget(self.modeSelect)


		# Add a launch button
		launch_button = QPushButton("Launch")
		layout.addWidget(launch_button)

		# Connect signals and slots
		#self.stream_data.toggled.connect(self.update_browse_button)
		self.browse_button.clicked.connect(self.browse_for_directory)
		launch_button.clicked.connect(self.launch_app)

		# Set the default selection
		self.local_data.setChecked(True)

		# Set the layout and window title
		self.setLayout(layout)
		self.setWindowTitle("App Startup")

	def update_browse_button(self, checked):
		if checked:
			self.browse_button.setEnabled(False)
			self.directory_path.setEnabled(False)
		else:
			self.browse_button.setEnabled(True)
			self.directory_path.setEnabled(True)

	def browse_for_directory(self):
		directory = QFileDialog.getExistingDirectory(self, "Select Directory")
		if directory:
			self.directory_path.setText(directory)

	def launch_app(self):
		self.accept()

		win = App(STREAM=False, folder=self.directory_path.text(), mode=self.modeSelect.currentText())
		print("App initialized")

def run():
	app = QApplication([])
	startup = StartupDialog(app)
	startup.exec()
	app.exec()
if __name__ == "__main__":
	run()
	
