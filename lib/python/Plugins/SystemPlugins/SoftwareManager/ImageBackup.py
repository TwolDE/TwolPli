#################################################################################
# FULL BACKUP UYILITY FOR ENIGMA2, SUPPORTS THE MODELS OE-A 4.1     			#
#	                         						                            #
#					MAKES A FULLBACK-UP READY FOR FLASHING.						#
#																				#
#################################################################################
from enigma import getEnigmaVersionString
from Screens.Screen import Screen
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import SystemInfo
from Components.Label import Label
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.About import about
from Components import Harddisk
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from time import time, strftime, localtime
from Tools.Directories import fileExists, fileCheck
from Tools.Multiboot import GetImagelist, GetCurrentImage, GetCurrentImageMode
from Tools.HardwareInfo import HardwareInfo
from os import path, system, makedirs, listdir, walk, statvfs, remove
import commands
import datetime


VERSION = "Version 6.2 OpenPli"

def Freespace(dev):
	statdev = statvfs(dev)
	space = (statdev.f_bavail * statdev.f_frsize) / 1024
	print "[FULL BACKUP] Free space on %s = %i kilobytes" %(dev, space)
	return space

class ImageBackup(Screen):
	skin = """
	<screen position="center,center" size="560,400" title="Image Backup">
		<ePixmap position="0,360"   zPosition="1" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,360" zPosition="1" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,360" zPosition="1" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,360" zPosition="1" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="info-hdd" position="10,30" zPosition="1" size="450,100" font="Regular;20" halign="left" valign="top" transparent="1" />
		<widget name="info-multi" position="10,80" zPosition="1" size="450,100" font="Regular;20" halign="left" valign="top" transparent="1" />
		<widget name="info-usb" position="10,150" zPosition="1" size="450,200" font="Regular;20" halign="left" valign="top" transparent="1" />
	</screen>"""

	def __init__(self, session, args = 0):
		Screen.__init__(self, session)
		self.session = session
		self.Recov = False
		self.selection = 0
		self.kernel = 1
		self.gigaboot = "/media/mmcblk0p1/STARTUP"
		self.getImageList = None
		self.imagelist = {}
		self.MODEL = HardwareInfo().get_device_model()
		self.MACHINEBUILD = HardwareInfo().get_device_model()
		self.MTDBOOT = "none"
		self.EMMCIMG = "none"
		if SystemInfo["canMultiBootHD"]:
			self.MTDBOOT = "mmcblk0p1"
			self.EMMCIMG = "disk.img"
			self.ROOTFSTYPE = 'hd-emmc'
			self.ROOTFSBIN = "rootfs.tar.bz2"
			self.KERNELBIN = "kernel.bin"
			self.kernel = GetCurrentImage()
			self.current_MTDKERNEL = "mmcblk0p%s" %(self.kernel*2)
			self.current_MTDROOTFS = "mmcblk0p%s" %(self.kernel*2 +1)
		elif SystemInfo["canMultiBootGB"]:
			if path.exists("/media/mmcblk0p1/STARTUP"):
				f = open("/media/mmcblk0p1/STARTUP", 'r')
				f.seek(22)
				self.kernel = int(f.read(1)) 
				f.close() 
			self.MTDBOOT = "mmcblk0p1"
			self.ROOTFSTYPE = 'tar.bz2'
			self.ROOTFSBIN = "rootfs.tar.bz2"
			self.KERNELBIN = "kernel.bin"
			self.current_MTDKERNEL = "mmcblk0p%s" %(self.kernel*2 +2)
			self.current_MTDROOTFS = "mmcblk0p%s" %(self.kernel*2 +3)
		print "[FULL BACKUP] BOX MACHINEBUILD = >%s<" %self.MACHINEBUILD
		print "[FULL BACKUP] BOX MODEL = >%s<" %self.MODEL
		print "[FULL BACKUP] MTDBOOT = >%s<" %self.MTDBOOT
		print "[FULL BACKUP] MTDKERNEL = >%s<" %self.current_MTDKERNEL
		print "[FULL BACKUP] MTDROOTFS = >%s<" %self.current_MTDROOTFS
		print "[FULL BACKUP] EMMCIMG = >%s<" %self.EMMCIMG

		self["key_red"] = StaticText("HDD")
		self["key_green"] = StaticText("USB")
		self["key_yellow"] = StaticText(_("Recovery"))
		self["key_blue"] = StaticText(_("STARTUP"))
		self["info-multi"] = Label(_("You can select with blue the OnlineFlash Image\n or select Recovery to create a USB Disk Image for clean Install."))
		self["info-usb"] = Label(_("USB = USB Back-up image on USB\n First insert a USB\nBackUp from 4 -> 15 minutes.\n A HD51 Restore -> 10 minutes"))		
		self["info-hdd"] = Label(_("HDD = USB Back-up image on HDD \n This only takes 2 or 10 minutes."))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], 
		{
			"red": self.red,
			"green": self.green,
			"yellow": self.recovery,
			"blue": self.blue,
			"cancel": self.quit,
		}, -2)

		self.getImageList = GetImagelist(self.getImagelistCallback)		

	def getImagelistCallback(self, imagedict):
		self.imagelist = imagedict

	def check_hdd(self):
		if not path.exists("/media/hdd"):
			self.session.open(MessageBox, _("No /hdd found !!\nPlease make sure you have a HDD mounted.\n"), type = MessageBox.TYPE_ERROR)
			return False
		if Freespace('/media/hdd') < 300000:
			self.session.open(MessageBox, _("Not enough free space on /hdd !!\nYou need at least 300Mb free space.\n"), type = MessageBox.TYPE_ERROR)
			return False
		return True

	def check_usb(self, dev):
		if Freespace(dev) < 300000:
			self.session.open(MessageBox, _("Not enough free space on %s !!\nYou need at least 300Mb free space.\n" % dev), type = MessageBox.TYPE_ERROR)
			return False
		return True
		
	def recovery(self):
		self.Recov = True
		self.MTDKERNEL = self.current_MTDKERNEL
		self.MTDROOTFS = self.current_MTDROOTFS
		
	def quit(self):
		self.close()
		
	def red(self):
		if self.check_hdd():
			self.MTDKERNEL = self.current_MTDKERNEL
			self.MTDROOTFS = self.current_MTDROOTFS	
			self.doFullBackup("/media/hdd")

	def green(self):
		USB_DEVICE = self.SearchUSBcandidate()
		if USB_DEVICE == 'XX':
			text = _("No USB-Device found for fullbackup !!\n\n\n")
			text += _("To back-up directly to the USB-stick, the USB-stick MUST\n")
			text += _("contain a file with the name: \n\n")
			text += _("backupstick or backupstick.txt")
			self.session.open(MessageBox, text, type = MessageBox.TYPE_ERROR)
		else:
			if self.check_usb(USB_DEVICE):
				self.MTDKERNEL = self.current_MTDKERNEL
				self.MTDROOTFS = self.current_MTDROOTFS
				self.doFullBackup(USB_DEVICE)

	def blue(self):
		imagedict = self.imagelist
		self.selection = self.selection + 1
		x = self.selection
		self.kernel = x
		self["key_blue"].setText(_("STARTUP_%s: %s") %(x, imagedict[x]['imagename']))
		if self.selection == len(self.imagelist):
			self.selection = 0
		if SystemInfo["canMultiBootHD"]:
			self.current_MTDKERNEL = "mmcblk0p%s" %(self.kernel*2)
			self.current_MTDROOTFS = "mmcblk0p%s" %(self.kernel*2 +1)
		elif SystemInfo["canMultiBootGB"]:
			self.current_MTDKERNEL = "mmcblk0p%s" %(self.kernel*2 +2)
			self.current_MTDROOTFS = "mmcblk0p%s" %(self.kernel*2 +3)

	def SearchUSBcandidate(self):
		for paths, subdirs, files in walk("/media"):
			for dir in subdirs:
				if not dir == 'hdd' and not dir == 'net':
					for file in listdir("/media/" + dir):
						if file.find("backupstick") > -1:
							print "[ImageBackup] USB-DEVICE found on: /media/%s" % dir
							return "/media/" + dir
			break
		return "XX"

	def doFullBackup(self, DIRECTORY):
		self.DIRECTORY = DIRECTORY
		self.IMAGEFOLDER = self.MODEL
		self.TITLE = _("Fullbackup on %s") % (self.DIRECTORY)
		self.START = time()
		self.DATE = strftime("%Y%m%d_%H%M", localtime(self.START))
		self.IMAGEVERSION = self.imageInfo() #strftime("%Y%m%d", localtime(self.START))
		self.MKFS = "/bin/tar"
		self.BZIP2 = "/usr/bin/bzip2"
		self.WORKDIR= "%s/bi" %self.DIRECTORY
		self.TARGET="XX"


		self.MAINDEST = "%s/%s" %(self.DIRECTORY,self.IMAGEFOLDER)
		self.EXTRA = "%s/fullbackup_%s/%s/%s" % (self.DIRECTORY, self.MODEL, self.DATE, self.IMAGEFOLDER)
		print "[ImageBackup] MAINDEST: ", self.MAINDEST
		print "[ImageBackup] EXTRA: ", self.EXTRA

		self.message = "echo -e '\n"
		self.message += (_("Fullback for %s\n" %self.MODEL)).upper()
		self.message += VERSION + '\n'
		self.message += "____________________________________________________\n"
		self.message += _("Please be patient, a fullbackup will now be created.\n")
		if SystemInfo["canMultiBoot"] and self.Recov:
			self.message += _("because of the used filesystem the backup\n")
			self.message += _("can take about 30 minutes for this system.\n")
		else:
			self.message += _("because of the used filesystem the backup\n")
			self.message += _("will take about 1-4 minutes for this system.\n")
		self.message += "\n_________________________________________________\n\n"
		self.message += "'"

		## PREPARING THE BUILDING ENVIRONMENT
		system("rm -rf %s" %self.WORKDIR)
		if not path.exists(self.WORKDIR):
			makedirs(self.WORKDIR)
		if not path.exists("/tmp/bi/root"):
			makedirs("/tmp/bi/root")
		system("sync")
		system("mount /dev/%s /tmp/bi/root" %self.MTDROOTFS)
		cmd1 = "%s -cf %s/rootfs.tar -C /tmp/bi/root --exclude ./var/nmbd --exclude ./var/lib/samba/private/msg.sock ." % (self.MKFS, self.WORKDIR)
		cmd2 = "%s %s/rootfs.tar" % (self.BZIP2, self.WORKDIR)
		cmdlist = []
		cmdlist.append(self.message)
		cmdlist.append('echo "Create: %s\n"' %self.ROOTFSBIN)
		cmdlist.append(cmd1)
		cmdlist.append(cmd2)
		cmdlist.append("chmod 644 %s/%s" %(self.WORKDIR, self.ROOTFSBIN))

		if self.MODEL in ("gbquad4k","gbue4k"):
			cmdlist.append('echo " "')
			cmdlist.append('echo "Create: boot dump"')
			cmdlist.append('echo " "')
			cmdlist.append("dd if=/dev/mmcblk0p1 of=%s/boot.bin" % self.WORKDIR)
			cmdlist.append('echo " "')
			cmdlist.append('echo "Create: rescue dump"')
			cmdlist.append('echo " "')
			cmdlist.append("dd if=/dev/mmcblk0p3 of=%s/rescue.bin" % self.WORKDIR)

		cmdlist.append('echo " "')
		cmdlist.append('echo "Create: kernel dump"')
		cmdlist.append('echo " "')
		cmdlist.append("dd if=/dev/%s of=%s/kernel.bin" % (self.MTDKERNEL ,self.WORKDIR))
		cmdlist.append('echo " "')

		cmdlist.append("sync")
		if SystemInfo["canMultiBootHD"] and self.Recov:
			BLOCK_SIZE=512
			BLOCK_SECTOR=2
			IMAGE_ROOTFS_ALIGNMENT=1024
			BOOT_PARTITION_SIZE=3072
			KERNEL_PARTITION_OFFSET = int(IMAGE_ROOTFS_ALIGNMENT) + int(BOOT_PARTITION_SIZE)
			KERNEL_PARTITION_SIZE=8192
			ROOTFS_PARTITION_OFFSET = int(KERNEL_PARTITION_OFFSET) + int(KERNEL_PARTITION_SIZE)
			ROOTFS_PARTITION_SIZE=819200
			SECOND_KERNEL_PARTITION_OFFSET = int(ROOTFS_PARTITION_OFFSET) + int(ROOTFS_PARTITION_SIZE)
			SECOND_ROOTFS_PARTITION_OFFSET = int(SECOND_KERNEL_PARTITION_OFFSET) + int(KERNEL_PARTITION_SIZE)
			THIRD_KERNEL_PARTITION_OFFSET = int(SECOND_ROOTFS_PARTITION_OFFSET) + int(ROOTFS_PARTITION_SIZE)
			THIRD_ROOTFS_PARTITION_OFFSET = int(THIRD_KERNEL_PARTITION_OFFSET) + int(KERNEL_PARTITION_SIZE)
			FOURTH_KERNEL_PARTITION_OFFSET = int(THIRD_ROOTFS_PARTITION_OFFSET) + int(ROOTFS_PARTITION_SIZE)
			FOURTH_ROOTFS_PARTITION_OFFSET = int(FOURTH_KERNEL_PARTITION_OFFSET) + int(KERNEL_PARTITION_SIZE)
			SWAP_PARTITION_OFFSET = int(FOURTH_ROOTFS_PARTITION_OFFSET) + int(ROOTFS_PARTITION_SIZE)
			EMMC_IMAGE = "%s/%s"% (self.WORKDIR,self.EMMCIMG)
			EMMC_IMAGE_SIZE=3817472
			EMMC_IMAGE_SEEK = int(EMMC_IMAGE_SIZE) * int(BLOCK_SECTOR)
			cmdlist.append('echo " "')
			cmdlist.append('echo "Create: Recovery Fullbackup %s"'% (self.EMMCIMG))
			cmdlist.append('echo " "')
			cmdlist.append('dd if=/dev/zero of=%s bs=%s count=0 seek=%s' % (EMMC_IMAGE, BLOCK_SIZE , EMMC_IMAGE_SEEK))
			cmdlist.append('parted -s %s mklabel gpt' %EMMC_IMAGE)
			PARTED_END_BOOT = int(IMAGE_ROOTFS_ALIGNMENT) + int(BOOT_PARTITION_SIZE)
			cmdlist.append('parted -s %s unit KiB mkpart boot fat16 %s %s' % (EMMC_IMAGE, IMAGE_ROOTFS_ALIGNMENT, PARTED_END_BOOT ))
			PARTED_END_KERNEL1 = int(KERNEL_PARTITION_OFFSET) + int(KERNEL_PARTITION_SIZE)
			cmdlist.append('parted -s %s unit KiB mkpart kernel1 %s %s' % (EMMC_IMAGE, KERNEL_PARTITION_OFFSET, PARTED_END_KERNEL1 ))
			PARTED_END_ROOTFS1 = int(ROOTFS_PARTITION_OFFSET) + int(ROOTFS_PARTITION_SIZE)
			cmdlist.append('parted -s %s unit KiB mkpart rootfs1 ext4 %s %s' % (EMMC_IMAGE, ROOTFS_PARTITION_OFFSET, PARTED_END_ROOTFS1 ))
			PARTED_END_KERNEL2 = int(SECOND_KERNEL_PARTITION_OFFSET) + int(KERNEL_PARTITION_SIZE)
			cmdlist.append('parted -s %s unit KiB mkpart kernel2 %s %s' % (EMMC_IMAGE, SECOND_KERNEL_PARTITION_OFFSET, PARTED_END_KERNEL2 ))
			PARTED_END_ROOTFS2 = int(SECOND_ROOTFS_PARTITION_OFFSET) + int(ROOTFS_PARTITION_SIZE)
			cmdlist.append('parted -s %s unit KiB mkpart rootfs2 ext4 %s %s' % (EMMC_IMAGE, SECOND_ROOTFS_PARTITION_OFFSET, PARTED_END_ROOTFS2 ))
			PARTED_END_KERNEL3 = int(THIRD_KERNEL_PARTITION_OFFSET) + int(KERNEL_PARTITION_SIZE)
			cmdlist.append('parted -s %s unit KiB mkpart kernel3 %s %s' % (EMMC_IMAGE, THIRD_KERNEL_PARTITION_OFFSET, PARTED_END_KERNEL3 ))
			PARTED_END_ROOTFS3 = int(THIRD_ROOTFS_PARTITION_OFFSET) + int(ROOTFS_PARTITION_SIZE)
			cmdlist.append('parted -s %s unit KiB mkpart rootfs3 ext4 %s %s' % (EMMC_IMAGE, THIRD_ROOTFS_PARTITION_OFFSET, PARTED_END_ROOTFS3 ))
			PARTED_END_KERNEL4 = int(FOURTH_KERNEL_PARTITION_OFFSET) + int(KERNEL_PARTITION_SIZE)
			cmdlist.append('parted -s %s unit KiB mkpart kernel4 %s %s' % (EMMC_IMAGE, FOURTH_KERNEL_PARTITION_OFFSET, PARTED_END_KERNEL4 ))
			PARTED_END_ROOTFS4 = int(FOURTH_ROOTFS_PARTITION_OFFSET) + int(ROOTFS_PARTITION_SIZE)
			cmdlist.append('parted -s %s unit KiB mkpart rootfs4 ext4 %s %s' % (EMMC_IMAGE, FOURTH_ROOTFS_PARTITION_OFFSET, PARTED_END_ROOTFS4 ))
			cmdlist.append('parted -s %s unit KiB mkpart swap linux-swap %s 100%%' % (EMMC_IMAGE, SWAP_PARTITION_OFFSET))
			BOOT_IMAGE_SEEK = int(IMAGE_ROOTFS_ALIGNMENT) * int(BLOCK_SECTOR)
			cmdlist.append('dd if=/dev/%s of=%s seek=%s' % (self.MTDBOOT, EMMC_IMAGE, BOOT_IMAGE_SEEK ))
			KERNAL_IMAGE_SEEK = int(KERNEL_PARTITION_OFFSET) * int(BLOCK_SECTOR)
			cmdlist.append('dd if=/dev/%s of=%s seek=%s' % (self.MTDKERNEL, EMMC_IMAGE, KERNAL_IMAGE_SEEK ))
			ROOTFS_IMAGE_SEEK = int(ROOTFS_PARTITION_OFFSET) * int(BLOCK_SECTOR)
			cmdlist.append('dd if=/dev/%s of=%s seek=%s' % (self.MTDROOTFS, EMMC_IMAGE, ROOTFS_IMAGE_SEEK ))
		self.session.open(Console, title = self.TITLE, cmdlist = cmdlist, finishedCallback = self.doFullBackupCB, closeOnSuccess = True)

	def doFullBackupCB(self):
		cmdlist = []
		cmdlist.append(self.message)
		system('rm -rf %s' %self.MAINDEST)
		if not path.exists(self.MAINDEST):
			makedirs(self.MAINDEST)
		if not path.exists(self.EXTRA):
			makedirs(self.EXTRA)

		f = open("%s/imageversion" %self.MAINDEST, "w")
		f.write(self.IMAGEVERSION)
		f.close()
		system('mv %s/rootfs.tar.bz2 %s/rootfs.tar.bz2' %(self.WORKDIR, self.MAINDEST))
		system('mv %s/kernel.bin %s/kernel.bin' %(self.WORKDIR, self.MAINDEST))

		if SystemInfo["canMultiBoot"] and self.Recov:
			system('mv %s/%s %s/%s' %(self.WORKDIR,self.EMMCIMG, self.MAINDEST,self.EMMCIMG))

		if SystemInfo["canMultiBootGB"]:
			system('mv %s/boot.bin %s/boot.bin' %(self.WORKDIR, self.MAINDEST))
			system('mv %s/rescue.bin %s/rescue.bin' %(self.WORKDIR, self.MAINDEST))
			system('cp -f /usr/share/gpt.bin %s/gpt.bin' %(self.MAINDEST))


		system('cp -r %s/* %s/' % (self.MAINDEST, self.EXTRA))
		cmdlist.append("sync")
		file_found = True

		if not path.exists("%s/%s" % (self.MAINDEST, self.ROOTFSBIN)):
			print '[ImageBackup] ROOTFS bin file not found'
			file_found = False

		if not path.exists("%s/%s" % (self.MAINDEST, self.KERNELBIN)):
			print '[ImageBackup] KERNEL bin file not found'
			file_found = False

		if SystemInfo["canMultiBoot"] and not self.Recov:
			cmdlist.append('echo "_________________________________________________\n"')
			cmdlist.append('echo "Multiboot Image created on:" %s' %self.MAINDEST)
			cmdlist.append('echo "and there is made an extra copy on:"')
			cmdlist.append('echo %s' %self.EXTRA)
			cmdlist.append('echo "_________________________________________________\n"')
			cmdlist.append('echo " "')
			cmdlist.append('echo "\nPlease wait...almost ready! "')
			cmdlist.append('echo " "')
			cmdlist.append('echo "To restore the image:"')
			cmdlist.append('echo "Use OnlineFlash in SoftwareManager"')
		elif file_found:
			cmdlist.append('echo "____________________________________________________\n"')
			cmdlist.append('echo "Fullbackup created on:" %s' %self.MAINDEST)
			cmdlist.append('echo "Extra copy of fullbackup created on:"')
			cmdlist.append('echo %s' %self.EXTRA)
			cmdlist.append('echo "____________________________________________________\n"')
			cmdlist.append('echo "Please wait...almost ready...\n"')
			cmdlist.append('echo "To restore the image:"')
			cmdlist.append('echo "Please check the manual of the receiver "')
			cmdlist.append('echo "on how to restore the image"')
		else:
			cmdlist.append('echo "____________________________________________________\n"')
			cmdlist.append('echo "Image creation failed - "')
			cmdlist.append('echo "Possible causes could be"')
			cmdlist.append('echo "     wrong back-up destination "')
			cmdlist.append('echo "     no space left on back-up device"')
			cmdlist.append('echo "     no writing permission on back-up device"')
			cmdlist.append('echo " "')

