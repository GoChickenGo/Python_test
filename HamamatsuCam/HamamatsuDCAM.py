# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 13:22:00 2020

@author: xinmeng
"""

"""
A ctypes based interface to Hamamatsu cameras.
(tested on a sCMOS Flash 4.0).
The documentation is a little confusing to me on this subject..
I used c_int32 when this is explicitly specified, otherwise I use c_int.
Hazen 10/13
George 11/17 - Updated for SDK4 and to allow fixed length acquisition

Xin Adapted for Brinks lab

"""

import ctypes
import ctypes.util
import numpy

import time

#import storm_control.sc_library.halExceptions as halExceptions

# Hamamatsu constants.

# DCAM4 API.
DCAMERR_ERROR = 0
DCAMERR_NOERROR = 1
DCAMERR_SUCCESS = 2

DCAMPROP_ATTR_HASVALUETEXT = int("0x10000000", 0)
DCAMPROP_ATTR_READABLE = int("0x00010000", 0)
DCAMPROP_ATTR_WRITABLE = int("0x00020000", 0)

DCAMPROP_OPTION_NEAREST = int("0x80000000", 0)
DCAMPROP_OPTION_NEXT = int("0x01000000", 0)
DCAMPROP_OPTION_SUPPORT = int("0x00000000", 0)

DCAMPROP_TYPE_MODE = int("0x00000001", 0)
DCAMPROP_TYPE_LONG = int("0x00000002", 0)
DCAMPROP_TYPE_REAL = int("0x00000003", 0)
DCAMPROP_TYPE_MASK = int("0x0000000F", 0)

DCAMCAP_STATUS_ERROR = int("0x00000000", 0)
DCAMCAP_STATUS_BUSY = int("0x00000001", 0)
DCAMCAP_STATUS_READY = int("0x00000002", 0)
DCAMCAP_STATUS_STABLE = int("0x00000003", 0)
DCAMCAP_STATUS_UNSTABLE = int("0x00000004", 0)

DCAMWAIT_CAPEVENT_FRAMEREADY = int("0x0002", 0)
DCAMWAIT_CAPEVENT_STOPPED = int("0x0010", 0)

DCAMWAIT_RECEVENT_MISSED = int("0x00000200", 0)
DCAMWAIT_RECEVENT_STOPPED = int("0x00000400", 0)
DCAMWAIT_TIMEOUT_INFINITE = int("0x80000000", 0)

#DCAMWAIT_RECEVENT_WRITEFAULT = 100
#DCAMWAIT_RECEVENT_WARNING = 101
#DCAMWAIT_RECEVENT_SKIPPED = 102

DCAM_DEFAULT_ARG = 0

DCAM_IDSTR_MODEL = int("0x04000104", 0)

DCAMCAP_TRANSFERKIND_FRAME = 0

DCAMCAP_START_SEQUENCE = -1
DCAMCAP_START_SNAP = 0

DCAMBUF_ATTACHKIND_FRAME = 0
DCAMBUF_ATTACHKIND_TIMESTAMP = 1
DCAMBUF_ATTACHKIND_FRAMESTAMP = 2

# Specify dcam-api location
try:
    dcam = ctypes.WinDLL(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Python_test\HamamatsuCam\19_12\dcamapi.dll')
except:
    pass


# Hamamatsu structures.

## DCAMAPI_INIT
#
# The dcam initialization structure
#
class DCAMAPI_INIT(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32), 
            ("iDeviceCount", ctypes.c_int32),
            ("reserved", ctypes.c_int32),
            ("initoptionbytes", ctypes.c_int32),
            ("initoption", ctypes.POINTER(ctypes.c_int32)),
            ("guid", ctypes.POINTER(ctypes.c_int32))]

## DCAMDEV_OPEN
#
# The dcam open structure
#
class DCAMDEV_OPEN(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32),
            ("index", ctypes.c_int32),
            ("hdcam", ctypes.c_void_p)]
    
# DCAMREC_OPEN
#
# The dcam record open structure
#
class DCAMREC_OPEN(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32),
            ("reserved", ctypes.c_int32),
            ("hrec", ctypes.c_void_p),
            ("path", ctypes.c_wchar_p), # const TCHAR*		path;
            ("ext", ctypes.c_wchar_p),
            ("maxframepersession", ctypes.c_int32),
            ("userdatasize", ctypes.c_int32),
            ("userdatasize_session", ctypes.c_int32),
            ("userdatasize_file", ctypes.c_int32),
            ("usertextsize", ctypes.c_int32),
            ("usertextsize_session", ctypes.c_int32),
            ("usertextsize_file", ctypes.c_int32)]

# DCAMREC_STATUS
# 
# retrieves the recording status
#
class DCAMREC_STATUS(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32),
            ("currentsession_index", ctypes.c_int32),
            ("maxframecount_per_session", ctypes.c_int32),
            ("currentframe_index", ctypes.c_int32),
            ("missingframe_count", ctypes.c_int32),
            ("flags", ctypes.c_int32),
            ("totalframecount", ctypes.c_int32),
            ("reserved", ctypes.c_int32)]
            
## DCAMWAIT_OPEN
#
# The dcam wait open structure
#
class DCAMWAIT_OPEN(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32),
            ("supportevent", ctypes.c_int32),
            ("hwait", ctypes.c_void_p),
            ("hdcam", ctypes.c_void_p)]

## DCAMWAIT_START
#
# The dcam wait start structure
#
class DCAMWAIT_START(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32),
            ("eventhappened", ctypes.c_int32),
            ("eventmask", ctypes.c_int32),
            ("timeout", ctypes.c_int32)]

## DCAMCAP_TRANSFERINFO
#
# The dcam capture info structure
#
class DCAMCAP_TRANSFERINFO(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32),
            ("iKind", ctypes.c_int32),
            ("nNewestFrameIndex", ctypes.c_int32),
            ("nFrameCount", ctypes.c_int32)]


## DCAMBUF_ATTACH
#
# The dcam buffer attachment structure
#
class DCAMBUF_ATTACH(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32), 
            ("iKind", ctypes.c_int32),
            ("buffer", ctypes.POINTER(ctypes.c_void_p)),# Set to the array of pointers of attached buffers.
            ("buffercount", ctypes.c_int32)]

## DCAMBUF_FRAME
#
# The dcam buffer frame structure
#
class DCAMBUF_FRAME(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32), 
            ("iKind", ctypes.c_int32),
            ("option", ctypes.c_int32),
            ("iFrame", ctypes.c_int32),
            ("buf", ctypes.c_void_p),
            ("rowbytes", ctypes.c_int32),
            ("type", ctypes.c_int32),
            ("width", ctypes.c_int32),
            ("height", ctypes.c_int32),
            ("left", ctypes.c_int32),
            ("top", ctypes.c_int32),
            ("timestamp", ctypes.c_int32),
            ("framestamp", ctypes.c_int32),
            ("camerastamp", ctypes.c_int32)]


## DCAMDEV_STRING
#
# The dcam device string structure
#
class DCAMDEV_STRING(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int32), 
            ("iString", ctypes.c_int32),
            ("text", ctypes.c_char_p),
            ("textbytes", ctypes.c_int32)]


## DCAMPROP_ATTR
#
# The dcam property attribute structure.
#
class DCAMPROP_ATTR(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_int32),
                ("iProp", ctypes.c_int32),
                ("option", ctypes.c_int32),
                ("iReserved1", ctypes.c_int32),
                ("attribute", ctypes.c_int32),
                ("iGroup", ctypes.c_int32),
                ("iUnit", ctypes.c_int32),
                ("attribute2", ctypes.c_int32),
                ("valuemin", ctypes.c_double),
                ("valuemax", ctypes.c_double),
                ("valuestep", ctypes.c_double),
                ("valuedefault", ctypes.c_double),
                ("nMaxChannel", ctypes.c_int32),
                ("iReserved3", ctypes.c_int32),
                ("nMaxView", ctypes.c_int32),
                ("iProp_NumberOfElement", ctypes.c_int32),
                ("iProp_ArrayBase", ctypes.c_int32),
                ("iPropStep_Element", ctypes.c_int32)]

## DCAMPROP_VALUETEXT
#
# The dcam text property structure.
#
class DCAMPROP_VALUETEXT(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_int32),
                ("iProp", ctypes.c_int32),
                ("value", ctypes.c_double),
                ("text", ctypes.c_char_p),
                ("textbytes", ctypes.c_int32)]


def convertPropertyName(p_name):
    """
    "Regularizes" a property name. We are using all lowercase names with
    the spaces replaced by underscores.
    """
    return p_name.lower().replace(" ", "_")


#class DCAMException(halExceptions.HardwareException):
#    pass

class HCamData(object):
    """
    Hamamatsu camera data object.
    Initially I tried to use create_string_buffer() to allocate storage for the 
    data from the camera but this turned out to be too slow. The software
    kept falling behind the camera and create_string_buffer() seemed to be the
    bottleneck.
    Using numpy makes a lot more sense anyways..
    """
    def __init__(self, size = None, **kwds):
        """
        Create a data object of the appropriate size.
        """
        super().__init__(**kwds)
        self.np_array = numpy.ascontiguousarray(numpy.empty(int(size/2), dtype=numpy.uint16))
        self.size = size

    def __getitem__(self, slice):
        return self.np_array[slice]

    def copyData(self, address):
        """
        Uses the C memmove function to copy data from an address in memory
        into memory allocated for the numpy array of this object.
        """
        ctypes.memmove(self.np_array.ctypes.data, address, self.size) # copies count bytes from src(adress) to dst.

    def getData(self):
        return self.np_array

    def getDataPtr(self):
        return self.np_array.ctypes.data # A pointer to the memory area of the array as a Python integer. 
                                         # Here it's the pointer to attached memory buffers(RAM) to receive streaming images.

class HamamatsuCamera(object):
    """
    Basic camera interface class.
    
    This version uses the Hamamatsu library to allocate camera buffers.
    Storage for the data from the camera is allocated dynamically and
    copied out of the camera buffers.
    """
    def __init__(self, camera_id = None, **kwds):
        """
        Open the connection to the camera specified by camera_id.
        """
        super().__init__(**kwds)

        self.buffer_index = 0
        self.camera_id = camera_id
        self.debug = False
        self.encoding = 'utf-8'
        self.frame_bytes = 0
        self.frame_x = 0
        self.frame_y = 0
        self.last_frame_number = 0
        self.properties = None
        self.max_backlog = 0
        self.number_image_buffers = 0

        self.acquisition_mode = "run_till_abort"
        self.number_frames = 0

        
        # Get camera model.
        self.camera_model = self.getModelInfo(camera_id)

        # Open the camera.
        # If this function succeeds, DCAMDEV_OPEN::hdcam will be set to the HDCAM handle of specified device. 
        # If DCAM fails to open the specified device, this function will return an error code.
        paramopen = DCAMDEV_OPEN(0, self.camera_id, None)
        paramopen.size = ctypes.sizeof(paramopen)
        self.checkStatus(dcam.dcamdev_open(ctypes.byref(paramopen)),
                         "dcamdev_open")
        # If a pointer's type is void*, the pointer can point to any variable that is not 
        # declared with the const or volatile keyword.
        self.camera_handle = ctypes.c_void_p(paramopen.hdcam)

        # Set up wait handle
        paramwait = DCAMWAIT_OPEN(0, 0, None, self.camera_handle)
        paramwait.size = ctypes.sizeof(paramwait)
        self.checkStatus(dcam.dcamwait_open(ctypes.byref(paramwait)), 
                "dcamwait_open")
        self.wait_handle = ctypes.c_void_p(paramwait.hwait)
        
        # Get camera properties.
        self.properties = self.getCameraProperties()

        # Get camera max width, height.
        self.max_width = self.getPropertyValue("image_width")[0]
        self.max_height = self.getPropertyValue("image_height")[0]


    def captureSetup(self):
        """
        Capture setup (internal use only). This is called at the start
        of new acquisition sequence to determine the current ROI and
        get the camera configured properly.
        """
        self.buffer_index = -1
        self.last_frame_number = 0

        # Set sub array mode.
        self.setSubArrayMode()

        # Get frame properties.
        self.frame_x = self.getPropertyValue("image_width")[0]
        self.frame_y = self.getPropertyValue("image_height")[0]
        self.frame_bytes = self.getPropertyValue("image_framebytes")[0]


    def checkStatus(self, fn_return, fn_name= "unknown"):
        """
        Check return value of the dcam function call.
        Throw an error if not as expected?
        """
        if fn_return == DCAMERR_ERROR:
            print('ERROR! {}'.format(fn_name))
#            print(fn_return)
        
        #if (fn_return != DCAMERR_NOERROR) and (fn_return != DCAMERR_ERROR):
        #    raise DCAMException("dcam error: " + fn_name + " returned " + str(fn_return))
#        if (fn_return == DCAMERR_ERROR):
#            c_buf_len = 80
#            c_buf = ctypes.create_string_buffer(c_buf_len)
#            c_error = dcam.dcam_getlasterror(self.camera_handle, # Can't find dcam.dcam_getlasterror
#                                             c_buf,
#                                             ctypes.c_int32(c_buf_len))
##            raise DCAMException("dcam error " + str(fn_name) + " " + str(c_buf.value))
#            print ("dcam error", fn_name, c_buf.value)
        return fn_return

    def getCameraProperties(self):
        """
        Return the ids & names of all the properties that the camera supports. This
        is used at initialization to populate the self.properties attribute.
        """
        c_buf_len = 64
        c_buf = ctypes.create_string_buffer(c_buf_len) # Set c_buf address pointer first to wait for names. 
        properties = {}
        prop_id = ctypes.c_int32(0)

        # Reset to the start.
        ret = dcam.dcamprop_getnextid(self.camera_handle,
                                      ctypes.byref(prop_id),
                                      ctypes.c_uint32(DCAMPROP_OPTION_NEAREST))
        if (ret != 0) and (ret != DCAMERR_NOERROR):
            self.checkStatus(ret, "dcamprop_getnextid")

        # Get the first property.
        # Use dcamprop_getnextid to get the id first and then use dcamprop_getname to get the name.
        ret = dcam.dcamprop_getnextid(self.camera_handle,
                                          ctypes.byref(prop_id),
                                          ctypes.c_int32(DCAMPROP_OPTION_NEXT))
        if (ret != 0) and (ret != DCAMERR_NOERROR):
            self.checkStatus(ret, "dcamprop_getnextid")
        self.checkStatus(dcam.dcamprop_getname(self.camera_handle,
                                                   prop_id,
                                                   c_buf,
                                                   ctypes.c_int32(c_buf_len)),
                         "dcamprop_getname")

        # Get the rest of the properties.
        last = -1
        while (prop_id.value != last):
            last = prop_id.value
            properties[convertPropertyName(c_buf.value.decode(self.encoding))] = prop_id.value
            
            # dcamprop_getnextid: If the host software calls this function with the iProp value set to 0
            #, the function will return the next property ID in the iProp value.
            # -- ctypes.byref(prop_id): the pointer to a property ID which will also receive the next property ID
            # -- ctypes.c_int32(DCAMPROP_OPTION_NEXT): Option for getting next property id.
            ret = dcam.dcamprop_getnextid(self.camera_handle,
                                              ctypes.byref(prop_id),
                                              ctypes.c_int32(DCAMPROP_OPTION_NEXT))
            if (ret != 0) and (ret != DCAMERR_NOERROR):
                self.checkStatus(ret, "dcamprop_getnextid")
            
            # The dcamprop_getname() function returns the character string as the name of the property 
            # specified by the iProp argument.
            # -- c_buf: the pointer of a buffer to receive the property name; prop_id: the property ID; 
            # -- ctypes.c_int32(c_buf_len): the size of the buffer that will receive the property name
            self.checkStatus(dcam.dcamprop_getname(self.camera_handle,
                                                       prop_id,
                                                       c_buf,
                                                       ctypes.c_int32(c_buf_len)),
                             "dcamprop_getname")
            
            
        return properties

    def getFrames(self):
        """
        Gets all of the available frames.
    
        This will block waiting for new frames even if 
        there new frames available when it is called.
        """
        frames = []
        for n in self.newFrames():

            paramlock = DCAMBUF_FRAME(
                    0, 0, 0, n, None, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            paramlock.size = ctypes.sizeof(paramlock)	

            # Lock the frame in the camera buffer & get address.
            self.checkStatus(dcam.dcambuf_lockframe(self.camera_handle,
                                                ctypes.byref(paramlock)),
                             "dcambuf_lockframe")

            # Create storage for the frame & copy into this storage.
            hc_data = HCamData(self.frame_bytes)
            hc_data.copyData(paramlock.buf)

            frames.append(hc_data)


        return [frames, [self.frame_x, self.frame_y]]

    def getModelInfo(self, camera_id):
        """
        Returns the model of the camera
        """

        c_buf_len = 20
        string_value = ctypes.create_string_buffer(c_buf_len)
        paramstring = DCAMDEV_STRING(
                        0, 
                        DCAM_IDSTR_MODEL, 
                        ctypes.cast(string_value, ctypes.c_char_p),
                        c_buf_len)
        paramstring.size = ctypes.sizeof(paramstring)

        self.checkStatus(dcam.dcamdev_getstring(ctypes.c_int32(camera_id),
                                                ctypes.byref(paramstring)),
                         "dcamdev_getstring")

        return string_value.value.decode(self.encoding)

    def getProperties(self):
        """
        Return the list of camera properties. This is the one to call if you
        want to know the camera properties.
        """
        return self.properties

    def getPropertyAttribute(self, property_name):
        """
        Return the attribute structure of a particular property.
        
        FIXME (OPTIMIZATION): Keep track of known attributes?
        """
        p_attr = DCAMPROP_ATTR()
        p_attr.cbSize = ctypes.sizeof(p_attr)
        p_attr.iProp = self.properties[property_name]
        ret = self.checkStatus(dcam.dcamprop_getattr(self.camera_handle,
                                                         ctypes.byref(p_attr)),
                               "dcamprop_getattr")
        if (ret == 0):
            print("property", property_id, "is not supported")
            return False
        else:
            return p_attr

    def getPropertyRange(self, property_name):
        """
        Return the range for an attribute.
        """
        prop_attr = self.getPropertyAttribute(property_name)
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if (temp == DCAMPROP_TYPE_REAL):
            return [float(prop_attr.valuemin), float(prop_attr.valuemax)]
        else:
            return [int(prop_attr.valuemin), int(prop_attr.valuemax)]

    def getPropertyRW(self, property_name):
        """
        Return if a property is readable / writeable.
        """
        prop_attr = self.getPropertyAttribute(property_name)
        rw = []

        # Check if the property is readable.
        if (prop_attr.attribute & DCAMPROP_ATTR_READABLE):
            rw.append(True)
        else:
            rw.append(False)

        # Check if the property is writeable.
        if (prop_attr.attribute & DCAMPROP_ATTR_WRITABLE):
            rw.append(True)
        else:
            rw.append(False)

        return rw

    def getPropertyText(self, property_name):
        """
        #Return the text options of a property (if any).
        """
        prop_attr = self.getPropertyAttribute(property_name)
        if not (prop_attr.attribute & DCAMPROP_ATTR_HASVALUETEXT):
            return {}
        else:
            # Create property text structure.
            prop_id = self.properties[property_name]
            v = ctypes.c_double(prop_attr.valuemin)

            prop_text = DCAMPROP_VALUETEXT()
            c_buf_len = 64
            c_buf = ctypes.create_string_buffer(c_buf_len)
            #prop_text.text = ctypes.c_char_p(ctypes.addressof(c_buf))
            prop_text.cbSize = ctypes.c_int32(ctypes.sizeof(prop_text))
            prop_text.iProp = ctypes.c_int32(prop_id)
            prop_text.value = v
            prop_text.text = ctypes.addressof(c_buf)
            prop_text.textbytes = c_buf_len

            # Collect text options.
            done = False
            text_options = {}
            while not done:
                # Get text of current value.
                self.checkStatus(dcam.dcamprop_getvaluetext(self.camera_handle, 
                                                ctypes.byref(prop_text)),
                                 "dcamprop_getvaluetext")
                text_options[prop_text.text.decode(self.encoding)] = int(v.value)

                # Get next value.
                ret = dcam.dcamprop_queryvalue(self.camera_handle,
                                           ctypes.c_int32(prop_id),
                                           ctypes.byref(v),
                                           ctypes.c_int32(DCAMPROP_OPTION_NEXT))
                prop_text.value = v

                if (ret != 1):
                    done = True

            return text_options

    def getPropertyValue(self, property_name):
        """
        Return the current setting of a particular property.
        """

        # Check if the property exists.
        if not (property_name in self.properties):
            print(" unknown property name:", property_name)
            return False
        prop_id = self.properties[property_name]

        # Get the property attributes.
        prop_attr = self.getPropertyAttribute(property_name)

        # Get the property value.
        c_value = ctypes.c_double(0)
        self.checkStatus(dcam.dcamprop_getvalue(self.camera_handle,
                                                    ctypes.c_int32(prop_id),
                                                    ctypes.byref(c_value)),
                         "dcamprop_getvalue")

        # Convert type based on attribute type.
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if (temp == DCAMPROP_TYPE_MODE):
            prop_type = "MODE"
            prop_value = int(c_value.value)
        elif (temp == DCAMPROP_TYPE_LONG):
            prop_type = "LONG"
            prop_value = int(c_value.value)
        elif (temp == DCAMPROP_TYPE_REAL):
            prop_type = "REAL"
            prop_value = c_value.value
        else:
            prop_type = "NONE"
            prop_value = False
    
        return [prop_value, prop_type]

    def isCameraProperty(self, property_name):
        """
        Check if a property name is supported by the camera.
        """
        if (property_name in self.properties):
            return True
        else:
            return False

    def newFrames(self):
        """
        Return a list of the ids of all the new frames since the last check.
        Returns an empty list if the camera has already stopped and no frames
        are available.
    
        This will block waiting for at least one new frame.
        """

        captureStatus = ctypes.c_int32(0)
        self.checkStatus(dcam.dcamcap_status(
            self.camera_handle, ctypes.byref(captureStatus)))

        # Wait for a new frame if the camera is acquiring.
        if captureStatus.value == DCAMCAP_STATUS_BUSY:
#            print('DCAMCAP_STATUS_BUSY')
            paramstart = DCAMWAIT_START(
                    0, 
                    0, 
                    DCAMWAIT_CAPEVENT_FRAMEREADY | DCAMWAIT_CAPEVENT_STOPPED, 
                    100)
            paramstart.size = ctypes.sizeof(paramstart)
            self.checkStatus(dcam.dcamwait_start(self.wait_handle,
                                            ctypes.byref(paramstart)),
                             "dcamwait_start")

        # Check how many new frames there are.
        paramtransfer = DCAMCAP_TRANSFERINFO(
                0, DCAMCAP_TRANSFERKIND_FRAME, 0, 0)
        paramtransfer.size = ctypes.sizeof(paramtransfer)
        self.checkStatus(dcam.dcamcap_transferinfo(self.camera_handle,
                                               ctypes.byref(paramtransfer)),
                         "dcamcap_transferinfo")
        cur_buffer_index = paramtransfer.nNewestFrameIndex
        cur_frame_number = paramtransfer.nFrameCount

        # Check that we have not acquired more frames than we can store in our buffer.
        # Keep track of the maximum backlog.
        backlog = cur_frame_number - self.last_frame_number # In the beginning,last_frame_number is 0.
        if (backlog > self.number_image_buffers):
            print(">> Warning! hamamatsu camera frame buffer overrun detected!")
        if (backlog > self.max_backlog):
            self.max_backlog = backlog  # Update the number of frames accumulated in the buffer.
        self.last_frame_number = cur_frame_number


        # Create a list of the new frames.
        # Example: If 1024 frames are assigned in buffer in continous mode, and we record more than 1024 images:
        # At 1025th image, cur_buffer_index = 0, self.buffer_index(where buffer index is during last check) = 1024.
        
        new_frames = []
        if (cur_buffer_index < self.buffer_index): 
            for i in range(self.buffer_index + 1, self.number_image_buffers): 
                new_frames.append(i)
            for i in range(cur_buffer_index + 1):
                new_frames.append(i)
        else:
            for i in range(self.buffer_index, cur_buffer_index):
                new_frames.append(i+1)
        self.buffer_index = cur_buffer_index

        if self.debug:
            print(new_frames)
        
#        print(new_frames)
        
        return new_frames

    def setPropertyValue(self, property_name, property_value):
        """
        Set the value of a property.
        """

        # Check if the property exists.
        if not (property_name in self.properties):
            print(" unknown property name:", property_name)
            return False

        # If the value is text, figure out what the 
        # corresponding numerical property value is.
        if (isinstance(property_value, str)):
            text_values = self.getPropertyText(property_name)
            if (property_value in text_values):
                property_value = float(text_values[property_value])
            else:
                print(" unknown property text value:", property_value, "for", property_name)
                return False

        # Check that the property is within range.
        [pv_min, pv_max] = self.getPropertyRange(property_name)
        if (property_value < pv_min):
            print(" set property value", property_value, "is less than minimum of", pv_min, property_name, "setting to minimum")
            property_value = pv_min
        if (property_value > pv_max):
            print(" set property value", property_value, "is greater than maximum of", pv_max, property_name, "setting to maximum")
            property_value = pv_max
        
        # Set the property value, return what it was set too.
        prop_id = self.properties[property_name]
        p_value = ctypes.c_double(property_value)
        self.checkStatus(dcam.dcamprop_setgetvalue(self.camera_handle,
                                           ctypes.c_int32(prop_id),
                                           ctypes.byref(p_value),
                                           ctypes.c_int32(DCAM_DEFAULT_ARG)),
                         "dcamprop_setgetvalue")
        return p_value.value

    def setSubArrayMode(self):
        """
        This sets the sub-array mode as appropriate based on the current ROI.
        """

        # Check ROI properties.
        roi_w = self.getPropertyValue("subarray_hsize")[0]
        roi_h = self.getPropertyValue("subarray_vsize")[0]

        # If the ROI is smaller than the entire frame turn on subarray mode
        if ((roi_w == self.max_width) and (roi_h == self.max_height)):
            self.setPropertyValue("subarray_mode", "OFF")
            
            print('Set subarray_mode OFF.')

            params = ["internal_frame_rate",
                      "timing_readout_time",
                      "exposure_time",
                      "subarray_hsize",
                      "subarray_mode",
                      "image_height",
                      "image_width",
                      "image_framebytes",
#                          "buffer_framebytes", # return byte size of a frame buffer that should be allocated 
                      # when you use dcambuf_attach() function
#                          "buffer_rowbytes",
#                          "buffer_top_offset_bytes",
                      "subarray_hsize",
                      "subarray_vsize",
#                          "binning",
#                          "record_fixedbytes_perfile", # return additional data size per a file.
#                          "record_fixedbytes_persession",
#                          "record_fixedbytes_perframe",
                      "buffer_framebytes", # return byte size of a frame buffer that should be allocated 
                      # when you use dcambuf_attach() function
                      "buffer_rowbytes",# return row byte size of user attached buffer
                      "buffer_top_offset_bytes",
                      "image_top_offset_bytes",
                      "record_fixed_bytes_per_file", # return additional data size per a file.
                      "record_fixed_bytes_per_session",
                      "record_fixed_bytes_per_frame"
                      ]
            # print('----------------------Settings-----------------------')
            # for param in params:
            #     if param == 'buffer_framebytes':
            #         try:
            #             print('A frame buffer that should be allocated: {} MB.'.format(rcam.getPropertyValue(param)[0]/1048576))
            #         except:
            #             print('A frame buffer that should be allocated: {} MB.'.format(hcam.getPropertyValue(param)[0]/1048576))
            #     else:
            #         print(param, self.getPropertyValue(param)[0])
            # print('-----------------------------------------------------')
        else:
            self.setPropertyValue("subarray_mode", "ON")
            print('Set subarray_mode ON.')

            params = ["internal_frame_rate",
                      "timing_readout_time",
                      "exposure_time",
                      "subarray_hsize",
                      "subarray_mode",
                      "image_height",
                      "image_width",
                      "image_framebytes",
#                          "buffer_framebytes", # return byte size of a frame buffer that should be allocated 
                      # when you use dcambuf_attach() function
#                          "buffer_rowbytes",
#                          "buffer_top_offset_bytes",
                      "subarray_hsize",
                      "subarray_vsize",
#                          "binning",
#                          "record_fixedbytes_perfile", # return additional data size per a file.
#                          "record_fixedbytes_persession",
#                          "record_fixedbytes_perframe",
                      "buffer_framebytes", # return byte size of a frame buffer that should be allocated 
                      # when you use dcambuf_attach() function
                      "buffer_rowbytes",# return row byte size of user attached buffer
                      "buffer_top_offset_bytes",
                      "image_top_offset_bytes",
                      "record_fixed_bytes_per_file", # return additional data size per a file.
                      "record_fixed_bytes_per_session",
                      "record_fixed_bytes_per_frame"
                      ]
            # print('----------------------Settings-----------------------')
            # for param in params:
            #     if param == 'buffer_framebytes':
            #         try:
            #             print('A frame buffer that should be allocated: {} MB.'.format(rcam.getPropertyValue(param)[0]/1048576))
            #         except:
            #             print('A frame buffer that should be allocated: {} MB.'.format(hcam.getPropertyValue(param)[0]/1048576))
            #     else:
            #         print(param, self.getPropertyValue(param)[0])
            # print('-----------------------------------------------------')
            

    def setACQMode(self, mode, number_frames = None):
        '''
        Set the acquisition mode to either run until aborted or to 
        stop after acquiring a set number of frames.
        mode should be either "fixed_length" or "run_till_abort"
        if mode is "fixed_length", then number_frames indicates the number
        of frames to acquire.
        '''

#        self.stopAcquisition()

        if self.acquisition_mode is "fixed_length" or \
                self.acquisition_mode is "run_till_abort":
            self.acquisition_mode = mode
            self.number_frames = number_frames
        else:
            raise DCAMException("Unrecognized acqusition mode: " + mode)


    def startAcquisition(self):
        """
        Start data acquisition.
        """
        self.captureSetup()

        #
        # Allocate Hamamatsu image buffers.
        # We allocate enough to buffer 2 seconds of data or the specified 
        # number of frames for a fixed length acquisition
        #
        if self.acquisition_mode is "run_till_abort":
            n_buffers = int(2.0*self.getPropertyValue("internal_frame_rate")[0])
        elif self.acquisition_mode is "fixed_length":
            n_buffers = self.number_frames

        self.number_image_buffers = n_buffers

	
        # The first method is to use the dcambuf_alloc() function to allocate the frame buffer
        # in the DCAM module. This is the most efficient way to receive images from the device. 
        # However, by using this method the host software needs to call the dcambuf_lockframe() function
        # to access this data or the dcambuf_copyframe() function to copy it.
        self.checkStatus(dcam.dcambuf_alloc(self.camera_handle,
                                  ctypes.c_int32(self.number_image_buffers)),
                         "dcambuf_alloc")

        # Start acquisition.
        if self.acquisition_mode is "run_till_abort":
            self.checkStatus(dcam.dcamcap_start(self.camera_handle,
                                    DCAMCAP_START_SEQUENCE),
                             "dcamcap_start")
        if self.acquisition_mode is "fixed_length":
            self.checkStatus(dcam.dcamcap_start(self.camera_handle,
                                    DCAMCAP_START_SNAP),
                             "dcamcap_start")

    def stopAcquisition(self):
        """
        Stop data acquisition.
        """

        # Stop acquisition.
        self.checkStatus(dcam.dcamcap_stop(self.camera_handle),
                         "dcamcap_stop")

        print("max camera backlog was", self.max_backlog, "of", self.number_image_buffers)
        self.max_backlog = 0

        # Free image buffers.
        self.number_image_buffers = 0
        self.checkStatus(dcam.dcambuf_release(self.camera_handle,
                                                DCAMBUF_ATTACHKIND_FRAME),
                         "dcambuf_release")

    def shutdown(self):
        """
        Close down the connection to the camera.
        """
        self.checkStatus(dcam.dcamwait_close(self.wait_handle),
                         "dcamwait_close")
        self.checkStatus(dcam.dcamdev_close(self.camera_handle),
                         "dcamdev_close")

    def sortedPropertyTextOptions(self, property_name):
        """
        Returns the property text options a list sorted by value.
        """
        text_values = self.getPropertyText(property_name)
        return sorted(text_values, key = text_values.get)


class HamamatsuCameraMR(HamamatsuCamera):
    """
    Memory recycling camera class.
    
    This version allocates "user memory" for the Hamamatsu camera 
    buffers. This memory is also the location of the storage for
    the np_array element of a HCamData() class. The memory is
    allocated once at the beginning, then recycled. This means
    that there is a lot less memory allocation & shuffling compared
    to the basic class, which performs one allocation and (I believe)
    two copies for each frame that is acquired.
    
    WARNING: There is the potential here for chaos. Since the memory
             is now shared there is the possibility that downstream code
             will try and access the same bit of memory at the same time
             as the camera and this could end badly.
    FIXME: Use lockbits (and unlockbits) to avoid memory clashes?
           This would probably also involve some kind of reference 
           counting scheme.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.hcam_data = []
        self.hcam_ptr = False
        self.old_frame_bytes = -1

        self.setPropertyValue("output_trigger_kind[0]", 2)
        

    def getFrames(self):
        """
        Gets all of the available frames.
        
        This will block waiting for new frames even if there new frames 
        available when it is called.
        
        FIXME: It does not always seem to block? The length of frames can
               be zero. Are frames getting dropped? Some sort of race condition?
        """
        frames = []
        for n in self.newFrames(): # self.newFrames typically looks like a list with integers like [0] and [1] in next frame.
            frames.append(self.hcam_data[n])
            
        return [frames, [self.frame_x, self.frame_y]]

    def startAcquisition(self):
        """
        Allocate as many frames as will fit in 4GB of memory and start data acquisition.
        """
        self.captureSetup()

        # Allocate new image buffers if necessary. This will allocate
        # as many frames as can fit in 2GB of memory, or 2000 frames,
        # which ever is smaller. The problem is that if the frame size
        # is small than a lot of buffers can fit in 2GB. Assuming that
        # the camera maximum speed is something like 1KHz 2000 frames
        # should be enough for 2 seconds of storage, which will hopefully
        # be long enough.
        #
        if (self.old_frame_bytes != self.frame_bytes) or \
                (self.acquisition_mode is "fixed_length"):
                    
            n_buffers = min(int((4.0 * 1024 * 1024 * 1024)/self.frame_bytes), 4000)
            print('Frame size: {} MB.'.format(self.frame_bytes/1024/1024))
            if self.acquisition_mode is "fixed_length":
                self.number_image_buffers = self.number_frames
            else:
                self.number_image_buffers = n_buffers

            # Allocate new image buffers.
            print('Number of image buffers: {}'.format(int(self.number_image_buffers)))
            ptr_array = ctypes.c_void_p * self.number_image_buffers # Create pointers to use.
            self.hcam_ptr = ptr_array() # The array of pointers of attached buffers.
            self.hcam_data = []
            for i in range(self.number_image_buffers):
                hc_data = HCamData(self.frame_bytes) # For each frame we allocate a numpy.ascontiguousarray buffer.
                self.hcam_ptr[i] = hc_data.getDataPtr() # Configure each frame memory pointer.
                self.hcam_data.append(hc_data) # List.append will not take up another memory space.

            self.old_frame_bytes = self.frame_bytes
            
            print('Buffer assigned: {} Gigabybtes.'.format(self.number_image_buffers*self.frame_bytes/1024/1024/1024))
        # Attach image buffers and start acquisition.
        #
        # We need to attach & release for each acquisition otherwise
        # we'll get an error if we try to change the ROI in any way
        # between acquisitions.

        # DCAMBUF_ATTACH structure:
        # self.hcam_ptr: Set to the array of pointers of attached buffers.
        # Set to the kind of attached buffers:
        # --DCAMBUF_ATTACHKIND_FRAME: Attach pointer array of user buffer to copy image.
        # --DCAMBUF_ATTACHKIND_TIMESTAMP: Attach pointer array of user buffer to copy timestamp.
        # --DCAMBUF_ATTACHKIND_FRAMESTAMP: Attach pointer array of user buffer to copy framestamp
        
        paramattach = DCAMBUF_ATTACH(0, DCAMBUF_ATTACHKIND_FRAME,
                self.hcam_ptr, self.number_image_buffers) # self.hcam_ptr: Set to the array of pointers of attached buffers.
        paramattach.size = ctypes.sizeof(paramattach)
        
        # The dcambuf_attach() function assigns allocated memory as the capturing buffer for the host software.
        # DCAM will transfer the image data directly from the device to these buffers. 
        if self.acquisition_mode is "run_till_abort":
            self.checkStatus(dcam.dcambuf_attach(self.camera_handle,
                                    paramattach),
                             "dcam_attachbuffer")
            self.checkStatus(dcam.dcamcap_start(self.camera_handle,
                                    DCAMCAP_START_SEQUENCE),
                             "dcamcap_start")
        if self.acquisition_mode is "fixed_length":
            paramattach.buffercount = self.number_frames
            self.checkStatus(dcam.dcambuf_attach(self.camera_handle,
                                    paramattach),
                             "dcambuf_attach")
            self.checkStatus(dcam.dcamcap_start(self.camera_handle,
                                    DCAMCAP_START_SNAP),
                             "dcamcap_start")
        self.AcquisitionStartTime = time.time()
        print("Acquisition starts at {} s.".format(self.AcquisitionStartTime))

    def stopAcquisition(self):
        """
        Stop data acquisition and release the memory associates with the frames.
        """


        # Stop acquisition.
        self.checkStatus(dcam.dcamcap_stop(self.camera_handle),
                         "dcamcap_stop")

        # Release image buffers.
        if (self.hcam_ptr):
            self.checkStatus(dcam.dcambuf_release(self.camera_handle,
                                                DCAMBUF_ATTACHKIND_FRAME),
                         "dcambuf_release")

        print("max camera backlog was:", self.max_backlog)
        self.max_backlog = 0

