import time
import uuid
import requests
import xml.etree.cElementTree as ElementTree

from config import TVRAGE
from mysql import DatabaseManager
from core.util import XmlDictConfig
from core.user_manager import UserManager

#Getting the offset from the xml is hard
TZ_OFFSET = TVRAGE['tz_offset']

TVRAGE_API_URL = ('http://services.tvrage.com/myfeeds/episodeinfo.php?key=%s' % TVRAGE['api_key']) + '&show=%s'

class ScheduleManager:

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
            if rdata['ended'] is None:
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
        return data

    def __get_show_data(self, name):
        data = {'season': None, 'episode': None, 'timestamp': None, 'tvrage_show_id': None, 'duration': None}
        #print (TVRAGE_API_URL % name.replace(' ', '%20'))
        response = requests.get(TVRAGE_API_URL % name.replace(' ', '%20'))
        if response.status_code == requests.codes['\o/']:
            root = ElementTree.XML(response.text.encode('ascii', 'ignore'))
            rdata = XmlDictConfig(root)
            print rdata
            if rdata['ended'] is None:
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

    def update_schedule(self, guid):
        query = """
            SELECT show_name, season_number, episode_number, duration, timestamp FROM EpisodeSchedule WHERE
            guid = %(guid)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'guid': guid})
        print "looking for schedule updates for %s" % result[0]
        sdata = self.__get_next_episode(result[0])
        if sdata:
            if result[4] is not None:
                prev_stamp = int(result[4])
            else:
                prev_stamp = 0
            if sdata['timestamp'] is None or (result[1] == int(sdata['season']) and result[2] == int(sdata['episode'])):
                print "none yet."
                return None
            else:
                if sdata['show_name'] == result[0] and sdata['timestamp'] > prev_stamp:
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

    def add_scheduled_episode(self, data):
        sdata = self.__get_show_data(data['name'])
        user = UserManager().get_user_id_by_phone(data['phone'])
        if sdata['tvrage_show_id'] is None:
            # TODO: make a better way of handling cancelled shows. this is kinda stupid.
            sdata['guid'] = uuid.uuid4()
            sdata['sms_guid'] = data['sms_guid']
            sdata['name'] = data['name']
            sdata['user_id'] = user
            query = """
                INSERT INTO EpisodeSchedule
                (guid, show_name, tvrage_show_id, duration, season_number, episode_number, timestamp, sms_guid, User)
                VALUES (%(guid)s, %(name)s, '0', '0', '0', '0', '4294967295', %(sms_guid)s, %(user_id)s)
            """
            DatabaseManager().execute_query_and_close(query, sdata)
            return None
        else:
            sdata['guid'] = uuid.uuid4()
            sdata['sms_guid'] = data['sms_guid']
            sdata['user_id'] = user
            sdata['new'] = int(sdata['timestamp'] > 0)
            query = """
                INSERT INTO EpisodeSchedule
                (guid, show_name, tvrage_show_id, duration, season_number, episode_number, timestamp, sms_guid, User, new)
                VALUES (%(guid)s, %(show_name)s, %(tvrage_show_id)s, %(duration)s, %(season)s, %(episode)s, %(timestamp)s, %(sms_guid)s, %(user_id)s, %(new)s)
            """
            DatabaseManager().execute_query_and_close(query, sdata)
            return sdata
