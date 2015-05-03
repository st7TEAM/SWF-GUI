import os
from Renderer import Renderer
from enigma import ePixmap
from Tools.Alternatives import GetWithAlternative
from Tools.Directories import pathExists, SCOPE_ACTIVE_SKIN, resolveFilename
from Components.Harddisk import harddiskmanager
from PIL import Image
from enigma import getBoxType

searchPaths = []
lastLcdPiconPath = None

def initLcdPiconPaths():
	global searchPaths
	searchPaths = []
	for mp in ('/usr/share/enigma2/', '/'):
		onMountpointAdded(mp)
	for part in harddiskmanager.getMountedPartitions():
		onMountpointAdded(part.mountpoint)

def onMountpointAdded(mountpoint):
	global searchPaths
	try:
		if getBoxType() == 'vuultimo':
			path = os.path.join(mountpoint, 'lcd_picon') + '/'
		else:
			path = os.path.join(mountpoint, 'picon') + '/'
		if os.path.isdir(path) and path not in searchPaths:
			for fn in os.listdir(path):
				if fn.endswith('.png'):
					print "[LcdPicon] adding path:", path
					searchPaths.append(path)
					break
	except Exception, ex:
		print "[LcdPicon] Failed to investigate %s:" % mountpoint, ex

def onMountpointRemoved(mountpoint):
	global searchPaths
	if getBoxType() == 'vuultimo':
		path = os.path.join(mountpoint, 'lcd_picon') + '/'
	else:
		path = os.path.join(mountpoint, 'picon') + '/'
	try:
		searchPaths.remove(path)
		print "[LcdPicon] removed path:", path
	except:
		pass

def onPartitionChange(why, part):
	if why == 'add':
		onMountpointAdded(part.mountpoint)
	elif why == 'remove':
		onMountpointRemoved(part.mountpoint)

def findLcdPicon(serviceName):
	global lastLcdPiconPath
	if lastLcdPiconPath is not None:
		pngname = lastLcdPiconPath + serviceName + ".png"
		if pathExists(pngname):
			return pngname
		else:
			return ""
	else:
		global searchPaths
		pngname = ""
		for path in searchPaths:
			if pathExists(path) and not path.startswith('/media/net'):
				pngname = path + serviceName + ".png"
				if pathExists(pngname):
					lastLcdPiconPath = path
					break
			elif pathExists(path):
				pngname = path + serviceName + ".png"
				if pathExists(pngname):
					lastLcdPiconPath = path
					break
		if pathExists(pngname):
			return pngname
		else:
			return ""

def getLcdPiconName(serviceName):
	#remove the path and name fields, and replace ':' by '_'
	sname = '_'.join(GetWithAlternative(serviceName).split(':', 10)[:10])
	pngname = findLcdPicon(sname)
	if not pngname:
		fields = sname.split('_', 3)
		if len(fields) > 2 and fields[2] != '2':
			#fallback to 1 for tv services with nonstandard servicetypes
			fields[2] = '1'
			pngname = findLcdPicon('_'.join(fields))
	return pngname

def resizePicon(pngname, size):
	try:
		im = Image.open(pngname)
		im.resize((size[0],size[1])).save("/tmp/picon.png")
		pngname = "/tmp/picon.png"
	except:
		print"[PiconRes] error resizePicon"
		pass
	return pngname

class LcdPicon(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.piconsize = (0,0)
		self.pngname = ""
		self.lastPath = None
		if getBoxType() == 'vuultimo':
			pngname = findLcdPicon("lcd_picon_default")
		else:
			pngname = findLcdPicon("picon_default")
		self.defaultpngname = None
		if not pngname:
			if getBoxType() == 'vuultimo':
				tmp = resolveFilename(SCOPE_ACTIVE_SKIN, "lcd_picon_default.png")
			else:
				tmp = resolveFilename(SCOPE_ACTIVE_SKIN, "picon_default.png")
			if pathExists(tmp):
				pngname = tmp
			else:
				if getBoxType() == 'vuultimo':
					pngname = resolveFilename(SCOPE_ACTIVE_SKIN, "lcd_picon_default.png")
				else:
					pngname = resolveFilename(SCOPE_ACTIVE_SKIN, "picon_default.png")
		if os.path.getsize(pngname):
			self.defaultpngname = pngname

	def addPath(self, value):
		if pathExists(value):
			global searchPaths
			if not value.endswith('/'):
				value += '/'
			if value not in searchPaths:
				searchPaths.append(value)

	def applySkin(self, desktop, parent):
		attribs = self.skinAttributes[:]
		for (attrib, value) in self.skinAttributes:
			if attrib == "path":
				self.addPath(value)
				attribs.remove((attrib,value))
			elif attrib == "size":
				self.piconsize = value
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		if self.instance:
			pngname = ""
			if what[0] != self.CHANGED_CLEAR:
				pngname = getLcdPiconName(self.source.text)
			if not pngname: # no picon for service found
				pngname = self.defaultpngname
			if self.pngname != pngname:
				if pngname:
					self.instance.setScale(1)
					self.instance.setPixmapFromFile(resizePicon(pngname, self.piconsize))
					self.instance.show()
				else:
					self.instance.hide()
				self.pngname = pngname

harddiskmanager.on_partition_list_change.append(onPartitionChange)
initLcdPiconPaths()
