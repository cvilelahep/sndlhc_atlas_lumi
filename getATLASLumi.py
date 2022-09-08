import argparse
import numpy as np
import datetime

parser = argparse.ArgumentParser(description='Get ATLAS Luminosity between two timestamps')

parser.add_argument("snd_lhc_run_number", type = str, help="SND@LHC run number")
parser.add_argument("start_time", type = str, help="Start time in Y-m-d H:M:S format")
parser.add_argument("end_time", type = str, help="Start time in Y-m-d H:M:S format")
parser.add_argument('--output_directory', dest='output_directory', default="./")
parser.add_argument('--generate_plot', dest='generate_plot', default=False, action='store_true')

args = parser.parse_args()

import pytimber

ldb = pytimber.LoggingDB(source="nxcals")

lumi_string = 'ATLAS:LUMI_TOT_INST'

# getScaled doesn't seem to work.
#fetched_data = ldb.getScaled(lumi_string, args.start_time, args.end_time, unixtime=True, scaleAlgorithm = 'AVG', scaleInterval = 'MINUTE', scaleSize = '5')
fetched_data = ldb.get(lumi_string, args.start_time, args.end_time, unixtime=True)
timestamp = np.array(fetched_data[lumi_string][0])
atlas_lumi = np.array(fetched_data[lumi_string][1])

# Sometimes there are "None" entries in the luminosity
mask = atlas_lumi == None
timestamp = timestamp[~mask]
atlas_lumi = atlas_lumi[~mask]

if len(timestamp) < 2 :
    exit()

f_out = open(args.output_directory+"/sndlhc_atlas_lumi_{0}.csv".format(args.snd_lhc_run_number), "w")
f_out.write("Timestamp,Instantaneous lumi (ub-1 s-1)\n")

for i in range(len(atlas_lumi)) :
    inst_lumi = atlas_lumi[i]
    date = datetime.datetime.utcfromtimestamp(timestamp[i])
    f_out.write("{0}Z,{1:.3f}\n".format(date.isoformat(), inst_lumi))
f_out.close()

if args.generate_plot :
    import matplotlib.pyplot as plt
    plt.plot(timestamp, atlas_lumi)
    plt.title("{0} to {1}".format(args.start_time, args.end_time))
    plt.xlabel("Time")
    plt.ylabel("Instantaneous luminosity [ub-1 s-1]")

    plt.savefig(args.output_directory+"/sndlhc_atlas_lumi_{0}".format(args.snd_lhc_run_number)+".png")

