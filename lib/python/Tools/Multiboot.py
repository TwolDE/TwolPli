from Components.SystemInfo import SystemInfo
from Components.Console import Console
import os

def GetCurrentImage():
	if SystemInfo["canMultiBootHD"]:
		return	int(open('/sys/firmware/devicetree/base/chosen/kerneldev', 'r').read().replace('\0', '')[-1])
	elif SystemInfo["canMultiBootGB"]:
		x = open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read().replace('\0', '').split('=')[1]
		x = x.split('p')[1]
		f = int(x.split(' ')[0])
		return (f-3)/2
	else:
		return	0

def GetCurrentImageMode():
	return SystemInfo["canMultiBootHD"] and int(open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read().replace('\0', '').split('=')[-1])

#		#default layout for Mut@nt HD51	& Giga4K								for GigaBlue 4K
# STARTUP_1 			Image 1: boot emmcflash0.kernel1 'root=/dev/mmcblk0p3 rw rootwait'	boot emmcflash0.kernel1: 'root=/dev/mmcblk0p5 
# STARTUP_2 			Image 2: boot emmcflash0.kernel2 'root=/dev/mmcblk0p5 rw rootwait'      boot emmcflash0.kernel2: 'root=/dev/mmcblk0p7
# STARTUP_3		        Image 3: boot emmcflash0.kernel3 'root=/dev/mmcblk0p7 rw rootwait'	boot emmcflash0.kernel3: 'root=/dev/mmcblk0p9
# STARTUP_4		        Image 4: boot emmcflash0.kernel4 'root=/dev/mmcblk0p9 rw rootwait'	NOT IN USE due to Rescue mode in mmcblk0p3

class GetImagelist():
	MOUNT = 0
	UNMOUNT = 1

	def __init__(self, callback):
		if SystemInfo["canMultiBoot"]:
			if SystemInfo["canMultiBootHD"]:
				self.addin = 1
				self.endslot = 4
			if SystemInfo["canMultiBootGB"]:
				self.addin = 3
				self.endslot = 3
			self.callback = callback
			self.imagelist = {}
			if not os.path.isdir('/tmp/testmount'):
				os.mkdir('/tmp/testmount')
			self.container = Console()
			self.slot = 1
			self.phase = self.MOUNT
			self.run()
		else:	
			callback({})
	
	def run(self):
		self.container.ePopen('mount /dev/mmcblk0p%s /tmp/testmount' % str(self.slot * 2 + self.addin) if self.phase == self.MOUNT else 'umount /tmp/testmount', self.appClosed)
			
	def appClosed(self, data, retval, extra_args):
		SlotEmpty = "EmptySlot"
		if retval == 0 and self.phase == self.MOUNT:
			BuildVersion = "  "
			Build = " "
			Version = " "
			if os.path.isfile("/tmp/testmount/usr/bin/enigma2") and os.path.isfile('/tmp/testmount/etc/image-version'):
				file = open('/tmp/testmount/etc/image-version', 'r')
				lines = file.read().splitlines()
				for x in lines:
					splitted = x.split('= ')
					if len(splitted) > 1:
						if splitted[0].startswith("Version"):
							Version = splitted[1].split(' ')[0]
						elif splitted[0].startswith("Build"):
							Build = splitted[1].split(' ')[0]
				file.close()
				BuildVersion = " " + Build
			if os.path.isfile("/tmp/testmount/usr/bin/enigma2"):
				self.imagelist[self.slot] =  { 'imagename': open("/tmp/testmount/etc/issue").readlines()[-2].capitalize().strip()[:-6] + BuildVersion}
			else:
				self.imagelist[self.slot] =  { 'imagename': SlotEmpty}
			self.phase = self.UNMOUNT
			self.run()
		elif self.slot < self.endslot:
			self.slot += 1
			self.imagelist[self.slot] =  { 'imagename': SlotEmpty}
			self.phase = self.MOUNT
			self.run()
		else:
			self.container.killAll()
			if not os.path.ismount('/tmp/testmount'):
				os.rmdir('/tmp/testmount')
			self.callback(self.imagelist)
