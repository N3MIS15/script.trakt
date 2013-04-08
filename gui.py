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

media_page_settings = ["Trending", "Popular", "Watched", "Played", "Recommended"]

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
			rating_key = "rating" if self.rating_type == "simple" else "rating_advanced"
			rating_badge = "badge-%s.png" % str(x[rating_key]) if x[rating_key] else ""
			in_watchlist = "true" if x['in_watchlist'] else "false"
			watched = "true" if x['watched'] else "false"

			if list_type == "trending":
				label =	 x['title']
				label2 = "%i watchers" % x['watchers']
				thumbnail = x['images']['poster']
				total_watching += x['watchers']

			else:
				label = ""
				label2 = ""
				thumbnail = ""

			li = xbmcgui.ListItem(label=label, label2=label2, thumbnailImage=thumbnail, iconImage=rating_badge)
			li.setProperty("media_type", media_type)
			li.setProperty("media_id", str(self.getMediaID(x)))
			li.setProperty("rating", str(x[rating_key]))
			li.setProperty("rating_image", rating_badge)
			li.setProperty("watched", watched)
			li.setProperty("in_watchlist", in_watchlist)
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
		if media_type.endswith("s"):
			media_type = media_type[:-1]

		params = {"type": media_type, "data": media_id}
		if media_type == "show":
			params['extended'] = True

		summary = api.getSummary(**params)
		comments = api.getComments(media_type, media_id, "all")
		gui = SummaryDialog(
			"SummaryDialog.xml",
			__addonpath__,
			media_type=media_type,
			media=summary,
			comments=comments
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
			self.renderPage("shows", "Shows [COLOR=blue]-[/COLOR] " + media_page_settings[utils.getSettingAsInt("gui_shows_default")])
		if controlID == 10008:
			self.renderPage("movies", "Movies [COLOR=blue]-[/COLOR] " + media_page_settings[utils.getSettingAsInt("gui_shows_default")])
		if controlID == 10021:
			utils.setProperty('traktManualSync', 'True')
		if controlID == 10022:
			__addon__.openSettings()

		# Media lists
		if controlID in [11201, 14101]:
			li = self.getControl(controlID).getSelectedItem()
			media_type = li.getProperty("media_type")
			media_id = li.getProperty("media_id")

			if self.current_page == 11000 and utils.getSettingAsInt("gui_home_media_goto") == 1:
				title = "%s [COLOR=blue]-[/COLOR] %s" % (media_type.title(), media_page_settings[utils.getSettingAsInt("gui_home_media")])
				self.renderPage(media_type, title)
			else:
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
		if utils.getSettingAsInt("gui_home_activity") == 0:
			activity_data = self.getActivityData("friends")

		elif utils.getSettingAsInt("gui_home_activity") == 1:
			activity_data = self.getActivityData("community")

		if utils.getSettingAsInt("gui_home_media") == 0:
			media_data = self.getMediaData("trending", "shows")

		elif utils.getSettingAsInt("gui_home_media") == 1:
			media_data = self.getMediaData("trending", "movies")

		self.getControl(11100).setLabel(activity_data[0]) # Activity title
		self.getControl(11101).addItems(activity_data[1]) # Activity list
		self.getControl(11200).setLabel(media_data[0]) # Media title
		self.getControl(11201).addItems(media_data[1]) # Media list

	def renderMediaPage(self, media_type):
		# Check settings for default
		if utils.getSettingAsInt("gui_%s_default" % media_type) == 0:
			# Get Trending
			media_data = self.getMediaData("trending", media_type)
		elif utils.getSettingAsInt("gui_%s_default" % media_type) == 1:
			# Get Popular
			#media_data = self.getMediaData("popular", media_type)
			pass
		elif utils.getSettingAsInt("gui_%s_default" % media_type) == 2:
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
	def __init__(self, xmlFile, resourcePath, forceFallback=False, media_type=None, media=None, comments=None):
		self.media_type = media_type
		self.media = media
		self.comments = comments

	def onInit(self):
		title = "%s [COLOR=blue]-[/COLOR] %s" % (self.media_type.title(), self.media['title'])
		poster = self.media['images']['poster']
		fanart = self.media['images']['fanart']
		rating_percent = "%i%%" % self.media['ratings']['percentage']
		rating_votes = "%i votes" % self.media['ratings']['votes'] # HARDCODED
		overview = self.media['overview']
		watchlist = "badge-watchlist.png" if self.media['in_watchlist'] else ""
		rating_type = api.settings['viewing']['ratings']['mode']
		rating = self.media['rating'] if rating_type == "simple" else self.media['rating_advanced']

		if self.media_type == "show":
			show_total_episodes = 0
			show_watched_episodes = 0
			season_list = []

			for season in self.media['seasons']:
				total_episodes = len(season['episodes'])
				show_total_episodes += total_episodes

				watched_episodes = len([x for x in season['episodes'] if x['watched']])
				show_watched_episodes += watched_episodes

				li = xbmcgui.ListItem(label="Season %i"%season['season'], thumbnailImage=small_poster(season['images']['poster'])) # HARDCODED
				li.setProperty("watched", "true" if total_episodes == watched_episodes else "false")
				season_list.append(li)

			watched = show_total_episodes == show_watched_episodes

			info_list = [
				xbmcgui.ListItem(label="Airs", label2="%s %s" % (self.media['air_day'], self.media['air_time'])), # HARDCODED
				xbmcgui.ListItem(label="Premiered", label2=str(datetime.datetime.fromtimestamp(int(self.media['first_aired'])).strftime('%B %d, %Y'))), # HARDCODED
				xbmcgui.ListItem(label="Certification", label2=str(self.media['certification'])), # HARDCODED
				xbmcgui.ListItem(label="Runtime", label2=str(self.media['runtime']) + "m"), # HARDCODED
				xbmcgui.ListItem(label="Genres", label2=" / ".join(self.media['genres'])), # HARDCODED
			]

			season_list = [xbmcgui.ListItem(label="Season %i"%x['season'], thumbnailImage=small_poster(x['images']['poster'])) for x in self.media['seasons']] #HARDCODED
			self.getControl(12100).addItems(season_list)

		elif self.media_type == "movie":
			watched = self.media['watched']
			info_list = [
				xbmcgui.ListItem(label="Runtime", label2=str(self.media['runtime']) + "m"), # HARDCODED
				xbmcgui.ListItem(label="Released", label2=str(datetime.datetime.fromtimestamp(int(self.media['released'])).strftime('%B %d, %Y'))), # HARDCODED
				xbmcgui.ListItem(label="Certification", label2=str(self.media['certification'])), # HARDCODED
			]

		stats_list = [
			xbmcgui.ListItem(label="Watchers", label2=str(self.media['stats']['watchers'])), # HARDCODED
			xbmcgui.ListItem(label="Plays", label2=str(self.media['stats']['plays'])), # HARDCODED
			xbmcgui.ListItem(label="Scrobbles", label2=str(self.media['stats']['scrobbles'])), # HARDCODED
			xbmcgui.ListItem(label="Checkins", label2=str(self.media['stats']['checkins'])), # HARDCODED
			xbmcgui.ListItem(label="Collection", label2=str(self.media['stats']['collection'])), # HARDCODED
		]

		comment_list = []
		for comment in self.comments:
			li = xbmcgui.ListItem(label=comment['user']['username'], label2=comment['text'], thumbnailImage=comment['user']['avatar'])
			li.setProperty("type", comment['type'])
			li.setProperty("spoiler", "true" if comment['spoiler'] else "false")
			comment_list.append(li)

		self.getControl(12000).setImage(fanart)
		self.getControl(12001).setLabel(title)
		self.getControl(12002).setImage(poster)
		self.getControl(12003).setImage("badge-%s.png" % rating if rating else "")
		self.getControl(12004).setImage(watchlist)
		self.getControl(12005).setImage("badge-seen.png" if watched else "")
		self.getControl(12007).setText(overview)
		self.getControl(12008).setLabel(rating_percent)
		self.getControl(12009).setLabel(rating_votes)
		self.getControl(12010).addItems(info_list)
		self.getControl(12011).addItems(stats_list)
		self.getControl(12200).addItems(comment_list)


	def onClick(self, controlID):
		Debug("[GUI][Summary] control pressed: %i" % controlID)
		if controlID == 12200:
			self.getControl(12200).getSelectedItem().setProperty("spoiler", "false")


if __name__ == '__main__':
	if not api.settings:
		api.getAccountSettings()

	gui = traktGUI('TraktGUI.xml', __addonpath__)
	gui.doModal()
	del gui