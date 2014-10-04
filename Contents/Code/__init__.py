
TITLE    = 'RSS Feeds'
PREFIX   = '/video/rssfeeds'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'
SHOW_DATA = 'rssdata.json'
NAMESPACES = {'feedburner': 'http://rssnamespace.org/feedburner/ext/1.0'}
NAMESPACES2 = {'media': 'http://search.yahoo.com/mrss/'}
NAMESPACE_SMIL = {'smil': 'http://www.w3.org/2005/SMIL21/Language'}

http = 'http:'

###################################################################################################
# Set up containers for all possible objects
def Start():

  ObjectContainer.title1 = TITLE
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON)
  VideoClipObject.thumb = R(ICON)
  
  HTTP.CacheTime = CACHE_1HOUR 

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
  oc.add(DirectoryObject(key=Callback(SectionTools, title="Channel Tools"), title="Channel Tools", thumb=R('icon-feed.png'), summary="Click here to for reset options, extras and special instructions"))

  return oc
#######################################################################################################################
# This is the section for system settings
@route(PREFIX + '/sectiontools')
def SectionTools (title):

  oc = ObjectContainer(title2=title)
  oc.add(DirectoryObject(key=Callback(RokuUsers, title="Special Instructions for Roku Users"), title="Special Instructions for Roku Users", summary="Click here to see special instructions necessary for Roku Users to add feeds to this channel"))
  oc.add(DirectoryObject(key=Callback(ResetShows, title="Reset RSS Feeds"), title="Reset RSS Feeds", thumb=R('feed-back.png'), summary="Click here to reset your RSS feed list back to the original default list from the JSON data file"))

  return oc

########################################################################################################################
# this is special instructions for Roku users
@route(PREFIX + '/rokuusers')
def RokuUsers (title):
  return ObjectContainer(header="Special Instructions for Roku Users", message="Adding the URL for feeds is made much easier with the Remoku (www.remoku.tv) WARNING: DO NOT DIRECTLY TYPE OR PASTE THE URL IN THE ADD FEEDS SECTION USING ROKU PLEX CHANNELS 2.6.4. THAT VERSION USES A SEARCH INSTEAD OF ENTRY SCREEN AND EVERY LETTER OF THE URL YOU ENTER WILL PRODUCE IN AN INVALID FEED ICON.")

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
        oc.add(DirectoryObject(key=Callback(ShowRSS, title=title, url=url, show_type=show_type, thumb=thumb), title=title, summary=description, thumb=thumb))
      except:
        oc.add(DirectoryObject(key=Callback(URLError, url=url), title="Invalid or Incompatible URL", thumb=R('no-feed.png'), summary="The URL was either entered incorrectly or is incompatible with this channel."))
    else:
      i+=1

  oc.objects.sort(key = lambda obj: obj.title)

  oc.add(InputDirectoryObject(key=Callback(AddShow, show_type=show_type), title="Add A RSS Feed", thumb=R('feed-add.png'), summary="Click here to add a new RSS Feed", prompt="Enter the full URL (including http://) for the RSS Feed you would like to add"))

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no RSS feeds to list right now.")
  else:
    return oc
########################################################################################################################
# This is for producing items in a RSS Feeds.  We try to make most things optional so it accepts the most feed formats
# But each feed must have a title, date, and either a link or media_url
@route(PREFIX + '/showrss')
def ShowRSS(title, url, show_type, thumb):

