import matplotlib.pyplot as plt
import datetime
import dateutil.parser as dp
import time
import ROOT
import numpy as np
import json

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

with open("/home/sndlumi/dead-time-and-emulsion-runs/dead_time.json", "r") as f :
    dead_periods = json.load(f)["deadtime_periods"]

with open("/home/sndlumi/dead-time-and-emulsion-runs/emulsion_runs.json", "r") as f :
    emulsion_runs = json.load(f)["emulsion_runs"]

atlas_online_lumi = ROOT.TChain("LuminosityIP1/ATLAS_LUMI_TOT_INST")

atlas_online_lumi.Add("/eos/experiment/sndlhc/nxcals_data/fill_*.root")

delivered_inst_lumi = []
delivered_unix_timestamp = []
delivered_run_number = []
delivered_fill_number = []

recorded_mask = []
dead_period_mask = [[] for i in range(len(dead_periods))]

emulsion_mask = [[] for i in range(len(emulsion_runs))]               

time_now = time.time()
last_24 = time_now - 24*60*60
last_72 = time_now - 3*24*60*60
last_week = time_now - 7*24*60*60

for entry in atlas_online_lumi :
    delivered_inst_lumi.append(entry.var)
    delivered_unix_timestamp.append(entry.unix_timestamp)
    delivered_run_number.append(entry.run_number)
    

    # Which emulsion run?
    for i_emulsion_run, emulsion_run in enumerate(emulsion_runs) :
        start_date = dp.parse(emulsion_run["start_date"]).timestamp()
        if emulsion_run["end_date"] is None :
            end_date = time_now 
        else :
            end_date = dp.parse(emulsion_run["end_date"]).timestamp()
            
        if entry.unix_timestamp >= start_date and entry.unix_timestamp < end_date :
            emulsion_mask[i_emulsion_run].append(True)
        else :
            emulsion_mask[i_emulsion_run].append(False)
    
    # Is it in dead period?
    recorded = entry.run_number >= 0
    for i_dead_period, dead_period in enumerate(dead_periods) :
        start_date = dp.parse(dead_period["start_date"]).timestamp()
        if dead_period["end_date"] is None :
            end_date = time_now
        else :
            end_date = dp.parse(dead_period["end_date"]).timestamp()
            
        if entry.unix_timestamp >= start_date and entry.unix_timestamp < end_date :
            dead_period_mask[i_dead_period].append(True)
            if dead_period["good_for_physics"] == False :
                recorded = False
        else :
            dead_period_mask[i_dead_period].append(False)
    recorded_mask.append(recorded)

delivered_inst_lumi = np.array(delivered_inst_lumi)
delivered_unix_timestamp = np.array(delivered_unix_timestamp)

emulsion_mask = np.array(emulsion_mask)
dead_period_mask = np.array(dead_period_mask)

recorded_mask = np.array(recorded_mask)

delivered_deltas = delivered_unix_timestamp[1:] - delivered_unix_timestamp[:-1]
delivered_mask = delivered_deltas < 60

recorded_delta_mask = np.logical_and(delivered_mask, recorded_mask[1:])

delivered_24 = np.logical_and(delivered_unix_timestamp[1:] > last_24, delivered_mask)
delivered_72 = np.logical_and(delivered_unix_timestamp[1:] > last_72, delivered_mask)
delivered_week = np.logical_and(delivered_unix_timestamp[1:] > last_week, delivered_mask)

recorded_24 = np.logical_and(delivered_unix_timestamp[1:] > last_24, recorded_delta_mask)
recorded_72 = np.logical_and(delivered_unix_timestamp[1:] > last_72, recorded_delta_mask)
recorded_week = np.logical_and(delivered_unix_timestamp[1:] > last_week, recorded_delta_mask)

delivered_unix_timestamp = np.array([datetime.datetime.fromtimestamp(x) for x in delivered_unix_timestamp])

fig_cumulative, ax_cumulative = plt.subplots(figsize = (10, 5))

ax_cumulative.plot(delivered_unix_timestamp[1:][delivered_mask], np.cumsum(np.multiply(delivered_deltas[delivered_mask], delivered_inst_lumi[1:][delivered_mask]))/1e9, label = "Delivered", color = color_inst)
ax_cumulative.plot(delivered_unix_timestamp[1:][recorded_delta_mask], np.cumsum(np.multiply(delivered_deltas[recorded_delta_mask], delivered_inst_lumi[1:][recorded_delta_mask]))/1e9, label = "Recorded", color = color_inst, linestyle = "--")

ax_cumulative._get_lines.get_next_color()

for i_emulsion in range(len(emulsion_mask)) :
    ax_cumulative.plot(delivered_unix_timestamp[1:][emulsion_mask[i_emulsion][1:]], np.cumsum(np.multiply(delivered_deltas[emulsion_mask[i_emulsion][1:]], delivered_inst_lumi[1:][emulsion_mask[i_emulsion][1:]]))/1e9, label = "Emulsion run {0}".format(i_emulsion))

