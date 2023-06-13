from .helpers import *
import os



class EventHandlerBase(object):
	def __init__(self, app):
		self.app = app

	def on_frame_change(self, event):
		input = self.app.frame_edit_display.text()
		input = (int(input) - 1) % self.app._frame_count
		self.app._frame_index = input
		self.app._update_frame()

	def on_zoom_in(self, event):
		self.app.image.zoom(1 / 1.1,self.app)
		self.app._update_image()

	def on_zoom_out(self, event):
		self.app.image.zoom(1.1, self.app)
		self.app._update_image()

	def on_next_frame(self, event):
		self.app._frame_index = min(self.app._frame_index + 1, self.app._frame_count - 10)
		self.app._update_frame()

	def on_previous_frame(self, event):
		self.app._frame_index = max(self.app._frame_index - 1, 0)
		self.app._update_frame()


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

	def keyPressEvent(self, event):
		#print(event.key())
		if event.key() == Qt.Key_K:
			self.app._frame_index = min(self.app._frame_index + 1, self.app._frame_count - 10)
			self.app._update_frame()
			return
		elif event.key() == Qt.Key_J:
			self.app._frame_index = max(self.app._frame_index - 1, 0)
			self.app._update_frame()
			return
		elif event.key() == Qt.Key_I:
			if self.app.image.scale < 0.01:
				return
			self.app.image.zoom(1 / 1.1, self.app)
			self.app._update_image()
		elif event.key() == Qt.Key_O:
			if self.app.image.scale > 10:
				return
			self.app.image.zoom(1.1, self.app)
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
		
		else:
			raise NotImplementedError

	def mousePressEvent(self, event):
		self.app.frame_edit_display.clearFocus()
		self.app.clickState = 1


		if self.app.mouseMode == "Pan":
			self.app.panStart = getUnscaledRelCoords(self.app, event.pos())
			self.app.panStartCoords = self.app.image.offset
			self.app.panning = True
		else:
			raise NotImplementedError

	def wheelEvent(self, event):
		#pan the image
		#check if shift is pressed
		if event.modifiers() == Qt.ShiftModifier:
			pan = np.array([0.0, 1.0])
		else:
			pan = np.array([1.0, 0.0])
		if event.angleDelta().y() > 0:
			pan *= -self.app.panLen

		elif event.angleDelta().y() < 0:
			pan *= self.app.panLen
		self.app.image.pan(pan)
		
		self.app._update_image()

	# on mouse release, stop dragging
	def mouseReleaseEvent(self, event):
		self.app.clickState = 0
		self.app.panning = False

	def mouseMoveEvent(self, event):
		
		if self.app.mouseMode == "Pan":
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
			raise NotImplementedError
		