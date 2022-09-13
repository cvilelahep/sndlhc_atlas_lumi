#!/bin/bash

SNDBUILD_DIR=/eos/home-c/cvilela/SND_Aug4/sw/
source /cvmfs/sndlhc.cern.ch/SNDLHC-2022/July14/setUp.sh
eval `alienv load -w $SNDBUILD_DIR --no-refresh sndsw/latest-master-release`

k5start -f ~/.Authentication/cvilela.kt -u cvilela
python3 makeSummaryPlot.py --lumi_path /eos/user/c/cvilela/sndlumi_2/
cp sndlhc_lumi_*.p* /eos/user/c/cvilela/SND-LHC/CommissioningPlots/Lumi/
rm sndlhc_lumi_*.p*
kdestroy -p cvilela@CERN.CH
