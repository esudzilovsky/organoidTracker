# -*- coding: utf-8 -*-
"""
Created on Tue Jun 05 09:23:07 2018

@author: Edward
"""

from __future__ import print_function

import logging
import traceback

"""
import configparser
config = None
configFilename = 'organoidTracker.config'

def loadConfigFile():
    global config
    config = configparser.ConfigParser()
    config.read(configFilename)
    
def saveConfigFile():
    global config
    with open(configFilename,'w') as configfile:
        config.write(configfile)

def getOrganoidTrackerVersion():
    #return globalSettings['organoidTracker version']
    return config['DEFAULT']['organoidTracker version'] 
"""

globalSettings = {
          'organoidTracker version' : 0.066,
        'errorLogfile' : 'organoidTracker-Errors.log'
}

def getErrorLogFile():
    return globalSettings['errorLogfile']

logging.basicConfig(filename=getErrorLogFile(), filemode='a', level=logging.ERROR)

def logError():
    logging.error(traceback.format_exc())
    print('Error was saved to log file: '+getErrorLogFile())

def getOrganoidTrackerVersion():
    return globalSettings['organoidTracker version']
