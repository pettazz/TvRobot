from googlevoice import Voice
import BeautifulSoup

from config import GOOGLE_VOICE

class GoogleVoiceManager:
    def __init__(self):
        self.voice = Voice()
        self.voice.login(GOOGLE_VOICE['username'], GOOGLE_VOICE['password'])

    #TODO: CLEANUPTHISCRAP
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
        
    def send_message(self, to, message):
        return self.voice.send_sms(to, message)