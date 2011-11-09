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
        if config.SELENIUM['server'] == "localhost" and False:
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
        
        print "Sup everybody. I'm a friendly TvRobot. Beep."

    def __signal_catch_stop(self, signal, frame = None):
        """catch a ctrl-c and kill the program"""
        if hasattr(self, "driver"):
            self.driver.quit()
        os.kill(os.getpid(), 9) 

    def __create_parser(self):
        """optparser"""
        usage = "usage: %prog [options]"
        desc = "TV ROBOT CAN GET YOUR TV AND MOVIES BECAUSE FUCK YEAH!"

        o = OptionParser(usage=usage, description=desc)
        #o.add_option("-l", "--log_path", default="logs", action="store", 
        #type="string", help="Path to dump all the logs into.")

        return o

    def __get_video_file_id(self, files):
        max_size = 0
        file_id = None
        for torrent_id in files:
            print "beep booping torrent #%s" % torrent_id
            for f in files[torrent_id]:
                ext = files[torrent_id][f]['name'].rsplit('.', 1)[1]
                if ext in config.FILETYPES['video'] and \
                    files[torrent_id][f]['size'] > max_size:
                    max_size = files[torrent_id][f]['size']
                    file_id = f
                elif ext in config.FILETYPES['compressed']:
                    #uggggggh
                    if ext == 'zip':
                        return None
                    elif ext == 'rar':
                        return None
                    else:
                        return None       
        return file_id

    def __get_torrent_type(self, torrent_id):
        query = """
            SELECT type FROM Download WHERE
            transmission_id = %(torrent_id)s
        """
        result = DatabaseManager().fetchone_query_and_close(query, {'torrent_id': torrent_id})
        if result is not None:
            result = result[0]
        return result
            
    def __move_video_file(self, file_path, file_type):
        if config.TVROBOT['completed_move_method'] == 'FABRIC':
            video_name = file_path.rsplit('/', 1)[1]
            local_path = self.__shellquote(file_path)
            remote_path = self.__shellquote(config.MEDIA['remote_path'][file_type])
            try:
                subprocess.check_call("fab move_video:local_path=%s,remote_path=%s" % (local_path, remote_path),
                    stdout=open("%s/log_fabfileOutput.txt" % (config.TVROBOT['log_path']), "a"),
                    stderr=open("%s/log_fabfileError.txt" % (config.TVROBOT['log_path']), "a"),
                    shell=True)
            except Exception, e:
                print "BEEEEEEEEEEEEEEEEEEEP. OW."
                raise e
        else: #config.TVROBOT['completed_move_method'] == 'LOCAL':
            pass

    def __shellquote(self, s):
        return "'" + s.replace("'", "'\\''") + "'"


    ##############################
    # public methods
    ##############################
    def clean_torrents(self):
        torrents = self.daemon.list()
        print "I'm gonna try to beep these torrents: %s" % torrents
        for num in torrents:
            if torrents[num].status == 'seeding' or torrents[num].status == 'stopped':
                video_type = self.__get_torrent_type(num)
                if video_type in ('Episode', 'Movie'):
                    video_file_id = self.__get_video_file_id(self.daemon.get_files(num))
                    if video_file_id is not None and video_type is not None:
                        video_path = "%s/%s" % (
                            self.daemon.get_session().download_dir,
                            self.daemon.get_files(num)[num][video_file_id]['name'])
                        print "beep beep bopping %s file `%s`..." % (video_type, self.daemon.get_files(num)[num][video_file_id]['name'])
                        self.__move_video_file(video_path, video_type)
                        self.daemon.remove(num, delete_data = True)
                        print "beep. File's done."
                    else:
                        print "I don't know how to beep boop this kind of download yet. Skipping torrent # %s" % num 
                elif video_type in ('Set', 'Season', 'Series'):
                    print "Beeeeeeeooooppppp I can't do it yet. Too many files. :( Skipping torrent # %s" % num 
                else:
                    print "Booeep. Do I know you? Skipping torrent # %s" % num 
            else:
                print "Boop. This one is still working. Skipping torrent # %s" % num 


#LETS DO THIS SHIT
if __name__ == '__main__':
    robot = TvRobot()
    robot.clean_torrents()