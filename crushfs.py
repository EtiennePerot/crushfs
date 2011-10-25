#!/usr/bin/env python3

import os
import sys
import shutil
import threading
import subprocess
from fuse import FUSE
import callbackfs

class Crusher(callbackfs.callback):
	enqueue = False
	crushingProcess = threading.RLock()
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.hasBeenWritten = False
	def getCrushPath(self):
		return self.getPath() + '.crush'
	def getArguments(self):
		return None
	def write(self, path, data, offset, fh):
		self.hasBeenWritten = True
	def crush(self, attempt=0):
		print('Crushing', self.getPath())
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
		print('Successful crush of', self.getPath())
		return True
	def close(self):
		if not self.hasBeenWritten:
			self.clear()
			return
		thr = threading.Thread(target=self.crush)
		if Crusher.enqueue:
			Crusher.crushingProcess.acquire()
			try:
				thr.run()
			except:
				print('Error while crushing', self.getPath())
			Crusher.crushingProcess.release()
		else:
			thr.start()
		self.hasBeenWritten = False
		self.clear()
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
		Crusher.enqueue = 'enqueue' in kwargs and kwargs['enqueue']
		if 'enqueue' in kwargs:
			del kwargs['enqueue']
		super().__init__(*args, **kwargs)
		self.addCallback(r'\.png$', PNGCrusher)
		self.addCallback(r'\.jpe?g$', JPEGCrusher)

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('usage: %s [--enqueue] <backing directory> <mountpoint>' % sys.argv[0])
		sys.exit(1)
	enqueue = '--enqueue' in sys.argv
	if enqueue:
		sys.argv.remove('--enqueue')
	kwargs = {}
	allow_other = '--allow_other' in sys.argv
	if allow_other:
		sys.argv.remove('--allow_other')
		kwargs['allow_other'] = True
	FUSE(crushfs(sys.argv[1], enqueue=enqueue), sys.argv[2], foreground=True, **kwargs)