class HamamatsuCameraRE(HamamatsuCamera):
    """
    Streaming to disk camera class. 
    """
    def __init__(self, path, ext, **kwds):
        super().__init__(**kwds)

        self.RECcam_data = []
        self.hcam_ptr = False
        self.old_frame_bytes = -1
        self.additional_bytes_per_frame = 0

        self.setPropertyValue("output_trigger_kind[0]", 2)
        
        self.recording_path = path
        self.recording_extension = ext
        self.USE_USERMETADATA = False
        # Set up record handle
        pararecord = DCAMREC_OPEN()
#        pararecord = DCAMREC_OPEN(0, 0, None, 
#                                  ctypes.addressof(path_string_buf),#self.recording_path, const TCHAR pointer
#                                  ctypes.addressof(ext_string_buf),#self.recording_extension, const TCHAR pointer
#                                  0, 0, 0, 0, 0, 0, 0)
        pararecord.size = ctypes.sizeof(pararecord)
        pararecord.path = self.recording_path
        pararecord.ext = self.recording_extension
        pararecord.maxframepersession = 2000
        
        if self.USE_USERMETADATA == True:
            pararecord.userdatasize = 64 #Set this to the maximum bytes of binary user meta data for each frame.
            pararecord.userdatasize_session = 128 # Set this to the maximum bytes of binary user meta data for each session.
            pararecord.userdatasize_file = 256 # Set this to the maximum bytes of binary user meta data for the file.
            pararecord.usertextsize = 64 # Set this to the maximum bytes of user text meta data for each frame.
            pararecord.usertextsize_session = 128 # Set this to the maximum bytes of user text meta data for each session.
            pararecord.usertextsize_file = 256 # Set this to the maximum bytes of user text meta data for the file.
        else:
            pararecord.userdatasize = 0 #Set this to the maximum bytes of binary user meta data for each frame.
            pararecord.userdatasize_session = 0 # Set this to the maximum bytes of binary user meta data for each session.
            pararecord.userdatasize_file = 0 # Set this to the maximum bytes of binary user meta data for the file.
            pararecord.usertextsize = 0 # Set this to the maximum bytes of user text meta data for each frame.
            pararecord.usertextsize_session = 0 # Set this to the maximum bytes of user text meta data for each session.
            pararecord.usertextsize_file = 0 # Set this to the maximum bytes of user text meta data for the file.

        # Dependent on the path is defined using ASCII or UNICODE character the function is called either as dcamrec_opeaA() for ASCII 
        # or as dcamrec_openW() as wide (unicode ) caracter version. 
        self.checkStatus(dcam.dcamrec_openW(ctypes.byref(pararecord)), 
                         "dcamrec_open") 
        self.record_handle = ctypes.c_void_p(pararecord.hrec)
    
    
    def checkRecStatus(self):
        '''
        Gets the current recording status.
        '''
        pararec_status = DCAMREC_STATUS()
        pararec_status.size = ctypes.sizeof(pararec_status)        
        
        self.checkStatus(dcam.dcamrec_status(self.record_handle,
                                ctypes.byref(pararec_status)),
                         "dcamrec_status")
        
