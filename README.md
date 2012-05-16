# Installation

You don't. Yet.  
For now, clone the repo, set up your core/config.py, then do a  
```sudo pip install -r requirements.pip ```  
and then  
```python tvrobot.py --help```  
will guide you.  



# TV ROBOT CAN GET YOUR TV AND MOVIES BECAUSE FUCK YEAH!

![lol](http://i.imgur.com/C0aKB.gif "HATERS GONNA HATE")



    Options:
      -h, --help            show this help message and exit
      -c, --clean-only      Cleans up any already completed downloads and exits.
                            Does not search for or add any torrents.
      -i CLEAN_IDS, --clean-ids=CLEAN_IDS
                            Cleans up specific Transmission download ids and then
                            stops. Comma separated list.
      -u, --schedule-updates-only
                            Attempts to update any existing schedules and then
                            exits.
      -x, --sms-update-only
                            Attempts to add any newly received sms schedules and
                            then exits.
      -p, --download-schedules-only
                            Attempts to find and download any torrents by
                            schedules and then exits.
      -s, --search-only     Searches for and adds any scheduled Episodes or Movies
                            and exits. Does not clean up finished torrents.
      -a ADD_TORRENT, --add-torrent=ADD_TORRENT
                            Adds the specified torrent file and exits.
      -m ADD_MAGNET, --add-magnet=ADD_MAGNET
                            Adds the specified magnet URI and exits. This will
                            usually have to be in quotes.
      -t ADD_TORRENT_TYPE, --torrent-type=ADD_TORRENT_TYPE
                            Specify the type of torrent to add. One of: Movie,
                            Episode (TV), Series (TV), Season (TV), Set(Movies)