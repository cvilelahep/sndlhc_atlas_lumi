import matplotlib.pyplot as plt
import matplotlib.dates as md
import os
import gc
import datetime
import dateutil.parser as dp
import time
import ROOT
import numpy as np
import json
from collections import OrderedDict

tol_bright = ['#4477AA', '#EE6677', '#228833', '#CCBB44', '#66CCEE', '#AA3377', '#BBBBBB']
tol_muted = ['#CC6677', '#332288', '#DDCC77', '#117733', '#88CCEE', '#882255', '#44AA99', '#999933', '#AA4499']
tol_light = ['#77AADD', '#EE8866', '#EEDD88', '#FFAABB', '#99DDFF', '#44BB99', '#BBCC33', '#AAAA00']
tol_dark = ['#222255', '#225555', '#225522', '#666633', '#663333', '#555555']

year_palette = tol_bright
emulsion_dash_palette = list(reversed(tol_muted))

color_inst = tol_bright[0]

MAX_DELTA = 120. # Maximum interval between data points in seconds. Skip data point if interval exceeds this number. This is to avoid integrating the luminosity over gaps in the data.

time_now = time.time()
last_24 = time_now - 24*60*60
last_72 = time_now - 3*24*60*60
last_week = time_now - 7*24*60*60

page_title = "SND@LHC luminosity summary"

html = []
html.append("<HEAD>")
html.append("   <style>")
#html.append("      table, th, td {")
#html.append("         border: 1px solid black;")
#html.append("         border-collapse: collapse;")
html.append("      table {")
html.append("         border: 1px solid black;")
html.append("         margin: 5px;")
html.append("      }")
html.append("      th, td {")
#html.append("         padding-top: 10px;")
#html.append("         padding-bottom: 20px;")
html.append("         padding-left: 10px;")
html.append("         padding-right: 10px;")
html.append("      }")
html.append("   </style>")
html.append("<TITLE>{}</TITLE>".format(page_title))
html.append("<META HTTP-EQUIV=\"CACHE-CONTROL\" CONTENT=\"NO-CACHE\">")
html.append("<META HTTP-EQUIV=\"EXPIRES\" CONTENT=\"Mon, 22 Jul 2002 11:12:01 GMT\">")
html.append("<meta http-equiv=\"refresh\" content=\"100000\"/>")
html.append("</HEAD>")
html.append(" <BODY>")
html.append("  <CENTER><H1>{}</H1></CENTER>".format(page_title))
html.append("<CENTER>")
html.append("<p>")
html.append("LAST UPDATE: {0}Z".format(datetime.datetime.fromtimestamp(time_now).isoformat()))
html.append("</p>")
html.append(" </BODY>")

plt.rcParams["legend.loc"] = "center left"

xfmt = md.DateFormatter('%m-%d')


os.makedirs("Plots", exist_ok = True)

# Get reported deadtime
with open("/home/sndlumi/dead-time-and-emulsion-runs/dead_time.json", "r") as f :
    dead_periods = json.load(f)["deadtime_periods"]

# Get emulsion run data
with open("/home/sndlumi/dead-time-and-emulsion-runs/emulsion_runs.json", "r") as f :
    emulsion_runs = json.load(f)["emulsion_runs"]

# just for testing
#emulsion_runs = []
    
# Get beam mode data
beam_modes_df = ROOT.RDataFrame("LHC/HX_BMODE", "/eos/experiment/sndlhc/nxcals_data/fill_*.root")

beam_mode = beam_modes_df.AsNumpy(columns = ["var"])["var"]
stable_start = beam_mode == "STABLE"
stable_end = np.concatenate([[False], stable_start[:-1]])

beam_mode_unix_timestamp = beam_modes_df.AsNumpy(columns = ["unix_timestamp"])["unix_timestamp"]

stable_beams_dataset = np.rec.fromarrays([beam_mode_unix_timestamp[stable_start], beam_mode_unix_timestamp[stable_end]], names = ["start", "end"])
del beam_modes_df, beam_mode, stable_start, stable_end, beam_mode_unix_timestamp

