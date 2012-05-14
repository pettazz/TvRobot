from googlevoice import Voice
import BeautifulSoup
import hashlib

from config import GOOGLE_VOICE
from mysql import DatabaseManager
from user_manager import UserManager

class GoogleVoiceManager:
    def __init__(self):
        self.voice = Voice()
        self.voice.login(GOOGLE_VOICE['username'], GOOGLE_VOICE['password'])

    def send_message(self, to, message):
        try:
            return self.voice.send_sms(to, message)
        except:
            print "BOOP. There was a problem sending the sms notification."
            return false

    def extractsms(self):
        """
        extractsms  --  extract SMS messages from BeautifulSoup tree of Google Voice SMS HTML.

        Output is a list of dictionaries, one per message.
        Ported from code by John Nagle (nagle@animats.com)
        """
        self.voice.sms()
        htmlsms = self.voice.sms.html

        msgitems = []										# accum message items here
        #	Extract all conversations by searching for a DIV with an ID at top level.
        tree = BeautifulSoup.BeautifulSoup(htmlsms)			# parse HTML into tree
        conversations = tree.findAll("div", attrs={"id" : True}, recursive=False)
        for conversation in conversations :
            #	For each conversation, extract each row, which is one SMS message.
            rows = conversation.findAll(attrs={"class" : "gc-message-sms-row"})
            for row in rows :								# for all rows
                #	For each row, which is one message, extract all the fields.
                msgitem = {"id" : conversation["id"]}		# tag this message with conversation ID
                spans = row.findAll("span", attrs={"class" : True}, recursive=False)
                for span in spans :							# for all spans in row
                    cl = span["class"].replace('gc-message-sms-', '')
                    msgitem[cl] = (" ".join(span.findAll(text=True))).strip()	# put text in dict
                msgitems.append(msgitem)					# add msg dictionary to list
        return [msg for msg in msgitems if msg['from'] != u'Me:']
        

    def get_new_schedule_messages(self):
        smses = self.extractsms()
        new_smses = []
        for sms in smses:
            sms['text'] = sms['text'].lower()
            if sms['text'].startswith('add schedule '):
                query = "SELECT guid FROM EpisodeSchedule WHERE sms_guid = %(sms_guid)s"
                if DatabaseManager().fetchone_query_and_close(query, {'sms_guid': hashlib.md5(sms['text']).hexdigest()}) is None:
                    #example sms: 
                    # {u'text': u'Poop', u'from': u'+14132976806:', 'id': u'd4f1ef49f44625f912e0ee757483ac3fb19d2a41', u'time': u'1:57 PM'}
                    sch = {}
                    sch['phone'] = sms['from'].split('+1')[1][:-1]
                    sch['user'] = UserManager().get_user_id_by_phone(sch['phone'])
                    sch['sms_guid'] = hashlib.md5(sms['text']).hexdigest()
                    sch['type'] = sms['text'].split('add schedule ')[1].split(' ')[0].upper()
                    sch['name'] = sms['text'].split('add schedule ')[1].split(' ', 1)[1]
                    new_smses.append(sch)
        return new_smses
