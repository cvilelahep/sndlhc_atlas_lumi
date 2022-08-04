#!/bin/bash

k5start -f ~/.Authentication/cvilela.kt -u cvilela
python3 makeSummaryPlot.py --lumi_path /eos/user/c/cvilela/sndlumi_2/
kdestroy -p cvilela@CERN.CH
