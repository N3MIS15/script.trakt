# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcaddon
import datetime
import utilities as utils
from utilities import Debug
from traktapi import traktAPI
api = traktAPI()

from cache import summary, friends_activities, trending_shows # ONLY FOR TESTING

__addon__        = xbmcaddon.Addon(id='script.trakt')
__addonpath__    = __addon__.getAddonInfo('path')

media_page_settings = ["Trending", "Popular", "Watched", "Played"]
def small_poster(image):
	if not 'poster-small' in image:
		x = image.rfind('.')
		image = image[:x] + '-138' + image[x:]
	return image

class traktGUI(xbmcgui.WindowXML):
	def onInit(self):
		self.current_page = 15000 # Loading
		self.rating_type = api.settings['viewing']['ratings']['mode']
		# Hide all pages by default
		self.getControl(11000).setVisible(False)
		self.getControl(13000).setVisible(False)
		self.getControl(14000).setVisible(False)
		self.renderPage("home", "Home")

	def getMediaID(self, media):
		if "tvdb_id" in media:
			return media['tvdb_id']
		elif "imdb_id" in media:
			return media['imdb_id']
		elif "tmdb_id" in media:
			return media['tmdb_id']
		else:
			return None

	def getMediaData(self, list_type, media_type):
		list_media = []
		total_watching = 0 # Trending only

		if list_type == "trending":
			#result = trending_shows
			result = api.getTrending(media_type) #USING CACHE FOR TESTING
		else:
			pass # MORE TO COME

		for x in result:
			if list_type == "trending":
				label =	 x['title']
				label2 = "%i watchers" % x['watchers']
				thumbnail = x['images']['poster']
				total_watching += x['watchers']
			else:
				label = ""
				label2 = ""
				thumbnail = ""

			li = xbmcgui.ListItem(label=label, label2=label2, thumbnailImage=thumbnail)
			li.setProperty("media_type", media_type)
			li.setProperty("media_id", str(self.getMediaID(x)))
			list_media.append(li)

		if list_type == "trending":
			title = "There are [B]%i[/B] %s being watched by [B]%i[/B] people right now!" % (len(result), media_type, total_watching) #HARDCODED
		else:
			title = ""
		return [title, list_media]

	def getActivityData(self, who):
		#activities = friends_activities
		activities = api.getActivity(who, "all", "all") #USING CACHE FOR TESTING
		list_activities = []
		if who == "friends":
			title = "See what your [B]friends[/B] are up to..." #HARDCODED
		else:
			title = "See what the [B]community[/B] is up to..." #HARDCODED

		for activity in activities['activity']:
			if activity['type'] == 'episode': # NEED TO ADD OTHER TYPES
				user = activity['user']['username']
				action = activity['action']
				show = activity['show']['title']
				season = activity['episode']['season']
				episode = activity['episode']['number']
				ep_name = activity['episode']['title']
				label = "[COLOR=blue]%s[/COLOR] [B]%s[/B][CR]%s %ix%02d \"%s\"" % (user, action, show, season, episode, ep_name)
				label2 = "%s %s" % (activity['when']['day'], activity['when']['time'])
				thumbnail = activity['user']['avatar']

				li = xbmcgui.ListItem(label=label, label2=label2, thumbnailImage=thumbnail)
				li.setProperty("username", user)
				list_activities.append(li)

		return [title, list_activities]

	def renderSummary(self, media_type, media_id):
		self.showLoading()
		summary = api.getSummary(media_type, media_id)
		gui = SummaryDialog(
			"SummaryDialog.xml",
			__addonpath__,
			media_type=media_type,
			media=summary,
		)
		self.hideLoading(dialog=True)
		gui.doModal()
		del gui

	def onClick(self, controlID):
		Debug("[GUI] control pressed: %i" % controlID)

		# Left Menu
		if controlID == 10005:
			self.renderPage("home", "Home")
		if controlID == 10006:
			self.renderPage("calendar", "Calendar")
		if controlID == 10007:
			self.renderPage("shows", "TV Shows [COLOR=blue]-[/COLOR] " + media_page_settings[utils.getBoolSetting("gui_shows_default")])
		if controlID == 10008:
			self.renderPage("movies", "Movies [COLOR=blue]-[/COLOR] " + media_page_settings[utils.getBoolSetting("gui_shows_default")])
		if controlID == 10021:
			utils.setProperty('traktManualSync', 'True')
		if controlID == 10022:
			__addon__.openSettings()

		# Media lists
		if controlID in [11201, 14101]:
			# Goto clicked item's summary
			li = self.getControl(controlID).getSelectedItem()
			media_type = li.getProperty("media_type")
			media_id = li.getProperty("media_id")

			if media_type.endswith("s"):
				media_type = media_type[:-1]

			self.renderSummary(media_type, media_id)

	def renderPage(self, page, title=""):
		self.showLoading()

		# Grab the data for the page
		if page == "home":
			page_id = 11000
			self.renderHomePage()
		if page == "calendar":
			page_id = 13000
			pass
		if page == "shows":
			page_id = 14000
			self.renderMediaPage("shows")
		if page == "movies":
			page_id = 14000
			self.renderMediaPage("movies")

		self.hideLoading()

		# Show new page
		self.getControl(10001).setLabel(title) # Change page title
		self.current_page = page_id
		self.getControl(page_id).setVisible(True)

	def showLoading(self):
		# Remove the current page and show loading...
		self.getControl(self.current_page).setVisible(False)
		self.getControl(10001).setVisible(False) # Hide title while loading
		self.getControl(15000).setVisible(True)

	def hideLoading(self, dialog=False):
		# Hide loading...
		self.getControl(15000).setVisible(False)
		self.getControl(10001).setVisible(True)
		if dialog:
			self.getControl(self.current_page).setVisible(True) # Show the previous page again

	def renderHomePage(self):
		# Populate users profile avatar and username
		self.getControl(11001).setImage(api.settings['profile']['avatar'])
		self.getControl(11002).setLabel(api.settings['profile']['username'])

		# Check settings for home layout
		if utils.getBoolSetting("gui_home_activity") == 0:
			activity_data = self.getActivityData("friends")

		elif utils.getBoolSetting("gui_home_activity") == 1:
			activity_data = self.getActivityData("community")

		if utils.getBoolSetting("gui_home_media") == 0:
			media_data = self.getMediaData("trending", "shows")

		elif utils.getBoolSetting("gui_home_media") == 1:
			media_data = self.getMediaData("trending", "movies")

		self.getControl(11100).setLabel(activity_data[0]) # Activity title
		self.getControl(11101).addItems(activity_data[1]) # Activity list
		self.getControl(11200).setLabel(media_data[0]) # Media title
		self.getControl(11201).addItems(media_data[1]) # Media list

	def renderMediaPage(self, media_type):
		# Check settings for default
		if utils.getBoolSetting("gui_%s_default" % media_type) == 0:
			# Get Trending
			media_data = self.getMediaData("trending", media_type)
		elif utils.getBoolSetting("gui_%s_default" % media_type) == 1:
			# Get Popular
			#media_data = self.getMediaData("popular", media_type)
			pass
		elif utils.getBoolSetting("gui_%s_default" % media_type) == 2:
			# Get Watched
			#media_data = self.getMediaData("watched", media_type)
			pass
		else:
			# Get Played
			#media_data = self.getMediaData("played", media_type)
			pass

		self.getControl(14100).setLabel(media_data[0]) # Page Title
		self.getControl(14101).addItems(media_data[1]) # Page List