fig_inst, ax_inst = plt.subplots(figsize = (10, 5))

ax_inst.plot(delivered_unix_timestamp, delivered_inst_lumi/1e9, label = "Delivered", color = color_inst)
ax_inst.plot(delivered_unix_timestamp[recorded_mask], delivered_inst_lumi[recorded_mask]/1e9, label = "Recorded", color = color_integrated)

addLogo(fig_cumulative)
addLogo(fig_inst)

ax_cumulative.set_ylabel("Integrated luminosity [fb$^{-1}$]")
ax_cumulative.legend()

ax_inst.set_ylabel("Instantaneous luminosity [fb$^{-1}$s$^{-1}$]")
ax_inst.set_yscale("log")
ax_inst.legend()

fig_cumulative.savefig("sndlhc_delivered_recorded_integrated_lumi.png")
fig_cumulative.savefig("sndlhc_delivered_recorded_integrated_lumi.pdf")
fig_cumulative.savefig("sndlhc_delivered_recorded_integrated_lumi.eps")

fig_inst.savefig("sndlhc_delivered_recorded_instantaneous_lumi.png")
fig_inst.savefig("sndlhc_delivered_recorded_instantaneous_lumi.pdf")
fig_inst.savefig("sndlhc_delivered_recorded_instantaneous_lumi.eps")

for i_emulsion in range(len(emulsion_mask)) :
    ax_inst.plot(delivered_unix_timestamp[emulsion_mask[i_emulsion]], delivered_inst_lumi[emulsion_mask[i_emulsion]]/1e9, label = "Emulsion run {0}".format(i_emulsion))

fig_inst.savefig("sndlhc_delivered_recorded_instantaneous_lumi_emulsion.png")
fig_inst.savefig("sndlhc_delivered_recorded_instantaneous_lumi_emulsion.pdf")
fig_inst.savefig("sndlhc_delivered_recorded_instantaneous_lumi_emulsion.eps")

    
print("LAST UPDATE: {0}Z".format(datetime.datetime.fromtimestamp(time_now).isoformat()))
print("All time:")
print("Delivered luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[delivered_mask], delivered_inst_lumi[1:][delivered_mask]))[-1]/1e9))
print("Recorded luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[recorded_delta_mask], delivered_inst_lumi[1:][recorded_delta_mask]))[-1]/1e9))
print()
print("Last 24 hours:")
print("Delivered luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[delivered_24], delivered_inst_lumi[1:][delivered_24]))[-1]/1e9))
print("Recorded luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[recorded_24], delivered_inst_lumi[1:][recorded_24]))[-1]/1e9))
print()
print("Last 72 hours:")
print("Delivered luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[delivered_72], delivered_inst_lumi[1:][delivered_72]))[-1]/1e9))
print("Recorded luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[recorded_72], delivered_inst_lumi[1:][recorded_72]))[-1]/1e9))
print()
print("Last week:")
print("Delivered luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[delivered_week], delivered_inst_lumi[1:][delivered_week]))[-1]/1e9))
print("Recorded luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[recorded_week], delivered_inst_lumi[1:][recorded_week]))[-1]/1e9))
print()
for i_emulsion in range(len(emulsion_mask)) :
    print("Emulsion run {0}:".format(i_emulsion))
    print("Delivered luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[emulsion_mask[i_emulsion][1:]], delivered_inst_lumi[1:][emulsion_mask[i_emulsion][1:]]))[-1]/1e9))
    print("Recorded luminosity: {0:0.3f} fb-1".format(np.cumsum(np.multiply(delivered_deltas[np.logical_and(emulsion_mask[i_emulsion][1:], recorded_delta_mask)], delivered_inst_lumi[1:][np.logical_and(emulsion_mask[i_emulsion][1:], recorded_delta_mask)]))[-1]/1e9))
print()

print("Delivered luminosity with electronic detector issues:")
for i_dead_period in range(len(dead_period_mask)) :
    print("{0}: {1:0.3f} fb-1".format(dead_periods[i_dead_period]["comment"], np.cumsum(np.multiply(delivered_deltas[dead_period_mask[i_dead_period][1:]], delivered_inst_lumi[1:][dead_period_mask[i_dead_period][1:]]))[-1]/1e9))

print()

# Let's try to make a table!
for i_dead_period in range(len(dead_period_mask)) :
    print(dead_periods[i_dead_period]["comment"], end = "")
    for j_emulsion in range(len(emulsion_mask)) :
        cell_mask = np.logical_and(emulsion_mask[j_emulsion][1:], dead_period_mask[i_dead_period][1:])
        if np.sum(cell_mask) == 0 :
            print(" {0:0.3f}".format(0), end = "")
        else :
            print(" {0:0.3f}".format(np.cumsum(np.multiply(delivered_deltas[cell_mask], delivered_inst_lumi[1:][cell_mask]))[-1]/1e9), end = "")
    print("")
    

plt.show()
