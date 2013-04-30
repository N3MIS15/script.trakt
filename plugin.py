# -*- coding: utf-8 -*-
#

import xbmc
import xbmcaddon
import xbmcgui
import random
import datetime
import urllib
from xbmcswift2 import Plugin, ListItem
import utilities as utils
from utilities import Debug
from traktapi import traktAPI

api = traktAPI()
plugin = Plugin()

__addon__ = xbmcaddon.Addon("script.trakt")
__addonpath__    = __addon__.getAddonInfo('path')
icon = __addon__.getAddonInfo("icon")


def show_busy():
    xbmc.executebuiltin('ActivateWindow(busydialog)')


def hide_busy():
    xbmc.executebuiltin('Dialog.Close(busydialog)')


def get_media_id(media):
    if "tvdb_id" in media:
        return media['tvdb_id']
    elif "imdb_id" in media:
        return media['imdb_id']
    elif "tmdb_id" in media:
        return media['tmdb_id']
    else:
        return None


def small_poster(image):
    if not 'poster-small' in image:
        x = image.rfind('.')
        image = image[:x] + '-138' + image[x:]
    return image


def base_media_li(media, media_type):
    if media_type == "episode":
        show = media['show']['title']
        season = media['episode']['season']
        episode = media['episode']['number'] if "number" in media['episode'] else media['episode']['episode']
        ep_name = media['episode']['title']
        label = "%s %ix%02d \"%s\"" % (show, season, episode, ep_name)
        thumbnail = media['show']['images']['poster']
        fanart = media['show']['images']['fanart']
        media_id = get_media_id(media['show'])
    elif media_type == "season":
        show = media['show']['title']
        season = media['season']
        label = "%s S%02d" % (show, season)
        thumbnail = media['show']['images']['poster']
        fanart = media['show']['images']['fanart']
        media_id = get_media_id(media['show'])
    else:
        if "movie" in media:
            media = media['movie']
        elif "show" in media:
            media = media['show']

        label = media['title']
        thumbnail = media['images']['poster']
        fanart = media['images']['fanart']
        media_id = get_media_id(media)

    li = {
        "label": label,
        "thumbnail": thumbnail,
        "replace_context_menu": True,
        "properties": {
            "Fanart_Image": fanart
        }
    }

    if media_type != "season":
        if media_type != "show":
            li['path'] = plugin.url_for("summary", media_type=media_type, media_id=media_id)
        else:
            li['path'] = plugin.url_for("index")

        if media_type != "episode":
            context_summary = ("Summary", "XBMC.RunPlugin(%s)" % plugin.url_for("summary", media_type=media_type, media_id=media_id))
            context_rate = ("Rate", "RunScript(script.trakt,action=rate,media_type=%s,remoteid=%s)" % (media_type, media_id))
            context_add_to_list = ("Add to list", "XBMC.RunPlugin(%s)" % plugin.url_for("add_to_list", media_type=media_type, media_id=media_id))

        else:
            context_summary = ("Summary", "XBMC.Notification(%s,%s,%i,%s)" % ("Add Me", "Episode Summary", 5000, icon))
            context_rate = ("Rate", "RunScript(script.trakt,action=rate,media_type=%s,remoteid=%s,season=%i,episode=%i)" % (media_type, media_id, season, episode))
            context_add_to_list = ("Add to list", "XBMC.RunPlugin(%s)" % plugin.url_for("add_episode_to_list", media_type=media_type, media_id=media_id, season=season, episode=episode))

        li['context_menu'] = [
            context_summary,
            context_rate,
            context_add_to_list
        ]
    else:
        li['path'] = plugin.url_for("index")
        li['context_menu'] = [
            ("Add to list", "XBMC.RunPlugin(%s)" % plugin.url_for("add_season_to_list", media_type=media_type, media_id=media_id, season=season))
        ]
    return li