#		if self.DIRECTORY == "/media/hdd":
#			cmdlist.append('echo "\n"')
#			cmdlist.append('echo "\n"')
#			cmdlist.append('echo "Please wait..."')
#			self.TARGET = self.SearchUSBcandidate()
#			print "[ImageBackup] TARGET = %s" % self.TARGET
#			if self.TARGET == 'XX':
#				cmdlist.append('echo "\n"')
#				cmdlist.append('echo "\n"')
#				cmdlist.append('echo "Please wait..."')
#			else:
#				cmdlist.append('echo "\n"')
#				cmdlist.append('echo "\n"')
#				cmdlist.append('echo "__________________________________________________\n"')
#				cmdlist.append('echo "There is a valid USB-flash drive detected in one "')
#				cmdlist.append('echo "of the USB-ports, therefor an extra copy of the "')
#				cmdlist.append('echo "back-up image will now be copied to that USB- "')
#				cmdlist.append('echo "flash drive. "')
#				cmdlist.append('echo "This only takes about 1 or 2 minutes"')
#				cmdlist.append('echo "\n"')
#
#				cmdlist.append('mkdir -p %s/%s' % (self.TARGET, self.IMAGEFOLDER))
#				cmdlist.append('cp -r %s %s/' % (self.MAINDEST, self.TARGET))
#
#
#				cmdlist.append("sync")
#				cmdlist.append('echo "Backup finished and copied to your USB-flash drive"')

		cmdlist.append("sleep 2")
		cmdlist.append("umount /tmp/bi/root")
		cmdlist.append("sleep 2")
		cmdlist.append("rmdir /tmp/bi/root")
		cmdlist.append("rmdir /tmp/bi")
		cmdlist.append("rm -rf %s" % self.WORKDIR)
		cmdlist.append("sleep 5")
		cmdlist.append('echo "\n"')
		END = time()
		DIFF = int(END - self.START)
		TIMELAP = str(datetime.timedelta(seconds=DIFF))
		cmdlist.append('echo "\n\n"')
		cmdlist.append('echo "Time required for this process: %s"' %TIMELAP)
		cmdlist.append('echo "\n"')

		self.session.open(Console, title = self.TITLE, cmdlist = cmdlist, closeOnSuccess = False)

	def imageInfo(self):
		AboutText = _("Full Image Backup ")
		AboutText += _("Thanks to openATV") + "\n"
		AboutText += _("Support at") + " Twol Home\n\n"
		AboutText += _("[Image Info]\n")
		AboutText += _("Model: %s %s\n") % (self.MODEL, self.MODEL)
		AboutText += _("Backup Date: %s\n") % strftime("%Y-%m-%d", localtime(self.START))
		AboutText += _("CPU: %s") % about.getCPUInfoString() + "\n"
		AboutText += _("Version: %s") % about.getVersionString() + "\n"
		AboutText += _("Build: %s") % about.getBuildDateString() + "\n"
		AboutText += _("Kernel: %s") % about.getKernelVersionString() + "\n"

		string = about.getDriverInstalledDate()
		year = string[0:4]
		month = string[4:6]
		day = string[6:8]
		driversdate = '-'.join((year, month, day))
		AboutText += _("Drivers:\t%s") % driversdate + "\n"

		AboutText += _("Last update:\t%s") % getEnigmaVersionString() + "\n\n"

		AboutText += _("[Enigma2 Settings]\n")
		AboutText += commands.getoutput("cat /etc/enigma2/settings")
		AboutText += _("\n\n[User - bouquets (TV)]\n")
		try:
			f = open("/etc/enigma2/bouquets.tv","r")
			lines = f.readlines()
			f.close()
			for line in lines:
				if line.startswith("#SERVICE:"):
					bouqet = line.split()
					if len(bouqet) > 3:
						bouqet[3] = bouqet[3].replace('"','')
						f = open("/etc/enigma2/" + bouqet[3],"r")
						userbouqet = f.readline()
						AboutText += userbouqet.replace('#NAME ','')
						f.close()
		except:
			AboutText += "Error reading bouquets.tv"
			
		AboutText += _("\n[User - bouquets (RADIO)]\n")
		try:
			f = open("/etc/enigma2/bouquets.radio","r")
			lines = f.readlines()
			f.close()
			for line in lines:
				if line.startswith("#SERVICE:"):
					bouqet = line.split()
					if len(bouqet) > 3:
						bouqet[3] = bouqet[3].replace('"','')
						f = open("/etc/enigma2/" + bouqet[3],"r")
						userbouqet = f.readline()
						AboutText += userbouqet.replace('#NAME ','')
						f.close()
		except:
			AboutText += "Error reading bouquets.radio"

		AboutText += _("\n[Installed Plugins]\n")
		AboutText += commands.getoutput("opkg list_installed | grep enigma2-plugin-")

		return AboutText
