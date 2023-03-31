from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
#from PyQt5 import QtGui
#from mImage import mImage
import numpy as np
import cv2
#point annotation object
class mAnnotation(object):
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
     
        self.color = color
        self.size = size

class point(mAnnotation):
    def __init__(self, x, y, colorIdx=0, size=3):
        self.colorIdx = colorIdx
        color = getColor(colorIdx)
        super().__init__(x, y, color, size)

        

    def show(self, arr, size=3):
        #print("showing point", type(arr))
        #print(f"self.x: {self.x}, self.y: {self.y}, arr.shape: {arr.shape}")
        #draw a point on the image which is a numpy array
        #x, y = self.transform(img)

        x = int(self.x*arr.shape[0])
        y = int(self.y*arr.shape[1])
        #cv2.circle(arr, (x,y), self.size, self.color, -1)
        #draw mostlly transparent circle
        #to do this we need rgba 
        #cv2.circle(arr, (x,y), self.size, self.color, -1)
        #cv2 using overlay and addWeighted
        alpha = 0.3
        #overlay = arr.copy()
        cv2.circle(arr, (x,y), size, self.color, -1)
        #cv2.addWeighted(overlay, alpha, arr,1-alpha, 0, arr)
    
    def updateColor(self, colorIdx):
        self.colorIdx = colorIdx
        self.color = getColor(colorIdx)



        
def getColor(colorIdx):
    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
    return colors[colorIdx]

        

        