#        self.recording_status = str(pararec_status.flags)
#        self.recording_totalframecount = pararec_status.totalframecount
#        self.recording_currentframe_index = pararec_status.currentframe_index
#            
#        print('Recording flag is: '+self.recording_status)
#        print('Total frame count in the file: '+str(self.recording_totalframecount))
        return pararec_status 
    
    def CalculateMaxFileSize(self):
        self.RecordParaDict = {}
        #---------------Get property values-----------------
#        print('**************')
        params = ["buffer_rowbytes",
                  "image_width",                  
                  "image_height",
                  "subarray_hpos",
                  "subarray_vpos",
                  "record_fixed_bytes_per_file", # return additional data size per a file.
                  "record_fixed_bytes_per_session",
                  "record_fixed_bytes_per_frame"                  
                  ]
        
        for paramter in params:
            self.RecordParaDict[paramter] = self.getPropertyValue(paramter)[0]
            print(self.RecordParaDict[paramter])
#        print('**************')

    def startAcquisition(self):
        """
        Allocate as many frames as will fit in 2GB of memory and start data acquisition.
        """
        self.captureSetup()#self.frame_bytes is set here
        
        # Allocate new image buffers if necessary. This will allocate
        # as many frames as can fit in 2GB of memory, or 2000 frames,
        # which ever is smaller. The problem is that if the frame size
        # is small than a lot of buffers can fit in 2GB. Assuming that
        # the camera maximum speed is something like 1KHz 2000 frames
        # should be enough for 2 seconds of storage, which will hopefully
        # be long enough.
        #
        if (self.old_frame_bytes != self.frame_bytes) or \
                (self.acquisition_mode is "fixed_length"):
                    
            n_buffers = min(int((2.0 * 1024 * 1024 * 1024)/self.frame_bytes), 2000)
            print('Frame size: {} MB.'.format(self.frame_bytes/1024/1024))
            if self.acquisition_mode is "fixed_length":
                self.number_image_buffers = self.number_frames
            else:
                self.number_image_buffers = n_buffers
        elif self.acquisition_mode is "fixed_length":
            self.number_image_buffers = int(2.0*self.getPropertyValue("internal_frame_rate")[0])
            
        print('Number of image buffers: {}'.format(int(self.number_image_buffers)))
        
            
        #--------------------------------Allocate new host software buffer to receive capturing buffers.--------------------------------------------------------
