"""
Image Data Processing
Copyright 2018(c), Andrew Ferlitsch
"""

import os

# Import numpy for the high performance in-memory matrix/array storage and operations.
import numpy as np

# Import h5py for the HD5 filesystem high performance file storage of big data.
import h5py

# Import PIL.Image for Python image manipulation library. 
import PIL
from PIL import Image

class Image(object):
    """ Base (super) Class for Classifying an Image """
    
    def __init__(self, image=None, dir='./', label=0, ehandler=None, thumbnail=(128,128), config=None):
        """ """
        self._image     = image     # image path
        self._name      = None      # name of image (no path or suffix)
        self._size      = 0         # byte size of the image on disk
        self._type      = None      # image type of the image
        self._dir       = None      # image storage
        self._shape     = None      # shape of the image
        self._ehandler  = ehandler  # event handler for asynchronous processing 
        self._thumbnail = thumbnail # thumbnail size
        self._label     = label     # image label
        self._grayscale = False     # convert to grayscale
        self._normalize = False     # normalize the image
        self._flatten   = False     # flatten the image
        self._resize    = None      # resize the image
        self._imgdata   = None      # image data in memory
        
        # value must be a string
        if image is not None and isinstance(image, str) == False:
            raise TypeError("String expected for image path")
        
        if dir is not None:
            if isinstance(dir, str) == False:
                raise TypeError("String expected for image storage path")
            if dir.endswith("/") == False:
                    dir += "/"  
            self._dir = dir
        
        # value must be a string
        if label is not None and isinstance(label, int) == False:
            raise TypeError("Integer expected for image label")
            
        if config is not None and isinstance(config, list) == False:
            raise TypeError("List expected for config settings")
        
        if config is not None:
            for setting in config:
                if setting in ['gray', 'grayscale']:
                    self._grayscale = True
                elif setting in ['normal', 'normalize']:
                    self._normalize = True
                elif setting in ['flat', 'flatten']:
                    self._flatten = True
                elif setting.startswith('resize='):
                    toks = setting.split('=')
                    if len(toks) != 2:
                        raise IndexError("Resize is wrong format")
                    vals = toks[1].split(',')
                    if len(vals) != 2:
                        raise IndexError("Resize is wrong format")
                    self._resize = ( int(vals[1]), int(vals[0]) )
        
        if self._image is not None:
            self._exist()
            self._collate()
        
    def _exist(self):
        """ Check if document exists """
        if isinstance(self._image, str) == False:
            raise TypeError("String expected for image path")
    
        # Check that image exists
        if os.path.isfile(self._image) == False:
            raise FileNotFoundError(self._image)
        
        # Get the file name and file type of the image without the extension 
        basename = os.path.splitext(os.path.basename(self._image))
        self._name = basename[0]
        self._type = basename[1][1:].lower()
        
        if self._type not in [ 'png', 'jpg', 'bmp', 'tif']:
            raise TypeError("Not an image file")
        
        # Get the size of the image
        self._size = os.path.getsize(self._image)
        
        # Size sanity check
        if self._size == 0:
            raise IOError("The image is an empty file")
            
    def _collate(self, dir='./'):
        """ Process the image """
        
        # Read in the image data
        pixels = PIL.Image.open(self._image)
        
        # Store the image
        pixels.save(dir + "/" + self._name + "." + self._type )
        
        # Store the thumbnail (TODO)
        if False:
            pixels.thumbnail( self._thumbnail )
            pixels.save(dir + "/" + self._name + "." + "thumbnail" + "." + self._type )
        
        if self._resize:
            if self._grayscale:
                pixels = pixels.resize(self._resize, resample=PIL.Image.LANCZOS)
            else:
                pixels = pixels.resize(self._resize, resample=PIL.Image.LANCZOS)
        
        
        # Convert to numpy array
        image = np.asarray(pixels)
        
        # Get the shape of the array
        self._shape = image.shape
        
        # Grayscale image
        if self._shape[2] == 1:
            # Extend to three channels, replicating the single channel
            if self._grayscale == False:
                pixels = pixels.convert('RGB')
                image = np.asarray(pixels)
        # RGBA image (RGB + alpha channel)
        elif self._shape[2] == 4:
            if self._grayscale == False:
                # Remove Alpha Channel from Image
                pixels = pixels.convert('RGB')
                image = np.asarray(pixels)
            else:
                # convert to grayscale
                pixels = pixels.convert('L')
                image = np.asarray(pixels)
            
        # Normalize the image (convert pixel values from int range 0 .. 255 to float range 0 .. 1)
        if self._normalize == True:
            image = image / 255
            
        # Flatten the image into a 1D vector
        if self._flatten == True:
            image = image.flatten()
        
        # Get the shape of the array
        self._shape = image.shape
            
        # Write the image to disk as HD5 file
        with h5py.File(self._dir + "/" + self._name + '.h5', 'w') as hf:
            hf.create_dataset("images",  data=[image])
            hf.create_dataset("labels",  data=[self._label])
            
        self._imgdata = image
            
    def load(self, image, dir='./'):
        """ Load an image from storage """
        # value must be a string
        if dir is not None:
            if isinstance(dir, str) == False:
                raise TypeError("String expected for image storage path")
            if dir.endswith("/") == False:
                    dir += "/"  
            self._dir = dir
        self._dir = dir 
        
        # value must be a string
        if image is not None and isinstance(image, str) == False:
            raise TypeError("String expected for image path")
        self._image = image
        
        basename = os.path.splitext(os.path.basename(self._image))
        self._name = basename[0]
        self._type = basename[1][1:].lower()
        
            
        # Read the image from disk as HD5 file
        with h5py.File(self._dir + "/" + self._name + '.h5', 'r') as hf:
            X =  hf['images'][:]
            Y =  hf['labels'][:]
            
        self._imgdata = X[0]
        self._label   = Y[0]
        self._shape   = self._imgdata.shape
       
    @property
    def image(self):
        """ Getter for the image name (path) """
        return self._image
        
    @image.setter
    def image(self, image):
        """ Setter for the image name (path) 
       image - path to the image
        """
        self._image = image 
        self._exist()
        self._collate(self._dir)

    @property
    def name(self):
        """ Getter for the image name (path) """
        return self._name

    @property
    def type(self):
        """ Getter for the image type (suffix) """
        return self._type

    @property
    def shape(self):
        """ Getter for the image shape (height, width [,planes]) """
        return self._shape
        
    @property
    def dir(self):
        """ Getter for the image directory """
        return self._dir
        
    @dir.setter
    def dir(self, dir):
        """ Setter for image directory """
        # value must be a string
        if dir is not None:
            if isinstance(dir, str) == False:
                raise TypeError("String expected for image storage path")
            if dir.endswith("/") == False:
                    dir += "/"  
            self._dir = dir
        self._dir = dir 
        
    @property
    def classification(self):
        """ Getter for image label (classification) """
        return self._label
        
    @classification.setter
    def classification(self, label):
        """ Setter for image label (classification) """
        self._label = label
        
            
        
        