# Get ATLAS lumi
#atlas_online_lumi_df = ROOT.RDataFrame("LuminosityIP1/ATLAS_LUMI_TOT_INST", "/eos/experiment/sndlhc/nxcals_data/fill_*.root")
#atlas_online_lumi_df = ROOT.RDataFrame("LuminosityIP1/ATLAS_OFFLINE_LUMI_TOT_INST", "/eos/experiment/sndlhc/nxcals_data/fill_*.root")
#lumi_scale = (1.-0.054) 
#atlas_online_lumi = atlas_online_lumi_df.AsNumpy(columns = ["var"])["var"]*lumi_scale

atlas_online_lumi_df = ROOT.RDataFrame("atlas_lumi", "/eos/experiment/sndlhc/atlas_lumi/fill_*.root")
atlas_online_lumi = atlas_online_lumi_df.AsNumpy(columns = ["var"])["var"]
lumi_scale = 1.

atlas_online_lumi_unix_timestamp = atlas_online_lumi_df.AsNumpy(columns = ["unix_timestamp"])["unix_timestamp"]
atlas_online_lumi_run_number = atlas_online_lumi_df.AsNumpy(columns = ["run_number"])["run_number"]

runs_with_lumi = np.unique(atlas_online_lumi_run_number)
runs_with_lumi = runs_with_lumi[runs_with_lumi != -1]

dataset = np.rec.fromarrays([atlas_online_lumi_run_number, atlas_online_lumi_unix_timestamp, atlas_online_lumi/1e9], names = ["run_number", "unix_timestamp", "lumi"])

del atlas_online_lumi, atlas_online_lumi_unix_timestamp, atlas_online_lumi_run_number

# Get Stable beams luminosity
# Placeholder for stable beams mask
stable_beams = [False]*len(dataset)
for stable_beam_period in stable_beams_dataset :
    stable_beams = np.logical_or(stable_beams, np.logical_and(dataset["unix_timestamp"] >= stable_beam_period["start"],
                                                              dataset["unix_timestamp"] < stable_beam_period["end"]))
year_mask = {}
for year in range(2022, datetime.date.today().year+1) :
    year_mask[year] = np.logical_and(dataset["unix_timestamp"] >= datetime.datetime(year, 1, 1).timestamp(),
                                     dataset["unix_timestamp"] < datetime.datetime(year+1, 1, 1).timestamp())
    
# Lists to keep integrated lumi
all_delivered = []
all_recorded = []

year_delivered = OrderedDict()
year_recorded = OrderedDict()

runs = []

emulsion_runs_delivered = []
emulsion_runs_recorded = []

dead_time_periods_delivered = []

last_time_periods_delivered = []
last_time_periods_recorded = []

# Function to integrate the luminosity and make plots
def integrate_and_plot(d, selection, axes_inst, axes_int, date_offset = None, **kwargs) :
    this_d = d[selection(d)]

    if not len(this_d) :
        return [0., 0., 0.]
    
    this_start = this_d[0]["unix_timestamp"]
    this_end = this_d[-1]["unix_timestamp"]
    
    this_delta = this_d[1:]["unix_timestamp"] - this_d[:-1]["unix_timestamp"]
    this_avg_lumi = (this_d[1:]["lumi"] + this_d[:-1]["lumi"])/2

    this_mask = this_delta < MAX_DELTA

    this_integrated = np.cumsum(np.multiply(this_avg_lumi[this_mask], this_delta[this_mask]))
    
    try :
        this_integral = this_integrated[-1]
    except IndexError :
        this_integral = 0
        return [this_integral, this_start, this_end]

    dates= np.array([ datetime.datetime.fromtimestamp(ts) for ts in this_d["unix_timestamp"] ])

    if axes_inst is not None :
        for i_ax, ax_inst in enumerate(axes_inst) :
            if date_offset is not None :
                offset = date_offset[i_ax]
            else :
                offset = datetime.timedelta(0.)
            ax_inst.plot(dates-offset, this_d["lumi"], **kwargs)
            ax_inst.xaxis.set_major_formatter(xfmt)
            ax_inst.set_ylim(ymin=0)
    if axes_int is not None :
        for i_ax, ax_int in enumerate(axes_int) :
            if date_offset is not None :
                offset = date_offset[i_ax]
            else :
                offset = datetime.timedelta(0.)
            ax_int.plot(dates[1:][this_mask]-offset, this_integrated, **kwargs)
            ax_int.xaxis.set_major_formatter(xfmt)
            ax_int.set_ylim(ymin=0)
    return [this_integral, this_start, this_end]