#        ptr_array = ctypes.c_void_p * self.number_image_buffers # Create pointers to use.
#        self.hcam_ptr = ptr_array() # The array of pointers of attached buffers.
#        self.RECcam_data = []
#        for i in range(self.number_image_buffers):
#            # Allocate buffer for each frame.
#            # ??? originally buffer size for each frame is int(self.frame_bytes/2)-----seems to be related to numpy.empty buffer occupied mechanism
#            #!!!!!!!!!!!! self.additional_bytes_per_frame is actually not ADDITIONAL size but sth bigger than the frame size.
#            # Here DCAM only dumps frame info into DCAMBUF_ATTACHKIND_FRAME buffer, NO metada, part that is bigger than a frame needed is wasted.
#            # There are meta data assigned for each file, session, and frame.
#            Record_buffer_np_array = numpy.ascontiguousarray(numpy.empty(int((self.frame_bytes)/2), dtype=numpy.uint16))
#            self.hcam_ptr[i] = Record_buffer_np_array.ctypes.data
#            self.RECcam_data.append(Record_buffer_np_array)
            
            #!!!!!!!!After recording, RECcam_data is a list with each element being the np array of each frame plus additional bytes in buffer behind.
            
#                hc_data = HCamData(self.frame_bytes) # For each frame we allocate a buffer.
#                self.hcam_ptr[i] = hc_data.getDataPtr() # Configure each frame memory pointer.
#                self.RECcam_data.append(hc_data)

        self.old_frame_bytes = self.frame_bytes
            
