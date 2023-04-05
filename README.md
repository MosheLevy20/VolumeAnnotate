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

### Second Section



