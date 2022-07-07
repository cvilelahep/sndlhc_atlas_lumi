import argparse

parser = argparse.ArgumentParser(description='Get ATLAS Luminosity between two timestamps')

parser.add_argument("snd_lhc_run_number", type = str, help="SND@LHC run number")
parser.add_argument("start_time", type = str, help="Start time in Y-m-d H:M:S format")
parser.add_argument("end_time", type = str, help="Start time in Y-m-d H:M:S format")
parser.add_argument('--generate_plot', dest='generate_plot', default=False, action='store_true')

args = parser.parse_args()

import pytimber

ldb = pytimber.LoggingDB(source="nxcals")

atlas_lumi = ldb.get('ATLAS:LUMI_TOT_INST', args.start_time, args.end_time, unixtime=False)

f_out = f.open("sndlhc_atlas_lumi_{0}.csv".format(args.snd_lhc_run_number), "w")
f_out.write("Timestamp,Seconds since start of run,Instantaneous lumi (ub-1),Integrated lumi (nb-1)")
integrated_lumi = 0.
t0 = timestamp[0]
for i in range(len(lumi)-1) :
    delta = timestamp[i+1]-timestamp[i]
    delta_t0 = timestamp[i+1]-t0
    integrated_lumi += (lumi[i] + lumi[i+1])/2*(delta.seconds + delta.microseconds/1e6)/1e3
    f_out.write("{0},{1:.3f},{2:.3f},{3:.3f}".format(str(timestamp[i+1]), delta_t0.seconds + delta_t0.microseconds/1e6, (lumi[i] + lumi[i+1])/2, integrated_lumi))
f_out.close()
print("Integrated luminosity: {0:.1f} nb-1".format(integrated_lumi))

if args.generate_plot :
    import matplotlib.pyplot as plt
    plt.plot(timestamp, lumi)
    timestamp = atlas_lumi['ATLAS:LUMI_TOT_INST'][0]
    lumi = atlas_lumi['ATLAS:LUMI_TOT_INST'][1]
    plt.title("{0} to {1}: {2:.1f} nb-1".format(args.start_time, args.end_time, integrated_lumi))
    plt.xlabel("Time")
    plt.ylabel("Instantaneous luminosity [ub-1]")

    plt.show()