# Just a helper function to save the figures and close them
def fig_save_and_close(fig, base_name) :
    fig.savefig(base_name+".png", dpi = 300)
    fig.savefig(base_name+".pdf", dpi = 300)
    fig.savefig(base_name+".eps", dpi = 300)
    fig.clf()
    plt.close(fig)
    gc.collect()

# Mask of ATLAS luminosity points where there was no SND@LHC active run
no_active_run = dataset["run_number"] == - 1

# Placeholder for mask of reported deadtime
reported_dead_time = [False]*len(dataset)

# Make plots and integrate lumi for reported deadtime
for i_dead_period, dead_period in enumerate(dead_periods) :
    
    start_date = dp.parse(dead_period["start_date"]).timestamp()
    if dead_period["end_date"] is None :
        end_date = time_now
    else :
        end_date = dp.parse(dead_period["end_date"]).timestamp()

    this_period = np.logical_and(dataset["unix_timestamp"] >= start_date, dataset["unix_timestamp"] < end_date)
    
    if dead_period["good_for_physics"] == False :
        reported_dead_time = np.logical_or(reported_dead_time, this_period)

    fig_instantaneous_dead, ax_instantaneous_dead = plt.subplots(figsize = (10, 5))
    fig_integrated_dead, ax_integrated_dead = plt.subplots(figsize = (10, 5))

    dead_time_periods_delivered.append(integrate_and_plot(dataset, lambda x : this_period, [ax_instantaneous_dead], [ax_integrated_dead], label = dead_period["comment"]))

    ax_integrated_dead.grid(alpha = 0.3)
    ax_instantaneous_dead.grid(alpha = 0.3)

    ax_integrated_dead.set_ylabel("Integrated luminosity [fb$^{-1}$]")
    ax_instantaneous_dead.set_ylabel("Instantaneous luminosity [fb$^{-1}$s$^{-1}$]")

    ax_instantaneous_dead.legend()
    ax_integrated_dead.legend()

    fig_save_and_close(fig_instantaneous_dead, "Plots/sndlhc_instantaneous_lumi_detector_period_{0}".format(i_dead_period))
    fig_save_and_close(fig_integrated_dead, "Plots/sndlhc_integrated_lumi_detector_period_{0}".format(i_dead_period))

# Mask of unreported deadtime
unreported_dead = np.logical_and(no_active_run, ~reported_dead_time)

# Plot unreported deadtime
fig_instantaneous_unreported_dead, ax_instantaneous_unreported_dead = plt.subplots(figsize = (10, 5))
fig_integrated_unreported_dead, ax_integrated_unreported_dead = plt.subplots(figsize = (10, 5))

unreported_dead_integral = integrate_and_plot(dataset, lambda x : unreported_dead, [ax_instantaneous_unreported_dead], [ax_integrated_unreported_dead], label = "Unreported dead time")

fig_save_and_close(fig_instantaneous_unreported_dead, "Plots/sndlhc_instantaneous_lumi_unreported_deadtime")
fig_save_and_close(fig_integrated_unreported_dead, "Plots/sndlhc_integrated_lumi_unreported_deadtime")

# Mask of all deadtime
dead_time = np.logical_or(no_active_run, reported_dead_time)

# Plot delivered and recorded lumi
fig_instantaneous, ax_instantaneous = plt.subplots(figsize = (10, 5))
fig_integrated, ax_integrated = plt.subplots(figsize = (10, 5))

all_delivered.append(integrate_and_plot(dataset, lambda x : [True]*len(dataset), [ax_instantaneous], [ax_integrated], label = "Delivered", color = color_inst))
all_recorded.append(integrate_and_plot(dataset, lambda x : ~dead_time, [ax_instantaneous], [ax_integrated], label = "Recorded", color = color_inst, linestyle = "--"))

# Plot delivered and recorded lumi for stable beams only
fig_instantaneous_stable, ax_instantaneous_stable = plt.subplots(figsize = (10, 5))
fig_integrated_stable, ax_integrated_stable = plt.subplots(figsize = (10, 5))