# The ProduceRSS try above tells us if the RSS feed is the correct format. so we do not need to put this function's data pull in a try/except
  oc = ObjectContainer(title2=title)
  feed_title = title
  xml = XML.ElementFromURL(url)
  for item in xml.xpath('//item'):
  
    # All Items must have a title
    title = item.xpath('./title//text()')[0]
    
    # Try to pull the link for the item
    try:
      link = item.xpath('./link//text()')[0]
    except:
      link = None
    # The link is not needed since these have a media url, but there may be a feedburner feed that has a Plex URL service
    try:
      new_url = item.xpath('./feedburner:origLink//text()', namespaces=NAMESPACES)[0]
      link = new_url
    except:
      pass
    if link and link.startswith('https://archive.org/'):
      # With Archive.org there is an issue where it is using https instead of http sometimes for the links and media urls
      # and when this happens it causes errors so we have to check those urls here and change them
      link = link.replace('https://', 'http://')
    # Test the link for a URL service
    if link:
      url_test = URLTest(link)
    else:
      url_test = 'false'
    # Feeds from archive.org load faster using the CreateObject() function versus the URL service.
    # Using CreateObject for Archive.org also catches items with no media and allows for feed that may contain both audio and video items
    # If archive.org is sent to URL service, adding #video to the end of the link makes it load faster
    if link and 'archive.org' in link:
      url_test = 'false'
      
    # Try to pull media url for item
    if url_test == 'false':
    # We try to pull the enclosure or the highest bitrate media:content. If no bitrate, the first one is taken.
    # There is too much variety in the way quality is specified to pull all and give quality options
    # This code can be added to only return media of type audio or video - [contains(@type,"video") or contains(@type,"audio")]
      try:
        # So first get the first media url and media type in case there are not multiples it will not go through the loop
        media_url = item.xpath('.//media:content/@url', namespaces=NAMESPACES2)[0]
        media_type = item.xpath('.//media:content/@type', namespaces=NAMESPACES2)[0]
        # Get a list of medias
        medias = item.xpath('.//media:content', namespaces=NAMESPACES2)
        bitrate = 0
        for media in medias:
          try: new_bitrate = int(media.get('bitrate', default=0))
          except: new_bitrate = 0
          if new_bitrate > bitrate:
            bitrate = new_bitrate
            media_url = media.get('url')
            #Log("taking media url %s with bitrate %s"  %(media_url, str(bitrate)))
            media_type = media.get('type')
      except:
        try:
          media_url = item.xpath('.//enclosure/@url')[0]
          media_type = item.xpath('.//enclosure/@type')[0]
        except:
          Log("no media:content objects found in bitrate check")
          media_url = None
    else:
      # If the URL test was positive we do not need a media_url
      media_url = None

    #Log("the value of media url is %s" %media_url)
    # With Archive.org there is an issue where it is using https instead of http sometimes for the media urls
    # and when this happens it causes errors so we have to check those urls here and change them
    if media_url and media_url.startswith('https://archive.org/'):
      media_url = media_url.replace('https://', 'http://')

    # theplatform stream links are SMIL, despite being referenced in RSS as the underlying mediatype
    if media_url and 'link.theplatform.com' in media_url:
      smil = XML.ElementFromURL(media_url)
      try:
        media_url = smil.xpath('//smil:video/@src', namespaces=NAMESPACE_SMIL)[0]
      except Exception as e:
        Log("Found theplatform.com link, but couldn't resolve stream: " + str(e))
        media_url = None

    
    # If there in not a url service or media_url produced No URL service object and go to next entry
    if url_test == 'false' and not media_url:
      Log('The url test failed and returned a value of %s' %url_test)
      oc.add(DirectoryObject(key=Callback(URLNoService, title=title),title="No URL Service or Media Files for Video", thumb=R('no-feed.png'), summary='There is not a Plex URL service or link to media files for %s.' %title))
      continue
    
    else: 
    # Collect all other optionnal data for item
      try:
        date = item.xpath('./pubDate//text()')[0]
      except:
        date = None
      try:
        item_thumb = item.xpath('./media:thumbnail//@url', namespaces=NAMESPACES2)[0]
      except:
        item_thumb = None
      try:
        # The description actually contains pubdate, link with thumb and description so we need to break it up
        epDesc = item.xpath('./description//text()')[0]
        (summary, new_thumb) = SummaryFind(epDesc)
        if new_thumb:
          item_thumb = new_thumb
      except:
        summary = None
      # Not having a value for the summary causes issues
      if not summary:
        summary = 'no summary'
      if item_thumb:
        thumb = item_thumb

      if url_test == 'true':
        # Build Video or Audio Object for those with a URL service
        # The date that go to the CreateObject() have to be processed separately so only process those with a URL service here
        if date:
          date = Datetime.ParseDate(date)
        if show_type == 'video':
          oc.add(VideoClipObject(
            url = link, 
            title = title, 
            summary = summary, 
            thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=ICON), 
            originally_available_at = date
          ))
        else:
          # I was told it was safest to use an album object and not a track object here since not sure what we may encounter
          # But was getting errors with an AlbumObject so using TrackObject instead
          # NEED TO TEST THIS WITH AN AUDIO SITE THAT HAS A URL SERVICE
          oc.add(TrackObject(
            url = link, 
            title = title, 
            summary = summary, 
            thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=ICON), 
            originally_available_at = date
          ))
        oc.objects.sort(key = lambda obj: obj.originally_available_at, reverse=True)
      else:
        # Send those that have a media_url to the CreateObject function to build the media objects
        oc.add(CreateObject(url=media_url, media_type=media_type, title=title, summary = summary, originally_available_at = date, thumb=thumb))

  # Additional directories for deleting a show and adding images for a show
  oc.add(DirectoryObject(key=Callback(DeleteShow, url=url, title=feed_title), title="Delete %s" %feed_title, thumb=R('delete.png'), summary="Click here to delete this feed"))
  oc.add(InputDirectoryObject(key=Callback(AddImage, title=feed_title, show_type='video', url=url), title="Add Image For %s" %feed_title, thumb=R('img-add.png'), summary="Click here to add an image url for this feed", prompt="Enter the full URL (including http://) for the image you would like displayed for this RSS Feed"))

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no videos to display for this RSS feed right now.")      
  else:
    return oc

