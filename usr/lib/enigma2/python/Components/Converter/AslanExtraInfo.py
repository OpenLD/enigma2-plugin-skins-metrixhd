# shamelessly copied from pliExpertInfo and edit by (aslan2006)

from enigma import iServiceInformation, iPlayableService
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.config import config
from Tools.Transponder import ConvertToHumanReadable
from Tools.ISO639 import LanguageCodes
from Poll import Poll

def addspace(text):
	if text:
		text += " "
	return text

class AslanExtraInfo(Poll, Converter, object):
	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.type = type
		self.poll_interval = 1000
		self.poll_enabled = True
		self.caid_data = (
			( "0x100",  "0x1ff", "Seca",    "S" ),
			( "0x500",  "0x5ff", "Via",     "V" ),
			( "0x600",  "0x6ff", "Irdeto",  "I" ),
			( "0x900",  "0x9ff", "NDS",     "Nd"),
			( "0xb00",  "0xbff", "Conax",   "Co"),
			( "0xd00",  "0xdff", "CryptoW", "Cw"),
			( "0xe00",  "0xeff", "PowerVU", "P" ),
			("0x1700", "0x17ff", "Beta",    "B" ),
			("0x1800", "0x18ff", "Nagra",   "N" ),
			("0x2600", "0x2600", "Biss",    "Bi"),
			("0x4ae0", "0x4ae1", "Dre",     "D" )
		)

		self.feraw = self.fedata = self.updateFEdata = None

	def createResolutionString(self,info):
		xres = info.getInfo(iServiceInformation.sVideoWidth)
		if xres == -1:
			return ""
		yres = info.getInfo(iServiceInformation.sVideoHeight)
		mode = ("i", "p", "")[info.getInfo(iServiceInformation.sProgressive)]
		fps  = str((info.getInfo(iServiceInformation.sFrameRate) + 500) / 1000)
		return str(xres) + "x" + str(yres) + mode + " " + fps + "fps"
