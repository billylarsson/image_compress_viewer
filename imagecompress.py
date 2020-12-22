from PIL              import  Image
from PyQt5            import  QtCore, QtWidgets
from PyQt5.QtGui      import  QKeySequence, QPixmap
from PyQt5.QtWidgets  import  QShortcut
from collections      import  deque
from functools        import  partial
import os
import sys
import tempfile

offset = 1
slices = 7

slice_path = f'{tempfile.gettempdir()}/longsnabel_use_alot_file.jpg.webp'

class SlicePart(QtWidgets.QLabel):
    def __init__(self, place, **kwargs):
        super(SlicePart, self).__init__(place)
        self.setStyleSheet('background-color: rgba(5,5,5,100); color: white')
        self.setLineWidth(0)
        self.pixmap = QPixmap(kwargs['path'])
        self.setPixmap(self.pixmap)
        height_taken = place.height() - 120
        self.label_one = QtWidgets.QLabel(
            self,
            styleSheet = 'font: 18pt',
            alignment  = QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter,
            text       = f'{kwargs["type"]}'
        )
        self.label_one.move(offset, height_taken)
        height_taken += self.label_one.height() + offset

        self.label_two = QtWidgets.QLabel(
            self,
            styleSheet ='font: 14pt',
            alignment  = QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter,
            text       = f'{kwargs["quality"]}'
        )
        self.label_two.move(offset, height_taken)
        height_taken += self.label_one.height()

        self.label_two = QtWidgets.QLabel(
            self,
            styleSheet ='font: 14pt',
            alignment  = QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter,
            text       = f'{kwargs["save"]} {kwargs["percent"]}%'
        )
        self.label_two.move(offset, height_taken)
        self.show()

class QualitySlicer(QtWidgets.QFrame):
    def __init__(self):
        super(QualitySlicer, self).__init__()
        self.width_taken = 0
        self.setStyleSheet('background-color: rgba(10,10,10,200) ; color: aliceblue')
        self.setLineWidth(0)
        self.resize(1920, 1080)
        self.button = QtWidgets.QPushButton(self, text='GO!')
        self.button.clicked.connect(self.load_file)
        self.button.setGeometry(0, 0, 70, 30)
        self.width_taken += self.button.width()
        self.chk_jpeg = QtWidgets.QRadioButton(self, text="JPEG")
        self.chk_jpeg.setGeometry(self.width_taken, 0, self.button.width(), self.button.height())
        self.width_taken += self.chk_jpeg.width()
        self.chk_webp = QtWidgets.QRadioButton(self, text="WEBP")
        self.chk_webp.setGeometry(self.width_taken, 0, self.button.width(), self.button.height())
        self.width_taken += self.chk_webp.width()
        self.chk_webp.setChecked(True)
        self.fileinput = QtWidgets.QPlainTextEdit(self)
        self.fileinput.setGeometry(self.width_taken,0,self.width() - self.width_taken, 30)
        self.fileinput.setAcceptDrops(True)
        self.backplate = QtWidgets.QFrame(self)
        self.backplate.setLineWidth(0)
        self.backplate.setGeometry(0,self.fileinput.height(),self.width(), self.height())
        self.fileinput.textChanged.connect(self.load_file)
        self.page_turn_shortcut_left = QShortcut(QKeySequence('left'), self)
        self.page_turn_shortcut_left.activated.connect(partial(self.redraw, 'plus'))
        self.page_turn_shortcut_right = QShortcut(QKeySequence("right"), self)
        self.page_turn_shortcut_right.activated.connect(partial(self.redraw, 'minus'))
        self.slice_list = []
        self.cycle = 0
        self.load_file()
        self.show()

    def redraw(self, boost):
        if boost == 'plus':
            if self.cycle < slices:
                self.cycle += 1
                self.load_file()
        else:
            if self.cycle > 0:
                self.cycle -= 1
                self.load_file()

    def load_file(self):
        image_path = self.fileinput.toPlainText()
        image_path = image_path.replace('file://', '')
        image_path = image_path.strip()

        if os.path.exists(image_path) == False or os.path.isfile(image_path) == False:
            return

        width_taken = 0
        for i in self.slice_list:
            i.close()
        pixmap = QPixmap(image_path).scaledToHeight(self.backplate.height())
        if pixmap.width() > self.backplate.width():
            pixmap = QPixmap.scaledToWidth(self.backplate.width())
        im = Image.open(image_path)
        self.setWindowTitle(f'Original filesize: {round(os.path.getsize(image_path)/1000)}kb resolution: {im.size[0]} x {im.size[1]}')
        im.thumbnail((pixmap.width(), pixmap.height()), Image.ANTIALIAS)
        self.quality_list = [x for x in range(1, slices+1)]
        self.quality_list = deque(self.quality_list)
        self.quality_list.rotate(self.cycle)
        for count in range(slices):
            if self.chk_webp.isChecked() == True:
                format = 'webp'
            else:
                format = 'jpeg'
            method = 6
            quality = self.quality_list[count] * 10
            width, height = im.size

            left = count * (width / slices)
            top = 0
            right = (count+1) * (width / slices)
            bottom = height

            croped_image = im.crop((left, top, right, bottom))
            croped_image.save(slice_path)
            pre_size = os.path.getsize(slice_path)
            croped_image.save(slice_path, format, quality=quality, method=method, optimized=True)
            post_size = os.path.getsize(slice_path)

            if (100 - (post_size / pre_size)*100) > 0:
                save = 'SAVE'
            else:
                save = 'LOSE'

            if format == 'webp':
                quality = f'Quality: {quality} Method: {method}'
            else:
                quality = f'Quality: {quality}'

            label = SlicePart(
                self.backplate,
                path      = slice_path,
                type      = f'Format: {format.upper()}',
                quality   = quality,
                pre_size  = pre_size,
                post_size = post_size,
                percent   = round(100 - (post_size / pre_size)*100),
                save      = save,
                method    = method,
            )
            self.slice_list.append(label)

            label.move(width_taken + (offset * count), 0)
            width_taken += label.pixmap.width() + offset

        self.resize(width_taken + offset, self.height())
        self.fileinput.setGeometry(self.width_taken, 0, self.width() - self.width_taken, 30)


app = QtWidgets.QApplication(sys.argv)
window = QualitySlicer()
app.exec_()