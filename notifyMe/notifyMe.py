from subprocess import Popen, PIPE, STDOUT
from epics import PV
from time import sleep, time
import smtplib
from email.mime.text import MIMEText

import logging, sys
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LOG_FORMAT = "%(asctime)-15s [%(name)5s:%(levelname)s] %(message)s"
fmt = logging.Formatter(LOG_FORMAT)

handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(fmt)
logger.addHandler(handler)

class NotifyMe(object):
  def __init__(self):
    self.messagePV1 = PV('OP{1}Message', callback = self._update)
    self.messagePV2 = PV('OP{2}Message', callback = self._update)
    self.new_message = False
    self.email_list = ['6317416194@messaging.sprintpcs.com']

  def _update(self, *args, **kwargs):
    logger.info("Recieved Callback from PV (%s).", kwargs['pvname'])
    self.new_message = True
  def update(self):
    logger.info("Updating Message")
    
    msg = "New Message From Operations........\n\n"
    msg1 = self.messagePV1.get(as_string = True)
    msg2 = self.messagePV2.get(as_string = True)

    logger.info("Msg1: %s", msg1)
    logger.info("Msg2: %s", msg2)

    msg = msg + msg1 + '\n' + msg2 + '\n'

    # Speak Message
    self._speak(msg)

    # Email Message
    self._email(msg)

  def _speak(self, msg):
    p = Popen(['espeak', '-a 100', '-s 150', '-ven-uk'],
              stdout = PIPE, stdin = PIPE, stderr = PIPE)
    p.communicate(input = msg)

  def _email(self, text):
    msg = MIMEText(text)
    msg['Subject'] = 'New NSLS-II OP Message'
    msg['From']    = 'donotreply@bnl.gov'
    msg['To']      = 'swilkins@bnl.gov'
  
    s = smtplib.SMTP('xf23id-ca.cs.nsls2.local')
    s.sendmail(msg['From'], self.email_list, msg.as_string())
    s.quit()

  def run(self):
    while 1:
      sleep(1)
      if self.new_message:
        logger.info("Waiting to anounce new message")
        new_time = time()
        while (time() - new_time) < 20:
          sleep(1)
        self.update()
        self.new_message = False
       
