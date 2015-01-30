# -*- coding: utf-8 -*-
# ThinkTV PBS XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.thinktv')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

qp  = urllib.quote_plus
uqp = urllib.unquote_plus

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def cleanname(name):    
    return name.replace('&apos;',"'").replace('&#8217;',"'").replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"')

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge


USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, user_data=None, headers = defaultHeaders ):
              log("getRequest URL:"+str(url))
              req = urllib2.Request(url.encode(UTF8), user_data, headers)

              try:
                 response = urllib2.urlopen(req)
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()
              except:
                 link1 = ""

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
              url = '0ABCDEFGHIJKLMNOPQRSTUVWXYZ'
              dolist = [('GA', 30012), ('GZ', 30013), ('GQ', 30014)]
              for mode, gstr in dolist:
                  name = __language__(gstr)
                  liz  = xbmcgui.ListItem(name,'',icon,icon)
                  xbmcplugin.addDirectoryItem(int(sys.argv[1]), '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), mode), liz, True)


def getQuery(cat_url):
        keyb = xbmc.Keyboard('', __addonname__)
        keyb.doModal()
        if (keyb.isConfirmed()):
              qurl = qp('/search/?q=%s' % (keyb.getText()))
              getCats(qurl, '')

def showAtoZ(azurl):
        ilist = []
        for a in azurl:
              name = a
              plot = ''
              url  = a
              mode = 'GA'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

                
def getAtoZ(gzurl):
              ilist = []
              azheaders = defaultHeaders
              azheaders['X-Requested-With'] = 'XMLHttpRequest'
              pg = getRequest('http://video.pbs.org/programs/list',None, azheaders)
              a = json.loads(pg)
              for y in gzurl:
                try:
                  b = a[y]
                  for x in b:
                     fullname = cleanname('%s [%s]' %(x['title'], x['video_count'])).encode(UTF8)
                     name = cleanname(x['title']).encode(UTF8)
                     plot = cleanname(x['producer']).encode(UTF8)
                     url = ('program/%s' % (x['slug'])).encode(UTF8)
                     mode = 'GV'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                     liz=xbmcgui.ListItem(fullname, '','DefaultFolder.png', icon)
                     liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                     ilist.append((u, liz, True))
                except:
                  pass
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

def getVids(gvurl,catname):
              gvurl = uqp(gvurl)
              pg = getRequest('http://video.pbs.org/%s' % (gvurl))
              dolist = [('episodes','<h2>Full Episodes',30020), ('shorts','<h2>Clips', 30021), ('previews', '<h2>Previews', 30022)]
              for gtype, gfind, gindex in dolist:
                if gfind in pg:
                  url = '%s/%s/' % (gvurl, gtype)
                  name = __language__(gindex)
                  mode = 'GC'
                  liz  = xbmcgui.ListItem(name,'',icon,icon)
                  liz.setInfo( 'Video', { "Title": catname, "Plot": name })
                  xbmcplugin.addDirectoryItem(int(sys.argv[1]), '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), catname, mode), liz, True)


def getCats(gcurl, catname):
              ilist = []
              gcurl = uqp(gcurl)
              if 'search/?q=' in gcurl:
                chsplit = '&'
                gcurl = gcurl.replace(' ','+')
              else:
                chsplit = '?'
              pg = getRequest('http://video.pbs.org/%s' % (gcurl))
              epis = re.compile('<li class="videoItem".+?data-videoid="(.+?)".+?data-title="(.+?)".+?src="(.+?)".+?class="description">(.+?)<(.+?)</li>').findall(pg)
              for url,name,img,desc,dur in epis:
                     if 'class="duration"' in dur:
                        dur = re.compile('<p class="duration">(.+?)</p>').search(dur).group(1)
                        dur = dur.strip()
                     else:
                        dur = ''
                     name = cleanname(name).encode(UTF8)
                     plot = cleanname(desc).encode(UTF8)
                     mode = 'GS'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                     liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Studio" : catname, "Plot": plot, "Duration": dur})
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))
              try:
                  nps = re.compile('visiblePage"><a href="(.+?)">(.+?)<').findall(pg)
                  (url, name) = nps[len(nps)-1]
                  if name == 'Next':
                     url = url.split(chsplit,1)[1]
                     url = qp(gcurl.split(chsplit,1)[0]+chsplit+url)
                     name = '[COLOR blue]%s[/COLOR]' % name
                     plot = name
                     mode = 'GC'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                     liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
                     liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                     ilist.append((u, liz, True))
              except:
                  pass
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getShow(gsurl):
              pg = getRequest('http://video.pbs.org/videoInfo/%s/?format=json' % (uqp(gsurl)))
              url = json.loads(pg)['recommended_encoding']['url']
              pg = getRequest('%s?format=json' % url)
              url = json.loads(pg)['url']
              if '.m3u8' in url:
                 try:
                   url = url.split('hls-64-800k',1)[0]
                   url += 'hls-2500k.m3u8'
                 except:
                   pass
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))


# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
       parms[key] = demunge(parms[key])
except:
    parms = {}

p = parms.get

mode = p('mode',None)

if mode==  None:  getSources(p('fanart'))
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='GA':  getAtoZ(p('url'))
elif mode=='GQ':  getQuery(p('url'))
elif mode=='GZ':  showAtoZ(p('url'))
elif mode=='GS':  getShow(p('url'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GV':  getVids(p('url'),p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

