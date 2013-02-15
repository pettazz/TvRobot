import os
import logging

from optparse import OptionParser, OptionValueError
from core.twilio_manager import TwilioManager
from core.transmission_manager import TransmissionManager

import core.strings as strings
import core.config as config
from core.mysql import DatabaseManager
from core.lock_manager import LockManager
from core.user_manager import UserManager

#hackyhackhack
from core.tvrobot import TvRobot as TvRobotCore

class TvRobot:

    def __init__(self):
        #set up ^c
        import signal
        signal.signal(signal.SIGINT, self.__signal_catch_stop)
        signal.signal(signal.SIGTERM, self.__signal_catch_stop)

        #get dem options
        o = self.__create_parser()
        (opts, args) = o.parse_args()
        self.options = opts

        self.robotcore = TvRobotCore()

    def __signal_catch_stop(self, signal, frame = None):
        """catch a ctrl-c and kill the program"""
        print strings.KILL_CAUGHT
        LockManager().unlock()
        os.kill(os.getpid(), 9)

    def __create_parser(self):
        """optparser"""
        usage = "usage: %prog [options]"
        desc = "TV ROBOT CAN GET YOUR TV AND MOVIES BECAUSE FUCK YEAH!"

        o = OptionParser(usage=usage, description=desc)
        o.add_option("-c", "--clean-only", action="store_true", dest="clean_only",
        help="Cleans up any already completed downloads and exits. Does not search for or add any torrents.")

        o.add_option("-i", "--clean-ids", action="store", type="string", dest="clean_ids",
        help="Cleans up specific Transmission download ids and then stops. Comma separated list.")

        o.add_option("-u", "--schedule-updates-only", action="store_true", dest="schedule_updates_only",
        help="Attempts to update any existing schedules and then exits.")

        # o.add_option("-x", "--sms-update-only", action="store_true", dest="sms_updates_only",
        # help="Attempts to add any newly received sms schedules and then exits.")
        # This action is deprecated through this API, the new core.tvrobot.TvRobot class handles this

        o.add_option("-p", "--download-schedules-only", action="store_true", dest="download_schedules_only",
        help="Attempts to find and download any torrents by schedules and then exits.")

        o.add_option("-s", "--search-only", action="store_true", dest="search_only",
        help="Searches for and adds any scheduled Episodes or Movies and exits. Does not clean up finished torrents.")

        # o.add_option("-a", "--add-torrent", action="store", default=None, dest="add_torrent",
        # help="Adds the specified torrent file and exits.")
        # Torrent files are deprecated. Use magnets.

        o.add_option("-m", "--add-magnet", action="store", default=None, dest="add_magnet",
        help="Adds the specified magnet URI and exits. This will usually have to be in quotes.")

        o.add_option("-t", "--torrent-type", action="store", default="Episode", dest="add_torrent_type", choices=("Movie", "Episode", "Series", "Season", "Set"),
        help="Specify the type of torrent to add. One of: Movie, Episode (TV), Series (TV), Season (TV), Set (Movies)")

        return o






    def __get_torrent_type(self, torrent_id):
        query = """
            SELECT type FROM Download WHERE
            transmission_id = %(torrent_id)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'torrent_id': torrent_id})
        if result is not None:
            result = result[0]
        return result

    def clean_torrent(self, torrent):
        if torrent.progress == 100:
            video_type = self.__get_torrent_type(torrent.id)
            if video_type in ('Episode', 'Movie'):
                #single file
                video_file_name = self.__get_video_file_path(TransmissionManager().get_files(torrent.id))
                if video_file_name is not None and video_type is not None:
                    video_path = "%s/%s" % (TransmissionManager().get_session().download_dir, video_file_name)
                    print strings.MOVING_VIDEO_FILE % (video_type, video_file_name)
                    self.__move_video_file(video_path, video_type)

                    #if this was a decompress created folder, we want to delete the whole thing
                    #otherwise we can count on transmission to delete it properly
                    if video_path.endswith('/*'):
                        print "DELETING GUID"
                        file_path = video_path[:-2]
                        self.__delete_video_file(file_path)
                    TransmissionManager().remove(torrent.id, delete_data = True)
                    print strings.DOWNLOAD_CLEAN_COMPLETED
                    self.__send_sms_completed(torrent)
                else:
                    print strings.UNSUPPORTED_FILE_TYPE % torrent.id
            elif video_type in ('Set', 'Season', 'Series'):
                #some movies bro
                video_files = self.__get_all_video_file_paths(TransmissionManager().get_files(torrent.id), kill_samples=("sample" not in torrent.name.lower()))
                if video_files is not None and video_type is not None:
                    for vidja in video_files:
                        video_path = "%s/%s" % (TransmissionManager().get_session().download_dir, vidja)
                        print strings.MOVING_VIDEO_FILE % (video_type, vidja)
                        self.__move_video_file(video_path, video_type)
                    TransmissionManager().remove(torrent.id, delete_data = True)
                    print strings.DOWNLOAD_CLEAN_COMPLETED
                    self.__send_sms_completed(torrent)
                else:
                    print strings.UNSUPPORTED_FILE_TYPE % torrent.id
            elif video_type is not None:
                print strings.UNSUPPORTED_DOWNLOAD_TYPE % torrent.id
            else:
                print strings.UNRECOGNIZED_TORRENT % torrent.id
        else:
            print strings.TORRENT_DOWNLOADING % torrent.id

    def clean_torrents(self, ids=None):
        lock_guid = LockManager().set_lock('clean')
        try:
            torrents = TransmissionManager().list()
            if ids is not None:
                torrents = [torrents[num] for num in torrents if str(num) in ids]
            else:
                torrents = [torrents[num] for num in torrents]
            print "I'm gonna try to beep these torrents: %s" % torrents
            for torrent in torrents:
                self.clean_torrent(torrent)
        finally:
            LockManager().unlock(lock_guid)


    ################################################################################################
    #   updated methods
    ################################################################################################

    def search(self):
        self.run_update_schedules()
        self.run_schedule_search()

    def run_update_schedules(self):
        self.robotcore.update_schedules()

    def run_schedule_search(self):
        self.robotcore.add_scheduled_downloads()

    def add_magnet(self, magnet_link = None, download_type = None, name = None, user = None):
        guid = self.robotcore.add_magnet(magnet_link, download_type)
        self.__add_subscription(guid, name = name, user = user)

    def __send_sms_completed(self, torrent):
        self.robotcore.send_completed_sms_subscribers(torrent)

    def __add_subscription(self, download_guid, name = "", user = None):
        if user is None:
            user_id = UserManager().get_user_id()
        self.robotcore.add_subscription(download_guid, user_id, name = "")


if __name__ == '__main__':
    robot = TvRobot()
    if robot.options.add_magnet is not None:
        robot.add_magnet()
    elif robot.options.clean_ids is not None:
        ids = [x.strip() for x in robot.options.clean_ids.split(',')]
        robot.clean_torrents(ids)
    elif robot.options.search_only:
        robot.search()
    elif robot.options.clean_only:
        robot.clean_torrents()
    elif robot.options.schedule_updates_only:
        robot.run_update_schedules()
    elif robot.options.download_schedules_only:
        robot.run_schedule_search()
    else:
        robot.search()
        robot.clean_torrents()