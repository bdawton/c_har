#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 19:47:25 2021

@author: billydawton
"""

from sklearn.metrics import classification_report


def c_mat_met(conf_mat):
    pred_labels = '0', '1', '2', '0', '1', '2', '0', '1', '2'

    real_labels = '0', '0', '0', '1', '1', '1', '2', '2', '2'

    y_pred = []

    y_real = []

    c = 0

    for entry in conf_mat.flatten():
        y_pred.append(pred_labels[c] * int(entry))
        y_real.append(real_labels[c] * int(entry))
        c = c + 1

    y_pp = ''.join(str(n) for n in y_pred)
    y_rr = ''.join(str(m) for m in y_real)
    y_ppp = ','.join(y_pp)
    y_rrr = ','.join(y_rr)
    y_pppp = y_ppp.split(',')
    y_rrrr = y_rrr.split(',')

    return classification_report(y_rrrr, y_pppp, digits=3)