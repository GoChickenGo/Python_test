#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 17:11:38 2020

@author: Izak de Heer
"""
from PyQt5 import QtWidgets

class adaptedQButtonGroup(QtWidgets.QButtonGroup):
    def __init__(self, *args, **kwargs):
        """
        
        Class inheriting from QButtonGroup. This class provides a function to
        enable or disable all buttons in the group with one function call. 
        
        """
        super().__init__(*args, **kwargs)
        
    def setEnabled(self, arg):
        """
        
        Enable or disable all buttons in the group
        
        param arg: True for enable, False for disable all buttons in group
        param type: True or False
        
        """
        if arg == True:
            for button in self.buttons():
                button.setEnabled(True)
        else:
            for button in self.buttons():
                button.setEnabled(False)