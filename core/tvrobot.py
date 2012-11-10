import os
import time
import uuid

from selenium import webdriver
import transmissionrpc

import core.strings as strings
import core.config as config

from core import selenium_launcher
from core.mysql import DatabaseManager
from core.lock_manager import LockManager
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

    def _start_selenium(self):
        # config.SELENIUM['port'] replaced with '4445' for now to avoid colliding with the cron tvrobot tasks
        if not hasattr(self, 'driver') or self.driver is None:
            if config.SELENIUM['server'] == "localhost":
                self.selenium_server = selenium_launcher.execute_selenium(
                    config.SELENIUM['server'],
                    '4445',
                    config.SELENIUM['log_path'])

            for x in range(config.SELENIUM['timeout']):
                try:
                    self.driver = webdriver.Remote("http://%s:%s/wd/hub"%
                        (config.SELENIUM['server'], '4445'),
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

    def add_download(self, download_type, search, user_id = None, user_phone = None):
        if user_id is None:
            user_id = UserManager().get_user_id_by_phone(user_phone)

        print "Beeeep, searching for %s" % search
        self._start_selenium()
        magnet = TorrentSearchManager(self.driver).get_magnet(search, download_type, False)
        if magnet is None:
            message = "BOOP. Couldn't find %s." % search
        elif magnet is False:
            message = "BOOEEP. The Pirate Bay is overloaded. Try again later."
        else:
            guid = self.add_magnet(magnet, download_type)
            self.add_subscription(guid, user_id, search)
            message = "BEEP. Downloading %s." % search
            
        return message

    def add_schedule(self, search, user_id = None, user_phone = None):
        if user_id is None:
            user_id = UserManager().get_user_id_by_phone(user_phone)

        print "Beeeep, searching TVRage for %s" % search
        sch = {'name': search, 'phone': user_phone, 'sms_guid': 'lolnah'} #sms_guid is here for backwards compatibility 
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

    def add_magnet(self, magnet_link, download_type):
        print strings.ADDING_MAGNET
        torrent = TransmissionManager().add_uri(magnet_link)

        print strings.ADDING_DOWNLOAD % download_type
        guid = uuid.uuid4()
        query = """
            INSERT INTO Download
            (guid, transmission_id, type)
            VALUES
            (%(guid)s, %(transmission_id)s, %(type)s)
        """
        DatabaseManager().execute_query_and_close(query, {
            "guid": guid,
            "transmission_id": torrent.keys()[0],
            "type": download_type
        })
        print strings.ADD_COMPLETED
        return guid


    # not in use yet

    # def send_sms_completed(self, torrent):
    #     query = """
    #         SELECT U.phone, S.name FROM User U, Download D, Subscription S WHERE
    #         D.transmission_id = %(torrent_id)s AND
    #         S.Download = D.guid AND
    #         U.id = S.User
    #     """
    #     result = DatabaseManager().fetchall_query_and_close(query, {'torrent_id': torrent.id})
    #     if result is not None:
    #         for res in result:
    #             phone = res[0]
    #             if res[1] is None:
    #                 name = torrent.name
    #             else:
    #                 name = res[1]
    #             TwilioManager().send_sms(phone, "BEEP. File's done: %s" % name)