#        print('Buffer assigned: {} Megabybtes.'.format(self.number_image_buffers*(self.frame_bytes)/1024/1024))
        '''
        #-----------------------------------------Allocate new buffers for TIMESTAMP.--------------------------------------------------------
        self.timestamp_bytes = 256
        timestamp_ptr_array = ctypes.c_void_p * self.number_image_buffers # Create pointers to use.
        self.rcam_timestamp_ptr = timestamp_ptr_array() # The array of pointers of attached buffers.
        for i in range(self.number_image_buffers):
            # Allocate buffer for each frame.
            # ??? originally buffer size for each frame is int(self.frame_bytes/2)-----seems to be related to numpy.empty buffer occupied mechanism
            #!!!!!!!!!!!! self.additional_bytes_per_frame is actually not ADDITIONAL size but sth bigger than the frame size.
            # Here DCAM only dumps frame info into DCAMBUF_ATTACHKIND_FRAME buffer, NO metada, part that is bigger than a frame needed is wasted.
            # There are meta data assigned for each file, session, and frame.
            timestamp_buffer_np_array = numpy.ascontiguousarray(numpy.empty(int((self.timestamp_bytes)/2), dtype=numpy.uint16))
            self.rcam_timestamp_ptr[i] = timestamp_buffer_np_array.ctypes.data    
        
        #-----------------------------------------Allocate new buffers for FRAMESTAMP.--------------------------------------------------------
        self.framestamp_bytes = 108
        framestamp_ptr_array = ctypes.c_void_p * self.number_image_buffers # Create pointers to use.
        self.rcam_framestamp_ptr = framestamp_ptr_array() # The array of pointers of attached buffers.
        for i in range(self.number_image_buffers):
            # Allocate buffer for each frame.
            # ??? originally buffer size for each frame is int(self.frame_bytes/2)-----seems to be related to numpy.empty buffer occupied mechanism
            #!!!!!!!!!!!! self.additional_bytes_per_frame is actually not ADDITIONAL size but sth bigger than the frame size.
            # Here DCAM only dumps frame info into DCAMBUF_ATTACHKIND_FRAME buffer, NO metada, part that is bigger than a frame needed is wasted.
            # There are meta data assigned for each file, session, and frame.
            framestamp_buffer_np_array = numpy.ascontiguousarray(numpy.empty(int((self.framestamp_bytes)/2), dtype=numpy.uint16))
            self.rcam_framestamp_ptr[i] = framestamp_buffer_np_array.ctypes.data 
        '''
                
        # Attach image buffers.
        #
        # We need to attach & release for each acquisition otherwise
        # we'll get an error if we try to change the ROI in any way
        # between acquisitions.

        # DCAMBUF_ATTACH structure:
        # self.hcam_ptr: Set to the array of pointers of attached buffers.
        # Set to the kind of attached buffers:
        # --DCAMBUF_ATTACHKIND_FRAME: Attach pointer array of user buffer to copy image.
        # --DCAMBUF_ATTACHKIND_TIMESTAMP: Attach pointer array of user buffer to copy timestamp.
        # --DCAMBUF_ATTACHKIND_FRAMESTAMP: Attach pointer array of user buffer to copy framestamp
        '''
        paramattach_frame = DCAMBUF_ATTACH(0, DCAMBUF_ATTACHKIND_FRAME,
                self.hcam_ptr, self.number_image_buffers) # self.hcam_ptr: Set to the array of pointers of attached buffers.
        paramattach_frame.size = ctypes.sizeof(paramattach_frame)
        
        
        paramattach_timestamp = DCAMBUF_ATTACH(0, DCAMBUF_ATTACHKIND_TIMESTAMP,
                self.rcam_timestamp_ptr, self.number_image_buffers) # self.hcam_ptr: Set to the array of pointers of attached buffers.
        paramattach_timestamp.size = ctypes.sizeof(paramattach_timestamp)
        
        paramattach_framestamp = DCAMBUF_ATTACH(0, DCAMBUF_ATTACHKIND_FRAMESTAMP,
                self.rcam_framestamp_ptr, self.number_image_buffers) # self.hcam_ptr: Set to the array of pointers of attached buffers.
        paramattach_framestamp.size = ctypes.sizeof(paramattach_framestamp)
        '''
        # The dcambuf_attach() function assigns allocated memory as the capturing buffer for the host software.
        # DCAM will transfer the image data directly from the device to these buffers.
        
        
        # To start recording, the dcamcap_record() function should be called during READY state.
