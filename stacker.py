import argparse
import os
import sys

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("f_in",
                    help="Input lightcurve: .lc file or a directory containing .lc files.")
parser.add_argument("f_out",
                    help="Output directory, created if required.")
parser.add_argument("new_moons",
                    help=".npy file containing list of new moon dates in MJD")
parser.add_argument("-s", "--stack",
                    help="Nights to stack for orange. Cyan gets stacked on moon cycle. Default:7",
                    default=7, type=int)
parser.add_argument("-e", "--error",
                    help="Error cut-off (uJy), first order. Default:45",
                    default=45, type=float)
parser.add_argument("-c", "--cyan",
                    help="Error cut-off (uJy), cyan. Default:35",
                    default=35, type=float)
parser.add_argument("-o", "--orange",
                    help="Error cut-off (uJy), orange. Default:50",
                    default=50, type=float)
args = parser.parse_args()

source = args.f_in
out_dir = args.f_out
error_lim = args.error
c_err_lim = args.cyan
o_err_lim = args.orange
stack = args.stack

cols = ["MJD", "m", "dm", r"$\mu$Jy", r"$d\mu$Jy",
        "F", "err", "chi/N", "RA", "Dec",
        "x", "y", "maj", "min", r"$\phi$",
        "apfit", r"$m_{5\sigma}$", "Sky", "Obs"]

new_moon_mjd = np.load(args.new_moons)  # new moon dates


def mean_func(x, filt, ra, dec, stack, err_lim, recursion=True):
    '''Helper function for stacking. Takes in a grouped
        dataframe and returns averaged data as a series.
    '''

    result = {}
    if len(x) > 2:
        date = float(x["###MJD"].iat[0])
        if filt == 'c':
            mjd = new_moon_mjd[np.argmin(np.abs(date - new_moon_mjd))]
        elif filt == 'o':
            if stack == 1:
                mjd = int(date)
            else:
                mjd = stack * round(date / stack)
        else:
            print("mean_func: Invalid filter")
            return None

        # Take the middle date of the group
        result["###MJD"] = mjd

        # Mean and median
        result["uJy"] = x["uJy"].mean()
        result["median"] = x["uJy"].median()
        result["duJym"] = x["duJy"].mean()

        # Median error is half the difference between 1st and 3rd quantile
        median_err = 0.5 * np.diff(np.quantile(x["uJy"], [0.25, 0.75]))[0]
        if median_err < result["duJym"]:
            result["duJy"] = result["duJym"]
            result["duJyl"] = result["duJym"]
            result["duJyu"] = result["duJym"]
        else:
            result["duJy"] = median_err
            result["duJyl"] = np.diff(np.quantile(x["uJy"], [0.25, 0.5]))[0]
            result["duJyu"] = np.diff(np.quantile(x["uJy"], [0.5, 0.75]))[0]

        result["phase_folded"] = result["###MJD"] % 365  # Phase folded date is the modulus of 365
        result["F"] = filt
        result["RA"] = ra
        result["Dec"] = dec

        if result["duJy"] > err_lim:
            if recursion:
                result = mean_func(x[np.abs(x["uJy"]) < np.max(np.abs(x["uJy"]))],
                                   filt, ra, dec, stack, err_lim, recursion=False)

    return pd.Series(result,
                     index=["###MJD", "uJy", "duJy", "duJyu", "duJyl", "duJym", "median", "phase_folded", "F",
                            "RA", "Dec"],
                     dtype="object")


def stack_and_save(raw, out_dir, stack, filename):
    # Remove high errors and poor data points.
    raw = raw[(raw["duJy"] < error_lim)]

    # Split filters and reset index
    c = raw[raw['F'] == 'c'].reset_index(drop=True)
    o = raw[raw['F'] == 'o'].reset_index(drop=True)

    ra = raw["RA"].iat[0]  # RA
    dec = raw["Dec"].iat[0]  # Dec

    # Cyan gets averaged to new moon
    c1 = c.groupby(pd.to_numeric(c['###MJD']).apply(lambda x: new_moon_mjd[np.argmin(np.abs(x - new_moon_mjd))])).apply(
        mean_func,
        'c', ra, dec, stack, c_err_lim)

    # Orange gets stacked to specified day bins
    if stack == 1:
        o1 = o.groupby(pd.to_numeric(o['###MJD']).apply(lambda x: int(x))).apply(mean_func,
                                                                                 'o', ra, dec, stack, o_err_lim)
    else:
        o1 = o.groupby(pd.to_numeric(o['###MJD']).apply(lambda x: stack * round(x / stack))).apply(mean_func,
                                                                                                   'o', ra, dec, stack,
                                                                                                   o_err_lim)

    # Clip new large error points
    o1 = o1[(o1["duJy"] < (o_err_lim))]
    c1 = c1[(c1["duJy"] < (c_err_lim))]

    # Combine and save new file
    combined = pd.concat([o1, c1], ignore_index=True)
    combined.to_csv(out_dir + "/" + filename, encoding='utf-8', index=False, sep=' ')


# Make output dir if not exisitng
if not os.path.exists(out_dir):
    try:
        os.mkdir(out_dir)
    except:
        sys.exit("Output path is not a directory.")

# Check if output dir is a dir
elif not os.path.isdir(out_dir):
    sys.exit("Output path is not a directory.")

# Source is a dir
if os.path.isdir(source):
    unrd_files = []  # Corrupted file list
    fnames = os.listdir(source)
    dir_len = len(fnames)
    rd_lc = 0
    print(f"Found {dir_len} files in {source}")

    # Iterate through all files
    for count, f in enumerate(fnames):
        if f.endswith('.lc'):
            print("Opening file {} - File {}/{} - Progress: {:.2f}%".format(f,
                                                                            count, dir_len, count / dir_len * 100),
                  end='\r')
            try:
                raw = pd.read_csv(source + '/' + f, delim_whitespace=True)  # read
            except Exception as e:  # Corrupted files
                print(f"Could not read file: {f} -- {type(e).__name__}" + " " * 25)
                unrd_files.append(f)
                continue
            stack_and_save(raw, out_dir, stack, f)
            rd_lc += 1

    # Unread files
    unrd_len = len(unrd_files)
    print(f"Read {rd_lc} files out of {dir_len}." + " " * 50)
    if unrd_len > 0:
        print(f"Could not read {unrd_len} files, unread filenames saved in {out_dir}/unread.txt")
        with open(out_dir + "/unread.txt", "w") as unrd:
            unrd.write("\n".join(unrd_files))

# Source is a valid file
elif source.endswith('.lc'):
    f = source.split('/')[-1]
    try:
        raw = pd.read_csv(source, delim_whitespace=True)  # read
        stack_and_save(raw, out_dir, stack, f)
    except Exception as e:  # Corrupted files
        print(f"Could not read file: {source}")
        print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

# Source is not valid
else:
    print(f"No `.lc` file found at {source}.")
