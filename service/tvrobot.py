import os
import grp
import signal
import daemon
import lockfile

context = daemon.DaemonContext(
    working_directory='/Users/pope/Sites/TvRobot/service/data/',
    umask=0o002,
    pidfile=lockfile.FileLock('/var/run/tvrobot.pid'),
    )

context.signal_map = {
    # signal.SIGTERM: program_cleanup,
    # signal.SIGHUP: 'terminate',
    # signal.SIGUSR1: reload_program_config,
    }

mail_gid = grp.getgrnam('mail').gr_gid
context.gid = mail_gid

important_file = open('spam.data', 'w')
interesting_file = open('eggs.data', 'w')
context.files_preserve = [important_file, interesting_file]

#initial_program_setup()

with context:
	while True:
	    print "llololol"