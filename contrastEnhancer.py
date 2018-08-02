# -*- coding: utf-8 -*-
"""
Created on Tue Apr 17 13:35:02 2018

@author: Edward
"""

# Implements ImageJ's Process/Enhance Contrast command.
class ContrastEnhancer:
    def __init__(self):
        self.max, self.range None,None
        self.classicEqualization = None
        self.stackSize = None
        self.updateSelectionOnly = None
        self.equalize, self.normalize = None, None
        self.processStack, self.useStackHistogram = None, None
        self.entireImage = None
        self.saturated = 0.35
        self.gEqualize, self.gNormalize = None, None
        
    def run(imp, arg):
        stackSize = imp.getStackSize()
        imp.trimProcessor()
        
        roi = imp.getRoi()
        
        if self.equalize:
            imp = self.equalize(imp)
        else:
            imp = self.stretchHistogram(imp, saturated)
            
        if self.normalize:
            ImageProcessor ip = imp.getProcessor()
            ip.setMinAndMax(0,ip.getBitDepth()==32?1.0:ip.maxValue())