from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from itertools import cycle
class DrawableLabel(QLabel):
    lineDrawn = pyqtSignal(list)  # Signal to emit average RGB data

    def __init__(self, parent=None):
        super(DrawableLabel, self).__init__(parent)
        self.originalPixmap = QPixmap()
        self.setMouseTracking(True)
        self.drawing = False
        self.pathPoints = []
        self.lineColors = cycle([Qt.red, Qt.green, Qt.blue, Qt.yellow])  # Add more colors as needed
        self.currentLineColor = next(self.lineColors)  # Initialize current line color
  # To store the path points

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            # Adjust the point based on potential scaling
            self.lastPoint = self.adjustPointToPixmapScale(event.pos())
            self.pathPoints = [self.lastPoint]  # Start a new path

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drawing:
            self.pathPoints.append(self.adjustPointToPixmapScale(event.pos()))  # Append point to path
            self.update()  # Request a repaint if needed for visual feedback

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.pathPoints.append(self.adjustPointToPixmapScale(event.pos()))  # Finalize the path
            self.extractLineColorData()  # Perform color extraction based on the path

    def adjustPointToPixmapScale(self, point):
        # Calculate the scaling factors if the label and pixmap sizes differ
        scaleX = self.originalPixmap.size().width() / self.size().width()
        scaleY = self.originalPixmap.size().height() / self.size().height()
        # Adjust the point based on the scaling factors and convert to integer
        adjustedX = int(point.x() * scaleX)
        adjustedY = int(point.y() * scaleY)
        return QPoint(adjustedX, adjustedY)

    def extractLineColorData(self):
        if not self.pathPoints or self.originalPixmap.isNull():
            return

        qimage = self.originalPixmap.toImage()
        color_sum = [0, 0, 0]
        count = 0

        for i in range(1, len(self.pathPoints)):
            # Extract color data along the line segment
            startPoint = self.pathPoints[i - 1]
            endPoint = self.pathPoints[i]
            dx = abs(endPoint.x() - startPoint.x())
            dy = -abs(endPoint.y() - startPoint.y())
            sx = 1 if startPoint.x() < endPoint.x() else -1
            sy = 1 if startPoint.y() < endPoint.y() else -1
            err = dx + dy
            x0, y0 = startPoint.x(), startPoint.y()

            while True:
                if x0 >= 0 and y0 >= 0 and x0 < qimage.width() and y0 < qimage.height():
                    color = QColor(qimage.pixel(x0, y0))
                    color_sum[0] += color.red()
                    color_sum[1] += color.green()
                    color_sum[2] += color.blue()
                    count += 1

                if x0 == endPoint.x() and y0 == endPoint.y():
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    x0 += sx
                if e2 <= dx:
                    err += dx
                    y0 += sy

        if count > 0:
            avg_color = [sum // count for sum in color_sum]
        else:
            avg_color = [0, 0, 0]  # Default to black if no pixels were processed

        # Draw the line after color extraction to avoid affecting the pixel colors
        painter = QPainter(self.originalPixmap)
        painter.setPen(QPen(self.currentLineColor, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        for i in range(1, len(self.pathPoints)):
            painter.drawLine(self.pathPoints[i - 1], self.pathPoints[i])
        self.update()  # Update the pixmap with the drawn line

        # Emit the averaged color data
        self.lineDrawn.emit(avg_color)
        
        # Update the current line color for the next drawn line
        self.currentLineColor = next(self.lineColors)
    def setPixmap(self, pixmap):
        resizedPixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super().setPixmap(resizedPixmap)
        self.originalPixmap = resizedPixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.originalPixmap)
        # Optionally, draw the pathPoints as visual feedback during drawing
        
