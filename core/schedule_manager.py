import time, datetime
import uuid
import requests
import xml.etree.cElementTree as ElementTree

from fuzzywuzzy import process

from config import TVRAGE
from mysql import DatabaseManager
from core.util import XmlDictConfig
from core.user_manager import UserManager

#Getting the offset from the xml is hard
TZ_OFFSET = TVRAGE['tz_offset']
ACTIVE_SHOW_STATUS = ['Returning Series', 'New Series', 'Final Season']

TVRAGE_API_URL = ('http://services.tvrage.com/myfeeds/episodeinfo.php?key=%s' % TVRAGE['api_key']) + '&show=%s'
TVRAGE_EPISODE_API = 'http://services.tvrage.com/feeds/episodeinfo.php?show=%s&ep=%sx%s&key=' + TVRAGE['api_key']

class ScheduleManager:

    def __get_episode_after(self, name, season, episode, try_increment_season = True):
        data = {'season': None, 'episode': None, 'timestamp': None}
        attempted_season = int(season)
        attempted_episode = int(episode) + 1
        try:
            response = requests.get(TVRAGE_EPISODE_API % (name.replace(' ', '%20'), attempted_season, attempted_episode))
        except:
            print "BEEP. TVRage isn't responding to our request for this one, we'll have to try again later."
            return data
        if response.status_code == requests.codes['\o/']:
            root = ElementTree.XML(response.text.encode('ascii', 'ignore'))
            rdata = XmlDictConfig(root)
            print rdata
            if 'status' in rdata.keys() and rdata['status'] in ACTIVE_SHOW_STATUS:
                if 'episode' not in rdata.keys():
                    if try_increment_season:
                        attempted_season = int(season) + 1
                        attempted_episode = 1
                        print "episode not found. searching next season for S%sE%s" % (str(attempted_season).zfill(2), str(attempted_episode).zfill(2))
                        return self.__get_episode_after(name, attempted_season, attempted_episode, False)
                    else:
                        return data

                if (rdata['episode']['number'] == "%sx%s" % (str(attempted_season).zfill(2), str(attempted_episode).zfill(2))) and not rdata['episode']['airdate'] == '0000-00-00' and 'airtime' in rdata.keys():
                    # EPAPI doesnt have timestamps HOORAY
                    airtime = rdata['airtime'].rsplit(' at ', 1)[1]
                    timestring = "%s %s" % (rdata['episode']['airdate'], airtime)
                    try:
                        timestamp = int(datetime.datetime.strptime(timestring, '%Y-%m-%d %I:%M %p').strftime("%s"))
                    except:
                        print "malformed timestring: %s" % timestring
                        return data
                    data['timestamp'] = timestamp
                    data['season'] = attempted_season
                    data['episode'] = attempted_episode
                    # data['timestamp'] = timestamp - TZ_OFFSET
                    data['duration'] = int(rdata['runtime']) * 60
                    data['show_name'] = rdata['name']
                else:
                    # handle this better
                    print "BOOP. Can't find the next episode of %s." % name
                    return data

            else:
                print "ended"
                return False
        else:
            print "BEEP BEEEEEP TVRAGE IS DOWN(%s)" % response.status_code
            raise TVRageDownException()
        return data

    def __get_episode_data(self, name, season, episode):
        data = {'season': None, 'episode': None, 'timestamp': None}
        try:
            response = requests.get(TVRAGE_EPISODE_API % (name.replace(' ', '%20'), season, episode))
        except:
            print "BEEP. TVRage isn't responding to our request for this one, we'll have to try again later."
            return data
        if response.status_code == requests.codes['\o/']:
            root = ElementTree.XML(response.text.encode('ascii', 'ignore'))
            rdata = XmlDictConfig(root)
            print rdata
            if 'status' in rdata.keys() and rdata['status'] in ACTIVE_SHOW_STATUS:
                if 'episode' not in rdata.keys():
                    # handle this better
                    print "BOOP. Can't find episode info for %s S%sE%s." % (name, season, episode)
                    return data

                if (rdata['episode']['number'] == "%sx%s" % (str(season).zfill(2), str(episode).zfill(2))) and not rdata['episode']['airdate'] == '0000-00-00' and 'airtime' in rdata.keys():
                    data['season'] = season
                    data['episode'] = episode
                    # EPAPI doesnt have timestamps HOORAY
                    airtime = rdata['airtime'].rsplit(' at ', 1)[1]
                    timestring = "%s %s" % (rdata['episode']['airdate'], airtime)
                    timestamp = int(datetime.datetime.strptime(timestring, '%Y-%m-%d %I:%M %p').strftime("%s"))
                    data['timestamp'] = timestamp
                    # data['timestamp'] = timestamp - TZ_OFFSET
                    data['duration'] = int(rdata['runtime']) * 60
                    data['show_name'] = rdata['name']
                else:
                    # handle this better
                    print "BOOP. Can't find the next episode of %s." % name
                    return data

            else:
                print "ended"
                return False
        else:
            print "BEEP BEEEEEP TVRAGE IS DOWN(%s)" % response.status_code
            raise TVRageDownException()
        return data

    def __get_next_episode(self, name):
        data = {'season': None, 'episode': None, 'timestamp': None}
        try:
            response = requests.get(TVRAGE_API_URL % name.replace(' ', '%20'))
        except:
            print "BEEP. TVRage isn't responding to our request for this one, we'll have to try again later."
            return data
        if response.status_code == requests.codes['\o/']:
            root = ElementTree.XML(response.text.encode('ascii', 'ignore'))
            rdata = XmlDictConfig(root)
            print rdata
            if 'status' in rdata.keys() and rdata['status'] in ACTIVE_SHOW_STATUS:
                required_keys = ['nextepisode', 'name', 'runtime']
                if set(required_keys).issubset(rdata.keys()) and 'number' in rdata['nextepisode'].keys():
                    epid = rdata['nextepisode']['number']
                    data['season'] = epid.split('x')[0]
                    data['episode'] = epid.split('x')[1]
                    if rdata['nextepisode']['airtime']['text'] is not None:
                        data['timestamp'] = int(rdata['nextepisode']['airtime']['text']) - TZ_OFFSET
                    else:
                        data['timestamp'] = 0
                    data['duration'] = int(rdata['runtime']) * 60
                    data['show_name'] = rdata['name']
                else:
                    print "incomplete data from TVRage. Missing keys:"
                    print [x for x in required_keys if x not in rdata.keys()]
            else:
                print "ended"
                return False
        else:
            print "BEEP BEEEEEP TVRAGE IS DOWN(%s)" % response.status_code
            raise TVRageDownException()
        return data

    def __get_show_data(self, name):
        data = {'season': None, 'episode': None, 'timestamp': None, 'tvrage_show_id': None, 'duration': None}
        #print (TVRAGE_API_URL % name.replace(' ', '%20'))
        response = requests.get(TVRAGE_API_URL % name.replace(' ', '%20'))
        if response.status_code == requests.codes['\o/']:
            root = ElementTree.XML(response.text.encode('ascii', 'ignore'))
            rdata = XmlDictConfig(root)
            print rdata
            if 'status' in rdata.keys() and rdata['status'] in ACTIVE_SHOW_STATUS:
                if 'nextepisode' in rdata.keys():
                    epid = rdata['nextepisode']['number']
                    data['season'] = epid.split('x')[0]
                    data['episode'] = epid.split('x')[1]
                    if rdata['nextepisode']['airtime']['text'] is not None:
                        data['timestamp'] = int(rdata['nextepisode']['airtime']['text']) - TZ_OFFSET
                    else:
                        data['timestamp'] = 0
                data['tvrage_show_id'] = rdata['id']
                data['duration'] = int(rdata['runtime']) * 60
                data['show_name'] = rdata['name']
            else:
                print "ended"
        else:
            print "BEEP BEEEEEP TVRAGE IS DOWN(%s)" % response.status_code
            raise TVRageDownException()
        return data

    def get_old_schedules(self):
        now = time.time()

        query = """
            SELECT * FROM EpisodeSchedule WHERE
            ((timestamp + duration) < %(now)s
            AND new = 0) OR
            timestamp IS NULL
        """
        result = DatabaseManager().fetchall_query_and_close(query, {'now': now})
        return result

    def get_scheduled_tv(self):
        now = time.time()

        query = """
            SELECT * FROM EpisodeSchedule WHERE
            (timestamp + duration) < %(now)s
            AND new = 1
        """
        result = DatabaseManager().fetchall_query_and_close(query, {'now': now})
        return result

    def update_schedule(self, guid, next_episode = True):
        query = """
            SELECT show_name, season_number, episode_number, duration, timestamp FROM EpisodeSchedule WHERE
            guid = %(guid)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'guid': guid})
        print "looking for schedule updates for %s" % result[0]
        try:
            if next_episode:
                if result[1] is not None and result[2] is not None:
                    print "looking for episode after S%sE%s..." % (str(result[1]).zfill(2), str(result[2]).zfill(2))
                    sdata = self.__get_episode_after(result[0], result[1], result[2])
                else:
                    print "looking for nextepisode..."
                    sdata = self.__get_next_episode(result[0])
            else:
                sdata = self.__get_episode_data(result[0], result[1], result[2])
        except TVRageDownException, e:
            return None
        if sdata:
            if result[4] is not None:
                prev_stamp = int(result[4])
            else:
                prev_stamp = 0
            if sdata['timestamp'] is None or (result[1] == int(sdata['season']) and result[2] == int(sdata['episode'])):
                print "none yet."
                return None
            else:
                if sdata['timestamp'] > prev_stamp:
                    sdata['guid'] = guid
                    print "got an update. updating timestamp to %s" % sdata['timestamp']
                    query = """
                        UPDATE EpisodeSchedule SET
                        season_number = %(season)s,
                        episode_number = %(episode)s,
                        timestamp = %(timestamp)s,
                        new = 1
                        WHERE guid = %(guid)s
                    """
                    return DatabaseManager().execute_query_and_close(query, sdata)
        else:
            return False

    def get_next_schedule(self, showname):
        print "raw schedule query for %s, fuzzy matching existing schedules..." % showname
        guessed_name = self.guess_series_name(showname)
        if guessed_name is None:
            return None
        print "querying my schedule for %s" % guessed_name
        query = """
            SELECT timestamp, new FROM EpisodeSchedule
            WHERE show_name = %(name)s
        """
        data = DatabaseManager().fetchone_query_and_close(query, {'name': guessed_name})
        if data is None:
            print "found nothing."
            return None
        if data[1] == 0:
            print "dont have a new schedule"
            return False
        else:
            print "gotcha"
            return data[0]

    def add_scheduled_episode(self, data):
        sdata = self.__get_show_data(data['name'])
        user = UserManager().get_user_id_by_phone(data['phone'])
        if sdata['tvrage_show_id'] is None:
            return None
        else:
            sdata['guid'] = uuid.uuid4()
            sdata['sms_guid'] = data['sms_guid']
            sdata['user_id'] = user
            sdata['new'] = int(sdata['timestamp'] > 0)
            sdata['schedule_method'] = data['schedule_method']
            query = """
                INSERT INTO EpisodeSchedule
                (guid, show_name, tvrage_show_id, duration, season_number, episode_number, timestamp, sms_guid, User, new, schedule_method)
                VALUES (%(guid)s, %(show_name)s, %(tvrage_show_id)s, %(duration)s, %(season)s, %(episode)s, %(timestamp)s, %(sms_guid)s, %(user_id)s, %(new)s, %(schedule_method)s)
            """
            DatabaseManager().execute_query_and_close(query, sdata)
            return sdata

    def guess_series_name(self, download_name):
        query = """ SELECT show_name FROM EpisodeSchedule WHERE 1 """
        shows = [x[0] for x in DatabaseManager().fetchall_query_and_close(query, {})]
        matched = process.extractOne(download_name, shows, score_cutoff=75)
        return matched[0] if matched else None


class TVRageDownException(Exception):
    def __init__(self):
        message = "TVRage is currently down and not responding to API requests."
        Exception.__init__(self, message)