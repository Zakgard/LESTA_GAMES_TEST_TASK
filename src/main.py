import sys

from PyQt5.QtWidgets import QApplication

from core import GameAPI
from game import Game

if __name__ == '__main__':
	app = QApplication([])
	window = GameAPI(Game())
	window.resize(1200, 800)
	window.show()
	sys.exit(app.exec())