# =============================================================================
#         if self.acquisition_mode is "run_till_abort":
#             # Attach the buffer.
#             '''
#             self.checkStatus(dcam.dcambuf_attach(self.camera_handle,
#                                     paramattach_frame),
#                              "dcam_attachbuffer")
#             '''
#             self.checkStatus(dcam.dcambuf_alloc(self.camera_handle,
#                           ctypes.c_int32(self.number_image_buffers)),
#                  "dcambuf_alloc")
#             # Prepares for the recording of images into storage during capturing. 
#             self.checkStatus(dcam.dcamcap_record(self.camera_handle,
#                                     self.record_handle),
#                              "dcamcap_record") 
# 
#             recordStatus = self.checkRecStatus()
#             # Starts image capturing and recording.
#             if recordStatus.flags == 0:
#                 
#                 self.checkStatus(dcam.dcamcap_start(self.camera_handle,
#                                         DCAMCAP_START_SEQUENCE),
#                                  "dcamcap_start")
#             
#                 self.AcquisitionStartTime = time.time()
#                 print("Acquisition starts at {} s.".format(self.AcquisitionStartTime))
#             
#             elif recordStatus.flags == DCAMCAP_STATUS_BUSY:
#                 print('DCAMCAP_STATUS_BUSY')
# =============================================================================
            
        if self.acquisition_mode is "fixed_length":
            '''
            paramattach_frame.buffercount = self.number_frames
            #--------------Attach frame buffers---------------------
            self.checkStatus(dcam.dcambuf_attach(self.camera_handle,
                                    paramattach_frame),
                             "dcambuf_attach")
#            #--------------Attach timestamp buffers-----------------
#            self.checkStatus(dcam.dcambuf_attach(self.camera_handle,
#                                    paramattach_timestamp),
#                             "dcambuf_attach")
#            #--------------Attach FRAMESTAMP buffers----------------
#            self.checkStatus(dcam.dcambuf_attach(self.camera_handle,
#                                    paramattach_framestamp),
#                             "dcambuf_attach")            
            '''
            # -------------------------------Allocate buffer------------------------------------
            self.checkStatus(dcam.dcambuf_alloc(self.camera_handle,
                          ctypes.c_int32(self.number_image_buffers)),
                 "dcambuf_alloc")
            
            self.checkStatus(dcam.dcamcap_record(self.camera_handle,
                                    self.record_handle),
                             "dcamcap_record")
            
#            recordStatus = self.checkRecStatus()

            if True:
#                print('try to start below...')
                
                self.checkStatus(dcam.dcamcap_start(self.camera_handle,
                                        DCAMCAP_START_SNAP),
                                 "dcamcap_start")
                
                self.AcquisitionStartTime = time.time()
                print("Acquisition starts at {} s.".format(self.AcquisitionStartTime))
                
                #-------------------------Wait until record event has stopped----------------------------------------
                paramRecWaitStart = DCAMWAIT_START(
                                            0, 
                                            0, 
                                            DCAMWAIT_RECEVENT_STOPPED | DCAMWAIT_RECEVENT_MISSED, 
                                            2000)
                paramRecWaitStart.size = ctypes.sizeof(paramRecWaitStart)
                
