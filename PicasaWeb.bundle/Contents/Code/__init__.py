'''
Created on May 03, 2009

@summary: A Plex Media Server plugin that integrates Google Picasa web albums into the Plex picture container.
@version: 0.2
@author: Ian.G
'''

# Import from Python

import socket
import datetime
from math import log, floor, pow

# Import the parts of the gdata API we need to talk to Picasa Web Albums

import gdata.photos.service
import gdata.media
import gdata.geo

# Gdata API settings

GDATA_PHOTO_SERVICE_CLIENT_NAME 	= "Plex Picasa Web Plugin"

# Plugin parameters

PLUGIN_TITLE						= "Picasa Web Albums"		# The plugin Title
PLUGIN_PREFIX   					= "/photos/PicasaWeb"		# The plugin's contextual path within Plex
PLUGIN_HTTP_CACHE_INTERVAL			= 0

# Plugin Icons

PLUGIN_ICON_DEFAULT					= "icon-default.png"
PLUGIN_ICON_ABOUT					= "icon-about.png"
PLUGIN_ICON_PREFS					= "icon-prefs.png"
PLUGIN_ICON_USER					= "icon-user.png"
PLUGIN_ICON_FRIENDS					= "icon-friends.png"
PLUGIN_ICON_TAG						= "icon-tag.png"
PLUGIN_ICON_ALBUM					= "icon-album.png"
PLUGIN_ICON_MORE					= "icon-more.png"
PLUGIN_ICON_FEATURED_PHOTOS 		= "icon-featured-photos.png"
PLUGIN_ICON_RECENT_PHOTOS			= "icon-recent-photos.png"
PLUGIN_ICON_POPULAR_TAGS			= "icon-popular-tags.png"
PLUGIN_ICON_USER_ALBUMS				= "icon-user-albums.png"
PLUGIN_ICON_USER_TAGS				= "icon-user-tags.png"
PLUGIN_ICON_USER_RECENT				= "icon-user-recent.png"
PLUGIN_ICON_SEARCH_USER				= "icon-search-user.png"
PLUGIN_ICON_SEARCH_COMMUNITY		= "icon-search-community.png"

# Plugin Preference Keys

PLUGIN_PREF_USERNAME				= "username"
PLUGIN_PREF_PASSWORD				= "password"
PLUGIN_PREF_SHOW_PRIVATE_ALBUMS		= "showprivatealbums"
PLUGIN_PREF_SHOW_PHOTO_SUMMARY		= "showphotosummary"
PLUGIN_PREF_SORT_ALBUM_BY               = "sortalbumby"

# Plugin Sort Keys

SORT_ALBUM_NAME_DESCENDING = "Album Name Descending"
SORT_ALBUM_NAME_ASCENDING = "Album Name Ascending"
SORT_ALBUM_DATE_DESCENDING = "Album Date Descending"
SORT_ALBUM_DATE_ASCENDING = "Album Date Ascending"

# Plugin Artwork

PLUGIN_ARTWORK						= "art-default.jpg"

gd_client = None
gd_client_logged_in = None

####################################################################################################