####################################################################################################
# This function creates an object container for RSS feeds that have a media file in the feed
@route(PREFIX + '/createobject')
def CreateObject(url, media_type, title, originally_available_at, thumb, summary, include_container=False):

  local_url=url.split('?')[0]
  audio_codec = AudioCodec.AAC
  # Since we want to make the date optional, we need to handle the Datetime.ParseDate() as a try in case it is already done or blank
  try:
    originally_available_at = Datetime.ParseDate(originally_available_at)
  except:
    pass
  if local_url.endswith('.mp3'):
    container = 'mp3'
    audio_codec = AudioCodec.MP3
  elif  local_url.endswith('.m4a') or local_url.endswith('.mp4') or local_url.endswith('MPEG4') or local_url.endswith('h.264'):
    container = Container.MP4
  elif local_url.endswith('.flv') or local_url.endswith('Flash+Video'):
    container = Container.FLV
  elif local_url.endswith('.mkv'):
    container = Container.MKV
  else:
    Log('container type is None')
    container = ''

  if 'audio' in media_type:
    # This gives errors with AlbumObject, so it has to be a TrackObject
    object_type = TrackObject
  elif 'video' in media_type:
    object_type = VideoClipObject
  else:
    Log('This media type is not supported')
    new_object = DirectoryObject(key=Callback(URLUnsupported, url=url, title=title), title="Media Type Not Supported", thumb=R('no-feed.png'), summary='The file %s is not a type currently supported by this channel' %url)
    return new_object
    
  new_object = object_type(
    key = Callback(CreateObject, url=url, media_type=media_type, title=title, summary=summary, originally_available_at=originally_available_at, thumb=thumb, include_container=True),
    rating_key = url,
    title = title,
    summary = summary,
    thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=ICON),
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
# THIS IS NOT BEING USED
@route(PREFIX + '/checkplaylist')
def CheckPlaylist(url):
  show_rss=''
  if url.find('playlist')  > -1:
    show_rss = 'play'
  else:
    show_rss = 'good'
  return show_rss

#############################################################################################################################
# The description actually contains pubdate, link with thumb and description so we need to break it up
@route(PREFIX + '/summaryfind')
def SummaryFind(epDesc):
  
  html = HTML.ElementFromString(epDesc)
  description = html.xpath('//p//text()')
  summary = ' '.join(description)
  if 'Tags:' in summary:
    summary = summary.split('Tags:')[0]
  try:
    item_thumb = html.cssselect('img')[0].get('src')
  except:
    item_thumb = None
  return (summary, item_thumb)

############################################################################################################################
# This is to test if there is a Plex URL service for  given url.  
#       if URLTest(url) == "true":
@route(PREFIX + '/urltest')
def URLTest(url):
  if URLService.ServiceIdentifierForURL(url) is not None:
    url_good = 'true'
  else:
    url_good = 'false'
  return url_good

############################################################################################################################
# This keeps a section of the feed from giving an error for the entire section if one of the URLs does not have a service or attached media
@route(PREFIX + '/urlnoservice')
def URLNoService(title):
  return ObjectContainer(header="Error", message='There is no Plex URL service or media file link for the %s feed entry. A Plex URL service or a link to media files in the feed entry is required for this channel to create playable media. If all entries for this feed give this error, you can use the Delete button shown at the end of the feed entry listings to remove this feed' %title)

############################################################################################################################
# This function creates an error message for feed entries that have an usupported media type and keeps a section of feeds from giving an error for the entire list of entries
@route(PREFIX + '/urlunsupported')
def URLUnsupported(url, title):
  oc = ObjectContainer()
  
  return ObjectContainer(header="Error", message='The media for the %s feed entry is of a type that is not supported. If you get this error with all entries for this feed, you can use the Delete option shown at the end of the feed entry listings to remove this feed from the channel' %title)

  return oc

############################################################################################################################
# This function creates a directory for incorectly entered urls and keeps a section of feeds from giving an error if one url is incorrectly entered
# Would like to allow for reentry of a bad url but for now, just allows for deletion. 
@route(PREFIX + '/urlerror')
def URLError(url):

  oc = ObjectContainer()
  
  oc.add(DirectoryObject(key=Callback(EditShow, url=url), title="Edit Feed"))

  oc.add(DirectoryObject(key=Callback(DeleteShow, title="Delete Feed", url=url), title="Delete Feed", thumb=R('delete.png'), summary="Delete this URL from your list of feeds"))

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
def DeleteShow(url, title):
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
    url = 'http://' + url
  # Checking for archive.org urls with https
  elif url.startswith('https://archive.org/') :
    url = url.replace('https://', 'http://')
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
