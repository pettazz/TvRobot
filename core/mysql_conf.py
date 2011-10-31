"""
This file contains database credentials
"""

class Apps:
    TVROBOT = "TvRobot"

APP_CREDS = {
   Apps.TVROBOT : {
        'PROD' : ("192.168.1.106", "tvrobot", "fuckinscience123", "TvRobot"),
        #QA : ("host", "user", "pass", "db")
   },

}