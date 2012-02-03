from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
import time
import core.config as config

env.hosts = [config.TRANSMISSION['SSH']['user'] + '@' + \
             config.TRANSMISSION['server'] + ':' + \
             str(config.TRANSMISSION['SSH']['port'])]
env.password = config.TRANSMISSION['SSH']['password']

def move_video(local_path, remote_path):
    local_path = __shellquote(local_path)
    remote_path = __shellquote(remote_path)
    cmd = "scp -P %s %s %s@%s:%s" % (
        config.MEDIA['port'],
        local_path,
        config.MEDIA['user'],
        config.MEDIA['server'],
        remote_path)
    run(cmd)

def unrar_file(rar_path, save_path):
    rar_path = __shellquote(rar_path)
    save_path = __shellquote(save_path)

    run("mkdir %s" % save_path)
    run("unrar e %s %s" % (rar_path, save_path))

def unzip_file(zip_path, save_path):
    zip_path = __shellquote(zip_path)
    save_path = __shellquote(save_path)

    run("mkdir %s" % save_path)
    run("unzip %s -d %s" % (zip_path, save_path))

def delete_file(remote_path):
    remote_path = __shellquote(remote_path)

    run("rm -r %s" % remote_path)
    time.sleep(20)

def __shellquote(s):
    return s.replace(' ', '\ ').replace('(', '\(').replace(')', '\)').replace("'", "\\'").replace('&', '\&').replace(',', '\,').replace('!', '\!')