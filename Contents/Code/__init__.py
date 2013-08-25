
TITLE    = 'RSS Feeds'
PREFIX   = '/video/rssfeeds'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'
SHOW_DATA = 'rssdata.json'
NAMESPACES = {'feedburner': 'http://rssnamespace.org/feedburner/ext/1.0'}

http = 'http:'

###################################################################################################
# Set up containers for all possible objects
def Start():

  ObjectContainer.title1 = TITLE
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON)
  DirectoryObject.art = R(ART)
  EpisodeObject.thumb = R(ICON)
  EpisodeObject.art = R(ART)
  VideoClipObject.thumb = R(ICON)
  VideoClipObject.art = R(ART)
  
  #HTTP.CacheTime = CACHE_1HOUR 

  #This Checks to see if there is a list of feeds
  if Dict['MyShows'] == None:
  # HERE WE PULL IN THE JSON DATA IN TO POPULATE THIS DICT THE FIRST TIME THEY LOAD THE CHANNEL
  # THIS ALSO ALLOWS USERS TO REVERT BACK TO A DEFAULT LIST IF THERE ARE ISSUES
  # ALSO NEED THE 50 ENTRIES IN THE JSON DATA TO HOLD ADDITIONS SINCE FORMAT DOES NOT TRULY ALLOW ADDTION OF ENTRIES
    Dict["MyShows"] = LoadData()

  else:
    Log(Dict['MyShows'])

###################################################################################################
# This Main Menu provides a section for each type of feed. It is hardcoded in since the types of feed have to be set and preprogrammed in
@handler(PREFIX, TITLE, art=ART, thumb=ICON)

def MainMenu():

  oc = ObjectContainer()
  
  json_data = Resource.Load(SHOW_DATA)
  Dict["shows"] = JSON.ObjectFromString(json_data)
  
  oc.add(DirectoryObject(key=Callback(ProduceRss, title="RSS Video Feeds", show_type='video'), title="RSS Video Feeds"))
  oc.add(DirectoryObject(key=Callback(ProduceRss, title="RSS Audio Feeds", show_type='audio'), title="RSS Audio Feeds"))
  oc.add(DirectoryObject(key=Callback(SectionTools, title="Channel Tools"), title="Channel Tools", summary="Click here to for reset options, extras and special instructions"))

  return oc
#######################################################################################################################
# This is the section for system settings
@route(PREFIX + '/sectiontools')
def SectionTools (title):

  oc = ObjectContainer(title2=title)
  oc.add(DirectoryObject(key=Callback(RokuUsers, title="Special Instructions for Roku Users"), title="Special Instructions for Roku Users", summary="Click here to see special instructions necessary for Roku Users to add feeds to this channel"))
  oc.add(DirectoryObject(key=Callback(ResetShows, title="Reset RSS Feeds"), title="Reset RSS Feeds", summary="Click here to reset your RSS feed list back to the original default list from the JSON data file"))

  return oc

########################################################################################################################
# this is special instructions for Roku users
@route(PREFIX + '/rokuusers')
def RokuUsers (title):
  return ObjectContainer(header="Special Instructions for Roku Users", message="To add a new feed, Roku users must be using version 2.6.5 or higher of the Plex Roku Channel (currently requires using PlexTest channel). Also, adding the URL for feeds is made much easier with the Remoku (www.remoku.tv) WARNING: DO NOT DIRECTLY TYPE OR PASTE THE URL IN THE ADD FEEDS SECTION USING ROKU PLEX CHANNELS 2.6.4. THAT VERSION USES A SEARCH INSTEAD OF ENTRY SCREEN AND EVERY LETTER OF THE URL YOU ENTER WILL PRODUCE IN AN INVALID FEED ICON.")

#############################################################################################################################
# The FUNCTION below can be used to reload the original data.json file if errors occur and you need to reset the program
@route(PREFIX + '/resetshows')
def ResetShows(title):
  Dict["MyShows"] = LoadData()
  return ObjectContainer(header="Reset", message='The feeds have been set back to the default list of feeds available in the JSON file.')

###################################################################################################
# This Menu produces a list of feeds for each type of feed.
@route(PREFIX + '/producerss')
def ProduceRss(title, show_type):
  json_data = Resource.Load(SHOW_DATA)
  Dict["shows"] = JSON.ObjectFromString(json_data)

  oc = ObjectContainer(title2=title)
  i=1
  shows = Dict["MyShows"]
  for show in shows:
    if show[i]['type'] == show_type:
      url = show[i]["url"]
      thumb = show[i]["thumb"]
      i+=1
      try:
        rss_page = XML.ElementFromURL(url)
        title = rss_page.xpath("//channel/title//text()")[0]
        # sometimes the description is blank and it gives an error, so we added this as a try
        try:
          description = rss_page.xpath("//channel/description//text()")[0]
        except:
          description = ' '
        if not thumb:
          try:
            thumb = rss_page.xpath("//channel/image/url//text()")[0]
          except:
            thumb = R(ICON)
        oc.add(DirectoryObject(key=Callback(ShowRSS, title=title, url=url), title=title, summary=description, thumb=thumb))
      except:
        oc.add(DirectoryObject(key=Callback(URLError, url=url), title="Invalid or Incompatible URL", summary="The URL entered in the database was either incorrect or incompatible with this channel."))
    else:
      i+=1

  oc.objects.sort(key = lambda obj: obj.title)

  oc.add(InputDirectoryObject(key=Callback(AddShow, show_type=show_type), title="Add A RSS Feed", summary="Click here to add a new RSS Feed", prompt="Enter the full URL (including http://) for the RSS Feed you would like to add"))

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no RSS feeds to list right now.")
  else:
    return oc
