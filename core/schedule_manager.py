import time
import uuid
import requests
import xml.etree.cElementTree as ElementTree

from mysql import DatabaseManager
from core.util import XmlDictConfig

TVRAGE_API_URL = 'http://services.tvrage.com/feeds/episodeinfo.php?show=%s&exact=1'

class ScheduleManager:

    def __get_next_episode(self, name):
        data = {'season': None, 'episode': None, 'timestamp': None}
        response = requests.get(TVRAGE_API_URL % name)
        if response.status_code == requests.codes['\o/']:
            root = ElementTree.XML(response.text)
            rdata = XmlDictConfig(root)
            if rdata['ended'] is None:
                epid = rdata['nextepisode']['number']
                data['season'] = epid.split('x')[0]
                data['episode'] = epid.split('x')[1]
                data['timestamp'] = rdata['nextepisode']['airtime']['text']
            else:
                print "ended"
        else:
            print "BEEP BEEEEEP TVRAGE IS DOWN(%s)" % response.status_code
        return data

    def __get_episode_data(self, name):
        data = {'season': None, 'episode': None, 'timestamp': None, 'tvrage_show_id': None, 'duration': None}
        response = requests.get(TVRAGE_API_URL % name)
        if response.status_code == requests.codes['\o/']:
            root = ElementTree.XML(response.text)
            rdata = XmlDictConfig(root)
            if rdata['ended'] is None:
                epid = rdata['nextepisode']['number']
                data['season'] = epid.split('x')[0]
                data['episode'] = epid.split('x')[1]
                data['timestamp'] = rdata['nextepisode']['airtime']['text']
                data['tvrage_show_id'] = rdata['id']
                data['duration'] = int(rdata['runtime']) * 60
                data['show_name'] = rdata['name']
        else:
            print "BEEP BEEEEEP TVRAGE IS DOWN(%s)" % response.status_code
        return data

    def get_scheduled_tv(self):
        now = time.time()

        query = """
            SELECT * FROM EpisodeSchedule WHERE
            (timestamp + duration) < %(now)s
        """
        result = DatabaseManager().fetchall_query_and_close(query, {'now': now})
        return result

    def update_schedule(self, guid):
        query = """
            SELECT show_name FROM EpisodeSchedule WHERE
            guid = %(guid)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'guid': guid})
        sdata = self.__get_next_episode(result[0])
        query = """
            UPDATE EpisodeSchedule SET
            season_number = %(season)s,
            episode_number = %(episode)s,
            timestamp = %(timestamp)s
        """
        return DatabaseManager().execute_query_and_close(query, sdata)

    def add_scheduled_episode(self, data):
        sdata = self.__get_episode_data(data['name'])
        sdata['guid'] = uuid.uuid4()
        sdata['sms_guid'] = data['sms_guid']
        query = """
            INSERT INTO EpisodeSchedule
            (guid, show_name, tvrage_show_id, duration, season_number, episode_number, timestamp, sms_guid)
            VALUES (%(guid)s, %(show_name)s, %(tvrage_show_id)s, %(duration)s, %(season)s, %(episode)s, %(timestamp)s, %(sms_guid)s)
        """
        DatabaseManager().execute_query_and_close(query, sdata)
        return sdata['guid']
