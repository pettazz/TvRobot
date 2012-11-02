from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor

import json, urlparse

from core.tvrobot import TvRobot

class SMSAPIHandler(Resource):
    def __init__(self):
        Resource.__init__(self)

    def render_POST(self, request):
        data = urlparse.parse_qs(request.content.getValue(), True)
        msg_from = data['From'][0]
        msg_to = data['To'][0]
        msg_body = data['Body'][0]
        if msg_body.lower().startswith('add '):
            if msg_body.lower().startswith('add movie '):
                response = TvRobot().add_download(download_type='Movie', search=msg_body[10:], user_phone=msg_from)

            if msg_body.lower().startswith('add episode '):
                response = TvRobot().add_download(download_type='Episode', search=msg_body[12:], user_phone=msg_from)

            if msg_body.lower().startswith('add schedule tv '):
                response = TvRobot().add_schedule(search=msg_body[16:], user_phone=msg_from)
        else:
            response = "Booeep. I don't know what that means."

        return '<?xml version="1.0" encoding="UTF-8"?><Response><Sms>%s</Sms></Response>' % response

class VoiceAPIHandler(Resource):
    def __init__(self):
        Resource.__init__(self)

    def render_POST(self, request):
        return '<?xml version="1.0" encoding="utf-8" ?><Response><Say voice="man">Hello I am Butlertron.</Say><Pause length="1"/><Say voice="woman">Or am I?</Say></Response>'

class GenericAPIHandler(Resource): 
    def __init__(self):
        Resource.__init__(self)

    def render_POST(self, request):
        data = json.loads(request.content.getvalue())
        return "<html><body>HEY EVERYBODY! GENERIC API HANDLER HERE<br /><pre>%s</pre></body></html>" % data

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