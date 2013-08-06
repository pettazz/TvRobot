from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor

import threading, uuid
import json, urlparse
import datetime, time

from core.tvrobot import TvRobot
from core.mysql import DatabaseManager
from core.schedule_manager import ScheduleManager
from core.user_manager import UserManager
from core.twilio_manager import TwilioManager

class SMSAPIHandler(Resource):
    def __init__(self):
        Resource.__init__(self)

    def render_POST(self, request):
        data = urlparse.parse_qs(request.content.getvalue(), True)
        msg_from = data['From'][0]
        msg_to = data['To'][0]
        msg_body = data['Body'][0]
        response = None
        
        if msg_body.lower().startswith('add '):
            if msg_body.lower().startswith('add movie '):
                # kick off a task that will need to remember to send an sms when it's finished
                # we should probably have some loop cleaning up dead threads or something.
                thread_name = "addmovie_%s" % uuid.uuid4().hex
                t = threading.Thread(name=thread_name, target=TvRobot().add_download, kwargs={
                    'download_type':'Movie', 
                    'search':msg_body[10:], 
                    'user_phone':msg_from, 
                    'send_sms':True
                })
                print "starting worker thread %s" % thread_name
                t.start()

            if msg_body.lower().startswith('add episode '):
                # kick off a task that will need to remember to send an sms when it's finished
                # we should probably have some loop cleaning up dead threads or something.
                thread_name = "addepisode_%s" % uuid.uuid4().hex
                t = threading.Thread(name=thread_name, target=TvRobot().add_download, kwargs={
                    'download_type':'Episode', 
                    'search':msg_body[12:], 
                    'user_phone':msg_from, 
                    'send_sms':True
                })
                print "starting worker thread %s" % thread_name
                t.start()

            if msg_body.lower().startswith('add schedule tv '):
                response = TvRobot().add_schedule(search=msg_body[16:], user_phone=msg_from)
                #hopefully TVRage responds in well under 15s, so we won't hit the timeout on this task

            if msg_body.lower().startswith('add schedule by date tv '):
                response = TvRobot().add_schedule(search=msg_body[16:], user_phone=msg_from, by_date=True)
                #hopefully TVRage responds in well under 15s, so we won't hit the timeout on this task
                
        elif msg_body.lower() == 'cleanup':
            thread_name = "cleanup_%s" % uuid.uuid4().hex
            t = threading.Thread(name=thread_name, target=TvRobot().cleanup_downloads())
            print "starting worker thread %s" % thread_name
            t.start()
            response = "Beep, cleaning up active downloads."

        elif msg_body.lower().startswith('when is the next '):
            schedule = ScheduleManager().get_next_schedule(msg_body[17:])
            if schedule is None:
                response = "Beeboop. I don't have a schedule for a show by that name."
            elif schedule is False:
                response = "Beep. I haven't found an airtime for the next episode yet."
            else:
                sch_time = datetime.datetime.fromtimestamp(int(schedule))
                response = time.strftime("%A, %b %d at %I:%M %p", sch_time.timetuple())

        elif msg_body.lower().startswith('broadcast '):
            user = UserManager().get_user_by_phone(msg_from)
            print "checking permission for user:"
            print user
            if user[5] == '999':
                query = """ SELECT phone FROM User WHERE phone <> '' """
                phones = DatabaseManager().fetchall_query_and_close(query, {})
                count = 0
                for phone in phones:
                    TwilioManager().send_sms(phone[0], msg_body[10:])
                    count = count + 1

                response = 'Broadcast sent to %s users.' % count
            else:
                response = 'Beeoop, you don\'t have permission for that.'

        elif msg_body.lower().startswith('sup'):
            # TODO: allow him to give some simple status updates here
            response = "Just bein' a tvrobot, doin' tvrobot things."

        elif msg_body.lower() == 'ping':
            response = "pong"

        else:
            response = "Booeep. I don't know what that means."


        if response is not None:
            response_tag = '<Response><Sms>%s</Sms></Response>' % response
        else:
            response_tag = '<Response />'
            
        return '<?xml version="1.0" encoding="UTF-8"?>%s' % response_tag

class VoiceAPIHandler(Resource):
    def __init__(self):
        Resource.__init__(self)

    def render_POST(self, request):
        return '<?xml version="1.0" encoding="utf-8" ?><Response><Say voice="man">Hello, I am Butler tron.</Say><Pause length="1"/><Say voice="woman">Or, am I?</Say></Response>'

class GenericAPIHandler(Resource): 
    def __init__(self):
        Resource.__init__(self)

    def render_POST(self, request):
        data = json.loads(request.content.getvalue())
        return "<html><body>HEY EVERYBODY! GENERIC API HANDLER HERE. I DON'T DO ANYTHING. <br /><pre>%s</pre></body></html>" % data

class EventHookHandler(Resource):
    def __init__(self):
        Resource.__init__(self)

    def render_POST(self, request):
        return 'wat?'


class APIDispatcher(Resource):
    def getChild(self, name, request):
        print request.__dict__
        #stupid sexy flanders

        if name == 'sms':
            return SMSAPIHandler()
        elif name == 'voice':
            return VoiceAPIHandler()
        elif name == 'event':
            return EventHookHandler()
        else:
            return GenericAPIHandler()

root = APIDispatcher()
factory = Site(root)
reactor.listenTCP(8880, factory)
reactor.run()