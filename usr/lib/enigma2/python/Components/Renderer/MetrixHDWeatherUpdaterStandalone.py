#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#######################################################################
#
#   MetrixMODWeather for VU+
#   Coded by iMaxxx (c) 2013
#   Support: www.vuplus-support.com
#
#
#  This plugin is licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#
#
#######################################################################

from Renderer import Renderer
from Components.VariableText import VariableText
#import library to do http requests:
import urllib2
from enigma import eLabel, ePixmap
#import easy to use xml parser called minidom:
from xml.dom.minidom import parseString
from Components.config import config, configfile, ConfigSubsection, ConfigSelection, ConfigNumber, ConfigSelectionNumber, ConfigYesNo, ConfigText
from Plugins.Extensions.MyMetrixLite.__init__ import initWeatherConfig
from threading import Timer, Thread
from time import time, strftime, localtime

g_updateRunning = False

initWeatherConfig()

class MetrixHDWeatherUpdaterStandalone(Renderer, VariableText):

    def __init__(self):
        Renderer.__init__(self)
        VariableText.__init__(self)
        #self.test = "3"
        #config.plugins.MetrixWeather.save()
        #configfile.save()
        self.woeid = config.plugins.MetrixWeather.woeid.value
        self.Timer = None
        self.refreshcnt = 0
        #self.startTimer()
        self.getWeather()

    GUI_WIDGET = eLabel

    def __del__(self):
        try:
            if self.Timer is not None:
                self.Timer.cancel()
        except AttributeError:
            pass

    def startTimer(self, refresh=False):
        seconds = int(config.plugins.MetrixWeather.refreshInterval.value) * 60

        if seconds < 60:
            seconds = 300

        if refresh:
            if self.refreshcnt >= 6:
                self.refreshcnt = 0
                seconds = 300
            else:
                seconds = 10

        if self.Timer:
            self.Timer.cancel()
            self.Timer = None

        self.Timer = Timer(seconds, self.getWeather)
        self.Timer.start()

    def onShow(self):
        self.text = config.plugins.MetrixWeather.currentWeatherCode.value

    def getWeather(self):
        self.startTimer()

        # skip if weather-widget is disabled
        if config.plugins.MetrixWeather.enabled.getValue() is False:
            config.plugins.MetrixWeather.currentWeatherDataValid.value = False
            return

        global g_updateRunning
        if g_updateRunning:
            print "MetrixHDWeatherStandalone lookup for ID " + str(self.woeid) + " skipped, allready running..."
            return
        g_updateRunning = True
        Thread(target = self.getWeatherThread).start()

    def getWeatherThread(self):
        global g_updateRunning
        print "MetrixHDWeatherStandalone lookup for ID " + str(self.woeid)
        url = "http://query.yahooapis.com/v1/public/yql?q=select%20item%20from%20weather.forecast%20where%20woeid%3D%22"+str(self.woeid)+"%22&format=xml"
        #url = "http://query.yahooapis.com/v1/public/yql?q=select%20item%20from%20weather.forecast%20where%20woeid%3D%22"+str(self.woeid)+"%22%20u%3Dc&format=xml"

        # where location in (select id from weather.search where query="oslo, norway")
        try:
            file = urllib2.urlopen(url, timeout=2)
            data = file.read()
            file.close()
        except Exception as error:
            print "Cant get weather data: %r" % error

            # cancel weather function
            config.plugins.MetrixWeather.currentWeatherDataValid.value = False
            g_updateRunning = False
            return


        dom = parseString(data)
        try:
            title = self.getText(dom.getElementsByTagName('title')[0].childNodes)
        except IndexError as error:
            print "Cant get weather data: %r" % error
            g_updateRunning = False
            self.startTimer(True,30)
            if self.check:
                #text = "%s\n%s|" % (str(error),data)
                text = "%s|" % str(error)
                self.writeCheckFile(text)
            return

        config.plugins.MetrixWeather.currentLocation.value = str(title).split(',')[0].replace("Conditions for ","")

        currentWeather = dom.getElementsByTagName('yweather:condition')[0]
        #check returned date from weather values
        t=time()
        lastday = strftime("%d %b %Y", localtime(t-3600*24)).strip("0")
        currday = strftime("%d %b %Y", localtime(t)).strip("0")
        currentWeatherDate = currentWeather.getAttributeNode('date').nodeValue
        #if not (currday in currentWeatherDate or lastday in currentWeatherDate):
            # print "MetrixHDWeatherStandalone - get weather data failed. (current date = %s, returned date = %s)" %(currday, currentWeatherDate)
        #    config.plugins.MetrixWeather.currentWeatherDataValid.value = False
        #    g_updateRunning = False
        #    self.refreshcnt += 1
        #    self.startTimer(True)
        #    return
        # print "MetrixHDWeatherStandalone - get weather data successful. (current date = %s, returned date = %s)" %(currday, currentWeatherDate)
        config.plugins.MetrixWeather.currentWeatherDataValid.value = True
        currentWeatherCode = currentWeather.getAttributeNode('code')
        config.plugins.MetrixWeather.currentWeatherCode.value = self.ConvertCondition(currentWeatherCode.nodeValue)
        currentWeatherTemp = currentWeather.getAttributeNode('temp')
        config.plugins.MetrixWeather.currentWeatherTemp.value = self.getTemp(currentWeatherTemp.nodeValue)
        currentWeatherText = currentWeather.getAttributeNode('text')
        config.plugins.MetrixWeather.currentWeatherText.value = currentWeatherText.nodeValue

        n = 0
        currentWeather = dom.getElementsByTagName('yweather:forecast')[n]
        if lastday in currentWeather.getAttributeNode('date').nodeValue and currday in currentWeatherDate:
            n = 1
            currentWeather = dom.getElementsByTagName('yweather:forecast')[n]
        currentWeatherCode = currentWeather.getAttributeNode('code')
        config.plugins.MetrixWeather.forecastTodayCode.value = self.ConvertCondition(currentWeatherCode.nodeValue)
        currentWeatherTemp = currentWeather.getAttributeNode('high')
        config.plugins.MetrixWeather.forecastTodayTempMax.value = self.getTemp(currentWeatherTemp.nodeValue)
        currentWeatherTemp = currentWeather.getAttributeNode('low')
        config.plugins.MetrixWeather.forecastTodayTempMin.value = self.getTemp(currentWeatherTemp.nodeValue)
        currentWeatherText = currentWeather.getAttributeNode('text')
        config.plugins.MetrixWeather.forecastTodayText.value = currentWeatherText.nodeValue

        currentWeather = dom.getElementsByTagName('yweather:forecast')[n + 1]
        currentWeatherCode = currentWeather.getAttributeNode('code')
        config.plugins.MetrixWeather.forecastTomorrowCode.value = self.ConvertCondition(currentWeatherCode.nodeValue)
        currentWeatherTemp = currentWeather.getAttributeNode('high')
        config.plugins.MetrixWeather.forecastTomorrowTempMax.value = self.getTemp(currentWeatherTemp.nodeValue)
        currentWeatherTemp = currentWeather.getAttributeNode('low')
        config.plugins.MetrixWeather.forecastTomorrowTempMin.value = self.getTemp(currentWeatherTemp.nodeValue)
        currentWeatherText = currentWeather.getAttributeNode('text')
        config.plugins.MetrixWeather.forecastTomorrowText.value = currentWeatherText.nodeValue

        config.plugins.MetrixWeather.save()
        g_updateRunning = False
        self.refreshcnt = 0

    def getText(self,nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)

    def ConvertCondition(self, c):
        c = int(c)
        condition = "("
        if c == 0 or c == 1 or c == 2:
            condition = "S"
        elif c == 3 or c == 4:
            condition = "Z"
        elif c == 5  or c == 6 or c == 7 or c == 18:
            condition = "U"
        elif c == 8 or c == 10 or c == 25:
            condition = "G"
        elif c == 9:
            condition = "Q"
        elif c == 11 or c == 12 or c == 40:
            condition = "R"
        elif c == 13 or c == 14 or c == 15 or c == 16 or c == 41 or c == 46 or c == 42 or c == 43:
            condition = "W"
        elif c == 17 or c == 35:
            condition = "X"
        elif c == 19:
            condition = "F"
        elif c == 20 or c == 21 or c == 22:
            condition = "L"
        elif c == 23 or c == 24:
            condition = "S"
        elif c == 26 or c == 44:
            condition = "N"
        elif c == 27 or c == 29:
            condition = "I"
        elif c == 28 or c == 30:
            condition = "H"
        elif c == 31 or c == 33:
            condition = "C"
        elif c == 32 or c == 34:
            condition = "B"
        elif c == 36:
            condition = "B"
        elif c == 37 or c == 38 or c == 39 or c == 45 or c == 47:
            condition = "0"
        else:
            condition = ")"
        return str(condition)

    def getTemp(self,temp):
        if config.plugins.MetrixWeather.tempUnit.value == "Fahrenheit":
            return str(int(round(float(temp),0)))
        else:
            celsius = (float(temp) - 32 ) * 5 / 9
            return str(int(round(float(celsius),0)))
