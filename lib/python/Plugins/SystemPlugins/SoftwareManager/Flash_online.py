from Plugins.SystemPlugins.Hotplug.plugin import hotplugNotifier
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.FileList import FileList
from Components.Task import Task, Job, job_manager, Condition
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import SystemInfo
from Components.config import config
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.Console import Console
from Screens.HelpMenu import HelpableScreen
from Screens.TaskView import JobView
from Tools.Downloader import downloadWithProgress
from Tools.Directories import fileExists, fileCheck
from enigma import fbClass
import urllib2
import os
import shutil
import math
from Tools.HardwareInfo import HardwareInfo
# from boxbranding import getBoxType,  getImageDistro, getMachineName, getMachineBrand, getImageVersion, getMachineKernelFile, getMachineRootFile, getMachineMake, getMachineBuild

#############################################################################################################
#
#        Thanks to OpenATV Team for supplyng most of this code
#
feedurl_ViX = 'http://192.168.0.171/openvix-builds' 
imagePathGB = '/media/hdd/images'
flashPathGB = '/media/hdd/images/flash'
flashTmpGB = '/media/hdd/images/tmp'
imagePath = '/media/HD51HDD/images'
flashPath = '/media/HD51HDD/images/flash'
flashTmp = '/media/HD51HDD/images/tmp'
ofgwritePath = '/usr/bin/ofgwrite'
#############################################################################################################

#		#default layout for Mut@nt HD51	& Giga4K								for GigaBlue 4K
# STARTUP_1 			Image 1: boot emmcflash0.kernel1 'root=/dev/mmcblk0p3 rw rootwait'	boot emmcflash0.kernel1: 'root=/dev/mmcblk0p5 
# STARTUP_2 			Image 2: boot emmcflash0.kernel2 'root=/dev/mmcblk0p5 rw rootwait'      boot emmcflash0.kernel2: 'root=/dev/mmcblk0p7
# STARTUP_3		        Image 3: boot emmcflash0.kernel3 'root=/dev/mmcblk0p7 rw rootwait'	boot emmcflash0.kernel3: 'root=/dev/mmcblk0p9
# STARTUP_4		        Image 4: boot emmcflash0.kernel4 'root=/dev/mmcblk0p9 rw rootwait'	NOT IN USE due to Rescue mode in mmcblk0p3

def Freespace(dev):
	statdev = os.statvfs(dev)
	space = (statdev.f_bavail * statdev.f_frsize) / 1024
	print "[Flash Online] Free space on %s = %i kilobytes" %(dev, space)
	return space