@plugin.route("/")
def index():
    return [
        {"label": "Trending", "icon": icon, "path": plugin.url_for("trending_sub", media_type="shows")},
        {"label": "Calendar", "icon": icon, "path": plugin.url_for("calendar_sub")},
        {"label": "Charts", "icon": icon, "path": plugin.url_for("index")},
        {"label": "Network", "icon": icon, "path": plugin.url_for("network_sub")},
        {"label": "Recommendations", "icon": icon, "path": plugin.url_for("recommendations_sub")},
        {"label": "Activity", "icon": icon, "path": plugin.url_for("activities_sub")},
        {"label": "My Profile", "icon": icon, "path": plugin.url_for("index")},
        {"label": "My Lists", "icon": icon, "path": plugin.url_for("my_lists")},
        {"label": "Search", "icon": icon, "path": plugin.url_for("search")},
        {"label": "Synchronize", "icon": icon, "path": plugin.url_for("sync")}
    ]


@plugin.route("/trending/")
def trending_sub():
    return [
        {"label": "Trending TV shows", "icon": icon, "path": plugin.url_for("get_trending", media_type="shows")},
        {"label": "Trending Movies", "icon": icon, "path": plugin.url_for("get_trending", media_type="movies")}
    ]


@plugin.route("/get_trending/<media_type>/")
def get_trending(media_type):
    trending_list = list()
    trending = api.getTrending(media_type)

    for media in trending:
        li = base_media_li(media, media_type)

        trending_list.append(li)

    return trending_list


@plugin.route("/calendar/")
def calendar_sub():
    return [
        {"label": "My Shows", "icon": icon, "path": plugin.url_for("get_calendar", calendar_type="my_shows")},
        {"label": "Premieres", "icon": icon, "path": plugin.url_for("get_calendar", calendar_type="premieres")},
        {"label": "All", "icon": icon, "path": plugin.url_for("get_calendar", calendar_type="shows")}
    ]


@plugin.route("/calendar/<calendar_type>/")
def get_calendar(calendar_type):
    calendar_list = list()
    now = datetime.datetime.now()
    calendar = api.getCalendar(calendar_type, "%d%02d%02d" % (now.year, now.month, now.day))

    for day in calendar:
        date = day['date'][5:]
        for ep in day['episodes']:
            li = base_media_li(ep, "episode")
            li['label'] = date + ". " + li['label']

            calendar_list.append(li)

    return calendar_list


@plugin.route("/network/")
def network_sub():
    return [
        {"label": "Friends", "icon": icon, "path": plugin.url_for("get_network", user=utils.getSetting('username').strip(), network_type="friends")},
        {"label": "Following", "icon": icon, "path": plugin.url_for("get_network", user=utils.getSetting('username').strip(), network_type="following")},
        {"label": "Followers", "icon": icon, "path": plugin.url_for("get_network", user=utils.getSetting('username').strip(), network_type="followers")}
    ]


@plugin.route("/network/<user>/<network_type>/")
def get_network(user, network_type):
    network = api.getNetwork(user, network_type)
    return [{"label": x['username'], "icon": x['avatar'], "path": plugin.url_for("index")} for x in network]


@plugin.route("/recommendations/")
def recommendations_sub():
    return [
        {"label": "TV shows", "icon": icon, "path": plugin.url_for("get_recommendations", media_type="shows")},
        {"label": "Movies", "icon": icon, "path": plugin.url_for("get_recommendations", media_type="movies")}
    ]


@plugin.route("/get_recommendations/<media_type>/")
def get_recommendations(media_type):
    recommends_list = list()
    recommends = api.getRecommendations(media_type)
    random.shuffle(recommends)

    for media in recommends:
        li = base_media_li(media, media_type)
        recommends_list.append(li)

    return recommends_list


@plugin.route("/activities/")
def activities_sub():
    return [
        {"label": "Friends Activity", "icon": icon, "path": plugin.url_for("get_activities", who="friends", actions="all")},
        {"label": "Community Activity", "icon": icon, "path": plugin.url_for("get_activities", who="community", actions="all")}
    ]


@plugin.route("/get_activities/<who>/<actions>/")
def get_activities(who, actions):
    activities_list = list()
    activities = api.getActivity(who, "all", actions)

    for activity in activities['activity']:
        if activity['type'] == "episode": # ADD MORE TYPES
            user = activity['user']['username']
            action = activity['action']
            show = activity['show']['title']
            season = activity['episode']['season']
            episode = activity['episode']['number']
            ep_name = activity['episode']['title']
            label = "[COLOR=blue]%s[/COLOR] [B]%s[/B] - %s %ix%02d \"%s\"" % (user, action, show, season, episode, ep_name)
            label2 = "%s %s" % (activity['when']['day'], activity['when']['time'])
            avatar = activity['user']['avatar']

            li = {"label": label, "icon": avatar, "path": plugin.url_for("index")}
            activities_list.append(li)

    return activities_list


