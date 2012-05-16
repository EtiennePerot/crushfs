#!/usr/bin/env python3

import os, sys
import subprocess
from callbackfs import CallbackSystem
from crushfs import PNGCrusher_pngcrush, PNGCrusher_pngout, PNGCrusher_pngout_pngcrush, JPEGCrusher, programExists

if len(sys.argv) < 2:
	print('Usage:', sys.argv[0], 'file_or_directory_1', 'file_or_directory_2', '...', 'file_or_directory_n')
	sys.exit(1)

paths = sys.argv[1:]
for d in paths:
	if not os.path.exists(d):
		print(d, 'does not exist.')
		sys.exit(1)

callbackSys = CallbackSystem()
enabled = False
if programExists('pngout') and programExists('pngcrush'):
	callbackSys.addCallback(r'(?<!\.crush)\.png$', PNGCrusher_pngout_pngcrush)
	enabled = True
elif programExists('pngout'):
	callbackSys.addCallback(r'(?<!\.crush)\.png$', PNGCrusher_pngout)
	enabled = True
elif programExists('pngcrush'):
	callbackSys.addCallback(r'(?<!\.crush)\.png$', PNGCrusher_pngcrush)
	enabled = True
if programExists('jpegtran'):
	callbackSys.addCallback(r'(?<!\.crush)\.jpe?g$', JPEGCrusher)
	enabled = True

if not enabled:
	print('No image compression programs have been found in your PATH environment variable.')
	sys.exit(1)

for p in paths:
	if os.path.isfile(p):
		callback = callbackSys.getCallback(p)
		if callback:
			callback.crush()
	elif os.path.isdir(p):
		for root, dirs, files in os.walk(p):
			for f in files:
				callback = callbackSys.getCallback(os.path.join(root, f))
				if callback:
					callback.crush()
