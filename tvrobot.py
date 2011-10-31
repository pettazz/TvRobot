import os 
import time
import logging
import math
import getpass
import uuid
import traceback

from optparse import OptionParser, OptionValueError
from selenium import webdriver
import transmissionrpc 
from core import selenium_launcher

import core.config as config
from core.mysql import DatabaseManager

class TvRobot:

    def __init__(self):
        #set up ^c
        if os.name == "nt":
            try:
                import win32api
                win32api.SetConsoleCtrlHandler(signal_catch_stop, True)
            except ImportError:
                version = ".".join(map(str, sys.version_info[:2]))
                raise Exception("pywin32 not installed for Python " + version)
        else:
            import signal
            signal.signal(signal.SIGINT, self.signal_catch_stop)
            signal.signal(signal.SIGTERM, self.signal_catch_stop)

        #get dem options
        o = self._create_parser()
        (opts, args) = o.parse_args()
        self.options = opts

        #set dem loggings
        if not os.path.exists(config.SELENIUM['log_path']):
            os.mkdir(config.SELENIUM['log_path'])

        #start the server if we need to and try to connect
        if config.SELENIUM['server'] == "localhost":
            selenium_launcher.execute_selenium(
                config.SELENIUM['server'], config.SELENIUM['port'],
                config.SELENIUM['log_path'])

        for x in range(config.SELENIUM['timeout']):
            try:
                print "trying connection"
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

        #try to connect to the database
        self.db = DatabaseManager()

        #try to connect to the Transmission server
        self.daemon = transmissionrpc.Client(
            address=config.TRANSMISSION['server'], 
            port=config.TRANSMISSION['port'], 
            user=config.TRANSMISSION['user'], 
            password=config.TRANSMISSION['password'])

    def signal_catch_stop(self, signal, frame = None):
        """catch a ctrl-c and kill the program"""
        os.kill(os.getpid(), 9) 

    def _create_parser(self):
        """optparser"""
        usage = "usage: %prog [options]"
        desc = "TV ROBOT CAN GET YOUR TV AND MOVIES BECAUSE FUCK YEAH!"

        o = OptionParser(usage=usage, description=desc)
        #o.add_option("-l", "--log_path", default="logs", action="store", 
        #type="string", help="Path to dump all the logs into.")

        return o

#LETS DO THIS SHIT
if __name__ == '__main__':
    robot = TvRobot()
    print robot.daemon.list()