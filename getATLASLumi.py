import argparse

parser = argparse.ArgumentParser(description='Get ATLAS Luminosity between two timestamps')

parser.add_argument("snd_lhc_run_number", type = str, help="SND@LHC run number")
parser.add_argument("start_time", type = str, help="Start time in Y-m-d H:M:S format")
parser.add_argument("end_time", type = str, help="Start time in Y-m-d H:M:S format")

args = parser.parse_args()

import pytimber
ldb = pytimber.LoggingDB(source="nxcals")

atlas_lumi = ldb.get('ATLAS:LUMI_TOT_INST', args.start_time, args.end_time, unixtime=False)

timestamp = atlas_lumi['ATLAS:LUMI_TOT_INST'][0]
lumi = atlas_lumi['ATLAS:LUMI_TOT_INST'][1]

import matplotlib.pyplot as plt

plt.plot(timestamp, lumi)


integrated_lumi = 0.
for i in range(len(lumi)-1) :
    delta = timestamp[i+1]-timestamp[i]
    integrated_lumi += (lumi[i] + lumi[i+1])/2*(delta.seconds + delta.microseconds/1e6)/1e3

print("Integrated luminosity: {0:.1f} nb-1".format(integrated_lumi))

plt.title("{0} to {1}: {2:.1f} nb-1".format(args.start_time, args.end_time, integrated_lumi))
plt.xlabel("Time")
plt.ylabel("Instantaneous luminosity [ub-1]")

plt.show()
