from subprocess import Popen, PIPE
from epics import PV
from time import sleep, time, localtime, strftime
import smtplib
from email.mime.text import MIMEText

import logging
import sys

from pyOlog.OlogHandler import OlogHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOG_FORMAT = "%(asctime)-15s [%(name)5s:%(levelname)s] %(message)s"
fmt = logging.Formatter(LOG_FORMAT)

handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(fmt)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

handler = OlogHandler(logbooks='Operations', tags=['Ops Message'])
handler.setLevel(logging.INFO)
logger.addHandler(handler)


class NotifyMe(object):

    def __init__(self, email_list=None, speak=False, log=False,
                 update_all=False):
        self.update_all = update_all

        self.email_list = email_list
        self.speak = speak
        self.log = log

        self.mesage_names = ['OP{1}Message', 'OP{2}Message']
        self.suplimental_names = [['OP{3}Message', 'OP{4}Message',
                                   'OP{5}Message', 'OP{6}Message'],
                                  ['OP{ST:1}Message', 'OP{ST:2}Message',
                                   'OP{ST:3}Message', 'OP{ST:4}Message',
                                   'OP{ST:5}Message'],
                                  ['OP{LT:1}Message',
                                   'OP{LT:2}Message', 'OP{LT:3}Message',
                                   'OP{LT:4}Message', 'OP{LT:5}Message']]

        self.message_pv = [PV(p, callback=self._update, form='time')
                           for p in self.mesage_names]

        if self.update_all:
            update = self._update
        else:
            update = None

        self.suplimental_pv = [[PV(p, callback=update, form='time')
                                for p in l]
                               for l in self.suplimental_names]

        self.message = ''
        self.supplimental_message = ''
        self.message_time = ''

        self.new_message = False
        self.update_time = 60

    def _update(self, *args, **kwargs):
        logger.debug("Recieved Callback from PV (%s).", kwargs['pvname'])
        time_text = self._time_to_string(kwargs['timestamp'])
        logger.debug("Timestamp is %s (%s).", time_text, kwargs['pvname'])
        self.new_message = True

    def _time_to_string(self, time):
        time_text = strftime("%H:%M on %A, %d %B %Y %Z",
                             localtime(time))
        return time_text

    def _updateMessage(self):

        latest_time = max([pv.timestamp for pv in self.message_pv])
        time_text = self._time_to_string(latest_time)
        logger.debug("Newest PV timestamp at %s", time_text)

        self.message_time = "Update at : {}\n".format(time_text)

        msg = ''
        for mpv in self.message_pv:
            text = mpv.get(as_string=True)
            msg += (text + '\n')
            logger.debug("Msg: %s", text)

        self.message = msg

        sup_msg = ''
        for sup_pv in self.suplimental_pv:
            sup_msg += '\n{:=^80}\n\n'.format('')
            for mpv in sup_pv:
                text = mpv.get(as_string=True)
                sup_msg += (text + '\n')
                logger.debug("Supp Msg: %s", text)

        self.suplimental_message = sup_msg

    def update(self):
        # Format Message

        self._updateMessage()

        if self.log:
            logger.debug('Sending message to logger')
            self._log()

        # Speak Message
        if self.speak:
            logger.debug('Sending message to e-speak')
            self._speak()

        # Email Message
        if self.email_list:
            logger.debug('Sending message to emails %s', str(self.email_list))
            self._email()

    def _log(self):
        lmsg = self.message_time + '\n'
        lmsg += self.message
        lmsg += '\n\n'
        lmsg += self.suplimental_message
        logger.info(lmsg)

    def _speak(self):
        smsg = "New Message From Operations.\n\n"
        smsg += self.message
        try:
            p = Popen(['espeak', '-a 100', '-s 150', '-ven-uk'],
                      stdout=PIPE, stdin=PIPE, stderr=PIPE)
            p.communicate(input=smsg)
        except OSError:
            logger.debug('OS Error on trying to speak')
            pass

    def _email(self):
        etext = "New Message From Operations.\n\n"
        etext += self.message_time + '\n\n'
        etext += self.message
        etext += "\n\n"
        etext += self.suplimental_message
        msg = MIMEText(etext)
        msg['Subject'] = 'New NSLS-II OP Message'
        msg['From'] = 'donotreply@bnl.gov'
        msg['To'] = 'swilkins@bnl.gov'

        s = smtplib.SMTP('xf23id-ca.cs.nsls2.local')
        s.sendmail(msg['From'], self.email_list, msg.as_string())
        s.quit()

    def run(self):
        while True:
            sleep(1)
            if self.new_message:
                logger.debug("Waiting to anounce new message")
                new_time = time()
                while (time() - new_time) < self.update_time:
                    sleep(10)
                    logger.debug('Tick - Tock')
                self.update()
                self.new_message = False
