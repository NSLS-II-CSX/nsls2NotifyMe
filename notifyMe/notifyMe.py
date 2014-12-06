from subprocess import Popen, PIPE
from epics import PV
from time import sleep, time, localtime, strftime
import smtplib
from email.mime.text import MIMEText

import logging
import sys
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LOG_FORMAT = "%(asctime)-15s [%(name)5s:%(levelname)s] %(message)s"
fmt = logging.Formatter(LOG_FORMAT)

handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(fmt)
logger.addHandler(handler)


class NotifyMe(object):

    def __init__(self):
        self.mesage_names = ['OP{1}Message', 'OP{2}Message']

        self.message_pv = [PV(p, callback=self._update, form='time')
                           for p in self.mesage_names]

        self.new_message = False
        self.email_list = ['swilkins@bnl.gov']
        self.update_time = 5

    def _update(self, *args, **kwargs):
        logger.info("Recieved Callback from PV (%s).", kwargs['pvname'])
        time_text = self._time_to_string(kwargs['timestamp'])
        logger.info("Timestamp is %s (%s).", time_text, kwargs['pvname'])
        self.new_message = True

    def _time_to_string(self, time):
        time_text = strftime("%H:%M on %A, %d %B %Y %Z",
                             localtime(time))
        return time_text

    def _updateMessage(self):
        msg = "New Message From Operations........\n\n"

        latest_time = max([pv.timestamp for pv in self.message_pv])
        time_text = self._time_to_string(latest_time)
        logger.info("Newest PV timestamp at %s", time_text)

        msg += "Update at : {}\n".format(time_text)

        for mpv in self.message_pv:
            text = mpv.get(as_string=True)
            msg += (text + '\n')
            logger.info("Msg: %s", text)

        self.message = msg

    def update(self):
        # Format Message

        self._updateMessage()

        # Speak Message
        self._speak(self.message)

        # Email Message
        self._email(self.message)

    def _speak(self, msg):
        p = Popen(['espeak', '-a 100', '-s 150', '-ven-uk'],
                  stdout=PIPE, stdin=PIPE, stderr=PIPE)
        p.communicate(input=msg)

    def _email(self, text):
        msg = MIMEText(text)
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
                logger.info("Waiting to anounce new message")
                new_time = time()
                while (time() - new_time) < self.update_time:
                    sleep(10)
                    logger.info('Tick - Tock')
                self.update()
                self.new_message = False