class SummaryDialog(xbmcgui.WindowXMLDialog):
	def __init__(self, xmlFile, resourcePath, forceFallback=False, media_type=None, media=None):
		self.media_type = media_type
		self.media = media

	def onInit(self):
		title = "%s [COLOR=blue]-[/COLOR] %s" % (self.media_type.title(), self.media['title'])
		poster = self.media['images']['poster']
		fanart = self.media['images']['fanart']
		rating_percent = "%i%%" % self.media['ratings']['percentage']
		rating_votes = "%i votes" % self.media['ratings']['votes'] # HARDCODED
		overview = self.media['overview']
		watchlist = "badge-watchlist.png" if self.media['in_watchlist'] == True else ""
		rating_type = api.settings['viewing']['ratings']['mode']
		rating = self.media['rating'] if rating_type == "simple" else self.media['rating_advanced']

		info_list = [
			xbmcgui.ListItem(label="Airs", label2='%s %s' % (self.media['air_day'], self.media['air_time'])), # HARDCODED
			xbmcgui.ListItem(label="First Aired", label2=str(datetime.datetime.fromtimestamp(int(self.media['first_aired'])).strftime('%B %d, %Y'))), # HARDCODED
			xbmcgui.ListItem(label="Genre", label2=' / '.join(self.media['genres'])), # HARDCODED
			xbmcgui.ListItem(label="Runtime", label2=str(self.media['runtime']) + "m"), # HARDCODED
			xbmcgui.ListItem(label="Certification", label2=str(self.media['certification'])), # HARDCODED
		]
		self.getControl(12000).setImage(fanart)
		self.getControl(12001).setLabel(title)
		self.getControl(12002).setImage(poster)
		if rating:
			self.getControl(12003).setImage("badge-%s.png" % rating)
		self.getControl(12004).setImage(watchlist)
		self.getControl(12007).setText(overview)
		self.getControl(12008).setLabel(rating_percent)
		self.getControl(12009).setLabel(rating_votes)
		self.getControl(12010).addItems(info_list)


if __name__ == '__main__':
	if not api.settings:
		api.getAccountSettings()

	gui = traktGUI('TraktGUI.xml', __addonpath__)
	gui.doModal()
	del gui