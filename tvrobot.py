import os 
import time
import logging
import math
import getpass
import uuid
import traceback
import subprocess

from optparse import OptionParser, OptionValueError
from selenium import webdriver
import transmissionrpc 
from core import selenium_launcher

import core.strings as strings
import core.config as config
from core.mysql import DatabaseManager

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
        if not (self.options.clean_only or (self.options.add_torrent is not None)):
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
                    break
                except:
                    time.sleep(1)

            if not hasattr(self, 'driver') or self.driver is None:
                raise Exception (
                "Couldn't connect to the selenium server at %s after %s seconds." % 
                (config.SELENIUM['server'], config.SELENIUM['timeout']))

        #try to connect to the Transmission server
        self.daemon = transmissionrpc.Client(
            address=config.TRANSMISSION['server'], 
            port=config.TRANSMISSION['port'], 
            user=config.TRANSMISSION['user'], 
            password=config.TRANSMISSION['password'])
        
        print strings.HELLO

    def __signal_catch_stop(self, signal, frame = None):
        """catch a ctrl-c and kill the program"""
        print strings.KILL_CAUGHT
        if hasattr(self, "driver"):
            self.driver.quit()
        os.kill(os.getpid(), 9) 

    def __create_parser(self):
        """optparser"""
        usage = "usage: %prog [options]"
        desc = "TV ROBOT CAN GET YOUR TV AND MOVIES BECAUSE FUCK YEAH!"

        o = OptionParser(usage=usage, description=desc)
        o.add_option("-c", "--clean-only", action="store_true", dest="clean_only", 
        help="Cleans up any already completed torrents and exits. Does not search for or add any torrents.")

        o.add_option("-s", "--search-only", action="store_true", dest="search_only", 
        help="Searches for and adds any scheduled Episodes or Movies and exits. Does not clean up finished torrents.")

        o.add_option("-a", "--add-torrent", action="store", default=None, dest="add_torrent",
        help="Adds the specified torrent and exits.")

        o.add_option("-t", "--torrent-type", action="store", default="Episode", dest="add_torrent_type", choices=("Movie", "Episode", "Series", "Season", "Set"),
        help="Specify the type of torrent to add.")

        return o

    def __get_video_file_path(self, files):
        max_size = 0
        file_id = None
        for torrent_id in files:
            print strings.FINDING_VIDEO_FILE % torrent_id
            for f in files[torrent_id]:
                ext = files[torrent_id][f]['name'].rsplit('.', 1)[1]
                if ext in config.FILETYPES['video'] and \
                    files[torrent_id][f]['size'] > max_size:
                    max_size = files[torrent_id][f]['size']
                    file_name = files[torrent_id][f]['name']
                elif ext in config.FILETYPES['compressed']:
                    #uggggggh
                    if ext == 'zip':
                        return None
                    elif ext == 'rar':
                        print strings.UNRAR
                        return self.__unrar_file(files[torrent_id][f]['name'])
                    else:
                        return None       
        return file_name

    def __get_all_video_file_paths(self, files, kill_samples = True):
        videos = []
        for torrent_id in files:
            print strings.FINDING_VIDEO_FILE % torrent_id
            for f in files[torrent_id]:
                ext = files[torrent_id][f]['name'].rsplit('.', 1)[1]
                if ext in config.FILETYPES['video']:
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
            
    def __unrar_file(self, file_path):
        guid = str(uuid.uuid4().hex)
        if config.TVROBOT['completed_move_method'] == 'FABRIC':
            local_path = self.__shellquote("%s/%s" % (self.daemon.get_session().download_dir, file_path))
            path_to = file_path.rsplit('/', 1)[0]
            remote_path = self.__shellquote("%s/%s/" % (self.daemon.get_session().download_dir, guid))
            try:
                subprocess.check_call("fab unrar_file:rar_path=%s,save_path=%s" % (local_path, remote_path),
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
            file_path = self.__shellquote(file_path)
            try:
                #this isnt a check_call because a lot can go wrong here and its not mission critical
                subprocess.call("fab delete_file:remote_path=%s" % (file_path),
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
            local_path = self.__shellquote(file_path)
            remote_path = self.__shellquote(config.MEDIA['remote_path'][file_type])
            try:
                subprocess.check_call("fab move_video:local_path='%s',remote_path='%s'" % (local_path, remote_path),
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


    ##############################
    # public methods
    ##############################
    def add_torrent(self):
        print strings.ADDING_TORRENT 
        torrent_file = open(self.options.add_torrent, "rb").read().encode("base64")
        torrent = self.daemon.add(torrent_file)

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

        print strings.ADD_COMPLETED

    def clean_torrents(self):
        torrents = self.daemon.list()
        print "I'm gonna try to beep these torrents: %s" % torrents
        for num in torrents:
            if torrents[num].status == 'seeding' or torrents[num].status == 'stopped':
                video_type = self.__get_torrent_type(num)
                if video_type in ('Episode', 'Movie'):
                    #single file 
                    video_file_name = self.__get_video_file_path(self.daemon.get_files(num))
                    if video_file_name is not None and video_type is not None:
                        video_path = "%s/%s" % (self.daemon.get_session().download_dir, video_file_name)
                        print strings.MOVING_VIDEO_FILE % (video_type, video_file_name)
                        self.__move_video_file(video_path, video_type)

                        #if this was a rar created folder, we want to delete the whole thing
                        #otherwise we can count on transmission to delete it properly
                        if video_path.endswith('/*'):
                            file_path = video_path[:-2]
                            self.__delete_video_file(file_path)
                        self.daemon.remove(num, delete_data = True)
                        print strings.DOWNLOAD_CLEAN_COMPLETED
                    else:
                        print strings.UNSUPPORTED_FILE_TYPE % num 
                elif video_type in ('Set', 'Season', 'Series'):
                    #some movies bro
                    video_files = self.__get_all_video_file_paths(self.daemon.get_files(num), kill_samples=("sample" not in torrents[num].name.lower()))
                    if video_files is not None and video_type is not None:
                        for vidja in video_files:
                            video_path = "%s/%s" % (self.daemon.get_session().download_dir, vidja)
                            print strings.MOVING_VIDEO_FILE % (video_type, vidja)
                            self.__move_video_file(video_path, video_type)
                        self.daemon.remove(num, delete_data = True)
                        print strings.DOWNLOAD_CLEAN_COMPLETED
                    else:
                        print strings.UNSUPPORTED_FILE_TYPE % num 
                elif video_type is not None:
                    print strings.UNSUPPORTED_DOWNLOAD_TYPE % num 
                else:
                    print strings.UNRECOGNIZED_TORRENT % num 
            else:
                print strings.TORRENT_DOWNLOADING % num 


#LETS DO THIS SHIT
if __name__ == '__main__':
    robot = TvRobot()
    if robot.options.add_torrent is not None:
        robot.add_torrent()
    else:
        robot.clean_torrents()