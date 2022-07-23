import argparse
import datetime
import numpy as np
import matplotlib.pyplot as plt
import csv
import gc

#import tol_colors as tc

import ROOT

# Which runs have a reco file
runs_with_reco = [0, 1, 2, 3, 4, 5, 6]

rate_label = r"Single-track events with $|\theta_{\mathrm{I.P.}}| < 0.1 \, \mathrm{rad}$"
rate_bin_width = 500 # in milliseconds

logo_location = "/afs/cern.ch/user/c/cvilela/Large__SND_Logo_blue.png"

converted_runs_location = "/eos/experiment/sndlhc/convertedData/commissioning/TI18/"
reconstructed_runs_location = "/afs/cern.ch/work/c/cvilela/private/tempReco/"
lumi_file = "/afs/cern.ch/user/c/cvilela/sndlhc_atlas_lumi/sndlhc_atlas_lumi_0000.csv"

color_inst = 'navy'
color_integrated = 'chocolate'
color_run_band = 'royalblue'

def recalc_integrated(data) :
    # assume first dt is the same as second dt
    last_t = data[0]['timestamp'] - (data[1]['timestamp'] - data[0]['timestamp'])

    this_integrated_lumi = 0
    integrated_lumi = []

    for d in data :
        this_integrated_lumi += d['inst_lumi']*(d['timestamp']-last_t)/np.timedelta64(1, 's')/1.e6
        integrated_lumi.append(this_integrated_lumi)
        last_t = d['timestamp']
    return np.array(integrated_lumi)

def draw_inst(data, axis, color, mask = None) :
    axis.set_ylabel('Instantaneous luminosity [$\mu$b$^{-1}$s$^{-1}$]', color=color)
    axis.tick_params(axis='y', labelcolor=color)
    axis.plot(data[mask]['timestamp'], data[mask]['inst_lumi'], label = "Instantaneous luminosity", color = color)
    axis.set_ylim(0, axis.get_ylim()[1]*1.2)


def draw_integrated(data, axis, color, mask = None) :
    axis.set_ylabel('Integrated luminosity [pb$^{-1}$]', color=color)
    axis.plot(data[mask]['timestamp'], recalc_integrated(data[mask]), label = "Integrated luminosity", color = color)
    axis.tick_params(axis='y', labelcolor=color)
    axis.set_ylim(0, axis.get_ylim()[1]*1.2)

def draw_sndlhcruns(data, axis) :
    y_range = axis.get_ylim()

    max_run_length = np.timedelta64(0, "s")
    for run in data :
        if (run[2]-run[1]) > max_run_length :
            max_run_length = run[2]-run[1]
    for run in data :
        axis.fill( [run[1], run[2], run[2], run[1]], [0., 0., y_range[1], y_range[1]], color = color_run_band, alpha = 0.1, edgecolor = None)
        if (run[2] - run[1])*2.0 < max_run_length :
            continue
        axis.text( run[1]+(run[2]-run[1])/2, y = 0.8*y_range[1], s = "Run\n{0}".format(run[0]), ha = 'center')

def getMuonEvents(runNumber, run_start) :
    data = ROOT.TChain("rawConv")
    data.Add(converted_runs_location+"/run_00{0}/sndsw_raw-000[0-9].root".format(runNumber))
    reco = ROOT.TChain("rawConv")
    reco.Add(reconstructed_runs_location+"/run_00{0}/sndsw_raw-000[0-9]_muonReco.root".format(runNumber))

    ipMuon_timestamps = []
    for i_event in range(data.GetEntries()) :
        reco.GetEntry(i_event)

        if len(reco.Reco_MuonTracks) != 1 :
            continue

        mom = reco.Reco_MuonTracks.At(0).getFittedState().getMom()

        thetaz = np.arctan2((mom.X()**2 + mom.Y()**2)**0.5, mom.Z())

        if abs(thetaz) > 0.1 :
            continue

        data.GetEntry(i_event)

        ipMuon_timestamps.append(run_start + np.timedelta64(int(data.EventHeader.GetEventTime()*6.25), "ns"))
    del data
    del reco
    return ipMuon_timestamps
        
def addLogo(fig) :

    try :
        im = plt.imread(logo_location)
        newax = fig.add_axes([0.125,0.275,0.175,0.175], anchor='NW', zorder=100)
        newax.imshow(im)
        newax.axis('off')
    except :
        print("Error getting logo")
        pass
            
    


runs = np.genfromtxt('run_summary.csv', delimiter=',', dtype=[('run_number', 'i4'), ('start_time', 'datetime64[ms]'), ('end_time', 'datetime64[ms]'), ('reco_prescale_factor', int)])
lumi = np.genfromtxt(lumi_file, delimiter=',', skip_header=1, dtype=[('timestamp', 'datetime64[ms]'), ('seconds_since_start', 'f8'), ('inst_lumi', 'f4'), ('integrated_lumi', 'f4')])

badlumi = np.logical_and(lumi[:]['inst_lumi'] > 500, lumi[:]['timestamp'] < np.datetime64("2022-07-09 11:29:56.466000"))

print(np.max(lumi[:]['inst_lumi']))

fig_no_rate, ax_inst_no_rate = plt.subplots(figsize = (10, 5))
addLogo(fig_no_rate)
draw_inst(lumi, ax_inst_no_rate, color_inst, ~badlumi)
ax_integrated_no_rate = ax_inst_no_rate.twinx()
draw_integrated(lumi, ax_integrated_no_rate, color_integrated, ~badlumi)

