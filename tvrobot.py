import os
import logging

from optparse import OptionParser, OptionValueError
from core.transmission_manager import TransmissionManager

import core.strings as strings
import core.config as config
from core.lock_manager import LockManager
from core.user_manager import UserManager

#hackyhackhacklazy
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

        o.add_option("-u", "--schedule-updates-only", action="store_true", dest="update_schedules_only",
        help="Attempts to update any existing schedules and then exits.")

        o.add_option("-p", "--download-schedules-only", action="store_true", dest="download_scheduled_only",
        help="Attempts to find and download any torrents by schedules and then exits.")

        o.add_option("-s", "--search-only", action="store_true", dest="search_only",
        help="Searches for and adds any scheduled Episodes or Movies and exits. Does not clean up finished torrents.")

        o.add_option("-m", "--add-magnet", action="store", default=None, dest="add_magnet",
        help="Adds the specified magnet URI and exits. This will usually have to be in quotes.")

        o.add_option("-t", "--torrent-type", action="store", default="Episode", dest="add_torrent_type", choices=("Movie", "Episode", "Series", "Season", "Set"),
        help="Specify the type of torrent to add. One of: Movie, Episode (TV), Series (TV), Season (TV), Set (Movies)")

        return o



    ################################################################################################
    #   updated methods using the new tvrobot core
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
        self.add_subscription(guid, name = name, user = user)

    def clean_torrents(self, ids=None):
        lock_guid = LockManager().set_lock('clean')
        try:
            self.robotcore.cleanup_downloads()
        finally:
            LockManager().unlock(lock_guid)

    def clean_torrent(self, torrent):
        lock_guid = LockManager().set_lock('clean_%s' % torrent.id)
        try:
            self.robotcore.cleanup_download(torrent)
        finally:
            LockManager().unlock(lock_guid)

    def add_subscription(self, download_guid, name = "", user = None):
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
    elif robot.options.update_schedules_only:
        robot.run_update_schedules()
    elif robot.options.download_scheduled_only:
        robot.run_schedule_search()
    else:
        robot.search()
        robot.clean_torrents()