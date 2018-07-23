import os
import sys
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigSelection, ConfigText, ConfigNumber, NoSave, ConfigEnableDisable, ConfigPassword
from Screens.Screen import Screen
import e2m3u2bouquet

config.IPTVcreate = ConfigSubsection()
config.IPTVcreate.Provname = ConfigText(default = '', fixed_size=False)
config.IPTVcreate.Username = ConfigText(default = '', fixed_size=False)
config.IPTVcreate.Password = ConfigPassword(default = '', fixed_size=False)
config.IPTVcreate.m3u_url = ConfigText(default = '', fixed_size=False)
config.IPTVcreate.epg_url = ConfigText(default = '', fixed_size=False)
config.IPTVcreate.Provname2 = ConfigText(default = '', fixed_size=False)
config.IPTVcreate.Username2 = ConfigText(default = '', fixed_size=False)
config.IPTVcreate.Password2 = ConfigPassword(default = '', fixed_size=False)
config.IPTVcreate.m3u2_url = ConfigText(default = '', fixed_size=False)
config.IPTVcreate.epg2_url = ConfigText(default = '', fixed_size=False)
config.IPTVcreate.Piconpath = ConfigSelection(default = '/usr/share/enigma2/picon/', choices=[
 '/usr/share/enigma2/picon/',
 '/media/usb/picon/',
 '/media/hdd/picon/'])
config.IPTVcreate.Picon = ConfigYesNo(default = False)
config.IPTVcreate.Uninstall = ConfigYesNo(default = False)
config.IPTVcreate.Multivod = ConfigYesNo(default = False)
config.IPTVcreate.bouquetpos = ConfigSelection(default='bottom', choices=[
 'bottom', 'top'])
config.IPTVcreate.bouquetdownload = ConfigEnableDisable(default=False)
config.IPTVcreate.AllBouquet = ConfigYesNo(default = False)
config.IPTVcreate.Xcludesref = ConfigYesNo(default = False)
config.IPTVcreate.iptvtypes = ConfigEnableDisable(default=False)

class IPTVcreate(Screen):
	skin = """<screen name="IPTVcreate" position="center,center" size="560,400" title="IPTVcreate">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="0,40" size="35,25" alphatest="blend" transparent="1" zPosition="3"/>
		<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
		<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
		<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"/>
		<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1"/>
		<widget name="cancel" position="22,1032" size="400,39" foregroundColor="grey" zPosition="1" font="Regular;33" halign="center"/>
		<widget name="ok" position="457,1032" size="400,39" foregroundColor="grey" zPosition="1" font="Regular;33" halign="center"/>
		<widget name="lab1" render="Label" position="100,700" size="580,200" halign="center" valign="center" font="Regular; 30" />
		<widget name="statusbar" position="10,410" size="500,20" font="Regular;18" />
		<applet type="onLayoutFinish">
		</applet>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		screentitle = _("IPTVcreate")
		title = screentitle
		Screen.setTitle(self, title)
		print "[IPTVcreate] Start Enabled"
		self['statusbar'] = Label()
		self.Prov = 1
		self.Config_List()
                self.session = session
	
		
	def Config_List(self):
            	print "[IPTVcreate] Display Menu"
		self["key_red"] = Button(_("Exit"))
		self["key_yellow"] = Label("%s" %config.IPTVcreate.Provname.value)
		self["key_blue"] = Label("%s" %config.IPTVcreate.Provname2.value)
		self['lab1'] = Label(_("Select Yellow button to download latest IPTV Bouquets"))
		self['myactions'] = ActionMap(['ColorActions', 'OkCancelActions', 'DirectionActions', "MenuActions", "HelpActions"],
									  {
									  'cancel': self.close,
									  'red': self.close,
									  'yellow': self.Prov1,
									  'blue': self.Prov2,
									  "ok": self.close,
									  }, -1)
                                                                              
                
                 
	def configOK(self, test=None):
            	print "[IPTVcreate] Config OK"

    	def Prov1(self):
		self.Prov = 1
		self.ProvUpdate()

	def Prov2(self):
		self.Prov = 2
		self.ProvUpdate()

	def ProvUpdate(self):
		sys.argv = []
		if self.Prov == 1:
			sys.argv.append(('-m={}').format(config.IPTVcreate.m3u_url.value))
			sys.argv.append(('-e={}').format(config.IPTVcreate.epg_url.value))
			sys.argv.append('-n={}'.format(config.IPTVcreate.Provname.value))
			sys.argv.append('-u={}'.format(config.IPTVcreate.Username.value))
			sys.argv.append('-p={}'.format(config.IPTVcreate.Password.value))
		else:
			sys.argv.append(('-m={}').format(config.IPTVcreate.m3u2_url.value))
			sys.argv.append(('-e={}').format(config.IPTVcreate.epg2_url.value))
			sys.argv.append('-n={}'.format(config.IPTVcreate.Provname2.value))
			sys.argv.append('-u={}'.format(config.IPTVcreate.Username2.value))
			sys.argv.append('-p={}'.format(config.IPTVcreate.Password2.value))
		sys.argv.append('-M')
		if config.IPTVcreate.iptvtypes.value:
		    sys.argv.append('-i')
		if config.IPTVcreate.AllBouquet.value:
		    sys.argv.append('-a')
		if config.IPTVcreate.Picon.value:
		    sys.argv.append('-P')
		    sys.argv.append('-q={}'.format(config.IPTVcreate.Piconpath.value))
		if config.IPTVcreate.Xcludesref.value:
		    sys.argv.append('-xs')
		if config.IPTVcreate.bouquetpos.value and config.IPTVcreate.bouquetpos.value == 'top':
		    sys.argv.append('-bt')
		if config.IPTVcreate.bouquetdownload.value:
		    sys.argv.append('-bd')
		if config.IPTVcreate.Uninstall.value:
		    sys.argv.append('-U')
		print "[IPTVcreate] Start Manual IPTV Import Enabled"
		e2m3u2bouquet.main(sys.argv)
		print "[IPTVcreate] Manual IPTV Import Complete"
