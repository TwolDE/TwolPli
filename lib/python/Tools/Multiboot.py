from Components.SystemInfo import SystemInfo
from Components.Console import Console
import os

def GetCurrentImage():
	if SystemInfo["canMultiBoot"]:
		if not SystemInfo["canMode12"]:
			return (int(open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read().replace('\0', '').split('=')[1].split('p')[1].split(' ')[0])-3)/2
		else:
			return	int(open('/sys/firmware/devicetree/base/chosen/kerneldev', 'r').read().replace('\0', '')[-1])

def GetCurrentImageMode():
	if SystemInfo["canMultiBoot"] and SystemInfo["canMode12"]: 
		return	int(open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read().replace('\0', '').split('=')[-1])

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
			self.addin = SystemInfo["canMultiBoot"][0]
			self.endslot = SystemInfo["canMultiBoot"][1]
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
				self.imagelist[self.slot] = { 'imagename': _("Empty slot")}
			self.phase = self.UNMOUNT
			self.run()
		elif self.slot < self.endslot:
			self.slot += 1
			self.imagelist[self.slot] = { 'imagename': _("Empty slot")}
			self.phase = self.MOUNT
			self.run()
		else:
			self.container.killAll()
			if not os.path.ismount('/tmp/testmount'):
				os.rmdir('/tmp/testmount')
			self.callback(self.imagelist)

class GetSTARTUP():
	MOUNT = 0
	UNMOUNT = 1

	def __init__(self, callback):
		if SystemInfo["canMultiBoot"]:
			self.addin = SystemInfo["canMultiBoot"][0]
			self.endslot = SystemInfo["canMultiBoot"][1]
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
		volume = SystemInfo["canMultiBoot"][2]
		self.container.ePopen('mount /dev/%s /tmp/testmount' %volume if self.phase == self.MOUNT else 'umount /tmp/testmount', self.appClosed)
			
	def appClosed(self, data, retval, extra_args):
		if retval == 0 and self.phase == self.MOUNT:
			for x in range(1, self.endslot + 1):
				if os.path.isfile("/tmp/testmount/STARTUP_%s" % self.slot):
					self.imagelist[self.slot] =  { 'STARTUP': open('/tmp/testmount/STARTUP_%s'% self.slot).read()}
					self.slot += 1
			if os.path.isfile("/tmp/testmount/STARTUP"):
				self.imagelist[self.endslot +1] =  { 'STARTUP': open('/tmp/testmount/STARTUP').read()}
			self.phase = self.UNMOUNT
			self.run()
		else:
			self.container.killAll()
			if not os.path.ismount('/tmp/testmount'):
				os.rmdir('/tmp/testmount')
			self.callback(self.imagelist)

class WriteStartup():
	MOUNT = 0
	UNMOUNT = 1

	def __init__(self, Contents, callback):
		if SystemInfo["canMultiBoot"]:
			if not os.path.isdir('/tmp/testmount'):
				os.mkdir('/tmp/testmount')
			self.callback = callback
			self.container = Console()
			self.phase = self.MOUNT
			if not SystemInfo["canMode12"]:
				self.slot = Contents
			else:
				self.contents = Contents			
			self.run()
		else:	
			callback({})
	
	def run(self):
		volume = SystemInfo["canMultiBoot"][2]
		self.container.ePopen('mount /dev/%s /tmp/testmount' %volume if self.phase == self.MOUNT else 'umount /tmp/testmount', self.appClosed)
#	If GigaBlue then Contents = slot, use slot to read STARTUP_slot
#	If multimode and bootmode 1 or 12, then Contents is STARTUP file, so just write it to STARTUP.			
	def appClosed(self, data, retval, extra_args):
		if retval == 0 and self.phase == self.MOUNT:
			if os.path.isfile("/tmp/testmount/STARTUP"):
				if 'coherent_poll=2M' in open("/proc/cmdline", "r").read():
					self.contents = open('/tmp/testmount/STARTUP_%s'% self.slot).read()
				open('/tmp/testmount/STARTUP', 'w').write(self.contents)
			self.phase = self.UNMOUNT
			self.run()
		else:
			self.container.killAll()
			if not os.path.ismount('/tmp/testmount'):
				os.rmdir('/tmp/testmount')
			self.callback()
