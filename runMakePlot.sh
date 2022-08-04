#!/bin/bash

k5start -f ~/.Authentication/cvilela.kt -u cvilela
python3 makeSummaryPlot.py --lumi_path /eos/user/c/cvilela/sndlumi_2/
cp sndlhc_lumi_*.p* /eos/user/c/cvilela/SND-LHC/CommissioningPlots/Lumi/
rm sndlhc_lumi_*.p*
kdestroy -p cvilela@CERN.CH
