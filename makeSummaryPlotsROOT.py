import argparse
import ROOT

import glob

parser = argparse.ArgumentParser(description='Luminosity summary plots for SND@LHC run')

parser.add_argument("--raw_data_dir", type = str, help="Raw data directory", required = True)
parser.add_argument("--lumi_dir", type = str, help="Luminosity directory", required = True)
parser.add_argument("-o", "--output_dir", type = str, help="Directory to store the output ROOT files", default="./")

args = parser.parse_args()

BIN_WIDTH = 5 # Bin width in seconds


data_files = glob.glob(args.raw_data_dir+"/data_*.root")

f = ROOT.TFile(data_files[0])

if hasattr(f, "event") :
    tree_name = "event"
    branch_name = "timestamp"
elif hasattr(f, "data") :
    tree_name = "data"
    branch_name = "evt_timestamp"
else :
    print("Data file not valid. Exitting.")
    exit(-1)

del f

events = ROOT.TChain(tree_name)
for f in data_files :
    events.Add(f)

events.GetEntry(events.GetEntries()-1)
last_time = getattr(events, branch_name)*6.25/1e9

n_bins = int(last_time/BIN_WIDTH)+1

h_event_rate = ROOT.TH1D("h_event_rate", ";Event rate [s^{-1}];Run time [s]", n_bins, 0, n_bins*BIN_WIDTH)

for e in events :
    h_event_rate.Fill(getattr(events, branch_name)*6.25/1e9, 1./BIN_WIDTH)

h_event_rate.Draw()
input()