#                dcam.dcamwait_start(self.wait_handle, ctypes.byref(paramRecWaitStart))        
                
                RECStop = False
                while RECStop != True:
                    # Keep checking if capture event is stopped.
        #                    self.checkStatus(fn_return = dcam.dcamwait_start(self.wait_handle,
        #                                    ctypes.byref(paramRecWaitStart)),
        #                                     "dcamwait_start")  
                    fn_return = dcam.dcamwait_start(self.wait_handle,
                                    ctypes.byref(paramRecWaitStart))
#                    print(fn_return)
                    
                    pararec_status = self.checkRecStatus()
                    print('latest index: {}'.format(pararec_status.currentframe_index))
                    print(pararec_status.flags)
                    print('missing frame count: {}'.format(pararec_status.missingframe_count))
                    RecStatusCheckTime = time.time()
                    print('Total frame count in the file: {}; Time past: {}'.format(pararec_status.totalframecount, (RecStatusCheckTime - self.AcquisitionStartTime)))
        #            if paramRecWaitStart.eventhappened == DCAMWAIT_RECEVENT_STOPPED:
                    if pararec_status.flags == 0:
                        RECStop = True
                #-------------------------
                
#                #-------------------------Wait-start capture----------------------------------------
#                paramCapWaitStart = DCAMWAIT_START(
#                                            0, 
#                                            0, 
#                                            DCAMWAIT_CAPEVENT_STOPPED,# | DCAMWAIT_RECEVENT_MISSED, 
#                                            100)
#                paramCapWaitStart.size = ctypes.sizeof(paramCapWaitStart)
#                
#                bStop = False
#                while bStop != True:
#                    # Keep checking if capture event is stopped.
##                    self.checkStatus(fn_return = dcam.dcamwait_start(self.wait_handle,
##                                    ctypes.byref(paramRecWaitStart)),
##                                     "dcamwait_start")  
#                    fn_return = dcam.dcamwait_start(self.wait_handle,
#                                    ctypes.byref(paramCapWaitStart))
#                    print(fn_return)
#                    
#                    if paramCapWaitStart.eventhappened == DCAMWAIT_CAPEVENT_STOPPED:
##                    if fn_return == 1:
#                        bStop = True    
                        
#                    pararec_status = self.checkRecStatus()
#                    print('latest index: {}'.format(self.recording_currentframe_index))
                        

#                #-------------------------Wait until record event has stopped----------------------------------------
#                paramRecWaitStart = DCAMWAIT_START(
#                                            0, 
#                                            0, 
#                                            DCAMWAIT_RECEVENT_STOPPED,# | DCAMWAIT_RECEVENT_MISSED, 
#                                            100)
#                paramRecWaitStart.size = ctypes.sizeof(paramRecWaitStart)
#                
##                dcam.dcamwait_start(self.wait_handle, ctypes.byref(paramRecWaitStart))        
#                
#                RECStop = False
#                while RECStop != True:
#                    # Keep checking if capture event is stopped.
#        #                    self.checkStatus(fn_return = dcam.dcamwait_start(self.wait_handle,
#        #                                    ctypes.byref(paramRecWaitStart)),
#        #                                     "dcamwait_start")  
#                    fn_return = dcam.dcamwait_start(self.wait_handle,
#                                    ctypes.byref(paramRecWaitStart))
#                    print(fn_return)
#                    
#        #            if paramRecWaitStart.eventhappened == DCAMWAIT_RECEVENT_STOPPED:
#                    if fn_return == 1:
#                        RECStop = True
#                #-------------------------
                # -------------------------------dcambuf_copyframe---------------------------------
                # copies image data from capturing buffer to a buffer provided by the host software.  
#                for i in range(self.number_image_buffers):
#                    for n in self.newFrames(): # n should start from 0.
##                        print(n)
#                        paramlock_copyframe = DCAMBUF_FRAME()
#                                
#                        paramlock_copyframe.iFrame = n
#                        paramlock_copyframe.size = ctypes.sizeof(paramlock_copyframe)	
#                        paramlock_copyframe.buf = self.hcam_ptr[n]
#                        paramlock_copyframe.rowbytes = RecordParaDict["buffer_rowbytes"]
#                        paramlock_copyframe.width = RecordParaDict["image_width"]
#                        paramlock_copyframe.height = RecordParaDict["image_height"]
#                        paramlock_copyframe.left = RecordParaDict["subarray_hpos"]
#                        paramlock_copyframe.width = RecordParaDict["subarray_vpos"]
#            
#                        # Copy the frame in the camera buffer.
#                        self.checkStatus(dcam.dcambuf_copyframe(self.camera_handle,
#                                                            ctypes.byref(paramlock_copyframe)),
#                                         "dcambuf_lockframe")
                    
                
            elif recordStatus.flags == DCAMCAP_STATUS_BUSY:
                print('DCAMCAP_STATUS_BUSY')

            
#        elif captureStatus.value == DCAMCAP_STATUS_BUSY:
#            print('Fail to start recording! Camera is busy!')

    def stopAcquisition(self):
        """
        Stop data acquisition and release the memory associates with the frames.
        """
        # Wait until capture event stopped.
#        paramstart = DCAMWAIT_START(
#                0, 
#                0, 
#                DCAMWAIT_RECEVENT_STOPPED,# | DCAMWAIT_RECEVENT_MISSED, 
#                2000)
#        paramstart.size = ctypes.sizeof(paramstart)
#        self.checkStatus(dcam.dcamwait_start(self.wait_handle,
#                                        ctypes.byref(paramstart)),
#                         "dcamwait_start")
        self.AcquisitionStopTime = time.time()  
        print('Capture for {} s.'.format(self.AcquisitionStopTime - self.AcquisitionStartTime))


        # Stop acquisition.
        # The dcamcap_stop() function terminates capture started by the dcamcap_start() function. 
        # If the capturing has already been terminated, this function will do nothing. 
        # If the device is recording, that process will also be terminated.
        #you need to stop the recording with dcamcap_stop() before dcamrec_close(). 
        self.checkStatus(dcam.dcamcap_stop(self.camera_handle),
                         "dcamcap_stop")
        
        
        
        # The dcamrec_close() function flushes all of the data including the meta data
        self.checkStatus(dcam.dcamrec_close(self.record_handle),
                         "dcamrec_close")
        print('dcamrec_close.')

#        time.sleep(5)

#            elif paramRecWaitStart.eventhappened == DCAMWAIT_RECEVENT_MISSED:
#                print('frame missing.')
                
        # Release image buffers.
        print('dcambuf_release')
        self.checkStatus(dcam.dcambuf_release(self.camera_handle, DCAMBUF_ATTACHKIND_FRAME | 
                DCAMBUF_ATTACHKIND_TIMESTAMP | DCAMBUF_ATTACHKIND_FRAMESTAMP),"dcambuf_release")
#                                            DCAMBUF_ATTACHKIND_FRAME | DCAMBUF_ATTACHKIND_TIMESTAMP | DCAMBUF_ATTACHKIND_FRAMESTAMP),
#                     "dcambuf_release")

#        print("max camera backlog was:", self.max_backlog)
#        self.max_backlog = 0
        
        self.checkStatus(dcam.dcamwait_close(self.wait_handle),
                         "dcamwait_close")
        self.checkStatus(dcam.dcamdev_close(self.camera_handle),
                         "dcamdev_close")
