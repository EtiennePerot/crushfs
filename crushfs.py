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
	def getCrushPath(self, extra=''):
		if extra:
			return self.getPath() + '.' + extra + '.crush.' + self.getExtensionLowercase()
		return self.getPath() + '.crush.' + self.getExtensionLowercase()
	def getArguments(self):
		return None
	def write(self, data, offset):
		self.hasBeenWritten = True
	def crushSub(self):
		return (subprocess.Popen(self.getArguments(), stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait(), self.getCrushPath())
	def crush(self, attempt=0):
		print('Crushing', self.getPath())
		if attempt > 5:
			try:
				os.remove(self.getCrushPath())
			except:
				pass
			return False
		result, bestFile = self.crushSub()
		if result:
			try:
				os.remove(self.getCrushPath())
			except:
				pass
			return self.crush(attempt + 1)
		os.remove(self.getPath())
		shutil.move(bestFile, self.getPath())
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

class PNGCrusher_pngcrush(Crusher):
	arguments = ['pngcrush', '-q', '-l', '9', '-reduce', '-rem', 'gAMA', '-rem', 'cHRM', '-rem', 'iCCP', '-rem', 'sRGB'] + [i for l in [('-m', str(i)) for i in range(138)] for i in l]
	def getArguments(self):
		return PNGCrusher_pngcrush.arguments + [self.getPath(), self.getCrushPath()]

class PNGCrusher_pngout(Crusher):
	arguments = ['pngout', '-y', '-r']
	lowerBlockSizes = [0, 192, 128, 64, 32]
	upperBlockSizes = [256, 512, 1024, 2048, 4096]
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.bestFile = None
	class PNGCrusher_pngout_thread(threading.Thread):
		def __init__(self, parent, filename, queue, *args, **kwargs):
			super().__init__(*args, **kwargs)
			self.result = None
			self.parent = parent
			self.filename = filename
			self.queue = queue[:]
			self.start()
		def getResult(self):
			return self.result
		def pngoutCrush(self, blockSize):
			return 
		def run(self):
			shutil.copyfile(self.parent.getPath(), self.filename)
			result = 0
			originalLength = len(self.queue)
			while len(self.queue):
				result = subprocess.Popen(PNGCrusher_pngout.arguments + ['-b' + str(self.queue.pop(0)), self.filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()
				if result:
					if len(self.queue) == originalLength - 1:
						self.result = result # Failrue at first try
					else:
						self.result = 0
					return
			self.result = 0
	def crushSub(self):
		lowPath = self.getCrushPath('low')
		lowThread = PNGCrusher_pngout.PNGCrusher_pngout_thread(self, lowPath, PNGCrusher_pngout.lowerBlockSizes)
		highPath = self.getCrushPath('high')
		highThread = PNGCrusher_pngout.PNGCrusher_pngout_thread(self, highPath, PNGCrusher_pngout.upperBlockSizes)
		self.bestFile = None
		lowThread.join()
		highThread.join()
		result = min(lowThread.getResult(), highThread.getResult())
		if result:
			try:
				os.remove(highPath)
			except:
				pass
			try:
				os.remove(lowPath)
			except:
				pass
			return (result, None)
		lowSize = os.path.getsize(lowPath)
		highSize = os.path.getsize(highPath)
		if lowSize < highSize:
			self.bestFile = lowPath
			os.remove(highPath)
		else:
			self.bestFile = highPath
			os.remove(lowPath)
		return (result, self.bestFile)

class JPEGCrusher(Crusher):
	arguments = ['jpegtran', '-optimize', '-copy', 'none', '-progressive', '-outfile']
	def getArguments(self):
		return JPEGCrusher.arguments + [self.getCrushPath(), self.getPath()]

def programExists(programName):
	try:
		result = subprocess.call(['which', programName], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		return result == 0
	except:
		return False

class crushfs(callbackfs.callbackfs):
	def __init__(self, *args, **kwargs):
		Crusher.enqueue = 'enqueue' in kwargs and kwargs['enqueue']
		if 'enqueue' in kwargs:
			del kwargs['enqueue']
		super().__init__(*args, **kwargs)
		if programExists('pngout'):
			self.addCallback(r'(?<!\.crush)\.png$', PNGCrusher_pngout)
		elif programExists('pngcrush'):
			self.addCallback(r'(?<!\.crush)\.png$', PNGCrusher_pngcrush)
		if programExists('jpegtran'):
			self.addCallback(r'(?<!\.crush)\.jpe?g$', JPEGCrusher)

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