all_delivered.append(integrate_and_plot(dataset, lambda x : stable_beams, [ax_instantaneous_stable], [ax_integrated_stable], label = "Delivered", color = color_inst))
all_recorded.append(integrate_and_plot(dataset, lambda x : np.logical_and(stable_beams, ~dead_time), [ax_instantaneous_stable], [ax_integrated_stable], label = "Recorded", color = color_inst, linestyle = "--"))

fig_instantaneous_mod, ax_instantaneous_mod = plt.subplots(figsize = (10, 5))
fig_integrated_mod, ax_integrated_mod = plt.subplots(figsize = (10, 5))

# Plot by year
for i_year, year in enumerate(year_mask.keys()) :
    year_delivered[year] = []
    year_recorded[year] = []
    
    fig_instantaneous_year, ax_instantaneous_year = plt.subplots(figsize = (10, 5))
    fig_integrated_year, ax_integrated_year = plt.subplots(figsize = (10, 5))
    
    year_delivered[year].append(integrate_and_plot(dataset, lambda x : year_mask[year], [ax_instantaneous_year, ax_instantaneous_mod], [ax_integrated_year, ax_integrated_mod], date_offset = [datetime.timedelta(0.), datetime.timedelta(days = int((year-2022)*365.25))], label = "Delivered {}".format(year), color = year_palette[i_year], linewidth = 2))
    
    year_recorded[year].append(integrate_and_plot(dataset, lambda x : np.logical_and(year_mask[year], ~dead_time), [ax_instantaneous_year, ax_instantaneous_mod], [ax_integrated_year, ax_integrated_mod], date_offset = [datetime.timedelta(0.), datetime.timedelta(days = int((year-2022)*365.25))], label = "Recorded {}".format(year), color = year_palette[i_year], linestyle = "--", linewidth = 1))
                            
    fig_instantaneous_stable_year, ax_instantaneous_stable_year = plt.subplots(figsize = (10, 5))
    fig_integrated_stable_year, ax_integrated_stable_year = plt.subplots(figsize = (10, 5))

    year_delivered[year].append(integrate_and_plot(dataset, lambda x : np.logical_and(stable_beams, year_mask[year]), [ax_instantaneous_stable_year], [ax_integrated_stable_year], label = "Delivered", color = color_inst, linewidth = 2))
    year_recorded[year].append(integrate_and_plot(dataset, lambda x : np.logical_and(stable_beams, np.logical_and(year_mask[year], ~dead_time)), [ax_instantaneous_stable_year], [ax_integrated_stable_year], label = "Recorded", color = color_inst, linestyle = "--", linewidth = 2))
    
    # Plot delivered and recorded lumi separately for each emulsion run
    for i_emulsion_run, emulsion_run in enumerate(emulsion_runs) :
        
