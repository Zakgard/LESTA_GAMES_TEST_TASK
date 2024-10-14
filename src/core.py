import traceback

from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QRect, QTimer, QSize
from PyQt5.QtGui import QPixmap, QPalette
from PyQt5.QtWidgets import QWidget, QLabel, QMainWindow, QScrollArea, QVBoxLayout, QSizePolicy

from constants import Sprite, GRID_SIZE

CELL_SIZE = 100
BORDER_SIZE = 50
TICK_TIME = 500


class ActionLog(QScrollArea):
	def __init__(self, *args, **kwargs):
		self.messages = []
		QScrollArea.__init__(self, *args, **kwargs)
		content = QWidget(self)
		self.setWidget(content)

		self.label = QLabel(content)
		self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
		self.label.setWordWrap(True)

		layout = QVBoxLayout(content)
		layout.addWidget(self.label)

		self.setWidgetResizable(True)
		self.setFocusPolicy(Qt.NoFocus)

	def addMessage(self, message):
		self.messages.append(message)
		self.label.setText('\n'.join(self.messages))


class Image(QLabel):
	def __init__(self, path):
		super().__init__()
		self.setPixmap(QPixmap(path))


	def setPosition(self, x: int, y: int) -> None:
		self.setGeometry(BORDER_SIZE + CELL_SIZE * int(x), BORDER_SIZE + CELL_SIZE * int(y), CELL_SIZE, CELL_SIZE)

	def remove(self) -> None:
		self.setParent(None)


class Marker(Image):
	def __init__(self, path):
		super().__init__(path)
		self.anim = QPropertyAnimation(self, b"pos")
		self.healthBar = QWidget(self)
		self.healthBar.setStyleSheet("background-color: white;")
		self.setHealth(1)
		self.selection = QLabel(self)
		self.selection.setPixmap(QPixmap(Sprite.SELECTION))
		self.setSelected(False)

	def moveTo(self, x: int, y: int) -> None:
		self.anim.setEndValue(QPoint(BORDER_SIZE + int(x) * CELL_SIZE, BORDER_SIZE + int(y) * CELL_SIZE))
		self.anim.setDuration(TICK_TIME)
		self.anim.start()

	def setHealth(self, part: float) -> None:
		self.healthBar.setGeometry(5, CELL_SIZE - 5, int((CELL_SIZE - 10) * part), 5)

	def setSelected(self, value: bool) -> None:
		if value:
			self.selection.show()
		else:
			self.selection.hide()


class GameAPI(QMainWindow):
	def __init__(self, game):
		super().__init__()
		self.game = game

		self.log = ActionLog(self)
		self.log.setGeometry(CELL_SIZE * GRID_SIZE + BORDER_SIZE * 2, 0, 400, CELL_SIZE * GRID_SIZE + BORDER_SIZE * 2)

		background = QLabel(self)
		background.setPixmap(QPixmap('assets/sea.png'))
		background.setGeometry(0, 0, CELL_SIZE * GRID_SIZE + BORDER_SIZE * 2, CELL_SIZE * GRID_SIZE + BORDER_SIZE * 2)

		gridContent = QWidget(self)
		gridContent.setGeometry(BORDER_SIZE, BORDER_SIZE, CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE)
		self.grid = QVBoxLayout(gridContent)
		self.grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
		self.setFocus()

		self.game.start(self)

	def mousePressEvent(self, event):
		x = (event.x() - BORDER_SIZE) // CELL_SIZE
		y = (event.y() - BORDER_SIZE) // CELL_SIZE
		if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
			try:
				self.game.click(self, x, y)
			except Exception as e:
				print('Exception while handling click at %s, %s: %s' % (event.x(), event.y(), e))
				traceback.print_exc()

	# API
	def addMessage(self, message: str) -> None :
		self.log.addMessage(message)

	def addImage(self, path: str, x: int, y: int) -> Image:
		assert isinstance(path, str), 'Wrong argument path on GameAPI.removeSprite(): %s' % path
		img = Image(path)
		img.setParent(self)
		img.setPosition(x, y)
		return img

	def addMarker(self, path: str, x: int, y: int) -> Marker:
		assert isinstance(path, str), 'Wrong argument path on GameAPI.removeSprite(): %s' % path
		img = Marker(path)
		img.setParent(self)
		img.setPosition(x, y)
		return img
