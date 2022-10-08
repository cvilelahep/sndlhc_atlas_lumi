import matplotlib.pyplot as plt
import datetime
import time
import ROOT
import numpy as np

logo_location = "/afs/cern.ch/user/c/cvilela/Large__SND_Logo_blue.png"

color_inst = 'navy'
color_integrated = 'chocolate'
color_run_band = 'royalblue'
muon_rate_color = 'black'
total_rate_color = 'tab:gray'

def addLogo(fig) :

    try :
        im = plt.imread(logo_location)
        newax = fig.add_axes([0.125,0.2,0.175,0.175], anchor='NW', zorder=100)
        newax.imshow(im)
        newax.axis('off')
    except :
        print("Error getting logo")
        pass


def makeUnixTime(year, month, day, hour, minute, second) :
    dt = datetime.datetime(year, month, day, hour, minute, second)
    return time.mktime(dt.timetuple())

off_runs = {"CAEN Mainframe dead" : [4965, 4966, 4967]

partial_off_runs = {"SciFi 5 off" : [4968, 4969, 4970, 4971]}

off_times = {}

off_times = []
partial_off_times = [[makeUnixTime(2022, 6, 27, 8, 0, 0), makeUnixTime(2022, 7, 6, 18, 0, 0)],
                     [makeUnixTime(2022, 8, 10, 0, 0, 0), makeUnixTime(2022, 9, 14, 8, 0, 0)],
                     [makeUnixTime(2022, 9, 14, 8, 0, 0), makeUnixTime(2022, 9, 28, 12, 0, 0)]]
partial_off_times = np.array(partial_off_times)


atlas_online_lumi = ROOT.TChain("LuminosityIP1/ATLAS_LUMI_TOT_INST")

atlas_online_lumi.Add("/eos/user/c/cvilela/nxcals_data_test/fill_*.root")

delivered_inst_lumi = []
delivered_unix_timestamp = []

recorded_mask = []
partial_mask = []

emulsion_runs = [[makeUnixTime(2022, 4, 7, 0, 0, 0), makeUnixTime(2022, 7, 26, 0, 0, 0)],
                 [makeUnixTime(2022, 7, 26, 0, 0, 0), makeUnixTime(2022, 9, 13, 0, 0, 0)],
                 [makeUnixTime(2022, 9, 13, 0, 0, 0), None]]

emulsion_mask = [[] for i in range(len(emulsion_runs))]                 

for entry in atlas_online_lumi :
    delivered_inst_lumi.append(entry.var)
    delivered_unix_timestamp.append(entry.unix_timestamp)

    is_in_partially_off_times = np.logical_and(entry.unix_timestamp > partial_off_times[:,0], entry.unix_timestamp < partial_off_times[:,1]).any()

    if entry.run_number in off_runs or entry.run_number < 0 :
        recorded_mask.append(False)
        partial_mask.append(False)
    elif is_in_partially_off_times or entry.run_number in partial_off_runs :
        recorded_mask.append(False)
        partial_mask.append(True)
    else :
        recorded_mask.append(True)
        partial_mask.append(True)

    for i_emulsion, [emulsion_run_start, emulsion_run_end] in enumerate(emulsion_runs) :
        if emulsion_run_end is not None :
            if entry.unix_timestamp > emulsion_run_start and entry.unix_timestamp < emulsion_run_end :
                emulsion_mask[i_emulsion].append(True)
            else :
                emulsion_mask[i_emulsion].append(False)
        else :
            if entry.unix_timestamp > emulsion_run_start :
                emulsion_mask[i_emulsion].append(True)
            else :
                emulsion_mask[i_emulsion].append(False)

emulsion_mask = np.array(emulsion_mask)

delivered_inst_lumi = np.array(delivered_inst_lumi)
delivered_unix_timestamp = np.array(delivered_unix_timestamp)

recorded_mask = np.array(recorded_mask)
partial_mask  = np.array(partial_mask)

delivered_deltas = delivered_unix_timestamp[1:] - delivered_unix_timestamp[:-1]
delivered_mask = delivered_deltas < 60

recorded_mask = np.logical_and(delivered_mask, recorded_mask[1:])
partial_mask = np.logical_and(delivered_mask, partial_mask[1:])


delivered_unix_timestamp = np.array([datetime.datetime.fromtimestamp(x) for x in delivered_unix_timestamp])

#plt.hist(delivered_deltas, bins = 1000)
#plt.yscale('log')

fig, ax = plt.subplots(figsize = (10, 5))

ax.plot(delivered_unix_timestamp[1:][delivered_mask], np.cumsum(np.multiply(delivered_deltas[delivered_mask], delivered_inst_lumi[1:][delivered_mask]))/1e9, label = "Delivered", color = color_inst)
ax.plot(delivered_unix_timestamp[1:][partial_mask], np.cumsum(np.multiply(delivered_deltas[partial_mask], delivered_inst_lumi[1:][partial_mask]))/1e9, label = "Recorded", color = color_inst, linestyle = "--")
ax.plot(delivered_unix_timestamp[1:][recorded_mask], np.cumsum(np.multiply(delivered_deltas[recorded_mask], delivered_inst_lumi[1:][recorded_mask]))/1e9, label = "Recorded (full detector operational)", color = color_inst, linestyle = ":")

ax._get_lines.get_next_color()

for i_emulsion in range(len(emulsion_mask)) :
    ax.plot(delivered_unix_timestamp[1:][emulsion_mask[i_emulsion][1:]], np.cumsum(np.multiply(delivered_deltas[emulsion_mask[i_emulsion][1:]], delivered_inst_lumi[1:][emulsion_mask[i_emulsion][1:]]))/1e9, label = "Emulsion run {0}".format(i_emulsion))


print("Delivered luminosity: {0} fb-1".format(np.cumsum(np.multiply(delivered_deltas[delivered_mask], delivered_inst_lumi[1:][delivered_mask]))[-1]/1e9))
print("Recorded luminosity: {0} fb-1".format(np.cumsum(np.multiply(delivered_deltas[partial_mask], delivered_inst_lumi[1:][partial_mask]))[-1]/1e9))
print("Recorded luminosity with full detector operational: {0} fb-1".format(np.cumsum(np.multiply(delivered_deltas[recorded_mask], delivered_inst_lumi[1:][recorded_mask]))[-1]/1e9))
for i_emulsion in range(len(emulsion_mask)) :
    print("Delivered luminosity for emulsion run {0}: {1} fb-1".format(i_emulsion, np.cumsum(np.multiply(delivered_deltas[emulsion_mask[i_emulsion][1:]], delivered_inst_lumi[1:][emulsion_mask[i_emulsion][1:]]))[-1]/1e9))
    print("Recorded luminosity for emulsion run {0}: {1} fb-1".format(i_emulsion, np.cumsum(np.multiply(delivered_deltas[np.logical_and(emulsion_mask[i_emulsion][1:], partial_mask)], delivered_inst_lumi[1:][np.logical_and(emulsion_mask[i_emulsion][1:], partial_mask)]))[-1]/1e9))
    print("Recorded luminosity with full detector operational for emulsion run {0}: {1} fb-1".format(i_emulsion, np.cumsum(np.multiply(delivered_deltas[np.logical_and(emulsion_mask[i_emulsion][1:], recorded_mask)], delivered_inst_lumi[1:][np.logical_and(emulsion_mask[i_emulsion][1:], recorded_mask)]))[-1]/1e9))

addLogo(fig)

ax.set_ylabel("Integrated luminosity [fb$^{-1}$]")

ax.legend()
#plt.plot(delivered_unix_timestamp, np.cumsum(delivered_inst_lumi))

fig.savefig("sndlhc_lumi_summary_20221004.png")
fig.savefig("sndlhc_lumi_summary_20221004.pdf")
fig.show()