#        this_color = plt.rcParams['axes.prop_cycle'].by_key()['color'][i_emulsion_run % len(plt.rcParams['axes.prop_cycle'].by_key()['color'])]
        this_color = emulsion_dash_palette[i_emulsion_run % len(emulsion_dash_palette)]
        
        start_date = dp.parse(emulsion_run["start_date"]).timestamp()
        if emulsion_run["end_date"] is None :
            end_date = time_now 
        else :
            end_date = dp.parse(emulsion_run["end_date"]).timestamp()
    
        dummy_fig, dummy_ax = plt.subplots(figsize = (10, 5))
        
        this_emu_delivered = integrate_and_plot(dataset, lambda x : np.logical_and(np.logical_and(x["unix_timestamp"] >= start_date, x["unix_timestamp"] < end_date), year_mask[year]), [dummy_ax] , [dummy_ax], label = "Emulsion run {0}".format(i_emulsion_run), color = this_color, linewidth = 1)

        dummy_fig.clf()
        plt.close(dummy_fig)
        gc.collect()
        
        if this_emu_delivered[0] :

            fig_instantaneous_emulsion, ax_instantaneous_emulsion = plt.subplots(figsize = (10, 5))
            fig_integrated_emulsion, ax_integrated_emulsion = plt.subplots(figsize = (10, 5))

            emulsion_axes_inst = [ax_instantaneous, ax_instantaneous_year, ax_instantaneous_emulsion, ax_instantaneous_mod]
            emulsion_axes_int = [ax_integrated, ax_integrated_year, ax_integrated_emulsion, ax_integrated_mod]
            emulsion_offsets = [datetime.timedelta(0.), datetime.timedelta(0.), datetime.timedelta(0.), datetime.timedelta(days = int((year-2022)*365.25))]
            
            emulsion_runs_delivered.append(integrate_and_plot(dataset, lambda x : np.logical_and(np.logical_and(x["unix_timestamp"] >= start_date, x["unix_timestamp"] < end_date), year_mask[year]), emulsion_axes_inst , emulsion_axes_int, date_offset = emulsion_offsets, label = "Emulsion run {0}".format(i_emulsion_run), color = this_color, linewidth = 1))
            emulsion_runs_recorded.append(integrate_and_plot(dataset, lambda x : np.logical_and(np.logical_and(~dead_time, np.logical_and(x["unix_timestamp"] >= start_date, x["unix_timestamp"] < end_date)), year_mask[year]), emulsion_axes_inst, emulsion_axes_int, date_offset = emulsion_offsets, label = None, color = this_color, linestyle = "--", linewidth = 1))
        
            ax_integrated_emulsion.grid(alpha = 0.3)
            ax_instantaneous_emulsion.grid(alpha = 0.3)
    
            ax_integrated_emulsion.set_ylabel("Integrated luminosity [fb$^{-1}$]")
            ax_instantaneous_emulsion.set_ylabel("Instantaneous luminosity [fb$^{-1}$s$^{-1}$]")
    
            ax_instantaneous_emulsion.legend()
            ax_integrated_emulsion.legend()
    
            fig_save_and_close(fig_instantaneous_emulsion, "Plots/sndlhc_instantaneous_lumi_emulsion_run_{0}".format(i_emulsion_run))
            fig_save_and_close(fig_integrated_emulsion, "Plots/sndlhc_integrated_lumi_emulsion_run_{0}".format(i_emulsion_run))

    ax_integrated_year.grid(alpha = 0.3)
    ax_instantaneous_year.grid(alpha = 0.3)

    ax_integrated_year.set_ylabel("Integrated luminosity [fb$^{-1}$]")
    ax_instantaneous_year.set_ylabel("Instantaneous luminosity [fb$^{-1}$s$^{-1}$]")
    
    ax_instantaneous_year.legend()
    ax_integrated_year.legend()
    
    fig_save_and_close(fig_instantaneous_year, "Plots/sndlhc_instantaneous_lumi_{}".format(year))
    fig_save_and_close(fig_integrated_year, "Plots/sndlhc_integrated_lumi_{}".format(year))

                               
ax_integrated_mod.grid(alpha = 0.3)
ax_instantaneous_mod.grid(alpha = 0.3)

ax_integrated_mod.set_ylabel("Integrated luminosity [fb$^{-1}$]")
ax_instantaneous_mod.set_ylabel("Instantaneous luminosity [fb$^{-1}$s$^{-1}$]")

ax_instantaneous_mod.legend()
ax_integrated_mod.legend()

fig_save_and_close(fig_instantaneous_mod, "Plots/sndlhc_instantaneous_lumi_mod")
fig_save_and_close(fig_integrated_mod, "Plots/sndlhc_integrated_lumi_mod")

ax_integrated.grid(alpha = 0.3)
ax_instantaneous.grid(alpha = 0.3)

ax_integrated.set_ylabel("Integrated luminosity [fb$^{-1}$]")
ax_instantaneous.set_ylabel("Instantaneous luminosity [fb$^{-1}$s$^{-1}$]")

ax_instantaneous.legend()
ax_integrated.legend()

fig_save_and_close(fig_instantaneous, "Plots/sndlhc_instantaneous_lumi")
fig_save_and_close(fig_integrated, "Plots/sndlhc_integrated_lumi")

