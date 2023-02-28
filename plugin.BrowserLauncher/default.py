#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib.parse
import sys
import re
import os
import subprocess
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs

__addon_id__ = 'plugin.BrowserLauncher'
__Addon = xbmcaddon.Addon(__addon_id__)
def XlationStr(string_id):
    return __Addon.getLocalizedString(string_id)
    
addon = xbmcaddon.Addon()
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
addonPath = addon.getAddonInfo('path')
useOwnProfile = addon.getSetting("useOwnProfile") == "true"
useCustomPath = addon.getSetting("useCustomPath") == "true"
customPath = xbmcvfs.translatePath(addon.getSetting("customPath"))
winBrowser = int(addon.getSetting("winBrowser"))
#prio_values = ['LOW', 'BELOWNORMAL', 'NORMAL', 'ABOVENORMAL', 'HIGH', 'REALTIME' ]
prio_values = [ 0x00000040, 0x00004000, 0x00000020, 0x00008000, 0x00000080, 0x00000100 ]
priority = prio_values[int(addon.getSetting("priority"))]
userDataFolder = xbmcvfs.translatePath("special://profile/addon_data/"+addonID)
profileFolder = os.path.join(userDataFolder, 'profile')
siteFolder = os.path.join(userDataFolder, 'sites')
avBrowsers = ['Standard', 'Internet Explorer', 'Kylo', 'Chrome', 'Firefox', 'Opera']
Dialog = xbmcgui.Dialog()

if not os.path.isdir(userDataFolder):
    os.mkdir(userDataFolder)
if not os.path.isdir(profileFolder):
    os.mkdir(profileFolder)
if not os.path.isdir(siteFolder):
    os.mkdir(siteFolder)

youtubeUrl = "http://www.youtube.com/leanback"
vimeoUrl = "http://www.vimeo.com/couchmode"

bPath = ['C:\\Program Files\\Internet Explorer\\iexplore.exe',
         'C:\\Program Files\\Hillcrest Labs\\Kylo\\Kylo.exe',
         'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
         'C:\\Program Files\\Mozilla Firefox\\firefox.exe',
         'C:\\Program Files\\Opera\opera.exe']
bKiosk = ['-k ', '', '--kiosk ', '', '-fullscreen ']
bProfile = ['', '', '--user-data-dir=', '-profile ', '-pd ']
bAgent = ['', '', '--user-agent=', '', '']
bExtra = ['',
          '', 
          '--start-maximized --disable-translate --disable-new-tab-first-run --no-default-browser-check --no-first-run ',
          '',
          '']

