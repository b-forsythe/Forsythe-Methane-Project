#!/usr/bin/env python
# coding: utf-8

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import os
from pathlib import Path
from math import *
import datetime
from slope_analysis import *
#########!!!INPUT!!!########!!!INPUT!!!####!!!INPUT!!!##################
#########!!!INPUT!!!########!!!INPUT!!!####!!!INPUT!!!##################
# Sample ID

# Edited by Nick Hasson and Simon Peterson for Hasson et al. ERL
# 08/20/2020

# TODO- make sample ID print to command line, automatically create the ID tag
# String names of the valid measurement devices:
measurement_devices = ["bucket_sediment", "bucket_snow", "chamber"]
# Greenhouse gases that can be measured:
gases = ["CH4", "CO2"]
# Current working directory
cwd = os.getcwd()
output_folder = os.path.join(cwd, "outputs")
lgr_input_folder = os.path.join(cwd, "inputs", "lgr")
weather_input_folder = os.path.join(cwd, "inputs", "weather_data")
print("Pulling LGR data from: \n" + lgr_input_folder)
print("Pulling weather data, when not from internet, from: \n" + weather_input_folder + "\n")

# Read the Excel file for the input. Close the file before reading it.
master_csv_path = os.path.join(cwd, "data", "simon_masters.xlsx")
master_data = pd.read_excel(master_csv_path, engine='openpyxl', header=0)  # Headers are the first row
# Apparently Excel formats their data with the dates also including a timestamp. Annoying
try:
    master_data["date_(yyyy-mm-dd)"] = master_data["date_(yyyy-mm-dd)"].apply(lambda x: x.date().isoformat())
except AttributeError:
    print("Read date as string")
    # Assume it is a string

# Temperature and pressure data
weather_input_filepath = os.path.join(weather_input_folder, 'June2019_T_P.csv')
t_p_data = pd.read_csv(weather_input_filepath, delimiter=',', parse_dates=[['date', 'time']])
t_p_data['date_time'] = pd.to_datetime(t_p_data['date_time'])
print("Using as master spreadsheet:\n" + master_csv_path)


# Read the data from the LGR files. Clean any "dirty" files.
# TODO- make so that junk at the end of the files is cleaned up
# Original header is 1 and index column is 0
first = True
for file in os.listdir(lgr_input_folder):
    if file.endswith(".txt"):
        with open(os.path.join(lgr_input_folder, file), 'r') as f:
            print("Reading file: " + file)
            file_text = f.read()
            if "BEGIN PGP MESSAGE" in file_text:
                print("Found text \"BEGIN PGP MESSAGE\", will clean file")
                f.close()
                with open(os.path.join(lgr_input_folder, file), 'r') as f:
                    lines = f.readlines()
                    f_new = open(os.path.join(lgr_input_folder, file.strip(".txt")) + "_cleaned.txt", 'w+')
                    for line in lines:
                        if "-----BEGIN PGP MESSAGE-----" not in line:
                            f_new.write(line)
                        else:
                            break
                    print("Successfully cleaned " + file)
                    f.close()
                    os.remove(os.path.join(lgr_input_folder, file))
                    file = file.strip(".txt") + "_cleaned.txt"
                    print("Removed old file, created " + file)
                    f_new.close()
        if first:
            lgr_data = pd.read_csv(os.path.join(lgr_input_folder, file), delimiter=',', header=1, index_col=0)
            first = False
        else:
            print("Appending data")
            print(file)
            new_data = pd.read_csv(os.path.join(lgr_input_folder, file), delimiter=',', header=1, index_col=0)
            lgr_data = lgr_data.append(new_data)
        print("Size of total LGR data array: " + str(lgr_data.shape))

# TODO- print the total LGR data into a nice CSV :)
# Make the LGR date index with date and time
lgr_data.index = pd.DatetimeIndex(lgr_data.index)


# Now we will create a new array with the times that we would like to add to the list
# Make a for loop to run through the data which has not already been run by the program
torun_rows = []
for row in range(master_data.shape[0]):
    if master_data.iloc[row]['program_run?'] != 'y':
        torun_rows.append(row)
print("The rows that will be run, starting at index 0:")
print(torun_rows)
print("Will run the program for a total of " + str(len(torun_rows)) + " times")

# Dictionary with the rows as keys and the sample IDs as values
row_ID = {}
row_gases = {}
for row in torun_rows:
    # Create the sample ID. The format is:
    # yyyy-mm-dd_hh:mm:ss_location_collection-instrument
    # where the hh:mm:ss is the START TIME
   
    sample_ID = ""
    if master_data.iloc[row]["date_(yyyy-mm-dd)"] != np.nan:
        sample_ID = str(master_data.iloc[row]["date_(yyyy-mm-dd)"]).replace('-', '_')
    else:
        print("Need a date for row: " + str(row))
        exit()
    if isinstance(master_data.iloc[row]["start_time_(hh:mm:ss)"], datetime.time):
        sample_ID = sample_ID + "_" + str(master_data.iloc[row]["start_time_(hh:mm:ss)"]).replace(":", "h", 1).replace(":", 'm', 1) + "s"
    else:
        sample_ID = sample_ID + "_" + str(master_data.iloc[row]["start_time_(hh:mm:ss)"]).replace(":", "h", 1).replace(":", 'm', 1) + "s"
    if not isinstance(master_data.iloc[row]["stop_time_(hh:mm:ss)"], datetime.time):
        print("Stop time is string")
        print("No stop time found for row: " + str(row))
    if master_data.iloc[row]["location_(lake)"] != np.nan:
        sample_ID = sample_ID + "_" + str(master_data.iloc[row]["location_(lake)"])
    else:
        print("No location for row: " + str(row))
        sample_ID = sample_ID + "_unentered"
    if master_data.iloc[row]["measurement_device"] not in measurement_devices:
        print("Invalid measurement_device: " + str(master_data.iloc[row]["measurement_device"]))
        print("Found in row: " + str(row))
        exit()
    else:
        sample_ID = sample_ID + "_" + str(master_data.iloc[row]["measurement_device"])
    if master_data.iloc[row]["gas"] not in gases:
        print("Invalid gas: " + str(master_data.iloc[row]["gas"]))
        print("Found in row: " + str(row))
        exit()
    else:
        sample_ID = sample_ID + "_" + str(master_data.iloc[row]["gas"])
        row_gases.update({row: str(master_data.iloc[row]["gas"])})
    row_ID.update({row: sample_ID})

print("Will run the following sample IDs:")
for value in row_ID.values():
    print(value)

# Convert the sample ID column to be of string data type
master_data['Sample ID'] = master_data['Sample ID'].astype('object')
master_data["program_run?"] = master_data["program_run?"].astype('object')



#### Attempt 2: Behavior Unknown

# List of R² values to iterate over
r_2_values = [round(x, 2) for x in np.arange(0.99, 0.89, -0.01)]

# Loop over each R² value and perform the analysis
for r_2 in r_2_values:
    print(f"Running analysis for R_2 value: {r_2}")
    for row, sample_ID in row_ID.items():
        master_data = analyze_slope(master_data, lgr_data, row, sample_ID, output_folder, [r_2], row_gases[row], t_p_data)
# Write the new master data file
master_data.to_excel(master_csv_path.replace('.xlsx', 'new_bf.xlsx'), index=False)
exit()