def Start():
        global gd_client
        global gd_client_logged_in
        
	# Register our plugins request handler
	
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)
	
	# Add in the views our plugin will support
	
	Plugin.AddViewGroup("CommunityList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("MyList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("AlbumList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("TagList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("FriendList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("PhotoList", viewMode="Pictures", mediaType="photos")
	
	# Set up our plugin's container
	
	MediaContainer.title1 = PLUGIN_TITLE
	MediaContainer.content = 'Items'
	MediaContainer.viewMode = "InfoList"
	MediaContainer.art = R(PLUGIN_ARTWORK)
	
	# Configure HTTP Cache lifetime
	
	HTTP.CacheTime = PLUGIN_HTTP_CACHE_INTERVAL

        gd_client = gdata.gdata.photos.service.PhotosService()
	gd_client_logged_in = InitializeGDataClient()

####################################################################################################
# The plugin's main menu. 

def MainMenu():
		
	dir = MediaContainer()
	dir.art = R(PLUGIN_ARTWORK)
	
	dir.Append(Function(DirectoryItem(CommunityMenu, title=L("COMMUNITY_MENU_TITLE"), thumb=R(PLUGIN_ICON_DEFAULT), summary=L("COMMUNITY_MENU_SUMMARY"))))
	dir.Append(Function(DirectoryItem(MyMenu, title=L("ME_MENU_TITLE"), thumb=R(PLUGIN_ICON_USER), summary=L("ME_MENU_SUMMARY"))))
	dir.Append(Function(DirectoryItem(GetFriendList, title=L("MY_FRIEND_LIST_TITLE"), thumb=R(PLUGIN_ICON_FRIENDS), summary=L("MY_FRIEND_LIST_SUMMARY")), user=Prefs[PLUGIN_PREF_USERNAME]))
	dir.Append(PrefsItem(L("PREFERENCES_TITLE"), thumb=R(PLUGIN_ICON_PREFS), summary=L("PREFERENCES_SUMMARY")))
	dir.Append(PhotoItem(R(PLUGIN_ARTWORK), title=L("ABOUT_TITLE"), thumb=R(PLUGIN_ICON_ABOUT)))
		 
	return dir

####################################################################################################
# The community menu

def CommunityMenu(sender):
	dir = MediaContainer()
	dir.viewGroup = "CommunityList"
	dir.art = R(PLUGIN_ARTWORK)
	dir.title2 = L("COMMUNITY_MENU_TITLE")
	
	dir.Append(Function(
                    DirectoryItem(GetPhotoList,
                                  title=L("COMMUNITY_FEATURED_PHOTOS_TITLE"),
                                  thumb=R(PLUGIN_ICON_FEATURED_PHOTOS),
                                  summary=L("COMMUNITY_FEATURED_PHOTOS_SUMMARY")),
                    kind="featured",
                    user=None,
                    page=1,
                    pagesize=51,
                    maxphotos=1000))
	
	dir.Append(Function(
                    DirectoryItem(GetPhotoList,
                                  title=L("COMMUNITY_RECENT_PHOTOS_TITLE"),
                                  thumb=R(PLUGIN_ICON_RECENT_PHOTOS),
                                  summary=L("COMMUNITY_RECENT_PHOTOS_SUMMARY")),
                    kind="recent",
                    user=None,
                    page=1,
                    pagesize=51,
                    maxphotos=1000))
	
	dir.Append(Function(InputDirectoryItem(DoSearch, title=L("SEARCH_TITLE"), prompt=L("COMMUNITY_SEARCH_SUMMARY"), thumb=R(PLUGIN_ICON_SEARCH_COMMUNITY))))
	
	return dir

####################################################################################################
# The user's menu

def MyMenu(sender):
	dir = MediaContainer()
	dir.viewGroup = "MyList"
	dir.art = R(PLUGIN_ARTWORK)
	dir.title2 = L("ME_MENU_TITLE")

	user = Prefs[PLUGIN_PREF_USERNAME]

	if user!= None:
		dir.Append(Function(DirectoryItem(GetAlbumList, title=L("MY_ALBUM_LIST_TITLE"), thumb=R(PLUGIN_ICON_USER_ALBUMS), summary=L("MY_ALBUM_LIST_SUMMARY")), user=user))
		dir.Append(Function(DirectoryItem(GetTagList, title=L("MY_TAG_LIST_TITLE"), thumb=R(PLUGIN_ICON_USER_TAGS), summary=L("MY_TAG_LIST_SUMMARY")), user=user))
		dir.Append(Function(DirectoryItem(GetPhotoList, title=L("MY_RECENT_PHOTOS_TITLE"), thumb=R(PLUGIN_ICON_USER_RECENT), summary=L("MY_RECENT_PHOTOS_SUMMARY")), kind="recent", user=user, page=1, pagesize=51, maxphotos=1000))
		dir.Append(Function(InputDirectoryItem(DoSearch, title=L("SEARCH_TITLE"), prompt=L("MY_SEARCH_SUMMARY"), thumb=R(PLUGIN_ICON_SEARCH_USER)), user=user))
		return dir
	else:
		return NoUserSpecified(sender)

####################################################################################################
# Returns a list of things that can be done to a Gallery

def GetFriendItems(sender, user=None, nickname=None):
	dir = MediaContainer()
	dir.viewGroup = "FriendList"
	dir.art = R(PLUGIN_ARTWORK)
	dir.title1 = PLUGIN_TITLE
	dir.title2 = nickname
	
	dir.Append(Function(DirectoryItem(GetAlbumList, title=L("ALBUM_LIST_TITLE") % nickname, thumb=R(PLUGIN_ICON_USER_ALBUMS), summary=L("ALBUM_LIST_SUMMARY") % nickname), user=user, nickname=nickname))
	dir.Append(Function(DirectoryItem(GetTagList, title=L('TAG_LIST_TITLE') % nickname, thumb=R(PLUGIN_ICON_USER_TAGS), summary=L("TAG_LIST_SUMMARY") % nickname), user=user, nickname=nickname))
	dir.Append(Function(DirectoryItem(GetPhotoList, title=L("RECENT_PHOTOS_TITLE") % nickname, thumb=R(PLUGIN_ICON_USER_RECENT), summary=L("RECENT_PHOTOS_SUMMARY") % nickname), kind="recent", user=user, nickname=nickname, page=1, pagesize=51))
	dir.Append(Function(DirectoryItem(GetFriendList, title=L("FRIEND_LIST_TITLE") % nickname, thumb=R(PLUGIN_ICON_FRIENDS), summary=L("FRIEND_LIST_SUMMARY") % nickname), user=user, nickname=nickname))	
	dir.Append(Function(InputDirectoryItem(DoSearch, title=L("SEARCH_TITLE"), prompt=L("FRIEND_SEARCH_SUMMARY") % nickname, thumb=R(PLUGIN_ICON_SEARCH_USER)), user=user, nickname=nickname))

	return dir

####################################################################################################
# Returns a search menu

def DoSearch(sender, query=None, user=None, nickname=None, page=1, pagesize=51, maxphotos=1000):	
	return GetPhotoList(sender, kind="search", user=user, nickname=nickname, query=query, page=page, pagesize=pagesize, maxphotos=maxphotos)

####################################################################################################
# Obtains a list of the user's friends

def GetFriendList(sender, user=None, nickname=None):
	global gd_client
	
	dir = MediaContainer()
	dir.viewGroup = "FriendList"
	dir.art = R(PLUGIN_ARTWORK)
	dir.title1 = PLUGIN_TITLE
	
	if user!= None:
		if user == Prefs[PLUGIN_PREF_USERNAME]:
			dir.title2 = L("MY_FRIEND_LIST_TITLE")
		else:
			dir.title2 = L("FRIEND_LIST_TITLE") % nickname
	else:
		return NoUserSpecified(sender)
			
	
	thumb = R(PLUGIN_ICON_USER)

	ShouldInitializeGDataClient()
		
	if gd_client != None:
		contacts = gd_client.GetFeed("/data/feed/api/user/%s/contacts?kind=user" % user)
		
		if len(contacts.entry) > 0:
			for contact in contacts.entry:
				dir.Append(Function(DirectoryItem(GetFriendItems, title=contact.nickname.text, thumb=thumb, summary=L('FRIEND_MENU_SUMMARY') % contact.nickname.text), user=contact.user.text, nickname=contact.nickname.text))
			return dir
		else:
			return MessageContainer(L("MESSAGE_NO_FRIENDS_TITLE"), L("MESSAGE_NO_FRIENDS_SUMMARY") % user)
	else:
		return ServiceError(sender)
	
####################################################################################################
# Obtains a list of Albums for the specified user

def GetAlbumList(sender, user=None, nickname=None):
        global gd_client
        
	dir = MediaContainer()
	dir.viewGroup = "AlbumList"
	dir.art = R(PLUGIN_ARTWORK)
	dir.title1 = PLUGIN_TITLE
	
	if user!= None:
		if user != Prefs[PLUGIN_PREF_USERNAME]:
			dir.title2 = L("ALBUM_LIST_TITLE") % nickname
		else:
			dir.title2 =L("MY_ALBUM_LIST_TITLE")
	else:
		return NoUserSpecified(sender)

	ShouldInitializeGDataClient()
		
	if gd_client != None:
		albums = gd_client.GetUserFeed(user=user)
		
		if len(albums.entry) > 0:
			for album in SortAlbums(albums.entry): 
				
				if album.media.thumbnail[0].url != None:
					thumb = album.media.thumbnail[0].url
				else:
					thumb = None
					
				if album.numphotos.text != None:
					numphotos = album.numphotos.text
				else:
					numphotos = 0
					
 				dir.Append(Function(
                                            DirectoryItem(GetPhotoList,
                                                           title=album.title.text + " (" + numphotos + ")",
                                                           thumb=thumb,
                                                           summary=GetAlbumSummary(album)),
                                            kind="album",
                                            albumid=album.gphoto_id.text,
                                            albumtitle=album.title.text,
                                            user=user))
		 	return dir
		else:
			return MessageContainer(L("MESSAGE_NO_ALBUMS_TITLE"), L("MESSAGE_NO_ALBUMS_SUMMARY") % user)
	else:
		return ServiceError(sender)


####################################################################################################
def SortAlbums(albums):
    sortBy = Prefs[PLUGIN_PREF_SORT_ALBUM_BY]
    if sortBy == SORT_ALBUM_NAME_ASCENDING:
        return sorted(albums, key=lambda a: a.title.text, reverse=True)
    elif sortBy == SORT_ALBUM_DATE_DESCENDING:
        return sorted(albums, key=lambda a: a.timestamp.datetime())
    elif sortBy == SORT_ALBUM_DATE_ASCENDING:
        return sorted(albums, key=lambda a: a.timestamp.datetime(), reverse=True)
    else:
        return sorted(albums, key=lambda a: a.title.text)
		
####################################################################################################
# Builds up a more complete summary string for the specified Album

def GetAlbumSummary(album):
	global gd_client
	
	summary_text = ""
	
	if album.summary.text != None:
		summary_text += "%s\n\n" % album.summary.text
	
	if album.location.text == None:
		album.location.text = "Unknown"
			
	summary_text += "Location: %s\n" % album.location.text
	
	if album.rights.text != None:
		summary_text += "Visibility: %s\n" % album.rights.text.capitalize()
	
	if album.bytesUsed != None and album.bytesUsed.text != "0":
		summary_text += "Space Used: %s" % ReadableSize(long(album.bytesUsed.text))
		
	return summary_text

####################################################################################################
# Displays a list of tags for the specified user

def GetTagList(sender, user=None, nickname=None):
        global gd_client
        
	dir = MediaContainer()
	dir.viewGroup = "TagList"
	dir.art = R(PLUGIN_ARTWORK)
	dir.title1 = PLUGIN_TITLE
	
	if user!= None:
		if user != Prefs[PLUGIN_PREF_USERNAME]:
			dir.title2 = L("TAG_LIST_TITLE") % nickname
		else:
			dir.title2 =L("MY_TAG_LIST_TITLE")
	else:
		return NoUserSpecified
	
	thumb = R(PLUGIN_ICON_TAG)

	ShouldInitializeGDataClient()
		
	if gd_client != None:
		tags = gd_client.GetFeed('/data/feed/api/user/%s?kind=tag' % user)
		
		if len(tags.entry) > 0:
			for tag in tags.entry:	
  		 		dir.Append(Function(DirectoryItem(GetPhotoList, title=tag.title.text, thumb=thumb, summary=L('ACTION_VIEW_TAG_SUMMARY') % (tag.title.text)), kind="tag", tag=tag.title.text, user=user))
  		 	return dir
  		else:
  		 	return MessageContainer(L("MESSAGE_NO_TAGS_TITLE"), L("MESSAGE_NO_TAGS_SUMMARY") % user)
	else:
		return ServiceError(sender)
	
####################################################################################################
# Returns a list of photos based upon criteria

def GetPhotoList(sender, kind=None, albumid=None, albumtitle=None, tag=None, user=None, nickname=None, query=None, page=None, pagesize=20, maxphotos=None):
	global gd_client
	
	if kind != None:		Log("kind=%s" % kind)
	if albumid != None:		Log("albumid=%s" % albumid)
	if albumtitle != None:	Log("albumtitle=%s" % albumtitle)
	if tag != None:			Log("tag=%s" % tag), 
	if user != None:		Log("user=%s" % user)
	if nickname != None:	Log("nickname=%s" % nickname)
	if page != None:		Log("page=%d" % page)
	if pagesize != None:	Log("pagesize=%d" % pagesize)
	if maxphotos != None:	Log("maxphotos=%d" % maxphotos)
		
	dir = MediaContainer()
	dir.viewGroup = "PhotoList"
	dir.art = R(PLUGIN_ARTWORK)
	dir.title1 = PLUGIN_TITLE
	
	FeedURI = ""

	ShouldInitializeGDataClient()
	
	if gd_client != None:
		if kind == "search":
			startindex = pagesize*(page-1)+1
			
			if user != None:
				if user != Prefs[PLUGIN_PREF_USERNAME]:
					dir.title2 = L("RECENT_PHOTOS_TITLE") % nickname
				else:
					dir.title2 = L("MY_RECENT_PHOTOS_TITLE")
	         
				FeedURI = "/data/feed/api/user/%s/?kind=photo&max-results=%d&start-index=%d&q=%s" % (user, pagesize, startindex, query)
			else:
				dir.title2 = L("COMMUNITY_RECENT_PHOTOS_TITLE")
				FeedURI = "/data/feed/api/all?kind=photo&max-results=%d&start-index=%d&q=%s" % (pagesize, startindex, query)
			
		if kind == "album":
			dir.title2 = albumtitle
			FeedURI = "/data/feed/api/user/%s/albumid/%s?kind=photo" % (user, albumid)
		
		if kind == "tag":
			dir.title2 = tag
			FeedURI = "/data/feed/api/user/%s?kind=photo&tag=%s" % (user, tag)
		
		if kind == "recent":
			
			startindex = pagesize*(page-1)+1
			
			if user != None:
				if user != Prefs[PLUGIN_PREF_USERNAME]:
					dir.title2 = L("RECENT_PHOTOS_TITLE") % nickname
				else:
					dir.title2 = L("FRIEND_SEARCH_RESULTS")
				
				FeedURI = "/data/feed/api/user/%s?kind=photo&max-results=%d&start-index=%d&q=" % (user, pagesize, startindex)
			else:
				dir.title2 = L("COMMUNITY_SEARCH_RESULTS")
				FeedURI = "/data/feed/api/all?kind=photo&max-results=%d&start-index=%d" % (pagesize, startindex)
			
		if kind == "featured":
			dir.title2 = L("COMMUNITY_FEATURED_PHOTOS_TITLE")
			FeedURI = "/data/feed/api/featured?max-results=%d&start-index=%d" % (pagesize, (pagesize*(page -1)+1))

		Log("FeedURI=%s" % FeedURI)
		
		photos = gd_client.GetFeed(FeedURI)
		
				
		if photos != None and len(photos.entry) > 0:
			for photo in photos.entry:				
				dir.Append(PhotoItem(photo.media.content[0].url.encode('utf-8','ignore'), title=Encode(photo.title.text), summary=GetPhotoSummary(photo), thumb=photo.media.thumbnail[0].url))
				
			if len(dir) == pagesize:
				if page != None:
					itemssofar = pagesize*(page-1)
					nextpagestartindex = pagesize*(page)+1
					
					Log("items so far: %d" % itemssofar)
					Log("next page start index: %d" % nextpagestartindex)
											
					if maxphotos != None and nextpagestartindex < maxphotos:
						displaynext = True 
					elif len(photos.entry) == pagesize:
						displaynext = True
					else:
						displaynext = False
						
					if displaynext == True:
						dir.Append(Function(DirectoryItem(GetPhotoList, title="More...", thumb=R(PLUGIN_ICON_MORE), summary="Show the next %d Items." % pagesize), kind=kind, user=user, query=query, page=page+1, pagesize=pagesize, maxphotos=maxphotos))
					
			return dir
		else:
			return MessageContainer(L("MESSAGE_NO_PHOTOS_TITLE"), L("MESSAGE_NO_PHOTOS_SUMMARY"))
	else:
		return ServiceError(sender)

####################################################################################################
# Builds up a more complete summary for for the specified Photo

def GetPhotoSummary(photo):

	if not Prefs[PLUGIN_PREF_SHOW_PHOTO_SUMMARY] or photo == None: return None
	
	summary_text = ""
	
	if photo.summary != None and Encode(photo.summary.text) != "":
		summary_text += "Summary: %s\n\n" % Encode(photo.summary.text)
		
	if photo.width != None and photo.height != None:
		summary_text += "Dimensions: %sx%s\n" % (photo.width.text, photo.height.text)
		
	if photo.timestamp != None:
                try:
                    summary_text += "Date Taken: %s\n" % str(DateTimeFromTimeStamp(photo.timestamp.text))
                except:
                    pass
			
	if photo.media != None:
		if photo.media.keywords != None and Encode(photo.media.keywords.text) != "":
			summary_text += "Tags: %s" % Encode(photo.media.keywords.text)
				
	return summary_text


####################################################################################################
def InitializeGDataClient():
    global gd_client
    Log("Initializing gdata PhotoService")

    if gd_client is None:
        gd_client= gdata.gdata.photos.service.PhotosService()

    gd_client.source = GDATA_PHOTO_SERVICE_CLIENT_NAME

    username = Prefs[PLUGIN_PREF_USERNAME]

    password = Prefs[PLUGIN_PREF_PASSWORD]

    if username is None or password is None:
        # We can't authenticate because the users credentials are not complete			
	return false

    elif not Prefs[PLUGIN_PREF_SHOW_PRIVATE_ALBUMS]:
        # User doesn't want access to private albums...respect wish and don't sign in
        return False
	
    else:
        # Authenticate against Google
		
	Log("Client authenticating against google as '%s'" % username)
			
	gd_client.email = username
	gd_client.password = password
	
	try:
            gd_client.ProgrammaticLogin()
			
	except gdata.service.BadAuthentication, e:
	    # The login to google failed
	    Log("Login failed for user '" + username + "'")
	    return false
			
	except socket.error, (value,message):
	    # Low-level network error not masked by the gdata api
	    Log("There was a network error connecting to the google service.  Error Code '" + str(value) +"' message '" + message + "'")
	    return False

    Log("Client login was successful")
    return True

####################################################################################################
def ShouldInitializeGDataClient():
    global gd_client_logged_in
    username = Prefs[PLUGIN_PREF_USERNAME]
    password = Prefs[PLUGIN_PREF_PASSWORD]
    private = Prefs[PLUGIN_PREF_SHOW_PRIVATE_ALBUMS]
    if gd_client_logged_in is None or not gd_client_logged_in and not username is None and not password is None and private:
        gd_client_logged_in = InitializeGDataClient()


####################################################################################################
def ValidatePrefs():
    u = Prefs[PLUGIN_PREF_USERNAME]
    p = Prefs[PLUGIN_PREF_PASSWORD]

    if u is None and not p is None or p is None and not u is None:
        return MessageContainer("Error", "You must enter a username and password")
    else:
        if not InitializeGDataClient():
            return MessageContainer("Error", "There was an error logging in")
        else:
            return MessageContainer("Success", "Preferences have been saved")
        

####################################################################################################
# Returns a message to the user informing them that they have not specified a user for picasa

def NoUserSpecified(sender):
	
	return MessageContainer(L("MESSAGE_NO_USER_SPECIFIED_TITLE"), L("MESSAGE_NO_USER_SPECIFIED_SUMMARY"))

####################################################################################################
# There was an authentication or general gdata service error

def ServiceError(sender):
	
	return MessageContainer(L("MESSAGE_SERVICE_ERROR_TITLE"), L("MESSAGE_SERVICE_ERROR_SUMMARY"))

####################################################################################################
# Try and force encoding to utf-8

def Encode(value):	

	if value == None: return ""
	
	try:
		value = value.encode('utf-8','ignore')
	except UnicodeDecodeError:
		value = "Encoing failed"
		
	return value

####################################################################################################
# convert a gdata timestamp into a python datetime object

def DateTimeFromTimeStamp(timestamp):
	
	epoch = float(timestamp)/1000
	return datetime.datetime.fromtimestamp(epoch)

####################################################################################################
# convert bytes to named size

def ReadableSize(value):
	
	unit = ("Kilobytes", "Megabytes", "Gigabytes", "Terabytes", "Petabytes", "Exabytes", "Zettabytes", "Yottabytes")

	increment = 1024
	
	bytes = long(value)
	index = int(floor(log(bytes, increment)))
	return "%.2f %s" % ((float(bytes) / pow(increment, index)), unit[index - 1].lower())
