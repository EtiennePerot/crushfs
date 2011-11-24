import os, sys
import subprocess
from callbackfs import CallbackSystem
from crushfs import PNGCrusher_pngcrush, PNGCrusher_pngout, JPEGCrusher, programExists

if len(sys.argv) < 2:
	print('Usage:', sys.argv[0], 'directory_1', 'directory_2', '...', 'directory_n')
	sys.exit(1)

rootDirs = sys.argv[1:]
for d in rootDirs:
	if not os.path.isdir(d):
		print(d, 'does not exist or is not a directory.')
		sys.exit(1)

callbackSys = CallbackSystem()
if programExists('pngout'):
	callbackSys.addCallback(r'(?<!\.crush)\.png$', PNGCrusher_pngout)
elif programExists('pngcrush'):
	callbackSys.addCallback(r'(?<!\.crush)\.png$', PNGCrusher_pngcrush)
if programExists('jpegtran'):
	callbackSys.addCallback(r'(?<!\.crush)\.jpe?g$', JPEGCrusher)

for d in rootDirs:
	for root, dirs, files in os.walk(d):
		for f in files:
			callback = callbackSys.getCallback(os.path.join(root, f))
			if callback:
				callback.crush()
