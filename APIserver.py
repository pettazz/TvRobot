from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor

import json, urlparse

from core.tvrobot import TvRobot

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
                TvRobot().add_download(download_type='Movie', search=msg_body[10:], user_phone=msg_from, send_sms=True)
                # kick off a task that will need to remember to send an sms when it's finished

            if msg_body.lower().startswith('add episode '):
                TvRobot().add_download(download_type='Episode', search=msg_body[12:], user_phone=msg_from, send_sms=True)
                # kick off a task that will need to remember to send an sms when it's finished

            if msg_body.lower().startswith('add schedule tv '):
                response = TvRobot().add_schedule(search=msg_body[16:], user_phone=msg_from)
                #hopefully TVRage responds in well under 15s, so we won't hit the timeout on this task
        else:
            response = "Booeep. I don't know what that means."

        if response is not None:
            response_tag = '<Response><Sms>%s</Sms></Response>' % response
        else:
            response_tag = '<Response />'
        return '<?xml version="1.0" encoding="UTF-8"?>' % response_tag

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