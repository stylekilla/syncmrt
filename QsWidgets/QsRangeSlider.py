from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
from functools import partial
import logging

__all__ = ['QRangeSlider','QRangeList','QRangeEdit']

class QRangeSlider(QtWidgets.QWidget):
    newRange = QtCore.pyqtSignal(int,int)

    def __init__(self,label='',minimum=1,maximum=100):
        """
        A class which overlays two QSliders and reports back a range.
        """
        super().__init__()
        # Set some internal vars.
        self.minimum = minimum
        self.maximum = maximum
        # Make the layout.
        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0,0,0,0)
        # Create the widgets.
        self.label = QtWidgets.QLabel(label)
        self.slider1 = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider1.setMinimum(self.minimum)
        self.slider1.setMaximum(self.maximum)
        self.slider1.setValue(self.minimum)
        self.slider2 = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider2.setMinimum(self.minimum)
        self.slider2.setMaximum(self.maximum)
        self.slider2.setValue(self.maximum)
        # Signals.
        self.slider1.sliderReleased.connect(partial(self._emitNewRange,1))
        self.slider2.sliderReleased.connect(partial(self._emitNewRange,2))
        # Fill the layout.
        if len(label) > 0: layout.addRow(self.label)
        layout.addRow(QtWidgets.QLabel('Min: '),self.slider1)
        layout.addRow(QtWidgets.QLabel('Max: '),self.slider2)
        # Set the layout.
        self.setLayout(layout)
        # Attempt to overlay them.
        self.slider2.move(self.slider1.geometry().bottomRight())

    def setRange(self,minimum,maximum):
        """ Set the minimum and maximum values for the slider. """
        self.slider1.setMinimum(minimum)
        self.slider1.setMaximum(maximum)
        self.slider1.setValue(minimum)
        self.slider2.setMinimum(minimum)
        self.slider2.setMaximum(maximum)
        self.slider2.setValue(maximum)

    def _emitNewRange(self,slider):
        # Get the values of each slider.
        val1 = self.slider1.value()
        val2 = self.slider2.value()
        # Check the slider position is valid. If not fix it.
        if (slider == 1) & (val1 > val2): self.slider1.setValue(val2-1)
        elif (slider == 2) & (val2 < val1): self.slider2.setValue(val1+1)
        # Emit the range.
        self.newRange.emit(self.slider1.value()-1,self.slider2.value()-1)

    def range(self):
        """ Return the range covered value of the sliders. """
        return self.slider1.value(), self.slider2.value()

class QRangeList(QtWidgets.QWidget):
    newRange = QtCore.pyqtSignal(float,float)

    def __init__(self,title=None):
        """
        Create a number range between two line edits.
        """
        super().__init__()
        # Make the layout.
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        # Create the widgets.
        self.left = QRangeEdit()
        self.right = QRangeEdit()
        # Signals.
        self.left.editingFinished.connect(partial(self._emitNewRange,1))
        self.right.editingFinished.connect(partial(self._emitNewRange,2))
        # Fill the layout.
        if title != None: layout.addWidget(QtWidgets.QLabel(str(title)))
        layout.addWidget(self.left)
        layout.addWidget(self.right)
        # Set the layout.
        self.setLayout(layout)

    def setRange(self,newRange):
        """ Set the minimum and maximum values for the boxes. """
        # Store the range list.
        self.range = np.round(newRange,2)
        # Calculate the direction of the range.
        if self.range[0] > self.range[1]: self.direction = -1
        elif self.range[0] < self.range[1]: self.direction = 1
        # Set the min and max values.
        self.left.setRange(self.range,self.range[0])
        self.right.setRange(self.range,self.range[1])

    def getRange(self):
        """ Return the range covered value of the boxes. """
        if self.left.isValid() & self.right.isValid():
            return (float(self.left.text()), float(self.right.text()))
        else: return (None,None)

    def _emitNewRange(self,box):
        # Get the left and right values:
        val1 = float(self.left.text())
        val2 = float(self.right.text())
        # Check the range for validity with direction.
        if (box == 1):
            if (self.direction == 1) & (val1 > val2):
                val1 = val2-1
                self.left.setText(str(val1))
            elif (self.direction == -1) & (val1 < val2):
                val1 = val2+1
                self.left.setText(str(val1))
        elif (box == 2):
            if (self.direction == 1) & (val2 < val1):
                val2 = val1+1
                self.right.setText(str(val2))
            elif (self.direction == -1) & (val2 > val1):
                val2 = val1-1
                self.right.setText(str(val2))
        # Emit the range.
        self.newRange.emit(val1,val2)

class QRangeEdit(QtWidgets.QLineEdit):
    def __init__(self):
        """
            A QLineEdit that shows a yellow border when the input is outside the desired range.
        """
        super().__init__()
        # Set the min and max values for the line edit.
        self.min = 0.0
        self.max = 100.0
        # A default value.
        self.defaultValue = 50.0
        # Create a isValid bool.
        self.valid = False
        # Tell the line edit to go through the _changed method.
        self.textChanged.connect(self._changed)

    def isValid(self):
        """ Return a bool stating whether the input is valid or not. """
        return self.valid

    def setRange(self,newRange,defaultValue):
        # Set the minimum and maximum values of the new range.
        self.min = min(newRange)
        self.max = max(newRange)
        # Set the default value.
        self.defaultValue = defaultValue
        self.setText(str(self.defaultValue))

    def _changed(self,text):
        # Validate the text.
        self._validate(text)
        # Set the style sheet according to it's validity.
        if self.valid:
            self.setStyleSheet("")
        elif not self.valid:
            self.setStyleSheet("border: 1px solid yellow")

    def _validate(self,text):
        # Validate the text: 'text'.
        if text == '':
            # If empty, reset to the default value.
            text = self.defaultValue
            # Set the text and return (this should go through this method again).
            self.setText(str(text))
            return
        try:
            # Convert to float.
            num = float(text)
            # Is it within the allowable range?
            if (num >= self.min) & (num <= self.max):
                self.valid = True
            else:
                self.valid = False
        except:
            self.valid = False