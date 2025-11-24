__author__ = 'DusX'

# GUI py create... ensure terminal is in project dir
# pyside6-uic first.ui  -o gui.py
# Note: *.ui is file from QT designer, and *.py is output name

import sys
import os
import itertools as it

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QMainWindow, QApplication, QFileDialog

import cv2
import numpy as np
import gui


class MyApplication(QMainWindow, gui.Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # PySide6 signal connections
        self.imgpathButton.clicked.connect(self.filedialog)
        self.processButton.clicked.connect(self.process_images)
        self.rangeStartVal.editingFinished.connect(self.set_range_start)
        self.rangeEndVal.editingFinished.connect(self.set_range_end)
        self.MosaicColsVal.valueChanged.connect(self.set_mosaic_cols)
        self.saveName.editingFinished.connect(self.set_savename)
        self.savepathButton.clicked.connect(self.folderdialog)

        # project vars
        self.selectedfilename = ""
        self.savename = ""
        self.foldername = ""

        self.SEQimageWidth = 0  # define the width and height for the SEQ image
        self.SEQimageHeight = 0  # note each MUST be the same...
        self.WxHdisplay = "NA x NA"
        self.WXH_LabelDisplay.setText(self.WxHdisplay)

        self.rangeStart = "0"
        print("-", self.rangeStart)
        self.rangeStartLabel.setText(self.rangeStart)

        self.rangeEnd = "1"
        print("-", self.rangeEnd)
        self.rangeEndLabel.setText(self.rangeEnd)

        self.rangeCount = int(self.rangeEnd) - int(self.rangeStart)  # duplicate code ??
        self.rangeCountLabelDisplay.setText(str(self.rangeCount))

        self.mosaicCols = self.MosaicColsVal.value()
        print("mosaic cols = ", self.mosaicCols)

    def set_savename(self):
        self.savename = self.saveName.text()
        print("savename = ", self.savename)

    def set_mosaic_cols(self):
        self.mosaicCols = self.MosaicColsVal.value()
        print("mosaic cols = ", self.mosaicCols)
        self.set_range_count()

    def set_range_start(self):
        self.rangeStart = self.rangeStartVal.text()
        self.rangeStartLabel.setText(self.rangeStart)
        print("range start = ", self.rangeStart)
        self.set_range_count()

    def set_range_end(self):
        self.rangeEnd = self.rangeEndVal.text()
        self.rangeEndLabel.setText(self.rangeEnd)
        print("range end = ", self.rangeEnd)
        self.set_range_count()

    def set_range_count(self):
        # check range start and end.. and output the number of items in range
        try:
            self.rangeCount = int(self.rangeEnd) - int(self.rangeStart) + 1
        except ValueError:
            self.rangeCount = 0
        print("range count = ", self.rangeCount)
        # divide by COLS, use modulus to see if even..
        # change output color based on this number.
        if self.mosaicCols:
            if self.rangeCount % self.mosaicCols > 0:
                formattedText = f"<font color='red'>{self.rangeCount}</font> - not a fit!"
            else:
                formattedText = f"<font color='green'>{self.rangeCount}</font> - perfect."
            self.rangeCountLabelDisplay.setText(formattedText)
        else:
            self.rangeCountLabelDisplay.setText(str(self.rangeCount))

    def process_images(self):  # called by Process button
        print("PROCESSSING....")
        # ensure a filepath was selected and a filename was set
        if not (self.selectedfilename and self.savename):
            print("can't run processing routine. Start conditions failed (missing path or save name).")
            return 0

        # ensure start is less than end (consider reversing if desired)
        try:
            start_val = int(self.rangeStart)
            end_val = int(self.rangeEnd)
        except ValueError:
            print("Start/End must be integers.")
            return 0
        if not (start_val < end_val):
            print("Start must be less than End.")
            return 0

        imageroot = self.find_imageroot(self.imgpathDisplay.text())
        print("imageroot- ", imageroot)
        # return tuple : string (path), int (num of value chars), string (file extension)

        # create a list of file paths
        path_list = [self.construct_count_string(i, imageroot) for i in range(start_val, end_val + 1)]
        print("List of files:\n", path_list)

        # choose the optimized routine
        mosaic = self.routine_row_by_row_mosaic(path_list)

        savepath = os.path.join(self.foldername, f"{self.savename}.png")  # create full path for saving.
        print(savepath)
        if mosaic is None:
            print("No mosaic created (possibly no valid images found).")
            return 0
        cv2.imwrite(savepath, mosaic)
        print("COMPLETE!")
        return 1

    def routine_row_by_row_mosaic(self, path_list):
        """
        optimized routine, only loads into memory the minimum size canvas,
        plus 1 seq image at a time.
        Uses a couple sub functions to process the image creation.
        """

        def create_blank_row(height, width, cols):
            """
            create a numpy image equal to the height of sequence image,
            and width of seq images * cols (the full width of image being created)
            """
            blankrow = np.zeros((height, width * cols, 3), np.uint8)
            return blankrow

        def tile_in_images(mosaic, path_list, cols, row):
            """
            extend the current mosaic with a blank row (black),
            then tile in sequence images over the blank
            """
            imgnum = row * cols
            if imgnum >= len(path_list):
                return mosaic  # nothing to place for this row

            # Load first image in the row to determine w, h
            img = cv2.imread(path_list[imgnum], cv2.IMREAD_COLOR)
            if img is None:
                print(f"Failed to read image: {path_list[imgnum]}")
                return mosaic
            w, h = img.shape[1::-1]  # get image width and height

            if mosaic is None:
                mosaic = create_blank_row(h, w, cols)
            else:
                blank_row = create_blank_row(h, w, cols)
                mosaic = np.vstack((blank_row, mosaic))  # add a new row on top

            # place images across the new top row
            startpos = 0
            for c in range(cols):
                if imgnum < len(path_list):
                    img = cv2.imread(path_list[imgnum], cv2.IMREAD_COLOR)
                    if img is None:
                        print(f"Failed to read image: {path_list[imgnum]}")
                        break
                    mosaic[0:h, startpos:startpos + w] = img
                    startpos += w
                    imgnum += 1
            return mosaic

        num_of_images = len(path_list)
        cols = self.mosaicCols
        rows = (num_of_images + cols - 1) // cols  # integer ceiling

        mosaic = None  # initialize
        # process through the number of rows the final image will have
        for r in range(rows):
            mosaic = tile_in_images(mosaic, path_list, cols, r)
        return mosaic

    def routine_basic_mosaic(self, path_list):
        # create a list of images (memory-heavy for large sets)
        img_list = []
        for i in range(len(path_list)):
            image = cv2.imread(path_list[i])
            if image is None:
                print(f"Failed to read image: {path_list[i]}")
                continue
            img_list.append(image)
        if not img_list:
            return None
        mosaic = self.mosaic(self.mosaicCols, img_list)
        return mosaic

    def folderdialog(self):  # Used for SAVE Path
        foldername = QFileDialog.getExistingDirectory(self, "Open folder", "\\", options=QFileDialog.ShowDirsOnly)
        self.foldername = foldername
        self.savepathDisplay.setText(self.foldername)
        print(self.foldername)

    def filedialog(self):  # Used for OPEN Path
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "\\", "Image Files (*.png *.jpg *.bmp)")
        self.selectedfilename = filename or ""
        self.imgpathDisplay.setText(self.selectedfilename)
        print(self.selectedfilename)

        if self.selectedfilename:
            img = cv2.imread(self.selectedfilename)
            if img is not None:
                self.SEQimageHeight, self.SEQimageWidth, depth = img.shape
                self.WxHdisplay = f"{self.SEQimageWidth} x {self.SEQimageHeight}"
                self.WXH_LabelDisplay.setText(self.WxHdisplay)

    def construct_count_string(self, count, imageroot):
        insert_count = imageroot[1] - len(str(count))  # convert counter to string then get length
        value_chars = ("0" * insert_count) + str(count)
        new_path = imageroot[0] + value_chars + "." + imageroot[2]
        return new_path

    def find_imageroot(self, start_image):
        """
        return tuple : string (path, eg "C:\\images\\tileimage_"),
        int (num of value chars, eg: '001' = 3),
        string (file extension, eg: "png"),
        example based on full path= "C:\\images\\tileimage_001.png"
        """
        extension_delimiter = -4  # count to the '.' before file extension

        if not start_image:
            raise Exception("ERROR, no image path selected.")

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
            image_type = start_image[extension_delimiter + 1:]
            print("image type = ", image_type)
            if span_count == 0:
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

    def grouper(self, n, iterable, fillvalue=None):
        '''grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx'''
        args = [iter(iterable)] * n
        # Python 3: use zip_longest
        return it.zip_longest(fillvalue=fillvalue, *args)

    def mosaic(self, w, imgs):
        ''' Make a grid from images.
        w    -- number of grid columns
        imgs -- images (must have same size and format)
        '''
        if not imgs:
            return None
        h, w0 = imgs[0].shape[:2]
        n = len(imgs)
        r = (n + w - 1) // w  # rows
        # create a blank mosaic image (BGR)
        mosaic = np.zeros((h * r, w0 * w, 3), np.uint8)
        for idx, img in enumerate(imgs):
            if img is None:
                continue
            row = idx // w
            col = idx % w
            mosaic[row * h:(row + 1) * h, col * w0:(col + 1) * w0] = img
        return mosaic


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApplication()
    window.show()
    sys.exit(app.exec())