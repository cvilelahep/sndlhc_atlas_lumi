import numpy as np
import os
import shutil
import argparse
import json
import datetime
import ROOT
import lumi_tools

converted_data_dir = "/eos/experiment/sndlhc/convertedData/commissioning/TI18/"
raw_data_dir = "/eos/experiment/sndlhc/raw_data/commissioning/TI18/data/"

parser = argparse.ArgumentParser()
parser.add_argument("--lumi_path", dest="lumi_path", help="Path to csv files containing ATLAS luminosity", required=True)
parser.add_argument("-f", "--run_summary_file", dest="run_summary_file", help="Path to run_summary_file", required=True)
options = parser.parse_args()

# Get luminosity
lumi = lumi_tools.getLumi(options.lumi_path)

# Now get the existing run list
if not os.path.isfile(options.run_summary_file) :
    # Initialize run summary file with committed copy (contains runs before automatic timestamp became available)
    script_dir = os.path.dirname(__file__)
    shutil.copy(script_dir+"/run_summary.csv.in", options.run_summary_file)

runs = np.genfromtxt(options.run_summary_file, delimiter=',', dtype=[('run_number', 'i4'), ('start_time', 'datetime64[ms]'), ('end_time', 'datetime64[ms]'), ('reco_prescale_factor', int)])

# Get the last run
last_run = runs[-1]['run_number']

# Get the last 100 converted data files
latest_converted = np.array([int(fname[-6:]) for fname in os.listdir(converted_data_dir)[-100:]])

# Get the run numbers after the last run
to_check = latest_converted[latest_converted > last_run]

lines_to_write = []

# For each run, check the run start and end time, then check if that time corresponds to a fill with collisions.
for i_run in to_check :
    with open(raw_data_dir+"/run_{0:06d}/run_timestamps.json".format(i_run)) as f_runtimes :
        runtimes = json.load(f_runtimes)
        start_time = np.datetime64(runtimes['start_time'])
        stop_time = np.datetime64(runtimes['stop_time'])

        mask = np.logical_and(lumi['timestamp']>start_time, lumi['timestamp'] < stop_time)
        # Skip if no entries in nxcals for the run duration
        if not mask.sum() :
            continue

        run_mean_lumi = lumi['inst_lumi'][mask].mean()*(stop_time-start_time)/np.timedelta64(1, "s")

        # Skip if no collisions in this run
        if run_mean_lumi < 0.01 :
            continue

        # Derive prescale factor from the luminosity
        prescale_factor = int(run_mean_lumi*0.028+1)
        
        string = "{0},{1}, {2}, {3}".format(i_run, start_time.astype(datetime.datetime).strftime("%Y-%m-%d %H:%M:%S"), stop_time.astype(datetime.datetime).strftime("%Y-%m-%d %H:%M:%S"), prescale_factor)
        lines_to_write.append(string)

with open("run_summary.csv", "a") as f_out :
    for line in lines_to_write :
        f_out.write(line+"\n")
        