html.append("<table>")
html.append("<tr>")
html.append("<th></th>")
html.append("<th colspan=\"4\">Integrated luminosity</th>")
html.append("<th colspan=\"3\">Plots</th>")
html.append("</tr>")
html.append("<tr>")
html.append("<th>Period</th>")
html.append("<th>Delivered [fb<sup>-1</sup>]</th>")
html.append("<th>Recorded [fb<sup>-1</sup>]</th>")
html.append("<th>From</th>")
html.append("<th>To</th>")
html.append("<th>Integrated</th>")
html.append("<th>Instantaneous</th>")
html.append("<th>Integrated modulo year</th>")
html.append("</tr>")
html.append("<tr>")
html.append("<td>All time</td>")
html.append("<td>{:.3f}</td>".format(all_delivered[0][0]))
html.append("<td>{:.3f}</td>".format(all_recorded[0][0]))
html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(all_recorded[0][1]).isoformat()))
html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(all_recorded[0][2]).isoformat()))
html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_integrated_lumi"+suffix for suffix in [".png", ".pdf", ".eps"]]))
html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_instantaneous_lumi"+suffix for suffix in [".png", ".pdf", ".eps"]]))
html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_integrated_lumi_mod"+suffix for suffix in [".png", ".pdf", ".eps"]]))
html.append("</tr>")
for year in reversed(year_mask.keys()) :
    html.append("<tr>")
    html.append("<td>{}</td>".format(year))
    html.append("<td>{:.3f}</td>".format(year_delivered[year][0][0]))
    html.append("<td>{:.3f}</td>".format(year_recorded[year][0][0]))
    html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(year_recorded[year][0][1]).isoformat()))
    html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(year_recorded[year][0][2]).isoformat()))
    html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_integrated_lumi_{}".format(year)+suffix for suffix in [".png", ".pdf", ".eps"]]))
    html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_instantaneous_lumi_{}".format(year)+suffix for suffix in [".png", ".pdf", ".eps"]]))
    html.append("<td></td>")
    html.append("</tr>")
html.append("</table>")

html.append("<table>")
html.append("<tr>")
html.append("<th></th>")
html.append("<th colspan=\"4\">Integrated luminosity [fb<sup>-1</sup>]</th>")
html.append("<th colspan=\"2\">Plots</th>")
html.append("</tr>")
html.append("<tr>")
html.append("<th>Emulsion run</th>")
html.append("<th>Delivered</th>")
html.append("<th>Recorded</th>")
html.append("<th>From</th>")
html.append("<th>To</th>")
html.append("<th>Integrated</th>")
html.append("<th>Instantaneous</th>")
html.append("</tr>")
for i_emulsion in range(len(emulsion_runs_delivered)-1, -1, -1) :
    html.append("<tr>")
    html.append("<td>{}</td>".format(i_emulsion))
    html.append("<td>{:.3f}</td>".format(emulsion_runs_delivered[i_emulsion][0]))
    html.append("<td>{:.3f}</td>".format(emulsion_runs_recorded[i_emulsion][0]))
    html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(emulsion_runs_delivered[i_emulsion][1]).isoformat()))
    html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(emulsion_runs_delivered[i_emulsion][2]).isoformat()))
    html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_integrated_lumi_emulsion_run_{0}".format(i_emulsion)+suffix for suffix in [".png", ".pdf", ".eps"]]))
    html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_instantaneous_lumi_emulsion_run_{0}".format(i_emulsion)+suffix for suffix in [".png", ".pdf", ".eps"]]))
    html.append("</tr>")
html.append("</table>")

#delivered_run = OrderedDict()
recorded_run = OrderedDict()
for run in runs_with_lumi :
    
    fig_instantaneous_run, ax_instantaneous_run = plt.subplots(figsize = (10, 5))
    fig_integrated_run, ax_integrated_run = plt.subplots(figsize = (10, 5))

