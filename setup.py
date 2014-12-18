'''
Copyright (c) 2010 Brookhaven National Laboratory
All rights reserved. Use is subject to license terms and conditions.

@author: swilkins
'''

from setuptools import setup

setup(name='nsls2NotifyMe',
      version='0.1.0',
      description='NSLS-II Notify Server',
      author='Stuart Wilkins',
      author_email='swilkins@bnl.gov',
      packages=['nsls2NotifyMe'],
      scripts=['scripts/notifyme.py'],
      entry_points={'console_scripts': ['notifyme = notifyme:main']}
      )
