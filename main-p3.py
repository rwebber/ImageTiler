import sys

# import numpy as np
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import gui

import numpy as np
import itertools as it
import cv2

__author__ = 'DusXproductions'

# NOTE: image files must be names as: name0000.type (eg tile_0001.jpg or shape-000.jpg)

# GUI py create... ensure terminal is in project dir
# pyside-uic first.ui  -o gui.py
# Note: *.ui is file from QT designer, and *.py is output name
# -- *the BAT file includes this command and can be run from terminal by name.*

# ref: http://pyside.github.io/docs/pyside/
# http://srinikom.github.io/pyside-docs/PySide/QtGui/

""" basic openCV load and display of image.
ref: http://docs.opencv.org/modules/highgui/doc/reading_and_writing_images_and_video.html
reads:
    Windows bitmaps - *.bmp, *.dib (always supported)
    JPEG files - *.jpeg, *.jpg, *.jpe (see the Notes section)
    JPEG 2000 files - *.jp2 (see the Notes section)
    Portable Network Graphics - *.png (see the Notes section)
    Portable image format - *.pbm, *.pgm, *.ppm (always supported)
    Sun rasters - *.sr, *.ras (always supported)
    TIFF files - *.tiff, *.tif (see the Notes section)
"""



class MyApplication(QMainWindow, gui.Ui_MainWindow):
        def __init__(self, parent=None):
            super(MyApplication, self).__init__(parent)
            self.setupUi(self)

            """ PySide connections """
            # connect the button to the test field
            # self.connect(self.pathButton, SIGNAL("clicked()"), self.filedialog)
            self.imgpathButton.clicked.connect(self.filedialog)
            self.processButton.clicked.connect(self.process_images)
            self.rangeStartVal.editingFinished.connect(self.set_range_start)
            self.rangeEndVal.editingFinished.connect(self.set_range_end)
            self.MosaicColsVal.valueChanged.connect(self.set_mosaic_cols)
            self.saveName.editingFinished.connect(self.set_savename)
            self.savepathButton.clicked.connect(self.folderdialog)

            """ project vars """
            self.selectedfilename = ""
            self.savename = ""
            self.foldername = ""

            self.SEQimageWidth = 0 # define the width and height for the SEQ image
            self.SEQimageHeight = 0 # note each MUST be the same...
            self.WxHdisplay = "NA x NA"
            self.WXH_LabelDisplay.setText(self.WxHdisplay)

            self.rangeStart = "0"
            print ("-" + self.rangeStart)
            self.rangeStartLabel.setText(self.rangeStart)

            self.rangeEnd = "1"
            print ("-" + self.rangeEnd)
            self.rangeEndLabel.setText(self.rangeEnd)

            self.rangeCount = int(self.rangeEnd) - int(self.rangeStart)  # duplicate code ??
            self.rangeCountLabelDisplay.setText(str(self.rangeCount))

            self.mosaicCols = self.MosaicColsVal.value()
            print("mosaic cols = ", self.mosaicCols)


        def set_savename(self):
            self.savename = self.saveName.text()
            print ("savename = ", self.savename)

        def set_mosaic_cols(self):
            self.mosaicCols = self.MosaicColsVal.value()
            print ("mosaic cols = ", self.mosaicCols)
            self.set_range_count()

        def set_range_start(self):
            self.rangeStart = self.rangeStartVal.text()
            self.rangeStartLabel.setText(self.rangeStart)
            print ("range start = ", self.rangeStart)
            self.set_range_count()

        def set_range_end(self):
            self.rangeEnd = self.rangeEndVal.text()
            self.rangeEndLabel.setText(self.rangeEnd)
            print ("range end = ", self.rangeEnd)
            self.set_range_count()

        def set_range_count(self):
            # check range start and end.. and output the number of items in range
            self.rangeCount = (int(self.rangeEnd) - int(self.rangeStart)) + 1
            self.rangeCountLabelDisplay.setText(str(self.rangeCount))
            print ("range end = ", self.rangeCount)
            # divide by COLS, use modulus to see if even..
            # change output color based on this number.
            if self.rangeCount % self.mosaicCols > 0:
                formattedText = "<font color='red'>%s</font> - not a fit!" % str(self.rangeCount)
            else:
                formattedText = "<font color='green'>%s</font> - perfect." % str(self.rangeCount)
            self.rangeCountLabelDisplay.setText(formattedText)

        def process_images(self): # called by Process button
            print ("PROCESSSING....")
            # if mode is set to X call X function
            # routine_basic_mosaic
            # routine_row-by-row_mosaic

            if (self.selectedfilename != ""  # ensure a filepath was selected
            and self.savename != ""  # ensure a filename was set
            and self.rangeStart < self.rangeEnd):  # ensure start is less than end. ** maybe not for reverse??
                imageroot = self.find_imageroot(self.imgpathDisplay.text())
                print ("imageroot- ", imageroot)
                # return tuple : string (path), int (num of value chars), string (file extension)
                start_val = int(self.rangeStart)
                end_val = int(self.rangeEnd)

                # create an list of file paths.
                path_list = []
                for i in range(start_val, end_val + 1):
                    path_list.append(self.construct_count_string(i, imageroot))
                print ("List of files: \n", path_list)


                # ^^^ SETUP A SWITCH FOR DIFFERENT ROUTINES
                # mosaic = self.routine_basic_mosaic(path_list)

                mosaic = self.routine_row_by_row_mosaic(path_list)

                savepath = self.foldername + "\\" + self.savename + ".png" # create full path for saving.
                print (savepath)
                cv2.imwrite(savepath, mosaic)

                print ("COMPLETE!")
            else:
                print ("can't run processing routine. Start conditions failed.")
                return 0

        def routine_row_by_row_mosaic(self, path_list):
            """
            optimized routine, only loads into memory the minimum size canvas,
            plus 1 seq image at a time.
            Uses a couple sub functions to process the image creation.
            """

            def create_blank_row(height, width, cols):
                """
                create a numpy image equal the hieght of sequence image,
                 and the width of sq images * cols the full width of image being created
                """
                blankrow = np.zeros((height, width*cols, 3), np.uint8)
                return blankrow

            def tile_in_images(mosaic, path_list, cols, row):
                """
                extend the current mosaic, with a blank row (black),
                 and then tile in Sequence image over the black
                """
                imgnum = row * cols
                startpos = 0
                img = cv2.imread(path_list[imgnum], cv2.IMREAD_COLOR)
                w, h = img.shape[1::-1] # get image width and height

                if mosaic is None:  # used to use ==
                    mosaic = create_blank_row(h, w, cols)
                else:
                    blank_row = create_blank_row(h, w, cols)
                    mosaic = np.vstack((blank_row, mosaic))  # combine the blank with the good

                # loop and place images in the blank row...
                for c in range(cols):
                    print ("imgLoaded = ", imgnum)
                    if imgnum <= len(path_list):
                        img = cv2.imread(path_list[imgnum], cv2.IMREAD_COLOR)
                        mosaic[0:h, startpos:startpos + w] = img  # paste in image - h:h, w:w
                        startpos = startpos + w
                        imgnum += 1
                return mosaic

            """
            start logic for routine.
            use above functions to process logic.
                # img = cv2.imread(path_list[0], cv2.IMREAD_COLOR)
                # h, w = img.shape[1::-1]  # get the image width and height
                # ref: http://stackoverflow.com/questions/19098104/python-opencv2-cv2-wrapper-get-image-size
                # mosaic = create_blank_row(h, w, cols)
                # ball = img[280:340, 330:390] -- select part of img as ball
                # img[273:333, 100:160] = ball -- set part of image to contents of ball
            """

            num_of_images = len(path_list)
            cols = self.mosaicCols
            rows = num_of_images // cols  # uses floor division op '//' to ensure int output
            if num_of_images % cols > 0: # a remainder row --- incomplete fill
                rows += 1

            mosaic = None  # set to test value. checked in tile routine
            """ process thru the number of rows the final image will have """
            for r in range(rows):
                # call tile in Images for each row.. and pass the count
                mosaic = tile_in_images(mosaic, path_list, cols, r)
                # cv2.imshow('image',mosaic)
                # cv2.waitKey(0)
                # cv2.destroyAllWindows()
            return mosaic


        def routine_basic_mosaic(self, path_list):
            # create an list of images.
            img_list = []
            for i in range(len(path_list)):
                image = cv2.imread(path_list[i])
                img_list.append(image)
            mosaic = self.mosaic(self.mosaicCols, img_list)
            return mosaic

        def folderdialog(self):  # method called by pathButton SIGNAL ! Used for SAVE Path

            foldername = QFileDialog.getExistingDirectory(self, "Open folder", "\\", options=QFileDialog.ShowDirsOnly)
            # filename = tuple..
            # [0] is the filepath, [1] is the type (same as type string passed with QFileDialog)
            # note both return '' if not selected

            self.foldername = foldername
            self.savepathDisplay.setText(self.foldername)
            print (self.foldername)

        def filedialog(self):  # method called by pathButton SIGNAL ! Used for OPEN Path
            """
            # dialog = QFileDialog(self)
            # dialog.setFileMode(QFileDialog.ExistingFile) # require existing file is selected
            # # dialog.setNameFilter(tr("Images (*.png *.jpg)"))
            # dialog.setNameFilter("Image files (*.jpg *.png)")
            # dialog.setDirectory("\\") # set to system root.. c: on windows
            # # filename, _ = dialog.getOpenFileName()  # get file location - simple path only
            # filename = dialog.getOpenFileName()  # get file location, unicode tuple
            # # path = dialog.directory() # try to get dir path
            # # path = dialog.getExistingDirectory()  # get only the folder location.
            """  # some other options ect... for the same control

            filename = QFileDialog.getOpenFileName(self, "Open Image", "\\", "Image Files (*.png *.jpg *.bmp)")
            # filename = tuple..
            # [0] is the filepath, [1] is the type (same as type string passed with QFileDialog)
            # note both return '' if not selected

            self.selectedfilename = filename[0]
            self.imgpathDisplay.setText(self.selectedfilename)
            print (self.selectedfilename)

            # get size of image
            img = cv2.imread(self.selectedfilename)
            self.SEQimageHeight, self.SEQimageWidth, depth = img.shape
            self.WxHdisplay = str(self.SEQimageWidth) + " x " + str(self.SEQimageHeight)
            self.WXH_LabelDisplay.setText(self.WxHdisplay)


        def construct_count_string(self, count, imageroot):
            insert_count = imageroot[1] - len(str(count))  # convert counter to string then get length
            value_chars = ("0" * insert_count) + str(count)
            # print "value chars= ", value_chars
            new_path = imageroot[0] + value_chars + "." + imageroot[2]
            # print "new path= ", new_path
            return new_path

        def find_imageroot(self, start_image):
            """
            return tuple : string (path, eg "C:\images\tileimage_"),
            int (num of value chars, eg: '001" = 3),
            string (file extension, eg: "png"),
            example based on full path= "C:\images\tileimage_001.png"
            """
            # start_image[-4] should give the '.' from file extension

            extension_delimiter = -4  # count to the '.' before file extension

            if start_image[extension_delimiter] == ".":
                i = extension_delimiter
                while True:
                    i -= 1
                    num = start_image[i]
                    if self.is_number(num):
                        pass
                    else:
                        i += 1  # set to last True value
                        break
                image_root = start_image[:i]
                count_span = start_image[i:extension_delimiter]
                print("span area- ", count_span)
                span_count = len(count_span)
                image_type = start_image[extension_delimiter+1:]
                print("image type = ", image_type)
                if count_span == 0:
                    raise Exception("ERROR, file increment area not found. def: find_imageroot")
                else:
                    return image_root, span_count, image_type
            else:
                raise Exception("ERROR, file extension delimiter not found. def: find_imageroot")

        def is_number(self, string):
            try:
                float(string)
                return True
            except ValueError:
                return False

        """
        def from : https://github.com/Itseez/opencv/blob/master/samples/python2/common.py
        """
        def grouper(self, n, iterable, fillvalue=None):
            '''grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx'''
            args = [iter(iterable)] * n
            return it.izip_longest(fillvalue=fillvalue, *args)

        def mosaic(self, w, imgs):
            ''' Make a grid from images.
            w    -- number of grid columns
            imgs -- images (must have same size and format)
            '''
            imgs = iter(imgs)
            img0 = imgs.next()
            pad = np.zeros_like(img0)
            imgs = it.chain([img0], imgs)
            rows = self.grouper(w, imgs, pad)
            return np.vstack(map(np.hstack, rows))


if __name__ == "__main__":
        app = QApplication(sys.argv)
        window = MyApplication()
        window.setFixedSize(210, 295)
        window.set_range_count() # do init setting of value
        window.show()
        sys.exit(app.exec_())