#    delivered_run[run] = integrate_and_plot(dataset, lambda x : dataset["run_number"] == run , [ax_instantaneous_run], [ax_integrated_run], label = "Delivered run {}".format(run), color = color_inst)
    recorded_run[run] = integrate_and_plot(dataset, lambda x : np.logical_and(~dead_time,  dataset["run_number"] == run), [ax_instantaneous_run], [ax_integrated_run], label = "Recorded run {}".format(run), color = color_inst)

    ax_integrated_run.grid(alpha = 0.3)
    ax_instantaneous_run.grid(alpha = 0.3)

    ax_integrated_run.set_ylabel("Integrated luminosity [fb$^{-1}$]")
    ax_instantaneous_run.set_ylabel("Instantaneous luminosity [fb$^{-1}$s$^{-1}$]")
    
    ax_instantaneous_run.legend()
    ax_integrated_run.legend()

    fig_save_and_close(fig_instantaneous_run, "Plots/sndlhc_instantaneous_lumi_run_{0}".format(run))
    fig_save_and_close(fig_integrated_run, "Plots/sndlhc_integrated_lumi_run_{0}".format(run))

html.append("<table>")
html.append("<tr>")
html.append("<th></th>")
html.append("<th></th>")
html.append("<th></th>")
html.append("<th></th>")
html.append("<th colspan=\"2\">Plots</th>")
html.append("</tr>")
html.append("<tr>")
html.append("<th>DAQ run</th>")
html.append("<th>Recorded luminosity [fb<sup>-1</sup>]</th>")
html.append("<th>From</th>")
html.append("<th>To</th>")
html.append("<th>Integrated</th>")
html.append("<th>Instantaneous</th>")
html.append("</tr>")
for i_run_index in range(len(runs_with_lumi)-1, -1, -1) :
    this_run = runs_with_lumi[i_run_index]
    if not recorded_run[this_run][0] :
        continue
    html.append("<tr>")
    html.append("<td>{}</td>".format(this_run))
    html.append("<td>{:.3f}</td>".format(recorded_run[this_run][0]))
    html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(recorded_run[this_run][1]).isoformat()))
    html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(recorded_run[this_run][2]).isoformat()))
    html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_integrated_lumi_run_{0}".format(this_run)+suffix for suffix in [".png", ".pdf", ".eps"]]))
    html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_instantaneous_lumi_run_{0}".format(this_run)+suffix for suffix in [".png", ".pdf", ".eps"]]))
    html.append("</tr>")
html.append("</table>")

html.append("<table>")
html.append("<tr>")
html.append("<th></th>")
html.append("<th></th>")
html.append("<th></th>")
html.append("<th></th>")
html.append("<th colspan=\"2\">Plots</th>")
html.append("</tr>")
html.append("<tr>")
html.append("<th>Detector periods</th>")
html.append("<th>Integrated luminosity [fb<sup>-1</sup>]</th>")
html.append("<th>From</th>")
html.append("<th>To</th>")
html.append("<th>Integrated</th>")
html.append("<th>Instantaneous</th>")
html.append("</tr>")
for i_dead_period, dead_period in enumerate(dead_periods) :
    html.append("<tr>")
    html.append("<td>{}</td>".format(dead_period["comment"]))
    html.append("<td>{:.3f}</td>".format(dead_time_periods_delivered[i_dead_period][0]))
    html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(dead_time_periods_delivered[i_dead_period][1]).isoformat()))
    html.append("<td>{}</td>".format(datetime.datetime.fromtimestamp(dead_time_periods_delivered[i_dead_period][2]).isoformat()))
    html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_integrated_lumi_detector_period_{0}".format(i_dead_period)+suffix for suffix in [".png", ".pdf", ".eps"]]))
    html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_instantaneous_lumi_detector_period_{0}".format(i_dead_period)+suffix for suffix in [".png", ".pdf", ".eps"]]))
    html.append("</tr>")
html.append("<tr>")
html.append("<td>{}</td>".format("Unreported dead time"))
html.append("<td>{:.3f}</td>".format(unreported_dead_integral[0]))
html.append("<td></td>")
html.append("<td></td>")
html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_integrated_lumi_unreported_deadtime"+suffix for suffix in [".png", ".pdf", ".eps"]]))
html.append("<td><a href=\"{}\">png</a>  <a href=\"{}\">pdf</a>  <a href=\"{}\">eps</a></td>".format(*["sndlhc_instantaneous_lumi_unreported_deadtime"+suffix for suffix in [".png", ".pdf", ".eps"]]))
html.append("</tr>")
html.append("</table>")
html.append("</CENTER>")
html.append("</BODY>")

with open("index.html", "w") as f :
    for line in html :
        f.write(line)
        
