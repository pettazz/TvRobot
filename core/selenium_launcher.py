"""Download and run the selenium v2 jar file"""

import subprocess
import os
import socket
import urllib
import time

#selenium_dl_site = "http:code.google.com/p/selenium/downloads/list"
selenium_jar = "http://selenium.googlecode.com/files/selenium-server-standalone-2.7.0.jar"
jar_file = "selenium-server.jar"

def download_selenium():
    """
    downloads the selenium v2 jar file from its online location and stores it locally
    """
    try:
        local_file = open(jar_file, 'wb')
        remote_file = urllib.urlopen(selenium_jar)
        print 'Please wait, downloading Selenium...\n'
        local_file.write(remote_file.read())
        local_file.close()
        remote_file.close()   
    except Exception, details:
        raise Exception("Error occured while downloading Selenium Server. Details: "+details)

def is_running_locally(host, port):
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        socket_s.connect((host, port))
        socket_s.close()
        return True
    except:
        return False
      
def is_available_locally():
    return os.path.isfile(jar_file)

def start_selenium_server(selenium_jar_location, port, file_path):

    """
    Starts selenium on the specified port (defaults to 4444)
    and configures the output and error files.
    Throws an exeption if the server does not start.
    """
    
    process_args = None
    process_args = ["java", "-jar", selenium_jar_location, "-port", port]
    selenium_exec = subprocess.Popen(process_args,
                                     stdout=open("%s/log_seleniumOutput.txt"%(file_path),"w"),
                                     stderr=open("%s/log_seleniumError.txt"%(file_path),"w"))
    time.sleep(2)
    if selenium_exec.poll() == 1:
        raise StartSeleniumException("The selenium server did not start." +\
                                     "Do you already have one runing?")
    return selenium_exec

def stop_selenium_server(selenium_server_process):
    """Kills the selenium server.  We are expecting an error 143"""
    
    try:
        selenium_server_process.terminate()
        return selenium_server_process.poll() == 143
    except Exception, details:
        raise Exception("Cannot kill selenium process, details: "+details)

class StartSeleniumException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
def execute_selenium(host, port, file_path):
    if is_running_locally(host, port):
        return
    if not is_available_locally():    
        download_selenium()
    try:
        return start_selenium_server(jar_file, port, file_path)
    except StartSeleniumException:
        print "Selenium Server might already be running.  Continuing"

