import os
import time, datetime
import uuid

import transmissionrpc
from transmissionrpc.error import TransmissionError

import core.strings as strings
import core.config as config

from core.mysql import DatabaseManager
from core.util import Util
from core.download_manager import DownloadManager
from core.download_manager import FakeDownloadException
from core.schedule_manager import ScheduleManager
from core.schedule_manager import TVRageDownException
from core.transmission_manager import TransmissionManager
from core.torrent_search_manager import TorrentSearchManager
from core.twilio_manager import TwilioManager
from core.user_manager import UserManager

class TvRobot:

    def __init__(self):
        #set dem loggings
        if not os.path.exists(config.TVROBOT['log_path']):
            os.mkdir(config.TVROBOT['log_path'])

        print strings.HELLO


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
        magnet = TorrentSearchManager().get_magnet(search, download_type, False)
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
        response = None
        if user_id is None:
            user_id = UserManager().get_user_id_by_phone(user_phone)

        print "Beeeep, searching TVRage for %s" % search
        if by_date:
            sch_method = 'DATE'
        else:
            sch_method = 'EPNUM'
        sch = {'name': search, 'phone': user_phone, 'sms_guid': 'lolnah', 'schedule_method': sch_method} #sms_guid is here for backwards compatibility 
        try:
            did = ScheduleManager().add_scheduled_episode(sch)
        except TVRageDownException, e:
            response = "Boop. TVRage is down right now, try again later."
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
        elif response is not None:
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
            exists = False
        except TransmissionError, e:
            exists = True

        torrent_hash = torrent.hashString
        query = """
            SELECT guid FROM Download WHERE
            transmission_guid = %(transmission_guid)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'transmission_guid': torrent_hash})
        if result is not None or exists:
            print strings.ADDING_DUPLICATE_MAGNET
            guid = result[0]
        else:
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
        self.send_sms_to_subscribers(torrent, "BEEP. File's done: %(name)s")

    def send_sms_to_subscribers(self, torrent, message):
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
                TwilioManager().send_sms(phone, message % {"name": name})


    def add_scheduled_downloads(self):
        schedules = ScheduleManager().get_scheduled_tv()
        for schedule in schedules:
            if schedule[10] == 1:
                if schedule[11] == 'EPNUM':
                    season_num = str(schedule[4]).zfill(2)
                    episode_num = str(schedule[5]).zfill(2)
                    search_str = "%s S%sE%s" % (schedule[1], season_num, episode_num)
                elif schedule[11] == 'DATE':
                    sch_time = datetime.datetime.fromtimestamp(int(schedule[6]))
                    search_str = "%s %s" % (schedule[1], time.strftime("%Y %m %d", sch_time.timetuple()))
                else:
                    raise Exception(strings.UNSUPPORTED_SCHEDULE_TYPE % schedule[10])
                print "Beeeep, searching for %s" % search_str
                magnet = TorrentSearchManager().get_magnet(search_str, 'Episode', (schedule[7] == 0))
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
                    ScheduleManager().update_schedule(schedule[0], False)


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
                if video_type in ['Episode', 'Series', 'Season']:
                    showname = ScheduleManager().guess_series_name(torrent.name)
                else:
                    showname = None
            if video_type in ('Episode', 'Movie'):
                #single file
                try:
                    video_file_name = DownloadManager().get_video_file_path(TransmissionManager().get_files(torrent.id))
                except FakeDownloadException, e:
                    print "FAKE DOWNLOAD DETECTED!"
                    self.send_sms_to_subscribers(torrent, "BOOP. Fake download detected: %(name)s")
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
                try:
                    video_files = DownloadManager().get_all_video_file_paths(TransmissionManager().get_files(torrent.id), kill_samples=("sample" not in torrent.name.lower()))
                except FakeDownloadException, e:
                    print "FAKE DOWNLOAD DETECTED!"
                    self.send_sms_to_subscribers(torrent, "BOOP. Fake download detected: %(name)s")
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