@plugin.route("/my_lists/")
def my_lists():
    username = utils.getSetting('username').strip()
    my_lists_list = [{"label": "Watchlist", "icon": icon, "path": plugin.url_for("user_watchlists", username=username)}]
    lists = api.getLists(username)
    my_lists_list.extend([{"label": x['name'], "icon": icon, "path": plugin.url_for("get_user_list", username=username, slug=x['slug'])} for x in lists])

    return my_lists_list


@plugin.route("/list/<username>/<slug>/")
def get_user_list(username, slug):
    _list = api.getUserList(username, slug)
    return [base_media_li(x, x['type']) for x in _list['items']]


@plugin.route("/watchlists/<username>/")
def user_watchlists(username):
    return [
        {"label": "Shows", "icon": icon, "path": plugin.url_for("get_watchlist", username=username, media_type="shows")},
        {"label": "Episodes", "icon": icon, "path": plugin.url_for("get_watchlist", username=username, media_type="episodes")},
        {"label": "Movies", "icon": icon, "path": plugin.url_for("get_watchlist", username=username, media_type="movies")}
    ]


@plugin.route("/watchlists/<username>/<media_type>/")
def get_watchlist(username, media_type):
    watchlist = api.getWatchlist(username, media_type)
    return [base_media_li(x, media_type) for x in watchlist]

@plugin.route("/search/")
def search():
    search_in_list = ["Shows", "Episodes", "Movies", "Users"]
    dialog = xbmcgui.Dialog()
    search_in = dialog.select("Search In", search_in_list)
    search_type = search_in_list[search_in].lower()

    if search_in != -1:
        kb = xbmc.Keyboard("", "Search For")
        kb.doModal()
        if kb.isConfirmed():
            query = urllib.quote_plus(kb.getText())
            results = api.getSearchResults(search_type, query)
            if search_type == "users":
                return [{"label": x['username'], "icon": x['avatar'], "path": plugin.url_for("index")} for x in results]
            else:
                return [base_media_li(x, search_type[:-1]) for x in results]


@plugin.route('/summary/<media_type>/<media_id>/')
def summary(media_type, media_id):
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
    gui.doModal()
    del gui


@plugin.route('/sync/')
def sync():
    utils.setProperty('traktManualSync', 'True')
    return


@plugin.route("/add_to_list/<media_type>/<media_id>/")
def add_to_list(media_type, media_id, season=None, episode=None):
    show_busy()
    username = utils.getSetting('username').strip()

    if media_type.endswith("s"):
        media_type = media_type[:-1]

    if media_id.startswith("tt"):
        id_type = "imdb_id"
    elif media_type in ["show", "episode", "season"] and str(media_id).isdigit():
        id_type = "tvdb_id"
    else:
        id_type = "tmdb_id"

    lists = ["Watchlist"]
    user_lists = api.getLists(username)
    lists.extend([x['name'] for x in user_lists])
    hide_busy()

    dialog = xbmcgui.Dialog()
    chosen_list = dialog.select("Search In", lists)
    show_busy()

    if chosen_list != -1:
        if chosen_list == 0:
            # add to watchlist
            pass
        else:
            _list = user_lists[chosen_list-1]
            data = {
                "slug": _list['slug'],
                "items": [
                    {
                        "type": media_type,
                        id_type: media_id

                    }
                ]
            }

            if season:
                data['items'][0]['season'] = int(season)
            if episode:
                data['items'][0]['episode'] = int(episode)

            result = api.addToList(data)
            hide_busy()
            if not result['skipped_items']:
                # show success dialog
                pass
            else:
                # show failed dialog
                pass
    

@plugin.route("/add_season_to_list/<media_type>/<media_id>/<season>/")
def add_season_to_list(media_type, media_id, season=None):
    add_to_list(media_type, media_id, season)


@plugin.route("/add_episode_to_list/<media_type>/<media_id>/<season>/<episode>/")
def add_episode_to_list(media_type, media_id, season=None, episode=None):
    add_to_list(media_type, media_id, season, episode)





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
            li.setProperty("length", str(len(comment['text'])))
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
    plugin.run()