class FlashOnline(Screen):
	skin = """
	<screen position="center,center" size="560,400" title="Flash On the Fly">
		<ePixmap position="0,360"   zPosition="1" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,360" zPosition="1" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,360" zPosition="1" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,360" zPosition="1" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,360" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="info-online" position="10,30" zPosition="1" size="450,100" font="Regular;20" halign="left" valign="top" transparent="1" />
		<widget name="info-local" position="10,150" zPosition="1" size="450,200" font="Regular;20" halign="left" valign="top" transparent="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.selection = 0
		self.multi = 1
		if SystemInfo["canMultiBootHD"]:
			self.devrootfs = "/dev/mmcblk0p3"
			self.list = self.list_files("/media/mmcblk0p1")
		if SystemInfo["canMultiBootGB"]:
			self.devrootfs = "/dev/mmcblk0p4"
			self.list = self.list_files("/media/mmc")

		Screen.setTitle(self, _("Flash On the Fly"))
		self["key_yellow"] = StaticText(_("STARTUP"))
		self["key_green"] = StaticText(_("Online"))
		self["key_red"] = StaticText(_("Exit"))
		self["key_blue"] = StaticText(_("Local"))
		self["info-local"] = Label(_("Local = Flash a image from local path /hdd/images"))
		self["info-online"] = Label(_("Online = Download a image and flash it"))
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], 
		{
			"blue": self.blue,
			"yellow": self.yellow,
			"green": self.green,
			"red": self.quit,
			"cancel": self.quit,
		}, -2)
		if SystemInfo["canMultiBootGB"]:
			self.hdd = "/media/hdd"
			self.multi = self.read_startup("/media/mmc/" + self.list[self.selection]).split(".",1)[1].split(":",1)[0]
			self.multi = self.multi[-1:]
		if SystemInfo["canMultiBootHD"]:
			self.hdd = "/media/HD51HDD"
			self.multi = self.read_startup("/media/mmcblk0p1/" + self.list[self.selection]).split(".",1)[1].split(" ",1)[0]
			self.multi = self.multi[-1:]
#		imagePath = "%s + %s" %(self.hdd, images)
#		flashPath = "%s + %s" %(imagePath, flash)
#		flashTmp = "%s + %s" %(imagePath, tmp)
		print "[Flash Online] MULTI:",self.multi

	def check_hdd(self):
		if not os.path.exists(ofgwritePath):
			self.session.open(MessageBox, _('ofgwrite not found !!\nPlease make sure you have ofgwrite installed in /usr/bin/ofgwrite.\n\nExit plugin.'), type = MessageBox.TYPE_ERROR)
			return False
		if not os.path.exists(self.hdd):
			self.session.open(MessageBox, _("No /hdd found !!\nPlease make sure you have a HDD mounted.\n\nExit plugin."), type = MessageBox.TYPE_ERROR)
			return False
		if Freespace(self.hdd) < 300000:
			self.session.open(MessageBox, _("Not enough free space on /hdd !!\nYou need at least 300Mb free space.\n\nExit plugin."), type = MessageBox.TYPE_ERROR)
			return False

		if SystemInfo["canMultiBootGB"]:
			if not os.path.exists("/media/hdd"):
				self.session.open(MessageBox, _("No /hdd found !!\nPlease make sure you have a HDD mounted.\n\nExit plugin."), type = MessageBox.TYPE_ERROR)
				return False
			if Freespace("/media/hdd") < 300000:
				self.session.open(MessageBox, _("Not enough free space on /hdd !!\nYou need at least 300Mb free space.\n\nExit plugin."), type = MessageBox.TYPE_ERROR)
				return False
			if not os.path.exists(imagePathGB):
				try:
					os.mkdir(imagePathGB) 
				except:
					pass
			if os.path.exists(flashPathGB):
				try:
					os.system('rm -rf ' + flashPathGB) 
				except:
					pass
			try:
				os.mkdir(flashPathGB)
			except:
				pass
			return True
		if SystemInfo["canMultiBootHD"]:
			if not os.path.exists("/media/HD51HDD"):
				self.session.open(MessageBox, _("No /hdd found !!\nPlease make sure you have a HDD mounted.\n\nExit plugin."), type = MessageBox.TYPE_ERROR)
				return False
			if Freespace("/media/HD51HDD") < 300000:
				self.session.open(MessageBox, _("Not enough free space on /hdd !!\nYou need at least 300Mb free space.\n\nExit plugin."), type = MessageBox.TYPE_ERROR)
				return False
			if not os.path.exists(imagePath):
				try:
					os.mkdir(imagePath)
				except:
					pass
			if os.path.exists(flashPath):
				try:
					os.system('rm -rf ' + flashPath) 
				except:
					pass
			try:
				os.mkdir(flashPath)
			except:
				pass
			return True

	def quit(self):
		self.close()
		
	def blue(self):
		if self.check_hdd():
			self.session.open(doFlashImage, online = False, list=self.list[self.selection], multi=self.multi, devrootfs=self.devrootfs)
		else:
			self.close()

	def green(self):
		if self.check_hdd():
			self.session.open(doFlashImage, online = True, list=self.list[self.selection], multi=self.multi, devrootfs=self.devrootfs)
		else:
			self.close()

	def yellow(self):
		self.selection = self.selection + 1
		if self.selection == len(self.list):
			self.selection = 0
		self["key_yellow"].setText(_(self.list[self.selection]))
		if SystemInfo["canMultiBootGB"]:
			self.multi = self.read_startup("/media/mmc/" + self.list[self.selection]).split(".",1)[1].split(":",1)[0]
			self.multi = self.multi[-1:]
		if SystemInfo["canMultiBootHD"]:
			self.multi = self.read_startup("/media/mmcblk0p1/" + self.list[self.selection]).split(".",1)[1].split(" ",1)[0]
			self.multi = self.multi[-1:]
		print "[Flash Online] MULTI:",self.multi
		self.devrootfs = self.find_rootfs_dev(self.list[self.selection])
		print "[Flash Online] MULTI rootfs ", self.devrootfs

	def read_startup(self, FILE):
		self.file = FILE
		with open(self.file, 'r') as myfile:
			data=myfile.read().replace('\n', '')
		myfile.close()
		return data

	def find_rootfs_dev(self, file):
		if SystemInfo["canMultiBootGB"]:
			startup_content = self.read_startup("/media/mmc/" + file)
		if SystemInfo["canMultiBootHD"]:
			startup_content = self.read_startup("/media/mmcblk0p1/" + file)
		return startup_content[startup_content.find("root=")+5:].split()[0]

	def list_files(self, PATH):
		files = []
		path = PATH
		if SystemInfo["canMultiBoot"]:
			for name in os.listdir(path):
				if name != 'bootname' and os.path.isfile(os.path.join(path, name)):
					try:
						cmdline = self.find_rootfs_dev(name)
					except IndexError:
						continue
					cmdline_startup = self.find_rootfs_dev("STARTUP")
					if (cmdline != cmdline_startup) and (name != "STARTUP"):
						files.append(name)
			files.insert(0,"STARTUP")
		else:
			files = "None"
		return files

class doFlashImage(Screen):
	skin = """
	<screen position="center,center" size="560,500" title="Flash On the fly (select a image)">
		<ePixmap position="0,460"   zPosition="1" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,460" zPosition="1" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,460" zPosition="1" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,460" zPosition="1" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,460" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,460" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,460" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,460" zPosition="2" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="imageList" position="10,10" zPosition="1" size="450,450" font="Regular;20" scrollbarMode="showOnDemand" transparent="1" />
	</screen>"""
		
	def __init__(self, session, online, list=None, multi=None, devrootfs=None ):
		Screen.__init__(self, session)
		self.session = session

		Screen.setTitle(self, _("Flash On the fly (select a image)"))
		self["key_green"] = StaticText(_("Flash"))
		self["key_red"] = StaticText(_("Exit"))
		self["key_blue"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self.filename = None
		self.imagelist = []
		self.Online = online
		self.List = list
		self.multi=multi
		self.devrootfs=devrootfs
		self.imagePath = imagePath
		self.feedurl = feedurl_ViX
		self["imageList"] = MenuList(self.imagelist)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"green": self.green,
			"yellow": self.yellow,
			"red": self.quit,
			"blue": self.blue,
			"cancel": self.quit,
		}, -2)
		self.onLayoutFinish.append(self.layoutFinished)


	def quit(self):
		if self.List not in ("STARTUP","cmdline.txt"):
			fbClass.getInstance().unlock()
		self.close()
		
	def blue(self):
		if self.Online:
			self.layoutFinished()
			return
		sel = self["imageList"].l.getCurrentSelection()
		if sel == None:
			print"Nothing to select !!"
			return
		self.filename = sel
		self.session.openWithCallback(self.RemoveCB, MessageBox, _("Do you really want to delete\n%s ?") % (sel), MessageBox.TYPE_YESNO)

	def RemoveCB(self, ret):
		if ret:
			if os.path.exists(self.imagePath + "/" + self.filename):
				os.remove(self.imagePath + "/" + self.filename)
			self.imagelist.remove(self.filename)
			self["imageList"].l.setList(self.imagelist)
		
	def box(self):
#		model = HardwareInfo().get_device_name()
#		if model == 'hd51':
		if SystemInfo["canMultiBootHD"]:
			box = "Mutant-HD51"
		if SystemInfo["canMultiBootGB"]:
			box = "gbquad4k"

		return box

	def green(self, ret = None):
		self.sel = self["imageList"].l.getCurrentSelection()
		if self.sel == None:
			print"Nothing to select !!"
			return

		self.feedurl = feedurl_ViX
		self.filename = self.imagePath + "/" + self.sel
		self.boxtype = self.box()
		self.hide()
		if self.Online:
			url = self.feedurl+'/'+self.boxtype+'/' + "/" + self.sel
			print "[Flash Online] Download image: >%s<" % url
			try:
				u = urllib2.urlopen(url)
				f = open(self.filename, 'wb')
				meta = u.info()
				file_size = int(meta.getheaders("Content-Length")[0])
				print "Downloading: %s Bytes: %s" % (self.sel, file_size)
				f.close()
				job = ImageDownloadJob(url, self.filename, self.sel)
				job.afterEvent = "close"
				job_manager.AddJob(job)
				job_manager.failed_jobs = []
				self.session.openWithCallback(self.ImageDownloadCB, JobView, job, backgroundable = False, afterEventChangeable = False)
			except urllib2.URLError as e:
				print "[Flash Online] Download failed !!\n%s" % e
				self.session.openWithCallback(self.ImageDownloadCB, MessageBox, _("Download Failed !!" + "\n%s" % e), type = MessageBox.TYPE_ERROR)
				self.close()
		else:
			if sel == str(flashTmp):
				self.Start_Flashing()
			else:
				self.unzip_image(self.filename, flashPath)

	def ImageDownloadCB(self, ret):
		if ret:
			return
		if job_manager.active_job:
			job_manager.active_job = None
			self.close()
			return
		if len(job_manager.failed_jobs) == 0:
			self.session.openWithCallback(self.askUnzipCB, MessageBox, _("The image is downloaded. Do you want to flash now?"), MessageBox.TYPE_YESNO)
		else:
			self.session.open(MessageBox, _("Download Failed !!"), type = MessageBox.TYPE_ERROR)

	def askUnzipCB(self, ret):
		if ret:
			self.unzip_image(self.filename, flashPath)
		else:
			self.show()

	def unzip_image(self, filename, path):
		print "Unzip %s to %s" %(filename,path)
		self.session.openWithCallback(self.cmdFinished, Console, title = _("Unzipping files, Please wait ..."), cmdlist = ['unzip ' + filename + ' -o -d ' + path, "sleep 3"], closeOnSuccess = True)

	def cmdFinished(self):
		self.prepair_flashtmp(flashPath)
		self.Start_Flashing()

	def Start_Flashing(self):
		cmdlist = []
		if os.path.exists(ofgwritePath):
			text = _("Flashing: ")
			text += _("root and kernel")
		print "[Flash Online] multi = %s, flashtmp = %s, flashtmpGB= %s" %(self.multi, flashTmp, flashTmpGB)
		if SystemInfo["canMultiBootHD"]:
			cmdlist.append("%s -r -k -m%s %s > /dev/null 2>&1" % (ofgwritePath, self.multi, flashTmp)) %unk
		else:
			cmdlist.append("%s -r -k -m%s %s > /dev/null 2>&1" % (ofgwritePath, self.multi, flashTmpGB))
		message = "echo -e '\n"
		message += _('ofgwrite will stop enigma2 now to run the flash.\n')
		message += _('Your STB will freeze during the flashing process.\n')
		message += _('Please: DO NOT remedia/mmc your STB and turn off the power.\n')
		message += _('The image or kernel will be flashing and auto media/mmced in few minutes.\n')
		message += "'"
		cmdlist.append(message)
		self.session.open(Console, title = text, cmdlist = cmdlist, finishedCallback = self.quit, closeOnSuccess = False)
		fbClass.getInstance().lock()

	def prepair_flashtmp(self, tmpPath):
		if os.path.exists(flashTmp):
			flashTmpold = flashTmp + 'old'
			os.system('mv %s %s' %(flashTmp, flashTmpold))
			os.system('rm -rf %s' %flashTmpold)
		if not os.path.exists(flashTmp):
			os.mkdir(flashTmp)
		kernel = True
		rootfs = True
		
		for path, subdirs, files in os.walk(tmpPath):
			for name in files:
				if name.find('kernel') > -1 and name.endswith('.bin') and kernel:
					binfile = os.path.join(path, name)
					dest = flashTmp + '/kernel.bin' 
					shutil.copyfile(binfile, dest)
					kernel = False
				elif name.find('root') > -1 and (name.endswith('.bin') or name.endswith('.jffs2') or name.endswith('.bz2')) and rootfs:
					binfile = os.path.join(path, name)
					dest = flashTmp + '/rootfs.tar.bz2'
					shutil.copyfile(binfile, dest)
					rootfs = False

	def yellow(self):
		if not self.Online:
			self.session.openWithCallback(self.DeviceBrowserClosed, DeviceBrowser, None, matchingPattern="^.*\.(zip|bin|jffs2|img)", showDirectories=True, showMountpoints=True, inhibitMounts=["/autofs/sr0/"])

	def DeviceBrowserClosed(self, path, filename, binorzip):
		if path:
			print path, filename, binorzip
			strPath = str(path)
			if strPath[-1] == '/':
				strPath = strPath[:-1]
			self.imagePath = strPath
			if os.path.exists(flashTmp):
				os.system('rm -rf ' + flashTmp)
			os.mkdir(flashTmp)
			if binorzip == 0:
				for files in os.listdir(self.imagePath):
					if files.endswith(".bin") or files.endswith('.jffs2') or files.endswith('.img'):
						self.prepair_flashtmp(strPath)
						break
				self.Start_Flashing()
			elif binorzip == 1:
				self.unzip_image(strPath + '/' + filename, flashPath)
			else:
				self.layoutFinished()
		else:
			self.imagePath = imagePath

	def layoutFinished(self):
		if SystemInfo["canMultiBootHD"]:
			self.boxtype = "Mutant-HD51"
			self.model = "mutant51"
		if SystemInfo["canMultiBootGB"]:
			self.boxtype = "gbquad4k"
			self.model = "gbquad4k"
		self.imagelist = []
		if self.Online:
			self["key_yellow"].setText("Flash")
			self["key_blue"] = StaticText("")
			self.feedurl = feedurl_ViX
			from bs4 import BeautifulSoup
			url = 'http://192.168.0.171/openvix-builds/'+self.boxtype+'/'
			conn = urllib2.urlopen(url)
			the_page = conn.read()

			soup = BeautifulSoup(the_page)
			links = soup.find_all('a')
			print "[Flash Online] -4 soup =  %s links = %s" %(soup, links)
			for tag in links: 
				link = tag.get('href',None) 
				if link != None and link.endswith('zip') and link.find(self.model) != -1:
					self.imagelist.append(str(link))
			self.imagelist.sort()
			self.imagelist.reverse()

		else:
			self["key_blue"].setText(_("Delete"))
			self["key_yellow"].setText(_("Devices"))
			for name in os.listdir(self.imagePath):
				if name.endswith(".zip"): # and name.find(box) > 1:
					self.imagelist.append(name)
			self.imagelist.sort()
			if os.path.exists(flashTmp):
				for file in os.listdir(flashTmp):
					if file.find(".bin") > -1:
						self.imagelist.insert( 0, str(flashTmp))
						break

		self["imageList"].l.setList(self.imagelist)

class ImageDownloadJob(Job):
	def __init__(self, url, filename, file):
		Job.__init__(self, _("Downloading %s") %file)
		ImageDownloadTask(self, url, filename)

class DownloaderPostcondition(Condition):
	def check(self, task):
		return task.returncode == 0

	def getErrorMessage(self, task):
		return self.error_message

class ImageDownloadTask(Task):
	def __init__(self, job, url, path):
		Task.__init__(self, job, _("Downloading"))
		self.postconditions.append(DownloaderPostcondition())
		self.job = job
		self.url = url
		self.path = path
		self.error_message = ""
		self.last_recvbytes = 0
		self.error_message = None
		self.download = None
		self.aborted = False

	def run(self, callback):
		self.callback = callback
		self.download = downloadWithProgress(self.url,self.path)
		self.download.addProgress(self.download_progress)
		self.download.start().addCallback(self.download_finished).addErrback(self.download_failed)
		print "[ImageDownloadTask] downloading", self.url, "to", self.path

	def abort(self):
		print "[ImageDownloadTask] aborting", self.url
		if self.download:
			self.download.stop()
		self.aborted = True

	def download_progress(self, recvbytes, totalbytes):
		if ( recvbytes - self.last_recvbytes  ) > 100000: # anti-flicker
			self.progress = int(100*(float(recvbytes)/float(totalbytes)))
			self.name = _("Downloading") + ' ' + _("%d of %d kBytes") % (recvbytes/1024, totalbytes/1024)
			self.last_recvbytes = recvbytes

	def download_failed(self, failure_instance=None, error_message=""):
		self.error_message = error_message
		if error_message == "" and failure_instance is not None:
			self.error_message = failure_instance.getErrorMessage()
		Task.processFinished(self, 1)

	def download_finished(self, string=""):
		if self.aborted:
			self.finish(aborted = True)
		else:
			Task.processFinished(self, 0)

class DeviceBrowser(Screen, HelpableScreen):
	skin = """
		<screen name="DeviceBrowser" position="center,center" size="520,430" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="message" render="Label" position="5,50" size="510,150" font="Regular;16" />
			<widget name="filelist" position="5,210" size="510,220" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, startdir, message="", showDirectories = True, showFiles = True, showMountpoints = True, matchingPattern = "", useServiceRef = False, inhibitDirs = False, inhibitMounts = False, isTop = False, enableWrapAround = False, additionalExtensions = None):
		Screen.__init__(self, session)

		HelpableScreen.__init__(self)
		Screen.setTitle(self, _("Please select medium"))

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText("Use")
		self["message"] = StaticText(message)

		self.filelist = FileList(startdir, showDirectories = showDirectories, showFiles = showFiles, showMountpoints = showMountpoints, matchingPattern = matchingPattern, useServiceRef = useServiceRef, inhibitDirs = inhibitDirs, inhibitMounts = inhibitMounts, isTop = isTop, enableWrapAround = enableWrapAround, additionalExtensions = additionalExtensions)
		self["filelist"] = self.filelist

		self["FilelistActions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"green": self.use,
				"red": self.exit,
				"ok": self.ok,
				"cancel": self.exit
			})

		hotplugNotifier.append(self.hotplugCB)
		self.onShown.append(self.updateButton)
		self.onClose.append(self.removeHotplug)

	def hotplugCB(self, dev, action):
		print "[hotplugCB]", dev, action
		self.updateButton()

	def updateButton(self):

		if self["filelist"].getFilename() or self["filelist"].getCurrentDirectory():
			self["key_green"].text = _("Flash")
		else:
			self["key_green"].text = ""

	def removeHotplug(self):
		print "[removeHotplug]"
		hotplugNotifier.remove(self.hotplugCB)

	def ok(self):
		if self.filelist.canDescent():
			if self["filelist"].showMountpoints == True and self["filelist"].showDirectories == False:
				self.use()
			else:
				self.filelist.descent()

	def use(self):
		print "[use]", self["filelist"].getCurrentDirectory(), self["filelist"].getFilename()
		if self["filelist"].getFilename() is not None and self["filelist"].getCurrentDirectory() is not None:
			if self["filelist"].getFilename().endswith(".bin") or self["filelist"].getFilename().endswith(".jffs2"):
				self.close(self["filelist"].getCurrentDirectory(), self["filelist"].getFilename(), 0)
			elif self["filelist"].getFilename().endswith(".zip"):
				self.close(self["filelist"].getCurrentDirectory(), self["filelist"].getFilename(), 1)
			else:
				return

	def exit(self):
		self.close(False, False, -1)
