#!/usr/bin/env python3

import os
import re
import loopbackfs

class callback:
	fileHandle = 1337
	def getFileHandle():
		callback.fileHandle += 1
		return callback.fileHandle
	def __init__(self, callbackSystem, path):
		self.callbackSystem = callbackSystem
		self.path = path
		self.dirname = os.path.dirname(path)
		if self.dirname[-1] != os.sep:
			self.dirname += os.sep
	def getPath(self):
		return self.path
	def getExtension(self):
		name = os.path.basename(self.path)
		index = name.find('.')
		if index == -1:
			return None
		return name[index + 1:]
	def getExtensionLowercase(self):
		ext = self.getExtension()
		if ext is not None:
			ext = ext.lower()
		return ext
	def getDirname(self):
		return self.dirname
	def clear(self):
		self.callbackSystem.clearCallback(self.path)
	def create(self):
		return None
	def open(self):
		return None
	def read(self, size, offset=0):
		return None
	def truncate(self, size):
		return None
	def close(self):
		return None
	def delete(self):
		return None
	def write(self, data, offset):
		return None

class CallbackSystem:
	def __init__(self):
		self.callbacks = {}
		self.compiledRegexes = {}
		self.definedCallbacks = {}
	def addCallback(self, regex, callbackClass, regexFlags=re.IGNORECASE):
		self.compiledRegexes[regex] = re.compile(regex, regexFlags)
		self.callbacks[regex] = callbackClass
	def getCallback(self, path):
		if path in self.definedCallbacks:
			return self.definedCallbacks[path]
		for r in self.callbacks:
			if self.compiledRegexes[r].search(path):
				callback = self.callbacks[r](self, path)
				self.definedCallbacks[path] = callback
				return callback
		return None
	def clearCallback(self, path):
		if path in self.definedCallbacks:
			del self.definedCallbacks[path]

class callbackfs(loopbackfs.Loopback, CallbackSystem):
	def __init__(self, *args, **kwargs):
		CallbackSystem.__init__(self)
		loopbackfs.Loopback.__init__(self, *args, **kwargs)
	def getCallback(self, path):
		if os.path.exists(os.path.join(self.root, path)):
			return None
		return super.getCallback(self, path)
	def create(self, path, mode):
		callback = self.getCallback(path)
		if callback:
			result = callback.create()
			if result is not None:
				return result
		return super().create(path, mode)
	def open(self, path, flags, mode=None):
		callback = self.getCallback(path)
		if callback:
			result = callback.open()
			if result is not None:
				return result
		if mode is None:
			return super().open(path, flags)
		return super().open(path, flags, mode)
	def read(self, path, size, offset, fh):
		callback = self.getCallback(path)
		if callback:
			result = callback.read(size, offset)
			if result is not None:
				return result
		return super().read(path, size, offset, fh)
	def readdir(self, path, fh):
		allFiles = super().readdir(path, fh)
		for p in self.definedCallbacks.values():
			plainpath = loopbackfs.getPlainPath(self, p.getPath())
			if p.getDirname() == path and plainpath not in allFiles:
				allFiles.append(plainpath)
		return allFiles
	def truncate(self, path, length, fh=None):
		callback = self.getCallback(path)
		if callback:
			result = callback.truncate(length)
			if result is not None:
				return result
		return super().truncate(path, length, fh)
	def release(self, path, fh):
		callback = self.getCallback(path)
		if callback:
			result = callback.close()
			if result is not None:
				return result
		return super().release(path, fh)
	def unlink(self, path):
		callback = self.getCallback(path)
		if callback:
			result = callback.delete()
			if result is not None:
				return result
		return super().unlink(path)
	def write(self, path, data, offset, fh):
		callback = self.getCallback(path)
		if callback:
			result = callback.write(data, offset)
			if result is not None:
				return result
		return super().write(path, data, offset, fh)
