from PyQt5 import QtCore

class Test(QtCore.QObject):
	sig1 = QtCore.pyqtSignal(int)
	sig2 = QtCore.pyqtSignal(int)

	def __init__(self):
		super().__init__()
		self.a = 1

	def emitSig1(self):
		self.sig1.emit(4)

	def emitSig2(self):
		self.sig2.emit()

# def _sig1(val):
	# print("Got signal 1.")

def success(val):
	print("Success! Got signal 2 with value {}.".format(val))

print("starting")
t = Test()
t.sig1.connect(t.sig2)
t.sig2.connect(success)
t.emitSig1()