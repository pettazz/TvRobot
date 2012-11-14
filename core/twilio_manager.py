from twilio.rest import TwilioRestClient

from config import TWILIO
from mysql import DatabaseManager
from user_manager import UserManager

class TwilioManager:
    def __init__(self):
        self.client = TwilioRestClient(TWILIO['ACCOUNT_SID'], TWILIO['AUTH_TOKEN'])

    def send_sms(self, to, body):
        if not to.startswith('+1'):
            to = "+1%s" % to
        if len(body) >= 159:
            self.send_sms(to, body[:155] + '...')
            if TWILIO['split_long_sms']:
                self.send_sms(to, body[155:])
        self.client.sms.messages.create(to="%s" % to,
                                        from_=TWILIO['phone_number'],
                                        body=body)

    def send_sms_to_user(self, user_id, body):
        self.send_sms(Usermanager().get_user_phone_by_id(user_id), body)