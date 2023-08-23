import os
from datetime import datetime

import matplotlib.dates as md
import matplotlib.pyplot as plt
import pandas as pd
from astropy.time import Time
from matplotlib import rcParams

# set default font characteristics
rcParams['font.size'] = 9

# set default lines
rcParams['lines.linewidth'] = 1.0
rcParams['axes.linewidth'] = 0.8

# change x-axis characteristics
rcParams['xtick.top'] = True
rcParams['xtick.direction'] = 'in'
rcParams['xtick.minor.visible'] = True
rcParams['xtick.major.size'] = 4
rcParams['xtick.minor.size'] = 3
rcParams['xtick.major.width'] = 0.75
rcParams['xtick.minor.width'] = 0.25
rcParams['xtick.major.pad'] = 4
rcParams['xtick.minor.pad'] = 4

# change y-axis characteristics
rcParams['ytick.right'] = True
rcParams['ytick.direction'] = 'in'
rcParams['ytick.minor.visible'] = True
rcParams['ytick.major.size'] = 4
rcParams['ytick.minor.size'] = 3
rcParams['ytick.major.width'] = 0.75
rcParams['ytick.minor.width'] = 0.25
rcParams['ytick.major.pad'] = 4
rcParams['ytick.minor.pad'] = 4

# set default legend characteristics
rcParams['legend.fontsize'] = 7
rcParams['legend.labelspacing'] = 0.2
rcParams['legend.loc'] = 'best'
rcParams['legend.frameon'] = False

# set figure size/resolution
rcParams['figure.figsize'] = (4, 3)
rcParams['figure.dpi'] = 200

# set figure saving size/resolution
rcParams['savefig.bbox'] = 'tight'

cols = ["###MJD", "uJy", "duJy", "duJyu", "duJyl", "duJym", "median", "phase_folded", "F",
        "RA", "Dec", "x", "dx", "y", "dy", "maj", "min", "phi"]


# Functions to convert MJD to matplotlib dates and back for plotting
def mjd2dt(mjd):
    '''MJD to matplotlib datetime'''
    x = Time(mjd, format='mjd')
    x = x.to_value('datetime64', 'date')
    ys = pd.to_datetime(x)
    return [datetime(y.year, y.month, y.day) for y in ys]


def dt2mjd(dt):
    '''Matplotlib datetime to MJD'''
    dt = md.num2date(dt)
    x = Time(dt, format='datetime')
    x = x.to_value('mjd', 'float')
    return x


def plot_func(in_dir, file, out_dir):
    data = pd.read_csv(in_dir + "/" + file, delim_whitespace=True)
    c = data[data['F'] == 'c'].reset_index(drop=True)
    o = data[data['F'] == 'o'].reset_index(drop=True)

    plt.figure(figsize=(8, 4))
    markers, caps, bars = plt.errorbar(c["###MJD"], c["median"], yerr=(c["duJyl"], c["duJyu"]),
                                       color='darkturquoise', fmt='.', ms=3, label='cyan')
    [bar.set_alpha(0.3) for bar in bars]
    markers, caps, bars = plt.errorbar(o["###MJD"], o["median"], yerr=(o["duJyl"], o["duJyu"]),
                                       color='orange', fmt='.', ms=3, label='orange')
    [bar.set_alpha(0.3) for bar in bars]

    plt.axvline(x=58417, color='k', alpha=0.25)
    plt.axvline(x=58882, color='k', alpha=0.25)
    plt.xlabel(cols[0])
    plt.ylabel(r"$\mu$Jy")
    # plt.xlim([57100,59700])
    plt.legend(loc='best', frameon=True)

    axis = plt.gca()
    axis.tick_params(axis='x', which='both', top=False)
    sec_ax = axis.secondary_xaxis('top', functions=(mjd2dt, dt2mjd))
    sec_ax.set_xlabel('Year')
    sec_ax.xaxis.set_major_formatter(md.DateFormatter('%Y'))

    plt.tight_layout()
    plt.savefig(out_dir + "/" + file[:-3] + ".png", facecolor='white', transparent=False)
    plt.clf()
    plt.close()


def read_dir(source, out_dir):
    """Read and plot lightcurves depending on whether
        source is a .lc file or a directory
        containing .lc files
    """
    # Make output dir if not exisitng
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # Check if output dir is a dir
    if not os.path.isdir(out_dir):
        print("Output path is not a directory.")

    else:
        # Source is a dir
        if os.path.isdir(source):
            for f in os.listdir(source):
                if f[-3:] == '.lc':
                    print("Working on file: " + f + ' ' * 35, end='\r')
                    plot_func(source, f, out_dir)

        # Source is a valid file
        elif source[-3:] == '.lc':
            plot_func(source[:-18], source[-18:], out_dir)

        # Source is not valid
        else:
            print("No `.lc` file found.")


read_dir("test_data/corrected_lcs/out/", "test_data/corrected_lcs/out/plots/")