# + ("MPEG2", "MPEG4", "MPEG1", "MPEG4-II", "VC1", "VC1-SM", "")[info.getInfo(iServiceInformation.sVideoType)]

	def createResolution(self,info):
		xres = info.getInfo(iServiceInformation.sVideoWidth)
		if xres == -1:
			return ""
		yres = info.getInfo(iServiceInformation.sVideoHeight)
		mode = ("i", "p", "")[info.getInfo(iServiceInformation.sProgressive)]
		return str(xres) + "x" + str(yres) + mode

	def createVideoCodec(self,info):
		return ("MPEG2", "MPEG4", "MPEG1", "MPEG4-II", "VC1", "VC1-SM", "")[info.getInfo(iServiceInformation.sVideoType)]

	def createAudioCodec(self,info):
		service = self.source.service
		audio = service.audioTracks()
		if audio:
			try:
				ct = audio.getCurrentTrack()
				i = audio.getTrackInfo(ct)
				languages = i.getLanguage()
				if "ger" in languages or "german" in languages or "deu" in languages:
					languages = "Deutsch"
				elif "und" in languages:
					languages = ""
				description = i.getDescription();
				return description + " " + languages
			except:
				return "unbekannt"

	def createTransponderInfo(self,fedata,feraw):
		return addspace(self.createTunerSystem(fedata)) + addspace(self.createFrequency(fedata)) + addspace(self.createPolarization(fedata))\
			+ addspace(self.createSymbolRate(fedata)) + addspace(self.createFEC(fedata)) + addspace(self.createModulation(fedata))\
			+ self.createOrbPos(feraw)

	def createFrequency(self,fedata):
		frequency = fedata.get("frequency")
		if frequency:
			return str(frequency / 1000)
		return ""

	def createSymbolRate(self,fedata):
		symbolrate = fedata.get("symbol_rate")
		if symbolrate:
			return str(symbolrate / 1000)
		return ""

	def createPolarization(self,fedata):
		polarization = fedata.get("polarization_abbreviation")
		if polarization:
			return polarization
		return ""

	def createFEC(self,fedata):
		fec = fedata.get("fec_inner")
		if fec:
			return fec
		return ""

	def createModulation(self,fedata):
		modulation = fedata.get("modulation")
		if modulation:
			return modulation
		return ""

	def createTunerType(self,feraw):
		tunertype = feraw.get("tuner_type")
		if tunertype:
			return tunertype
		return ""

	def createTunerSystem(self,fedata):
		tunersystem = fedata.get("system")
		if tunersystem:
			return tunersystem
		return ""

	def createOrbPos(self,feraw):
		orbpos = feraw.get("orbital_position")
		if orbpos > 1800:
			return str((float(3600 - orbpos)) / 10.0) + "W"
		elif orbpos > 0:
			return str((float(orbpos)) / 10.0) + "E"
		return ""

	def createProviderName(self,info):
		return info.getInfoString(iServiceInformation.sProvider)

	def createCaids(self,info):
		caids = info.getInfoObject(iServiceInformation.sCAIDs)

		caidstr = ""
		if caids != 0.0:
			if len(caids) > 0:
				caidstr += "caid\'s: "
				for caid in caids:
					tmp = hex(caid).lstrip("0x")
					if len(tmp) < 4:
						tmp = "0" + tmp
					caidstr += tmp + ", "
			return caidstr
		return ""

	@cached
	def getText(self):

		service = self.source.service
		if service is None:
			return ""
		info = service and service.info()

		if not info:
			return ""

		if self.type == "ResolutionString":
			return self.createResolutionString(info)

		if self.type == "Resolution":
			return self.createResolution(info)

		if self.type == "VideoCodec":
			return self.createVideoCodec(info)

		if self.type == "AudioCodec":
			return self.createAudioCodec(info)

		if self.updateFEdata:
			feinfo = service.frontendInfo()
			if feinfo:
				self.feraw = feinfo.getAll(False)
				if self.feraw:
					self.fedata = ConvertToHumanReadable(self.feraw)

		feraw=self.feraw
		fedata=self.fedata

		if not feraw or not fedata:
			return ""

		if self.type == "ServiceInfo":
			return addspace(self.createProviderName(info)) + addspace(self.createTunerSystem(fedata)) + addspace(self.createFrequency(fedata)) + addspace(self.createPolarization(fedata))\
			+ addspace(self.createSymbolRate(fedata)) + addspace(self.createFEC(fedata)) + addspace(self.createModulation(fedata)) + addspace(self.createOrbPos(feraw))\
			+ addspace(self.createVideoCodec(info)) + self.createResolutionString(info)

		if self.type == "TransponderInfo":
			return self.createTransponderInfo(fedata,feraw)

		if self.type == "TransponderFrequency":
			return self.createFrequency(fedata)

		if self.type == "TransponderSymbolRate":
			return self.createSymbolRate(fedata)

		if self.type == "TransponderPolarization":
			return self.createPolarization(fedata)

		if self.type == "TransponderFEC":
			return self.createFEC(fedata)

		if self.type == "TransponderModulation":
			return self.createModulation(fedata)

		if self.type == "OrbitalPosition":
			return self.createOrbPos(feraw)

		if self.type == "TunerType":
			return self.createTunerType(feraw)

		if self.type == "TunerSystem":
			return self.createTunerSystem(fedata)

		if self.type == "Provider":
			return self.createProviderName(info)

		if self.type == "Caids":
			return self.createCaids(info)

		return _("invalid type")

	text = property(getText)

	def changed(self, what):
		if what[0] == self.CHANGED_SPECIFIC:
			if what[1] in (iPlayableService.evEnd, iPlayableService.evStart, iPlayableService.evUpdatedInfo):
				self.updateFEdata = True
			Converter.changed(self, what)
		elif what[0] == self.CHANGED_POLL and self.updateFEdata is not None:
			self.updateFEdata = False
			Converter.changed(self, what)

