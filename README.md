# VolumeAnnotate
Virtual Unwrapping Tool for the Vesuvius Challenge, inspired by volume-cartographer (https://github.com/educelab/volume-cartographer).

## Getting Started
### Installation
Note: Python3 is required.
1. Clone the repo
```sh
git clone https://github.com/MosheLevy20/VolumeAnnotate.git
cd VolumeAnnotate
```
2. Install dependencies
```sh
pip install -r requirements.txt
```
### Running
To run simply do
```sh
python VolumeAnnotate.py
```

## Usage
If everything worked as it's supposed to, you should see a popup asking for the directory where your tif slices are stored. Once you select it, you should see a window that looks something like this:
![layout](https://github.com/MosheLevy20/VolumeAnnotate/blob/main/Images/Layout.png)

There are four sections to the control panel.
### First Section
Here are the basic buttons for scrubbing between frames, as well as zooming (these can be controlled with the arrow keys. 
### Second Section
Next is the mouse menu:
1. Pan (WASD). This is the default, it allows you to move around the image when zoomed in, you can also pan using the 'W','A','S','D' keys.
2. Outline Fragment. This allows you to outline the surface of a fragment by clicking on a series of points, as shown in the image below
![outline fragment](https://github.com/MosheLevy20/VolumeAnnotate/blob/main/Images/outlinefragment.png)
3. Move Points. Allows you to move already placed points.
4. Delete Points. Allows you to delete already placed points.
5. Annotate. Allows you to color existing points, for example to label where you think ink is. You can select various colors to annotate various different features that you wish to see in the unwrapped image. The default for ink is green, it is used in the automatic ink detection described below.
![outline fragment](https://github.com/MosheLevy20/VolumeAnnotate/blob/main/Images/annotations.png)

### Third Section
This is where you can select various parameters for the automated ink detection and segmentation. The ink detection is quite simple, it is just a brightness threshold. You can adjust the threshold directly, as well as the radius that the threshold takes into consideration. Adjusting the contrast will also impact where ink is detected. I have found that inverting the image and then applying strong contrast picks out the iron gal ink in the campfire scroll quite well (keep in mind that when you invert the image, the threshold is now an upper bound instead of a lower bound). All of these can be tuned by eye to try and isolate signal from noise. 

The "Annotation Radius" slider and "Hide Annotations" button are just for visual purposes and have no impact on the ink detection.

The "Find Ink" button applies the threshold to the current frame only. 

The "Copy Previous Frame" button duplicates the points and annoations from the previous frame. 

The "Edge Detection" button takes the current frame's points and tries to adjust their positions in the next N frames (where N is specified by the slider) to keep them along the edge you outlined. It also automatically applies the ink detection to all the frames it went through. (This is still a work in progress, so you may need to manually adjust the points if the algorithm gets it wrong).


### Fourth Section
Here you can save and load annotations (if the app crashes you can load the most recent autosave).

Finally, you can use the "Save 2D Projection" button to virtually unwrap your annotations (including the automatically detected ink). There are two options here: "Annotations" just unwraps your annotations, while "Pure Projection" simply takes the pixel values of the points (including the interpolated ones) that you onlined, ignoring the color of your annotations. Below is an example of a virtual unwrapping using both options.