#
# Testing.
#
if (__name__ == "__main__"):

    import time
    import random
    import numpy as np
    import skimage.external.tifffile as skimtiff
    #
    # Initialization
    # Load dcamapi.dll version 19.12.641.5901
    dcam = ctypes.WinDLL(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\People\Xin Meng\Code\Python_test\HamamatsuCam\19_12\dcamapi.dll')
    
    paraminit = DCAMAPI_INIT(0, 0, 0, 0, None, None) 
    paraminit.size = ctypes.sizeof(paraminit)
    error_code = dcam.dcamapi_init(ctypes.byref(paraminit))
    #if (error_code != DCAMERR_NOERROR):
    #    raise DCAMException("DCAM initialization failed with error code " + str(error_code))
    
    n_cameras = paraminit.iDeviceCount

    print("found:", n_cameras, "cameras")
    
    Streaming_to_disk = False # False: Filling RAM first, Saving to hard disk afterwards. 
                           # True: Streaming to disk while capturing.
    
    if (n_cameras > 0):
        
        if Streaming_to_disk == False:
    
            hcam = HamamatsuCameraMR(camera_id = 0)
            print(hcam.setPropertyValue("defect_correct_mode", 1))
            print("camera 0 model:", hcam.getModelInfo(0))
            
            # List support properties.
            # Property names are converted. For example, internal_frame_rate = DCAM_IDPROP_INTERNALFRAMERATE in API reference.
            if True:
                print("Supported properties:")
                props = hcam.getProperties()
                for i, id_name in enumerate(sorted(props.keys())):
                    [p_value, p_type] = hcam.getPropertyValue(id_name)
                    p_rw = hcam.getPropertyRW(id_name)
                    read_write = ""
                    if (p_rw[0]):
                        read_write += "read"
                    if (p_rw[1]):
                        read_write += ", write"
                    print("  ", i, ")", id_name, " = ", p_value, " type is:", p_type, ",", read_write)
                    text_values = hcam.getPropertyText(id_name)
                    if (len(text_values) > 0):
                        print("          option / value")
                        for key in sorted(text_values, key = text_values.get):
                            print("         ", key, "/", text_values[key])
                            
            # Test setting & getting some parameters.
            if True:
                
                #print(hcam.setPropertyValue("subarray_hsize", 2048))
                #print(hcam.setPropertyValue("subarray_vsize", 2048))
                # print(hcam.setPropertyValue("subarray_hpos", 512))  # This property allows you to specify the LEFT position of capturing area. 
                print(hcam.setPropertyValue("subarray_vpos", 512))  # This property allows you to specify the top position of capturing area. 
                print(hcam.setPropertyValue("subarray_hsize", 2048))
                print(hcam.setPropertyValue("subarray_vsize", 1024))
                
                # hcam.setSubArrayMode()            
                
                print(hcam.setPropertyValue("exposure_time", 0.002))#0.0006/16
    
                print(hcam.setPropertyValue("binning", "1x1"))
                print(hcam.setPropertyValue("readout_speed", 2))
        
    
                #hcam.startAcquisition()
                #hcam.stopAcquisition()
    
                params = ["internal_frame_rate",
                          "timing_readout_time",
                          "exposure_time",
                          "subarray_hsize",
                          "subarray_vsize",
                          "subarray_mode"]
    
                #                      "image_height",
                #                      "image_width",
                #                      "image_framebytes",
                #                      "buffer_framebytes",
                #                      "buffer_rowbytes",
                #                      "buffer_top_offset_bytes",
                #                      "subarray_hsize",
                #                      "subarray_vsize",
                #                      "binning"]
                for param in params:
                    print(param, hcam.getPropertyValue(param)[0])
                    if param == "subarray_hsize":
                        subarray_hsize = hcam.getPropertyValue(param)[0]
                    if param == "subarray_vsize":
                        subarray_vsize = hcam.getPropertyValue(param)[0]
                        
                frame_pixelsize = subarray_hsize * subarray_vsize
            # Test 'run_till_abort' acquisition.
            if True:
                print("Testing run till abort acquisition")
                hcam.startAcquisition()
                
                video_list = []
                frame_num = 200
                cnt = 0
                for i in range(frame_num): # Record for range() number of images.
                    if i == 0:
                        print('Start getting frames at {} s...'.format(time.time()))
                    [frames, dims] = hcam.getFrames() # frames is a list with HCamData type, with np_array being the image.
                    for aframe in frames:
                        video_list.append(aframe.np_array)
                        cnt += 1
    #                print('frames size is {}'.format(len(frames)))
                AcquisitionEndTime = time.time()
                print("Frames acquired: " + str(cnt))
                print('Total time is: {} s.'.format(AcquisitionEndTime-hcam.AcquisitionStartTime))
                print('Estimated fps: {} hz.'.format(int(cnt/(AcquisitionEndTime-hcam.AcquisitionStartTime))))
                hcam.stopAcquisition()
            
            if True:
                video_name = r"M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Xin\2020-3-31 cam matrix reconstruct\recordtest.tif"
                with skimtiff.TiffWriter(video_name, append = True, imagej = True)\
                as tif:                
                    write_starttime = time.time()
                    for eachframe in range(frame_num): 
                        image = np.resize(video_list[eachframe], (subarray_vsize, subarray_hsize))
                        
                        tif.save(image, compress=0)
                print("Done writing " + str(frame_num) + " frames, recorded for "\
                + str(round(AcquisitionEndTime,2)) + " seconds, saving video takes {} seconds.".format(round(time.time()-write_starttime, 2)))
            
            # Test 'fixed_length' acquisition.
            if False:
                for j in range (10000):
                    print("Testing fixed length acquisition")
                    hcam.setACQMode("fixed_length", number_frames = 10)
                    hcam.startAcquisition()
                    cnt = 0
                    iterations = 0
                    while cnt < 11 and iterations < 20:
                        [frames, dims] = hcam.getFrames()
                        waitTime = random.random()*0.03
                        time.sleep(waitTime)
                        iterations += 1
                        print('Frames loaded: ' + str(len(frames)))
                        print('Wait time: ' + str(waitTime))
                        for aframe in frames:
                            print(cnt, aframe[0:5])
                            cnt += 1
                    if cnt < 10:
                        print('##############Error: Not all frames found#########')
                        input("Press enter to continue")
                    print("Frames acquired: " + str(cnt))        
                    hcam.stopAcquisition()
    
                    hcam.setACQMode("run_till_abort")
                    hcam.startAcquisition()
                    time.sleep(random.random())
                    contFrames = hcam.getFrames()
                    hcam.stopAcquisition()
                            
            hcam.shutdown()
        
        #--------------------------------------------------------------------------------------------------------------------------------
        elif Streaming_to_disk == True:
            
            rcam = HamamatsuCameraRE(path = 'M:\\tnw\\ist\\do\\projects\\Neurophotonics\\Brinkslab\\People\\Xin Meng\\Code\\Python_test\\HamamatsuCam\\test_fullframe',
                                     ext = 'dcimg',
                                     camera_id = 0)
            
            # List support properties.
            # Property names are converted. For example, internal_frame_rate = DCAM_IDPROP_INTERNALFRAMERATE in API reference.
            if False:
                print("Supported properties:")
                props = rcam.getProperties()
                for i, id_name in enumerate(sorted(props.keys())):
                    [p_value, p_type] = rcam.getPropertyValue(id_name)
                    p_rw = rcam.getPropertyRW(id_name)
                    read_write = ""
                    if (p_rw[0]):
                        read_write += "read"
                    if (p_rw[1]):
                        read_write += ", write"
                    print("  ", i, ")", id_name, " = ", p_value, " type is:", p_type, ",", read_write)
                    text_values = rcam.getPropertyText(id_name)
                    if (len(text_values) > 0):
                        print("          option / value")
                        for key in sorted(text_values, key = text_values.get):
                            print("         ", key, "/", text_values[key])            
            
            # Test setting & getting some parameters.
            if True:
                #// set subarray mode off. This setting is not mandatory, but you have to control the setting order of offset and size when mode is on.
                rcam.setPropertyValue("subarray_mode", "OFF")
                rcam.setPropertyValue("subarray_hpos", 512)  # This property allows you to specify the LEFT position of capturing area. 
                rcam.setPropertyValue("subarray_vpos", 768)  # This property allows you to specify the top position of capturing area. 
                rcam.setPropertyValue("subarray_hsize", 128)
                rcam.setPropertyValue("subarray_vsize", 512)
                
#                rcam.setSubArrayMode()            
                
                rcam.setPropertyValue("exposure_time", 0.002)
    
                rcam.setPropertyValue("binning", "1x1")
                rcam.setPropertyValue("readout_speed", 2)
        
            if False:
                #// set subarray mode off. This setting is not mandatory, but you have to control the setting order of offset and size when mode is on.
                rcam.setPropertyValue("subarray_mode", "OFF")    
                rcam.setPropertyValue("exposure_time", 0.001003)
    
                rcam.setPropertyValue("binning", "1x1")
                rcam.setPropertyValue("readout_speed", 2)
                    
            # Test 'run_till_abort' acquisition.
            if True:
                print("----------------Testing fixed length acquisition-------------------")
                rcam.setACQMode("fixed_length", number_frames = 200*2)
                print('Acquisition_mode is: '+str(rcam.acquisition_mode))
#                time.sleep(1)

                
                rcam.startAcquisition()
#                time.sleep(3)
#                rcam.checkRecStatus() # If this is called during recording, it sort of block it, resulting in smaller file size??
#                AcquisitionEndTime = time.time()
#                print("Frames acquired: " + str(cnt))
#                print('Total time is: {} s.'.format(AcquisitionEndTime-rcam.AcquisitionStartTime))
#                print('Estimated fps: {} hz.'.format(int(cnt/(AcquisitionEndTime-hcam.AcquisitionStartTime))))
#                recordStatus = rcam.checkRecStatus()
#                print('Total frame count in the file: '+str(recordStatus.totalframecount))
#                time.sleep(20)
                rcam.stopAcquisition()
#                time.sleep(10)
                # The resulting file size should be 75.3 MB from HoKaWo(128*512, 600 frames)
#                time.sleep(2)# Release buffer time??--Doesn't work.
#                RECcam_data = rcam.RECcam_data
#            rcam.shutdown()
            
            # Access the binary data
            # Seems start from 576 it's the frist pixel value.
#            xbash = np.fromfile(r'M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Equipment\Hamamatsu Orca Flash\test.tif', dtype='uint16')
#            print(xbash[576])
#            print(xbash[72])
    dcam.dcamapi_uninit()
#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#