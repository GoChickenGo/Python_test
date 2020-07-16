# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 17:30:31 2020

@author: xinmeng
"""

import scipy
import scipy.fftpack
import pylab
import numpy as np

tracekk =np.load( \
r"M:\tnw\ist\do\projects\Neurophotonics\Brinkslab\Data\Patch clamp\2020-06-11 Helios PMT\cell5_pCAG_PMT\cell2_trial_3_10e6\PMT_array_2020-06-11_16-36-52.npy",allow_pickle=True)

FFT = abs(scipy.fft(tracekk))
freqs = fftpack.fftfreq(len(tracekk)) * 5000

pylab.subplot(211)
pylab.plot(tracekk[2:,])
pylab.subplot(212)
pylab.plot(freqs,20*scipy.log10(FFT),'x')
pylab.xlim(1, 500)
pylab.show()