########################################################################################################################
# This is for video RSS Feeds.  Seems to work with different RSS feeds
@route(PREFIX + '/showrss')
def ShowRSS(title, url):

# The ProduceRSS try above tells us if the RSS feed is the correct format. so we do not need to put this function's data pull in a try/except
  oc = ObjectContainer(title2=title)
  feed_title = title
  xml = XML.ElementFromURL(url)
  for item in xml.xpath('//item'):
    try:
      epUrl = item.xpath('./link//text()')[0]
    except:
      continue
    title = item.xpath('./title//text()')[0]
    date = Datetime.ParseDate(item.xpath('./pubDate//text()')[0])
    # The description actually contains pubdate, link with thumb and description so we need to break it up
    epDesc = item.xpath('./description//text()')[0]
    try:
      new_url = item.xpath('./feedburner:origLink//text()', namespaces=NAMESPACES)[0]
      Log('the value of new_url is %s' %new_url)
      epUrl = new_url
    except:
      pass
    html = HTML.ElementFromString(epDesc)
    els = list(html)
    try:
      thumb = html.cssselect('img')[0].get('src')
    except:
      thumb = R(ICON)

    summary = []

    for el in els:
      if el.tail: summary.append(el.tail)
	
    summary = '. '.join(summary)
    try:
      media_url = item.xpath('./enclosure//@url')[0]
    except:
      media_url = ''

    test = URLTest(epUrl)
    # Internet Archives RSS Feed sometimes have a mix of video and audio so best to use alternate function for it
    if test == 'true' and 'archive.org' not in url:
      oc.add(VideoClipObject(
        url = epUrl, 
        title = title, 
        summary = summary, 
        thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)), 
        originally_available_at = date
      ))
      oc.objects.sort(key = lambda obj: obj.originally_available_at, reverse=True)

    else:
      if media_url:
        oc.add(CreateObject(title=title, summary = summary, originally_available_at = date, url=media_url))
      else:
        Log('The url test failed and returned a value of %s' %test)
        oc.add(DirectoryObject(key=Callback(URLNoService, title=title),title="No URL Service or Media Files for Video", summary='There is not a Plex URL service or media files for %s.' %title))

  oc.add(DirectoryObject(key=Callback(DeleteShow, url=url, title=feed_title, show_type='video'), title="Delete %s" %feed_title, summary="Click here to delete this feed"))

  oc.add(InputDirectoryObject(key=Callback(AddImage, title=feed_title, show_type='video', url=url), title="Add Image For %s" %feed_title, summary="Click here to add an image url for this feed", prompt="Enter the full URL (including http://) for the image you would like displayed for this RSS Feed"))

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no videos to display for this RSS feed right now.")      
  else:
    return oc

####################################################################################################
# This function creates an object container for RSS feeds that have a media file in the feed
# Not sure what other types there may be to add. Should we put flac or ogg here? Are there containers for these and what are they?
@route(PREFIX + '/createobject')
def CreateObject(url, title, summary, originally_available_at, include_container=False):

  if url.endswith('.mp3'):
    container = 'mp3'
    audio_codec = AudioCodec.MP3
  elif  url.endswith('.m4a') or url.endswith('.mp4') or url.endswith('MPEG4') or url.endswith('h.264'):
    container = Container.MP4
    audio_codec = AudioCodec.AAC
  elif url.endswith('.flv') or url.endswith('Flash+Video'):
    container = Container.FLV
  elif url.endswith('.mkv'):
    container = Container.MKV

  if url.endswith('.mp3') or url.endswith('.m4a'):
    object_type = TrackObject
  elif url.endswith('.mp4') or url.endswith('MPEG4') or url.endswith('h.264') or url.endswith('.flv') or url.endswith('Flash+Video') or url.endswith('.mkv'):
    audio_codec = AudioCodec.AAC
    object_type = VideoClipObject
  else:
    Log('entered last else the value of url is %s' %url)
    new_object = DirectoryObject(key=Callback(URLNoService, title=title), title="Media Type Not Supported", summary='The video file %s is not a type currently supported by this channel' %url)
    return new_object

  new_object = object_type(
    key = Callback(CreateObject, url=url, title=title, summary=summary, originally_available_at=originally_available_at, include_container=True),
    rating_key = url,
    title = title,
    summary = summary,
    originally_available_at = originally_available_at,
    items = [
      MediaObject(
        parts = [
          PartObject(key=url)
            ],
            container = container,
            audio_codec = audio_codec,
            audio_channels = 2
      )
    ]
  )

  if include_container:
    return ObjectContainer(objects=[new_object])
  else:
    return new_object
