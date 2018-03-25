from Screens.InfoBar import InfoBar
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components import Harddisk
from Components.SystemInfo import SystemInfo
from Tools.Multiboot import GetImagelist, GetCurrentImage
from os import path, listdir, system

class MultiBootStartup(ConfigListScreen, Screen):

	skin = """
	<screen name="MultiBootStartup" position="center,center" size="500,200"  flags="wfNoBorder" title="ImageChange" backgroundColor="transparent">
		<eLabel name="b" position="0,0" size="500,200" backgroundColor="#00ffffff" zPosition="-2" />
		<eLabel name="a" position="1,1" size="498,198" backgroundColor="#00000000" zPosition="-1" />
		<widget source="Title" render="Label" position="10,10" foregroundColor="#00ffffff" size="480,50" halign="center" font="Regular; 28" backgroundColor="#00000000" />
		<eLabel name="line" position="1,60" size="498,1" backgroundColor="#00ffffff" zPosition="1" />
		<widget source="config" render="Label" position="2,70" size="480,60" halign="center" font="Regular; 22" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_red" render="Label" position="35,162" size="170,30" noWrap="1" zPosition="1" valign="center" font="Regular; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<widget source="key_green" render="Label" position="228,162" size="170,30" noWrap="1" zPosition="1" valign="center" font="Regular; 20" halign="left" backgroundColor="#00000000" foregroundColor="#00ffffff" />
		<eLabel position="25,159" size="6,40" backgroundColor="#00e61700" />
		<eLabel position="216,159" size="6,40" backgroundColor="#0061e500" />
	</screen>
	"""

	def __init__(self, session, *args):
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("ReBoot"))
		self["config"] = StaticText(_("Select Image: STARTUP_1"))
		self.STARTUPslot = 0
		self.images = []
		self.STARTUPslot = GetCurrentImage()
		self.title = " " 
		self.getImageList = None
		self.selection = 0
		self.STARTUPmedia = "/media/mmc"
		self.list = self.list_STARTUPfiles()
		self.startit()

		self["actions"] = ActionMap(["WizardActions", "SetupActions", "ColorActions"],
		{
			"left": self.left,
			"right": self.right,
			"green": self.reboot,
			"red": self.cancel,
			"cancel": self.cancel,
			"ok": self.reboot,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.title)

	def startit(self):
		self.getImageList = GetImagelist(self.startup0)

	def startup0(self, imagedict):
		self.images = imagedict
		self.startup()

	def startup(self):
		x = self.selection + 1
		self.title = "Current Image: STARTUP_%s" %self.STARTUPslot
#		self["config"].setText(_("Reboot Image: STARTUP_%s: %s\n Use < > keys to select Image and then ReBoot.") %(x, self.images[x]['imagename']))


	def reboot(self):
		x = self.selection + 1
		system("cp -f '%s/STARTUP_%s' '%s/STARTUP'" %(self.STARTUPmedia, x, self.STARTUPmedia))
		restartbox = self.session.openWithCallback(self.restartBOX,MessageBox,_("Image %s chosen for reboot now(Yes) or later manual restart(No)"%self.list[self.selection]), MessageBox.TYPE_YESNO)

	def cancel(self):
		self.close()

	def left(self):
		self.selection = self.selection - 1
		if self.selection == -1:
			self.selection = len(self.list) - 1
		self.startup()

	def right(self):
		self.selection = self.selection + 1
		if self.selection == len(self.list):
			self.selection = 0
		self.startup()

	def list_STARTUPfiles(self):
		files = []
		for media in ['/media/%s' % x for x in listdir('/media') if x.startswith('mmc')]:
				if 'STARTUP' in listdir(media):
						for name in listdir(media):
							if not name == "STARTUP":
								files.append(name)
						break
		self.STARTUPmedia = media
		return files

	def restartBOX(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 2)
		else:
			self.close()
