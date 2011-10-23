import os 
import time
import logging
import math
import getpass
import uuid
import traceback
from core import selenium_launcher
from optparse import OptionParser, OptionValueError
from selenium import webdriver

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
        if not os.path.exists(self.options.log_path):
            os.mkdir(self.options.log_path)

        #start the server if we need to and try to connect
        if self.options.servername == "localhost":
            selenium_launcher.execute_selenium(self.options.servername, self.options.port,
                                               self.options.log_path)

        count = 0
        while count < self.options.connection_retries:
            try:
                self.driver = webdriver.Remote("http://%s:%s/wd/hub"%
                                           (self.options.servername, self.options.port),
                                           webdriver.DesiredCapabilities.FIREFOX)
                break
            except:
                time.sleep(10)
                count = count + 1
                if count == self.options.connection_retries:
                    raise Exception ("Couldn't connect to the selenium server at %s after %s retries." % 
                    (self.options.servername, self.options.connection_retries))
        
        self.driver.get('http://google.com')

    def signal_catch_stop(self, signal, frame=None):
        """catch a ctrl-c and kill the program"""
        os.kill(os.getpid(), 9) 

    def _create_parser(self):
        """optparser"""
        usage = "usage: %prog [options]"
        desc = "TV ROBOT CAN GET YOUR TV AND MOVIES BECAUSE FUCK YEAH!"

        o = OptionParser(usage=usage, description=desc)
        o.add_option("-s", "--servername", default="localhost", action="store", type="string", help="Selenium server to connect to.")
        o.add_option("-p", "--port", default="4444", action="store", type="string", help="Selenium server port to connect to.")
        o.add_option("-l", "--log_path", default="logs", action="store", type="string", help="Path to dump all the logs into.")
        o.add_option("-r", "--connection_retries", default=5, action="store", 
        type="int", help="Number of times to try to connect to Selenium server before throwing an exception.")

        return o

#LETS DO THIS SHIT
if __name__ == '__main__':
    robot = TvRobot()
