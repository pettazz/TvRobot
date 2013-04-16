import os
import time, datetime
import uuid

from selenium import webdriver
import transmissionrpc
from transmissionrpc.error import TransmissionError


import core.strings as strings
import core.config as config

from core import selenium_launcher
from core.mysql import DatabaseManager
from core.util import Util
from core.download_manager import DownloadManager
from core.schedule_manager import ScheduleManager
from core.transmission_manager import TransmissionManager
from core.torrent_search_manager import TorrentSearchManager
from core.twilio_manager import TwilioManager
from core.user_manager import UserManager

class TvRobot:

    def __init__(self):
        #set dem loggings
        if not os.path.exists(config.SELENIUM['log_path']):
            os.mkdir(config.SELENIUM['log_path'])
        if not os.path.exists(config.TVROBOT['log_path']):
            os.mkdir(config.TVROBOT['log_path'])

        print strings.HELLO

        

    def __del__(self):
        try:
            self.driver.quit()
        except:
            pass

    def _start_selenium(self):
        if not hasattr(self, 'driver') or self.driver is None:
            if config.SELENIUM['server'] == "localhost":
                self.selenium_server = selenium_launcher.execute_selenium(
                    config.SELENIUM['server'],
                    config.SELENIUM['port'],
                    config.SELENIUM['log_path'])

            for x in range(config.SELENIUM['timeout']):
                try:
                    self.driver = webdriver.Remote("http://%s:%s/wd/hub"%
                        (config.SELENIUM['server'], config.SELENIUM['port']),
                        webdriver.DesiredCapabilities.HTMLUNITWITHJS)
                    #self.driver = webdriver.Firefox()
                    break
                except Exception, e:
                    print e
                    time.sleep(1)

            if not hasattr(self, 'driver') or self.driver is None:
                raise Exception (
                "Couldn't connect to the selenium server at %s after %s seconds." %
                (config.SELENIUM['server'], config.SELENIUM['timeout']))
        else:
            print "selenium driver already initialized"


    def add_download(self, download_type, search, user_id = None, user_phone = None, send_sms = False):
        if user_id is None:
            if user_phone is None:
                raise Exception('Either a user id or phone number is required.')
            user_id = UserManager().get_user_id_by_phone(user_phone)
        if user_phone is None:
            if user_id is None:
                raise Exception('Either a user id or phone number is required.')
            user_phone = UserManager().get_user_phone_by_id(user_id)

        print "Beeeep, searching for %s" % search
        self._start_selenium()
        magnet = TorrentSearchManager(self.driver).get_magnet(search, download_type, False)
        if magnet is None:
            message = "BOOP. Couldn't find %s." % search
        elif magnet is False:
            message = "BOOEEP. The Pirate Bay is overloaded. Try again later."
        else:
            guid, name = self.add_magnet(magnet, download_type)
            self.add_subscription(guid, user_id, search)
            message = "BEEP. Downloading %s." % search
            
        if send_sms:
            TwilioManager().send_sms(user_phone, message)
        return message

    def add_schedule(self, search, user_id = None, user_phone = None, by_date = False):
        if user_id is None:
            user_id = UserManager().get_user_id_by_phone(user_phone)

        print "Beeeep, searching TVRage for %s" % search
        if by_date:
            sch_method = 'DATE'
        else:
            sch_method = 'EPNUM'
        sch = {'name': search, 'phone': user_phone, 'sms_guid': 'lolnah', 'schedule_method': sch_method} #sms_guid is here for backwards compatibility 
        did = ScheduleManager().add_scheduled_episode(sch)
        if did is not None:
            print "added %s as %s" % (sch['name'], did['guid'])
            if 'timestamp' in did.keys() and did['timestamp'] is not None:
                diff = int(did['timestamp']) - time.time()
                days, remainder = divmod(diff, 86400)
                hours = remainder / 3600
                if days > 0:
                    timestr = "Next episode is on in %s day(s), %s hour(s)" % (int(days), int(hours))
                else:
                    timestr = "Next episode is on in %s hour(s)" % int(hours)
            else:
                timestr = ""
            response = "Ok, I added a schedule for %s. %s" % (did['show_name'], timestr)
        else:
            print "Couldn't find a currently airing show called %s " % sch['name']
            response = "Couldn't find a currently airing show called %s " % sch['name']

        return response

    def add_subscription(self, download_guid, user_id, name = ""):
        guid = uuid.uuid4()
        query = """
            INSERT INTO Subscription
            (guid, User, Download, name)
            VALUES
            (%(guid)s, %(user_id)s, %(download_guid)s, %(name)s)
        """
        return DatabaseManager().execute_query_and_close(query, 
            {'guid': guid, 'user_id': user_id, 'download_guid': download_guid, 'name': name})

    def add_magnet(self, magnet_link, download_type, schedule_guid = None):
        print strings.ADDING_MAGNET
        try:
            torrent = TransmissionManager().add_torrent(magnet_link)
            torrent_hash = torrent.hashString
            query = """
                SELECT guid FROM Download WHERE
                transmission_guid = %(transmission_guid)s
            """
            result = DatabaseManager().fetchone_query_and_close(query, {'transmission_guid': torrent_hash})
            if result is not None:
                raise Exception('Torrent already exists in Download Database')
                # same error as below
        except TransmissionError, e:
            # probably due to duplicate torrent trying to be added, TODO: handle this somehow
            # https://github.com/pettazz/TvRobot/issues/19
            raise e

        print strings.ADDING_DOWNLOAD % download_type
        guid = uuid.uuid4()
        
        query = """
            INSERT INTO Download
            (guid, transmission_guid, type, EpisodeSchedule)
            VALUES
            (%(guid)s, %(transmission_guid)s, %(type)s, %(EpisodeSchedule)s)
        """
        DatabaseManager().execute_query_and_close(query, {
            "guid": guid,
            "transmission_guid": torrent_hash,
            "type": download_type, 
            "EpisodeSchedule": schedule_guid
        })
        print strings.ADD_COMPLETED
        return guid, torrent._getNameString()


    def send_completed_sms_subscribers(self, torrent):
        query = """
            SELECT U.phone, S.name FROM User U, Download D, Subscription S WHERE
            D.transmission_guid = %(transmission_guid)s AND
            S.Download = D.guid AND
            U.id = S.User
        """
        result = DatabaseManager().fetchall_query_and_close(query, {'transmission_guid': torrent.hashString})
        if result is not None:
            for res in result:
                phone = res[0]
                if res[1] is None:
                    name = torrent.name
                else:
                    name = res[1]
                TwilioManager().send_sms(phone, "BEEP. File's done: %s" % name)


    def add_scheduled_downloads(self):
        schedules = ScheduleManager().get_scheduled_tv()
        if schedules:
            self._start_selenium()
        for schedule in schedules:
            if schedule[10] == 1:
                if schedule[11] == 'EPNUM':
                    season_num = str(schedule[4]).zfill(2)
                    episode_num = str(schedule[5]).zfill(2)
                    search_str = "%s S%sE%s" % (schedule[1], season_num, episode_num)
                elif schedule[11] == 'DATE':
                    sch_time = datetime.datetime.fromtimestamp(int(schedule[6]))
                    search_str = "%s %s" % (schedule[1], time.strftime(sch_time, "%Y %m %d"))
                else:
                    raise Exception(strings.UNSUPPORTED_SCHEDULE_TYPE % schedule[10])
                print "Beeeep, searching for %s" % search_str
                magnet = TorrentSearchManager(self.driver).get_magnet(search_str, 'Episode', (schedule[7] == 0))
                if magnet:
                    guid, torrent_name = self.add_magnet(magnet, 'Episode', schedule[0])
                    self.add_subscription(guid, schedule[9], search_str)
                    query = """
                        UPDATE EpisodeSchedule SET
                        new = 0 WHERE guid = %(guid)s
                    """
                    DatabaseManager().execute_query_and_close(query, {'guid': schedule[0]})
                else:
                    print "couldn't find a good one. trying again later."
                    ScheduleManager().update_schedule(schedule[0])


    def update_schedules(self, guids=None):
        if guids is None or not type(guids) == list:
            schedules = ScheduleManager().get_old_schedules()
        else:
            schedules = guids
        for schedule in schedules:
            updated = ScheduleManager().update_schedule(schedule[0])
            if updated == False:
                phone = UserManager().get_user_phone_by_id(schedule[9])
                query = """
                    DELETE FROM EpisodeSchedule
                    WHERE guid = %(guid)s
                """
                DatabaseManager().execute_query_and_close(query, {'guid': schedule[0]})
                TwilioManager().send_sms(phone, "Oh noes, looks like %s was cancelled. I had to delete it from my schedules. If this doesn't sound right, try adding it again." % download[1])


    def cleanup_downloads(self, ids=None):
        torrents = TransmissionManager().list()
        if ids is not None:
            torrents = [torrents[num] for num in torrents if str(num) in ids]
        else:
            torrents = [torrents[num] for num in torrents]
        print "I'm gonna try to beep these torrents: %s" % torrents
        for torrent in torrents:
            self.cleanup_download(torrent)

    def cleanup_download(self, torrent):
        if torrent.progress == 100:
            schedule_data = DownloadManager().get_schedule_data(torrent.hashString)
            if schedule_data:
                video_type = 'Episode'
                showname = schedule_data[1]
            else:
                video_type = DownloadManager().get_torrent_type(torrent.hashString)
                showname = None
            if video_type in ('Episode', 'Movie'):
                #single file
                video_file_name = DownloadManager().get_video_file_path(TransmissionManager().get_files(torrent.id))
                if video_file_name is not None and video_type is not None:
                    video_path = "%s/%s" % (TransmissionManager().get_session().download_dir, video_file_name)
                    print strings.MOVING_VIDEO_FILE % (video_type, video_file_name.encode('ascii', 'ignore'))
                    DownloadManager().move_video_file(video_path, video_type, showname)

                    #if this was a decompress created folder, we want to delete the whole thing
                    #otherwise we can count on transmission to delete it properly
                    if video_path.endswith('/*'):
                        print "DELETING GUID"
                        file_path = video_path[:-2]
                        DownloadManager().delete_video_file(file_path)
                    TransmissionManager().remove(torrent.id, delete_data = True)
                    print strings.DOWNLOAD_CLEAN_COMPLETED
                    self.send_completed_sms_subscribers(torrent)
                else:
                    print strings.UNSUPPORTED_FILE_TYPE % torrent.id
            elif video_type in ('Set', 'Season', 'Series'):
                #some movies bro
                video_files = DownloadManager().get_all_video_file_paths(TransmissionManager().get_files(torrent.id), kill_samples=("sample" not in torrent.name.lower()))
                if video_files is not None and video_type is not None:
                    for vidja in video_files:
                        video_path = "%s/%s" % (TransmissionManager().get_session().download_dir, vidja)
                        print strings.MOVING_VIDEO_FILE % (video_type, vidja.encode('ascii', 'ignore'))
                        DownloadManager().move_video_file(video_path, video_type)
                    TransmissionManager().remove(torrent.id, delete_data = True)
                    print strings.DOWNLOAD_CLEAN_COMPLETED
                    self.send_completed_sms_subscribers(torrent)
                else:
                    print strings.UNSUPPORTED_FILE_TYPE % torrent.id
            elif video_type is not None:
                print strings.UNSUPPORTED_DOWNLOAD_TYPE % torrent.id
            else:
                print strings.UNRECOGNIZED_TORRENT % torrent.id
        else:
            print strings.TORRENT_DOWNLOADING % torrent.id