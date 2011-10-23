#!/usr/bin/env python3

import os
import sys
import shutil
import threading
import subprocess
from fuse import FUSE
import callbackfs

class Crusher(callbackfs.callback):
	def getCrushPath(self):
		return self.getPath() + '.crush'
	def getArguments(self):
		return None
	def crush(self, attempt=0):
		if attempt > 5:
			try:
				os.remove(self.getCrushPath())
			except:
				pass
			return False
		p = subprocess.Popen(self.getArguments())
		result = p.wait()
		if result:
			try:
				os.remove(self.getCrushPath())
			except:
				pass
			return self.crush(attempt + 1)
		os.remove(self.getPath())
		shutil.move(self.getCrushPath(), self.getPath())
		return True
	def close(self):
		threading.Thread(target=self.crush).start()
		return None

class PNGCrusher(Crusher):
	arguments = ['pngcrush', '-q', '-l', '9', '-reduce', '-rem', 'gAMA', '-rem', 'cHRM', '-rem', 'iCCP', '-rem', 'sRGB'] + [i for l in [('-m', str(i)) for i in range(138)] for i in l]
	def getArguments(self):
		return PNGCrusher.arguments + [self.getPath(), self.getCrushPath()]

class JPEGCrusher(Crusher):
	arguments = ['jpegtran', '-optimize', '-copy', 'none', '-progressive', '-outfile']
	def getArguments(self):
		return JPEGCrusher.arguments + [self.getCrushPath(), self.getPath()]

class crushfs(callbackfs.callbackfs):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.addCallback(r'\.png$', PNGCrusher)
		self.addCallback(r'\.jpe?g$', JPEGCrusher)

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('usage: %s <backing directory> <mountpoint>' % sys.argv[0])
		sys.exit(1)
	FUSE(crushfs(sys.argv[1]), sys.argv[2], foreground=True)
