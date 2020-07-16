# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 17:14:01 2020

@author: xinmeng
"""

from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QApplication
import sys
import threading
import time

def run_in_thread(fn):
    """
    https://stackoverflow.com/questions/23944657/typeerror-method-takes-1-positional-argument-but-2-were-given
    """
    @staticmethod
    def run(*k):
        
        thread = threading.Thread(target=fn, args=(*k,), daemon = False)
        thread.start()
        print(1)
        return thread # <-- return the thread
    return run

class test(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout() 
        self.aabuttom = QPushButton('Top')
        self.layout.addWidget(self.aabuttom)
        self.aabuttom.clicked.connect(self.call)

        self.setLayout(self.layout) 
                
    @run_in_thread
    def call(self):

        for i in range(10):
            print('jaja')
            time.sleep(2)
        
if __name__ == "__main__":
    def run_app():
        app = QApplication(sys.argv)
        mainwin = test()
        mainwin.show()
        app.exec_()
    run_app()  