from Components.SystemInfo import SystemInfo
from Components.Console import Console
import os
#		#default layout for Mut@nt HD51	& Giga4K								for GigaBlue 4K
# STARTUP_1 			Image 1: boot emmcflash0.kernel1 'root=/dev/mmcblk0p3 rw rootwait'	boot emmcflash0.kernel1: 'root=/dev/mmcblk0p5 
# STARTUP_2 			Image 2: boot emmcflash0.kernel2 'root=/dev/mmcblk0p5 rw rootwait'      boot emmcflash0.kernel2: 'root=/dev/mmcblk0p7
# STARTUP_3		        Image 3: boot emmcflash0.kernel3 'root=/dev/mmcblk0p7 rw rootwait'	boot emmcflash0.kernel3: 'root=/dev/mmcblk0p9
# STARTUP_4		        Image 4: boot emmcflash0.kernel4 'root=/dev/mmcblk0p9 rw rootwait'	NOT IN USE due to Rescue mode in mmcblk0p3

def GetCurrentImage():
	if SystemInfo["canMultiBoot"]:
		slot = [x[-1] for x in open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read().split() if x.startswith('rootsubdir')]
		if slot:
			return int(slot[0])
		elif "%s" %(SystemInfo["canMultiBoot"][2]) in open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read():
			return (int(open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read()[:-1].split("%s" % SystemInfo["canMultiBoot"][2])[1].split(' ')[0])-SystemInfo["canMultiBoot"][0])/2
		else:
			return 0	# if media not in SystemInfo["canMultiBoot"], then using SDcard and Image is in eMMC (1st slot) so tell caller with 0 return
def GetCurrentImageMode():
	return SystemInfo["canMultiBoot"] and SystemInfo["canMode12"] and int(open('/sys/firmware/devicetree/base/chosen/bootargs', 'r').read().replace('\0', '').split('=')[-1])

class GetImagelist():
	MOUNT = 0
	UNMOUNT = 1
	NoRun = 0		# receivers only uses 1 media for multiboot
	FirstRun = 1		# receiver uses eMMC and SD card for multiboot - so handle SDcard slots 1st via SystemInfo(canMultiBoot)
	LastRun = 2		# receiver uses eMMC and SD card for multiboot - and then handle eMMC (currently one time)

	def __init__(self, callback):
		if SystemInfo["canMultiBoot"]:
			(self.firstslot, self.numberofslots) = SystemInfo["canMultiBoot"][:2]
			self.callback = callback
			self.imagelist = {}
			if not os.path.isdir('/tmp/testmount'):
				os.mkdir('/tmp/testmount')
			self.container = Console()
			self.slot = 1
			self.slot2 = 1
			if SystemInfo["HasHiSi"]:
				self.SDmmc = self.FirstRun	# process SDcard slots
			else:
				self.SDmmc = self.NoRun		# only mmc slots
			self.phase = self.MOUNT
			self.part = SystemInfo["canMultiBoot"][2]	# pick up slot type
			self.run()
		else:
			callback({})

	def run(self):
		if SystemInfo["HasRootSubdir"]:
			if self.slot == 1 and os.path.islink("/dev/block/by-name/linuxrootfs"):
				self.part2 = os.readlink("/dev/block/by-name/linuxrootfs")[5:]
				self.container.ePopen('mount /dev/block/by-name/linuxrootfs /tmp/testmount' if self.phase == self.MOUNT else 'umount /tmp/testmount', self.appClosed)
			else:
				self.part2 = os.readlink("/dev/block/by-name/userdata")[5:]
				self.container.ePopen('mount /dev/block/by-name/userdata /tmp/testmount' if self.phase == self.MOUNT else 'umount /tmp/testmount', self.appClosed)
			if self.phase == self.MOUNT:
				self.imagelist[self.slot2] = { 'imagename': _("Empty slot"), 'part': '%s' %self.part2 }
		else:
			if self.SDmmc == self.LastRun:
				self.part2 = getMachineMtdRoot()	# process mmc slot
				self.slot2 = 1
			else:
				self.part2 = "%s" %(self.part + str(self.slot * 2 + self.firstslot))
				if self.SDmmc == self.FirstRun:
					self.slot2 += 1			# allow for mmc slot"
			if self.phase == self.MOUNT:
				self.imagelist[self.slot2] = { 'imagename': _("Empty slot"), 'part': '%s' %self.part2 }
			self.container.ePopen('mount /dev/%s /tmp/testmount' %self.part2 if self.phase == self.MOUNT else 'umount /tmp/testmount', self.appClosed)

	def appClosed(self, data, retval, extra_args):
		if retval == 0 and self.phase == self.MOUNT:
			def getImagename(target):
				from datetime import datetime
				date = datetime.fromtimestamp(os.stat(os.path.join(target, "var/lib/opkg/status")).st_mtime).strftime('%Y-%m-%d')
				if date.startswith("1970"):
					try:
						date = datetime.fromtimestamp(os.stat(os.path.join(target, "usr/share/bootlogo.mvi")).st_mtime).strftime('%Y-%m-%d')
					except:
						pass
					date = max(date, datetime.fromtimestamp(os.stat(os.path.join(target, "usr/bin/enigma2")).st_mtime).strftime('%Y-%m-%d'))
				return "%s (%s)" % (open(os.path.join(target, "etc/issue")).readlines()[-2].capitalize().strip()[:-6], date)
			if SystemInfo["HasRootSubdir"]:
				if self.slot == 1 and os.path.isfile("/tmp/testmount/linuxrootfs1/usr/bin/enigma2"):
					self.OsPath = "/tmp/testmount/linuxrootfs1"
				elif os.path.isfile("/tmp/testmount/linuxrootfs%s/usr/bin/enigma2" % self.slot):
					self.OsPath = "/tmp/testmount/linuxrootfs%s" % self.slot
					print "multiboot tools 1 slots", self.slot, self.slot2
			else:
				if os.path.isfile("/tmp/testmount/usr/bin/enigma2"):
					self.OsPath = '/tmp/testmount'
					self.imagelist[self.slot2] = { 'imagename': getImagename("%s" %self.OsPath), 'part': '%s' %self.part2  }
			self.phase = self.UNMOUNT
			self.run()
		elif self.slot < self.numberofslots:
			self.slot += 1
			self.slot2 = self.slot
			self.phase = self.MOUNT
			self.run()
		elif self.SDmmc == self.FirstRun:
			self.phase = self.MOUNT
			self.SDmmc = self.LastRun	# processed SDcard now process mmc slot
			self.run()
		else:
			self.container.killAll()
			if not os.path.ismount('/tmp/testmount'):
				os.rmdir('/tmp/testmount')
			self.callback(self.imagelist)
