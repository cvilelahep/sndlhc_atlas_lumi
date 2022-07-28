import argparse

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

fetched_data = ldb.get(lumi_string, args.start_time, args.end_time, unixtime=False)
timestamp = fetched_data[lumi_string][0]
atlas_lumi = fetched_data[lumi_string][1]

f_out = open(args.output_directory+"/sndlhc_atlas_lumi_{0}.csv".format(args.snd_lhc_run_number), "w")
f_out.write("Timestamp,Seconds since start of run,Instantaneous lumi (ub-1),Integrated lumi (nb-1)\n")
integrated_lumi = 0.
t0 = timestamp[0]
for i in range(len(atlas_lumi)-1) :
    delta = timestamp[i+1]-timestamp[i]
    delta_seconds = delta.seconds + delta.microseconds/1e6
    delta_t0 = timestamp[i+1]-t0
    delta_t0_seconds = delta_t0.seconds + delta_t0.microseconds/1e6
    avg_lumi = (atlas_lumi[i] + atlas_lumi[i+1])/2

    integrated_lumi += avg_lumi*delta_seconds/1e3

    f_out.write("{0},{1:.3f},{2:.3f},{3:.3f}\n".format(timestamp[i+1].isoformat(), delta_t0_seconds, avg_lumi, integrated_lumi))
f_out.close()
print("Integrated luminosity: {0:.1f} nb-1".format(integrated_lumi))

if args.generate_plot :
    import matplotlib.pyplot as plt
    plt.plot(timestamp, atlas_lumi)
    plt.title("{0} to {1}: {2:.1f} nb-1".format(args.start_time, args.end_time, integrated_lumi))
    plt.xlabel("Time")
    plt.ylabel("Instantaneous luminosity [ub-1]")

    plt.savefig(args.output_directory+"/sndlhc_atlas_lumi_{0}".format(args.snd_lhc_run_number)+".png")

