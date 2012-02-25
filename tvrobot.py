import os 
import time
import logging
import math
import getpass
import uuid
import traceback
import subprocess
import hashlib

from optparse import OptionParser, OptionValueError
from selenium import webdriver
import transmissionrpc 
from core import selenium_launcher
from core.google_voice_manager import GoogleVoiceManager
from core.transmission_manager import TransmissionManager

import core.strings as strings
import core.config as config
from core.mysql import DatabaseManager
from core.lock_manager import LockManager
from core.user_manager import UserManager
from core.schedule_manager import ScheduleManager
from core.torrent_search_manager import TorrentSearchManager

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

        #set dem loggings
        if not os.path.exists(config.SELENIUM['log_path']):
            os.mkdir(config.SELENIUM['log_path'])
        if not os.path.exists(config.TVROBOT['log_path']):
            os.mkdir(config.TVROBOT['log_path'])

        #start the selenium server if we need to and try to connect
        if not (self.options.clean_only or (self.options.add_torrent is not None) or (self.options.clean_ids is not None) or (self.options.add_magnet is not None)):
            if config.SELENIUM['server'] == "localhost":
                selenium_launcher.execute_selenium(
                    config.SELENIUM['server'], 
                    config.SELENIUM['port'],
                    config.SELENIUM['log_path'])

            for x in range(config.SELENIUM['timeout']):
                try:
                    self.driver = webdriver.Remote("http://%s:%s/wd/hub"%
                        (config.SELENIUM['server'], config.SELENIUM['port']),
                        webdriver.DesiredCapabilities.HTMLUNIT)
                    #self.driver = webdriver.Firefox()
                    break
                except:
                    time.sleep(1)

            if not hasattr(self, 'driver') or self.driver is None:
                raise Exception (
                "Couldn't connect to the selenium server at %s after %s seconds." % 
                (config.SELENIUM['server'], config.SELENIUM['timeout']))
        
        print strings.HELLO

    def __del__(self):
        self.driver.quit()

    def __signal_catch_stop(self, signal, frame = None):
        """catch a ctrl-c and kill the program"""
        print strings.KILL_CAUGHT
        LockManager().unlock()
        if hasattr(self, "driver"):
            self.driver.quit()
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

        o.add_option("-s", "--search-only", action="store_true", dest="search_only", 
        help="Searches for and adds any scheduled Episodes or Movies and exits. Does not clean up finished torrents.")

        o.add_option("-a", "--add-torrent", action="store", default=None, dest="add_torrent",
        help="Adds the specified torrent file and exits.")

        o.add_option("-m", "--add-magnet", action="store", default=None, dest="add_magnet",
        help="Adds the specified magnet URI and exits. This will usually have to be in quotes.")

        o.add_option("-t", "--torrent-type", action="store", default="Episode", dest="add_torrent_type", choices=("Movie", "Episode", "Series", "Season", "Set"),
        help="Specify the type of torrent to add. One of: Movie, Episode (TV), Series (TV), Season (TV), Set(Movies)")

        return o

    def __get_video_file_path(self, files):
        max_size = 0
        file_id = None
        decompress = False
        for torrent_id in files:
            print strings.FINDING_VIDEO_FILE % torrent_id
            for f in files[torrent_id]:
                ext = files[torrent_id][f]['name'].rsplit('.', 1)[1]
                if ext in config.FILETYPES['video'] and files[torrent_id][f]['size'] > max_size:
                    decompress = False
                    max_size = files[torrent_id][f]['size']
                    file_name = files[torrent_id][f]['name']
                elif ext in config.FILETYPES['compressed'] and files[torrent_id][f]['size'] > max_size:
                    if ext == 'zip':
                        decompress = 'zip'
                        max_size = files[torrent_id][f]['size']
                        file_name = files[torrent_id][f]['name']
                    elif ext == 'rar':
                        decompress = 'rar'
                        max_size = files[torrent_id][f]['size']
                        file_name = files[torrent_id][f]['name']
                    else:
                        return None    
        if decompress == 'rar':
            file_name = self.__unrar_file(file_name)
        if decompress == 'zip':
            file_name = self.__unzip_file(file_name)
        return file_name

    def __get_all_video_file_paths(self, files, kill_samples = True):
        videos = []
        for torrent_id in files:
            print strings.FINDING_VIDEO_FILE % torrent_id
            for f in files[torrent_id]:
                ext = files[torrent_id][f]['name'].rsplit('.', 1)[1]
                if ext in config.FILETYPES['video'] and (files[torrent_id][f]['selected']):
                    if kill_samples:
                        if "sample" not in files[torrent_id][f]['name'].lower() and "trailer" not in files[torrent_id][f]['name'].lower():
                            videos.append(files[torrent_id][f]['name'])
                    else:
                        videos.append(files[torrent_id][f]['name'])
                elif ext in config.FILETYPES['compressed']:
                    raise Exception("I NEVER THOUGHT THIS WOULD HAPPEN OH GOD WHAT KIND OF A SICK MIND DOES THIS??")
        if len(videos) > 0:
            return videos
        else:
            return None

    def __get_torrent_type(self, torrent_id):
        query = """
            SELECT type FROM Download WHERE
            transmission_id = %(torrent_id)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'torrent_id': torrent_id})
        if result is not None:
            result = result[0]
        return result
            
    def __send_sms_completed(self, torrent):
        query = """
            SELECT U.phone, S.name FROM User U, Download D, Subscription S WHERE
            D.transmission_id = %(torrent_id)s AND
            S.Download = D.guid AND
            U.id = S.User
        """
        result = DatabaseManager().fetchall_query_and_close(query, {'torrent_id': torrent.id})
        if result is not None:
            for res in result:
                phone = res[0]
                if res[1] is not None:
                    name = torrent.name
                else:
                    name = res[1]
                GoogleVoiceManager().send_message(phone, "BEEP. File's done: %s" % name)
        
    def __add_subscription(self, download_guid, name = ""):
        guid = uuid.uuid4()
        user_id = UserManager().get_user_id()
        query = """
            INSERT INTO Subscription
            (guid, User, Download, name)
            VALUES
            (%(guid)s, %(user_id)s, %(download_guid)s, %(name)s)
        """
        return DatabaseManager().execute_query_and_close(query, {'guid': guid, 'user_id': user_id, 'download_guid': download_guid, 'name': name})

    def __unrar_file(self, file_path):
        print strings.UNRAR
        guid = str(uuid.uuid4().hex)
        if config.TVROBOT['completed_move_method'] == 'FABRIC':
            # local_path = "%s/%s" % (TransmissionManager().get_session().download_dir, file_path)
            local_path = self.__shellquote("%s/%s" % (TransmissionManager().get_session().download_dir, file_path))
            path_to = file_path.rsplit('/', 1)[0]
            # remote_path = "%s/%s/" % (TransmissionManager().get_session().download_dir, guid)
            remote_path = self.__shellquote("%s/%s/" % (TransmissionManager().get_session().download_dir, guid))
            try:
                subprocess.check_call("fab unrar_file:rar_path='%s',save_path='%s'" % (local_path, remote_path),
                    stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            except Exception, e:
                print strings.CAUGHT_EXCEPTION
                raise e
        else: #config.TVROBOT['completed_move_method'] == 'LOCAL':
            pass    
        return "%s/*" % guid 
            
    def __unzip_file(self, file_path):
        print strings.UNZIP
        guid = str(uuid.uuid4().hex)
        if config.TVROBOT['completed_move_method'] == 'FABRIC':
            # local_path = "%s/%s" % (TransmissionManager().get_session().download_dir, file_path)
            local_path = self.__shellquote("%s/%s" % (TransmissionManager().get_session().download_dir, file_path))
            path_to = file_path.rsplit('/', 1)[0]
            # remote_path = "%s/%s/" % (TransmissionManager().get_session().download_dir, guid)
            remote_path = self.__shellquote("%s/%s/" % (TransmissionManager().get_session().download_dir, guid))
            try:
                subprocess.check_call("fab unzip_file:zip_path='%s',save_path='%s'" % (local_path, remote_path),
                    stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            except Exception, e:
                print strings.CAUGHT_EXCEPTION
                raise e
        else: #config.TVROBOT['completed_move_method'] == 'LOCAL':
            pass    
        return "%s/*" % guid 
            
    def __delete_video_file(self, file_path):
        if config.TVROBOT['completed_move_method'] == 'FABRIC':
            # file_path = self.__shellquote(file_path)
            try:
                #this isnt a check_call because a lot can go wrong here and its not mission critical
                subprocess.call("fab delete_file:remote_path=\"%s\"" % (file_path),
                    stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            except Exception, e:
                print strings.CAUGHT_EXCEPTION
                raise e
        else: #config.TVROBOT['completed_move_method'] == 'LOCAL':
            pass     

    def __move_video_file(self, file_path, file_type):
        if config.TVROBOT['completed_move_method'] == 'FABRIC':
            video_name = file_path.rsplit('/', 1)[1]
            local_path = file_path
            # local_path = self.__shellquote(file_path)
            remote_path = config.MEDIA['remote_path'][file_type]
            # remote_path = self.__shellquote(config.MEDIA['remote_path'][file_type])
            try:
                cmd = "fab move_video:local_path=\"%s\",remote_path=\"%s\"" % (local_path, remote_path)
                subprocess.check_call(cmd,
                    stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            except Exception, e:
                print strings.CAUGHT_EXCEPTION
                raise e
        else: #config.TVROBOT['completed_move_method'] == 'LOCAL':
            pass

    def __shellquote(self, s):
        return s.replace(' ', '\ ').replace('(', '\(').replace(')', '\)').replace("'", "\\'").replace('&', '\&').replace(',', '\,').replace('!', '\!')

    def __compare_passwords(self, given_password, existing_hash):
        salt = existing_hash.split('$')[0]
        hashed_password = self.__hash_password(given_password, salt)
        return hashed_password == existing_hash

    def __hash_password(self, password, salt=None):
        if salt is None:
            salt = str(uuid.uuid4().hex)
        return "%s$%s" % (salt, hashlib.sha512(password + salt).hexdigest())


    ##############################
    # public methods
    ##############################
    def add_torrent(self, name = None):
        print strings.ADDING_TORRENT 
        torrent_file = open(self.options.add_torrent, "rb").read().encode("base64")
        torrent = TransmissionManager().add(torrent_file)

        print strings.ADDING_DOWNLOAD % self.options.add_torrent_type
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
            "type": self.options.add_torrent_type
        })

        self.__add_subscription(guid, name)
        print strings.ADD_COMPLETED

    def add_magnet(self, magnet_link = None, download_type = None, name = None):
        print strings.ADDING_MAGNET
        if magnet_link is None:
            magnet_link = self.options.add_magnet
        if download_type is None:
            download_type = self.options.add_torrent_type
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

        self.__add_subscription(guid, name)
        print strings.ADD_COMPLETED

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

    def search(self):
        lock_guid = LockManager().set_lock('update_schedules')
        try:
            tv_downloads = ScheduleManager().get_scheduled_tv()
            for download in tv_downloads:
                if download[6] is None:
                    ScheduleManager().update_schedule(download[0])
        finally:
            LockManager().unlock(lock_guid)

        lock_guid = LockManager().set_lock('sms_schedules')
        try:
            sms_schedules = GoogleVoiceManager().get_new_schedule_messages()
            for sch in sms_schedules:
                if sch['type'] == 'TV':
                    #print sch
                    did = ScheduleManager().add_scheduled_episode(sch)
                    if did is not None:
                        print "added %s as %s" % (sch['name'], did)
                        GoogleVoiceManager().send_message(sch['phone'], "Ok, I added a schedule for %s" % sch['name'])
                    else:
                        print "Couldn't find a show called %s " % sch['name']
                        GoogleVoiceManager().send_message(sch['phone'], "Couldn't find a show called %s " % sch['name'])
                elif sch['type'] == 'MOVIE':
                    print "No movies yet."
                    #ScheduleManager().add_scheduled_movie(sch)
                else:
                    print "I dunno wat dat shit be."
        finally:
            LockManager().unlock(lock_guid)

        lock_guid = LockManager().set_lock('schedule_search')
        try:
            tv_downloads = ScheduleManager().get_scheduled_tv()
            for download in tv_downloads:
                season_num = str(download[4]).zfill(2)
                episode_num = str(download[5]).zfill(2)
                search_str = "%s S%sE%s" % (download[1], season_num, episode_num)
                print "Beeeep, searching for %s" % search_str
                magnet = TorrentSearchManager(self.driver).get_magnet(search_str, 'TV', (download[7] == 0))
                if magnet is not None:
                    self.add_magnet(magnet, 'Episode', search_str)
                    ScheduleManager().update_schedule(download[0])
                else:
                    print "couldn't find a good one. trying again later."
        finally:
            LockManager().unlock(lock_guid)

        """lock_guid = LockManager().set_lock('sms_search')
        try:
            sms_downloads = GoogleVoiceManager().get_new_download_messages()
            for download in sms_downloads:
                print "Not yet."
        finally:
            LockManager().unlock(lock_guid)"""
        


if __name__ == '__main__':
    robot = TvRobot()
    if robot.options.add_torrent is not None:
        robot.add_torrent()
    elif robot.options.add_magnet is not None:
        robot.add_magnet()
    elif robot.options.clean_ids is not None:
        ids = [x.strip() for x in robot.options.clean_ids.split(',')]
        robot.clean_torrents(ids)
    elif robot.options.search_only:
        robot.search()
    elif robot.options.clean_only:
        robot.clean_torrents()
    else:
        robot.search()
        robot.clean_torrents()