#############################################################################################################################
# this checks to see if the RSS feed is a YouTube playlist. Currently this plugin does not work with YouTube Playlist
@route(PREFIX + '/checkplaylist')
def CheckPlaylist(url):
  show_rss=''
  if url.find('playlist')  > -1:
    show_rss = 'play'
  else:
    show_rss = 'good'
  return show_rss

############################################################################################################################
# This is to test if there is a Plex URL service for  given url.  
# Seems to return some RSS feeds as not having a service when they do, so currently unused and needs more testing
#       if URLTest(url) == "true":
@route(PREFIX + '/urltest')
def URLTest(url):
  if URLService.ServiceIdentifierForURL(url) is not None:
    url_good = 'true'
  else:
    url_good = 'false'
  return url_good

############################################################################################################################
# This keeps a section of the feed from giving an error for the entire section if one of the URLs does not have a service
@route(PREFIX + '/urlnoservice')
def URLNoService(title):
  return ObjectContainer(header="Error", message='There is no Plex URL service for the %s. A Plex URL service is required for RSS feeds to work. You can use the Delete Show button to remove this show' %title)

############################################################################################################################
# This function creates a directory for feeds that do not have a URL service and keeps a section of feeds from giving an error for the entire
# section if one of the URLs does not have a URL service and directs the user to delete the bad url
@route(PREFIX + '/urlunsupported')
def URLUnsupported(url):
  oc = ObjectContainer()
  
  oc.add(DirectoryObject(key=Callback(DeleteShow, title="Delete RSS Feed", url=url), title="Delete RSS Feed", summary="Delete this Unsupported URL from your list of feeds"))

  return oc

############################################################################################################################
# This function creates a directory for incorectly entered urls and keeps a section of feeds from giving an error if one url is incorrectly entered
# Would like to allow for reentry of a bad url but for now, just allows for deletion. 
@route(PREFIX + '/urlerror')
def URLError(url):

  oc = ObjectContainer()
  
  oc.add(DirectoryObject(key=Callback(EditShow, url=url), title="Edit Feed"))

  oc.add(DirectoryObject(key=Callback(DeleteShow, title="Delete Feed", url=url), title="Delete Feed", summary="Delete this URL from your list of feeds"))

  return oc

#############################################################################################################################
# Here we could possible and tell them to delete the url and try again
@route(PREFIX + '/editshow')
def EditShow(url):
  return ObjectContainer(header="Error", message='Unable to edit feed urls at this time. Please delete the url and try again')

############################################################################################################################
# This is a function to delete a feed from the json data file
# cannot just delete the entry or it will mess up the numbering and cause errors in the program.
# Instead we will make the entry blank and then check for reuse in the add function
@route(PREFIX + '/deleteshow')
def DeleteShow(url, title, show_type):
  i=1
  shows = Dict["MyShows"]
  for show in shows:
    if show[i]['url'] == url:
      show[i] = {"type":"", "url":"", "thumb":""}
      # once we find the feed to delete we need to break out of the for loop
      break
    else:
      i += 1
  # Then send a message
  return ObjectContainer(header=L('Deleted'), message=L('Your RSS feed has been deleted from the channel'))

#############################################################################################################################
# This is a function to add a feed to the json data file.  Wanted to make a true add but running into errors based on 
# the structure of my dictionary, so we created 50 items and just taking the first empty feed and filling it with
# the feed info
@route(PREFIX + '/addshow')
def AddShow(show_type, query, url=''):

  url = query
  # Checking to make sure http on the front
  if url.startswith('www'):
    url = http + '//' + url
  else:
    pass
  i=1

  shows = Dict["MyShows"]
  for show in shows:
    if show[i]['url'] == "":
      show[i]['type'] = show_type
      show[i]['url'] = url
      break
    else:
      i += 1
      if i > len(Dict['MyShows']):
        return ObjectContainer(header=L('Error'), message=L('Unable to add new feed. You have added the maximum amount of 50 feeds. Please delete a feed and try again'))
      else:
        pass

  return ObjectContainer(header=L('Added'), message=L('Your RSS feed has been added to the channel'))

#############################################################################################################################
# This is a function to add an url for an image to a feed.  
@route(PREFIX + '/addimage')
def AddImage(show_type, title, query, url=''):

  thumb = query
  # Checking to make sure http on the front
  if thumb.startswith('www'):
    thumb = http + '//' + thumb
  else:
    pass
  i=1

  shows = Dict["MyShows"]
  for show in shows:
    if show[i]['url'] == url:
      show[i]['thumb'] = thumb
      break
    else:
      i += 1
      if i > len(Dict['MyShows']):
        return ObjectContainer(header=L('Error'), message=L('Unable to add image for %s.' %title))
      else:
        pass

  return ObjectContainer(header=L('Added'), message=L('Your RSS feed image has been added to %s' %title))
#############################################################################################################################
# This function loads the json data file
@route(PREFIX + '/loaddata')
def LoadData():
  json_data = Resource.Load(SHOW_DATA)
  return JSON.ObjectFromString(json_data)