draw_sndlhcruns(runs, ax_inst_no_rate)

plt.title("LHC Run 3")

fig_name = "sndlhc_lumi"

plt.savefig(fig_name+".png", dpi=300)
plt.savefig(fig_name+".pdf", dpi=300)

plt.draw()
plt.clf()
plt.close("all")
plt.close()
gc.collect()
print("Plotted no rate")

if len(runs_with_reco) :
    fig, (ax_inst, ax_murate) = plt.subplots(figsize = (10, 5), nrows = 2, sharex = True)

    addLogo(fig)
    
    draw_inst(lumi, ax_inst, color_inst, ~badlumi)
    ax_integrated = ax_inst.twinx()
    draw_integrated(lumi, ax_integrated, color_integrated, ~badlumi)

    draw_sndlhcruns(runs, ax_inst)

    plt.title("LHC Run 3")

    for i_run in runs_with_reco :
    
        nbins = int((runs[i_run][2]-runs[i_run][1])/np.timedelta64(rate_bin_width, 's'))
        bin_width = (runs[i_run][2]-runs[i_run][1])/np.timedelta64(1, 's')/nbins

        ip_muons = getMuonEvents(runs[i_run][0], runs[i_run][1])

        n, bins, _ = ax_murate.hist(ip_muons, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = "black", weights = [1.*runs[i_run]['reco_prescale_factor']/bin_width]*len(ip_muons))
        err = np.sqrt(n*bin_width/runs[i_run]['reco_prescale_factor'])/bin_width*runs[i_run]['reco_prescale_factor']
        x = (bins[:-1] + bins[1:])/2

        ax_murate.errorbar(x, n, yerr = err, color = "black", fmt = 'none')
        del ip_muons

    ax_murate.set_xlabel("Date")
    ax_murate.set_ylim((0, ax_murate.get_ylim()[1]*1.1))
    ax_murate.text( x = ax_murate.get_xlim()[0] + (ax_murate.get_xlim()[1]-ax_murate.get_xlim()[0])/2, y = ax_murate.get_ylim()[1]*0.9, s = rate_label, ha = "center")
    ax_murate.set_ylabel(r"Event rate [s$^{-1}$]")
    
    fig_name += "_rate"

    plt.savefig(fig_name+".png", dpi=300)
    plt.savefig(fig_name+".pdf", dpi=300)

    plt.draw()
    plt.clf()
    plt.close("all")
    plt.close()
    gc.collect()

    print("Plotted with rate")
    
    proc_min = np.min(runs[runs_with_reco]["start_time"])
    proc_max = np.max(runs[runs_with_reco]["end_time"])

    sub_intervals = [["proconly", runs_with_reco, proc_min, proc_max]]

    for i_run in runs_with_reco :
        sub_intervals.append([str(runs[i_run]["run_number"]), [i_run], runs[i_run]['start_time'], runs[i_run]['end_time']])
    
    for interval in sub_intervals :
        mask = np.logical_and(~badlumi, lumi['timestamp'] > interval[2])
        mask = np.logical_and(mask, lumi['timestamp'] < interval[3])
    
        fig_proconly, (ax_inst_proconly, ax_murate_proconly) = plt.subplots(figsize = (10, 5), nrows = 2, sharex = True)

        addLogo(fig_proconly)
        
        draw_inst(lumi, ax_inst_proconly, color_inst, mask)
        ax_integrated_proconly = ax_inst_proconly.twinx()
        draw_integrated(lumi, ax_integrated_proconly, color_integrated, mask)

        draw_sndlhcruns(runs[interval[1]], ax_inst_proconly)

        plt.title("LHC Run 3")
        
        for i_run in interval[1] :
    
            nbins = int((runs[i_run][2]-runs[i_run][1])/np.timedelta64(rate_bin_width, 's'))
            bin_width = (runs[i_run][2]-runs[i_run][1])/np.timedelta64(1, 's')/nbins
            
            ip_muons = getMuonEvents(runs[i_run][0], runs[i_run][1])

            n, bins, _ = ax_murate_proconly.hist(ip_muons, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = "black", weights = [1.*runs[i_run]["reco_prescale_factor"]/bin_width]*len(ip_muons))
            err = np.sqrt(n*bin_width/runs[i_run]["reco_prescale_factor"])/bin_width*runs[i_run]["reco_prescale_factor"]
            x = (bins[:-1] + bins[1:])/2
            ax_murate_proconly.errorbar(x, n, yerr = err, fmt = 'none', color = "black")
            del ip_muons
            
        ax_murate_proconly.set_xlabel("Date")
        ax_murate_proconly.set_ylim((0, ax_murate_proconly.get_ylim()[1]*1.1))
        ax_murate_proconly.text( x = ax_murate_proconly.get_xlim()[0] + (ax_murate_proconly.get_xlim()[1]-ax_murate_proconly.get_xlim()[0])/2, y = ax_murate_proconly.get_ylim()[1]*0.9, s = rate_label, ha = "center")
        ax_murate_proconly.set_ylabel(r"Event rate [s$^{-1}$]")
        
        plt.savefig(fig_name+"_"+interval[0]+".png", dpi=300)
        plt.savefig(fig_name+"_"+interval[0]+".pdf", dpi=300)
        print("Plotted with rate sub {0}".format(interval[0]))

        plt.draw()
        plt.clf()
        plt.close("all")
        plt.close()
        gc.collect()