def index():
    files = os.listdir(siteFolder)
    for file in files:
        if file.endswith(".link"):
            fh = open(os.path.join(siteFolder, file), 'r')
            title = ""
            url = ""
            thumb = ""
            kiosk = "yes"
            stopPlayback = "no"
            custBrowser = ""
            userAgent = ""
            for line in fh.readlines():
                entry = line[:line.find("=")]
                content = line[line.find("=")+1:]
                if entry == "title":
                    title = content.strip()
                elif entry == "url":
                    url = content.strip()
                elif entry == "thumb":
                    thumb = content.strip()
                elif entry == "kiosk":
                    kiosk = content.strip()
                elif entry == "stopPlayback":
                    stopPlayback = content.strip()
                elif entry == "custBrowser":
                    custBrowser = content.strip()
                elif entry == "userAgent":
                    userAgent = content.strip()
            fh.close()
            addSiteDir(title, url, 'showSite', os.path.join(siteFolder,thumb), stopPlayback, kiosk, custBrowser, userAgent)
    addDir("[B]- "+XlationStr(30001)+"[/B]", "", 'addSite', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def addSite(site="", title=""):
    if site:
        filename = getFileName(title)
        content = "title="+title+"\nurl="+site+"\nthumb=DefaultFolder.png\nstopPlayback=no\nkiosk=yes\ncustBrowser=\nuserAgent="
        fh = open(os.path.join(siteFolder, filename+".link"), 'w')
        fh.write(content)
        fh.close()
    else:
        keyboard = xbmc.Keyboard('', XlationStr(30003))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            title = keyboard.getText()
            keyboard = xbmc.Keyboard('https://', XlationStr(30004))
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                url = keyboard.getText()
                keyboard = xbmc.Keyboard('yes', XlationStr(30009))
                keyboard.doModal()
                if keyboard.isConfirmed() and keyboard.getText():
                    stopPlayback = keyboard.getText()
                    keyboard = xbmc.Keyboard('yes', XlationStr(30016))
                    keyboard.doModal()
                    if keyboard.isConfirmed() and keyboard.getText():
                        kiosk = keyboard.getText()
                        custBrowser = Dialog.select(XlationStr(30017), avBrowsers)
                        if custBrowser > -1:
                            content = "title=%s\nurl=%s\nthumb=DefaultFolder.png\nstopPlayback=%s\nkiosk=%s\nuserAgent=" % (title, url, stopPlayback, kiosk)
                            if custBrowser > 0: content += "\ncustBrowser=%s" % (custBrowser-1)
                            fh = open(os.path.join(siteFolder, getFileName(title)+".link"), 'w')
                            fh.write(content)
                            fh.close()
    xbmc.executebuiltin("Container.Refresh")


def getFileName(title):
    return (''.join(c for c in title if c not in '/\\:?"*|<>')).strip()


def getFullPath(path, url, useKiosk, userAgent, selBrowser):
    profile = ""
    if (useOwnProfile) and (bProfile[selBrowser]):
        profile = bProfile[selBrowser]+'"'+os.path.join(profileFolder,str(selBrowser))+'" '
    kiosk = ""
    if (useKiosk=="yes") and (bKiosk[selBrowser]):
        kiosk = bKiosk[selBrowser]
    if (userAgent) and (bAgent[selBrowser]):
        userAgent = bAgent[selBrowser]+'"'+userAgent+'" '
    return '"'+path+'" '+profile+userAgent+bExtra[selBrowser]+kiosk+'"'+url+'"'


def showSite(url, stopPlayback, kiosk, userAgent, custBrowser):
    if stopPlayback == "yes": xbmc.Player().stop()
    selBrowser = winBrowser
    if custBrowser: selBrowser = int(custBrowser)
    path = bPath[selBrowser]
    fullUrl = False
    path86 = path.replace("\\Program Files\\", "\\Program Files (x86)\\")
    if useCustomPath and os.path.exists(customPath) and not custBrowser:
        fullUrl = getFullPath(customPath, url, kiosk, userAgent, selBrowser)
    elif os.path.exists(path):
        fullUrl = getFullPath(path, url, kiosk, userAgent, selBrowser)
    elif os.path.exists(path86):
        fullUrl = getFullPath(path86, url, kiosk, userAgent, selBrowser)
    if fullUrl:
        print (fullUrl)
        if xbmc.getCondVisibility('system.platform.windows'):
            subprocess.Popen(fullUrl, creationflags=priority)
        else:
            subprocess.Popen(fullUrl, shell=True)
    else:
        xbmc.executebuiltin('XBMC.Notification(Info:,'+str(XlationStr(30005))+'!,5000)')
        addon.openSettings()

def removeSite(title):
    os.remove(os.path.join(siteFolder, getFileName(title)+".link"))
    xbmc.executebuiltin("Container.Refresh")


def editSite(title):
    filenameOld = getFileName(title)
    file = os.path.join(siteFolder, filenameOld+".link")
    fh = open(file, 'r')
    title = ""
    url = ""
    kiosk = "yes"
    thumb = "DefaultFolder.png"
    stopPlayback = "no"
    custBrowser = ""
    for line in fh.readlines():
        entry = line[:line.find("=")]
        content = line[line.find("=")+1:]
        if entry == "title":
            title = content.strip()
        elif entry == "url":
            url = content.strip()
        elif entry == "kiosk":
            kiosk = content.strip()
        elif entry == "thumb":
            thumb = content.strip()
        elif entry == "stopPlayback":
            stopPlayback = content.strip()
        elif entry == "custBrowser":
            custBrowser = content.strip()
        elif entry == "userAgent":
            userAgent = content.strip()
    fh.close()

    oldTitle = title
    keyboard = xbmc.Keyboard(title, XlationStr(30003))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        title = keyboard.getText()
        keyboard = xbmc.Keyboard(url, XlationStr(30004))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            url = keyboard.getText()
            keyboard = xbmc.Keyboard(stopPlayback, XlationStr(30009))
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                stopPlayback = keyboard.getText()
                keyboard = xbmc.Keyboard(kiosk, XlationStr(30016))
                keyboard.doModal()
                if keyboard.isConfirmed() and keyboard.getText():
                    kiosk = keyboard.getText()
                    custBrowser = Dialog.select(XlationStr(30017), avBrowsers)
                    if custBrowser > -1:
                        content = "title="+title+"\nurl="+url+"\nthumb="+thumb+"\nstopPlayback="+stopPlayback+"\nkiosk="+kiosk+"\nuserAgent="+userAgent
                        if custBrowser > 0: content += "\ncustBrowser=%s" % (custBrowser-1)
                        fh = open(os.path.join(siteFolder, getFileName(title)+".link"), 'w')
                        fh.write(content)
                        fh.close()
                        if title != oldTitle:
                            os.remove(os.path.join(siteFolder, filenameOld+".link"))
    xbmc.executebuiltin("Container.Refresh")


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addDir(name, url, mode, iconimage, stopPlayback="", kiosk="", custBrowser="", userAgent=""):
    u = sys.argv[0]+"?url="+urllib.parse.quote_plus(url)+"&mode="+urllib.parse.quote_plus(mode)+"&stopPlayback="+urllib.parse.quote_plus(stopPlayback)+"&kiosk="+urllib.parse.quote_plus(kiosk)+"&custBrowser="+urllib.parse.quote_plus(custBrowser)+"&userAgent="+urllib.parse.quote_plus(userAgent)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon':'DefaultFolder.png', 'thumb':iconimage})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    return ok


def addSiteDir(name, url, mode, iconimage, stopPlayback, kiosk, custBrowser, userAgent):
    u = sys.argv[0]+"?url="+urllib.parse.quote_plus(url)+"&mode="+urllib.parse.quote_plus(mode)+"&stopPlayback="+urllib.parse.quote_plus(stopPlayback)+"&kiosk="+urllib.parse.quote_plus(kiosk)+"&custBrowser="+urllib.parse.quote_plus(custBrowser)+"&userAgent="+urllib.parse.quote_plus(userAgent)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon':'DefaultFolder.png', 'thumb':iconimage})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.addContextMenuItems([(XlationStr(30006), 'RunPlugin(plugin://'+addonID+'/?mode=editSite&url='+urllib.parse.quote_plus(name)+')',), (XlationStr(30002), 'RunPlugin(plugin://'+addonID+'/?mode=removeSite&url='+urllib.parse.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.parse.unquote_plus(params.get('mode', ''))
name = urllib.parse.unquote_plus(params.get('name', ''))
url = urllib.parse.unquote_plus(params.get('url', ''))
stopPlayback = urllib.parse.unquote_plus(params.get('stopPlayback', 'yes'))
kiosk = urllib.parse.unquote_plus(params.get('kiosk', 'yes'))
userAgent = urllib.parse.unquote_plus(params.get('userAgent', ''))
custBrowser = urllib.parse.unquote_plus(params.get('custBrowser', ''))

if mode == 'addSite':
    addSite()
elif mode == 'showSite':
    showSite(url, stopPlayback, kiosk, userAgent, custBrowser)
elif mode == 'removeSite':
    removeSite(url)
elif mode == 'editSite':
    editSite(url)
else:
    index()
