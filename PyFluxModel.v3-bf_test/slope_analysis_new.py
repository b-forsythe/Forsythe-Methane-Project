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
import re

def analyze_slope(master_data, lgr_data,row,sample_ID,output_folder,r_values,gas_to_read,t_p_data):
	'''program that analyzes the slope and performs fitting'''
	#get the start and stop times from the file
	start_time = master_data.at[row, "start_time_(hh:mm:ss)"]
	stop_time = master_data.at[row, "stop_time_(hh:mm:ss)"]
	
	# Data Processing (OLD VERSION): Will pull from the June 11 2019 p_mean values.
	#lgr_datap = pd.read_csv(r'C:\Users\Simon\Documents\methane\June2019_T_P.csv', delimiter=',', parse_dates=[['date','time']])
	#P_Pa = lgr_datap.loc[lgr_datap['date_time'] == '6/11/2019 0:00','air_p_mean_Pa'].values
	
	# F File fixing:
	# Depending on the type of device used, the f files are either tab separated, or comma space separated.
	# this changes the entire spacing of the rest of the f file which needs to be correct in order to run
	# for instance, the typical bucket is right adjusted 20 spaces
	# while the Micro is right adjusted 15 spaces.
	ts = ""
	ts          = lgr_data.between_time(start_time = "{}".format(start_time), end_time = "{}".format(stop_time))[('[' + gas_to_read + ']d_ppm').rjust(15)]
	temperature = lgr_data.between_time(start_time = "{}".format(start_time), end_time = "{}".format(stop_time))['         GasT_C']


	#Plot the raw LGR data for the measurement window
	#change to check if ts is empty
	try:
		ts = xr.DataArray(ts, coords = [ts.index], dims = ['time'])
		ts.plot()
	except ImportError:
		print("the given start time for data: " + sample_ID + "is not valid. will skip for now")
		master_data.at[row, "program_run?"] = "n"
		return master_data
	new_ts = ts.dropna('time')
	if new_ts.time.size == 0:
		print("the gives start time for data: " + sample_ID + "is not valid. will skip for now")
		return master_data
	temperature_mean = xr.DataArray(temperature, coords = [temperature.index], dims = ['time']).mean().data
	temperature_error = temperature.std() + 1
	type(temperature_mean)

	# Set Data Quality Thresholds:
	# in searching for an r^2 value of the given threshold (0.99 - 0.9), if the original slope is under, smoothing will begin
	# currently there exists functions to attempt a smoothing window of 0, 5, 10, and 15, but more can be added later if necessary.
	min_section_length_original = 45
	max_section_length = 210
	smoothing_window = 0

	####################### Begin Smoothing Section ###################
	section_length   = np.arange(min_section_length_original,max_section_length+1)[::-1]
	for r_2_value in r_values:
		max_r_2 = []
		print(f"Running for {start_time}")
		print("running with r^2 of: " + str(r_2_value))
		valid_section_length, slope, a, R_squared, max_r_squared = brain(section_length, ts,r_2_value )
		max_r_2.append(max_r_squared)
		if slope:
			print('valid section length = %.3f' %valid_section_length)
			print('Smoothing_window = %.3f' %smoothing_window)
			break
		# Attempt smoothing window of 5
		else:
			print("running with smoothing window of 5")
			smoothing_window  = 5
			min_section_length = min_section_length_original*2
			section_length   = np.arange(min_section_length,max_section_length+1)[::-1]
			ts_smooth = ts.rolling(time = smoothing_window, center = True).mean().dropna(dim='time')
			valid_section_length, slope, a, R_squared, max_r_sqaured = brain(section_length, ts,r_2_value)
			max_r_2.append(max_r_squared)
			if slope:
				print('valid section length = %.3f' %valid_section_length)
				print('Smoothing_window = %.3f' %smoothing_window)
				break
			# Attempt smoothing window of 10
			else:
				print("running with smoothing window of 10")
				smoothing_window  = 10
				min_section_length = int(min_section_length_original*2)
				section_length   = np.arange(min_section_length,max_section_length+1)[::-1]
				ts_smooth = ts.rolling(time = smoothing_window, center = True).mean().dropna(dim='time')
				valid_section_length, slope, a, R_squared, max_r_squared = brain(section_length, ts,r_2_value )
				max_r_2.append(max_r_squared)
				if slope:
					print('valid section length = %.3f' %valid_section_length)
					print('Smoothing_window = %.3f' %smoothing_window)     
					break
				# Attempt smoothing window of 15
				else:
					smoothing_window  = 15
					min_section_length = min_section_length_original*3
					section_length   = np.arange(min_section_length,max_section_length+1)[::-1]
					ts_smooth = ts.rolling(time = smoothing_window, center = True).mean().dropna(dim='time')
					valid_section_length, slope, a, R_squared, max_r_squared = brain(section_length, ts,r_2_value )
					max_r_2.append(max_r_squared)
					if slope:
						print('valid section length = %.3f' %valid_section_length)
						print('Smoothing_window = %.3f' %smoothing_window)
						break
					elif r_2_value == min(r_values):
						print('Didn\'t work with lowest R_2 threshold value! Baaad data!!! will still print R^2 value to excel')
						master_data.at[row, "program_run?"] = "y"
						master_data.at[row, "Use Data? (See Notes)"] = "rejected"
						master_data.at[row, "R_value_used"] = max(max_r_2)
						return master_data
					
	# Debug text for accepted R^2 value
	print('valid section length = %d' %valid_section_length)
	print('Smoothing_window = %d' %smoothing_window)
	print('Slope = %.5f ppm/s' %slope)
	print('R^2 = %.4f ' %R_squared[0].data)
	print('R^2 = %.4f ' %R_squared[0].data)
	print('Temperature = %.3f deg. C' %temperature_mean)
	print('Section start timestamp = ' +str(a[0].time.data))

	########### End Smoothing Window ############

	#Convert the section start time from datetime stamp to actual index of the original section window.
	index = np.where(ts.time ==a[0].time)[0][0]
	slope, slope_error, ts_section, y, y_hat = get_slope_error(ts[index: index+valid_section_length], plot = True)
	#Calculate Flux and its +/- uncertainty (micromoles m^-2 s^-1)
	#Gas Constant L atm mol^-1 K^-1
	#pressure in atmospheres (atm)
	# Pull Value of Volume from excel spreadsheet
	V = master_data.at[row, "V"]
	# Pull Value of Volume Error from excel spreadsheet
	V_error = master_data.at[row, "V_error"]
	# Pull Value of area from excel spreadsheet
	area = master_data.at[row, "area"]
	# Pull value of Pressure (in pascal) from spreadsheet
	P_Pa = master_data.at[row, "P_Pa"]
	P = 9.86923e-6 * P_Pa
	P_error = P * 0.01
	R = 0.082057338
	# Begin R^2 Calculations
	moles = (P*V)/(R*(temperature_mean+273.15))
	moles_RE = sqrt((P_error/P)**2 + (V_error/V)**2 + (temperature_error/(temperature_mean+273.15))**2)
	moles_error = moles_RE * moles
	flux = slope*moles/area
	#Relative Error
	flux_RE = sqrt((slope_error/abs(slope))**2 + (moles_error/moles)**2)
	print('Flux = %.3f ' %flux + '± %.3f ' %flux_RE)
	print('Units = micromol CH4 m^-2 s^-1')
	flux_error = flux_RE * flux

	print('Moles RE =>  ', moles_RE)
	print('Flux RE =>   ', flux_RE)

	# If slope is found, regardless of smoothing size, create and save a figure of accepted slope to 'outputs' file
	figure, ax = plt.subplots(figsize = (10,8))
	ax.plot(ts_section.time, y)
	ax.plot(ts_section.time, y_hat)
	plt.ylabel('PPM ' + gas_to_read + '_$', fontsize = 12)
	plt.xlabel('Time',fontsize = 12)
	legend = plt.legend(('Raw Data', 'Linear Fit'), title = sample_ID, loc='upper left', fontsize = 12, shadow=True)
	plt.setp(legend.get_title(),fontsize='large', fontweight = 'bold')
	plt.text(0.02,0.7, 'Flux = %.3f ± %.3f \nmicromol $CH_4$ $m^{-2}$ $s^{-1}$ \nR$^2$ = %.3f' %(flux, flux_error,R_squared[0].data), fontsize = 13, transform=ax.transAxes)
	filename = f"{output_folder}/{sample_ID}_{r_2_value:0.2f}.jpg"
	plt.savefig(filename, dpi=60)

    # Create the reference graph with only the raw data and start/stop times
	figure, ax = plt.subplots(figsize=(10, 8))
	ax.plot(ts_section.time, y, label='Raw Data')
	plt.ylabel('PPM ' + gas_to_read + '_$', fontsize=12)
	plt.xlabel('Time', fontsize=12)
	legend = plt.legend(loc='upper left', fontsize=12, shadow=True)
	plt.setp(legend.get_title(), fontsize='large', fontweight='bold')
	plt.title(f'Reference Graph for {sample_ID}')

	ref_filename = f"{output_folder}/{sample_ID}_reference.jpg"
	plt.savefig(ref_filename, dpi=60)


	# Rewrite all data back INTO excel spreadsheet
	output_data_headers = ["sample_ID", "Temperature","Pressure","area", "volume", "valid_section_length","smoothing_window","slope", "slope error",
	"R^2","time","flux","flux error"]
	output_data = [sample_ID.replace("꞉",":"),temperature_mean,P_Pa,area,V,valid_section_length,smoothing_window,slope,slope_error,
				   R_squared[0].data,str(a[0].time.data),flux,flux_error]	
	#updating the master spreadsheet
	#update the sample ID
	master_data.at[row, "Sample ID"] = sample_ID
	#the pressure used in the measurements, measured in pascals
	master_data.at[row, "air_Pa"] = P
	
	#the flux found- need to know which gas we are measuring
	if gas_to_read == "CH4" or gas_to_read == "CO2":
		print("INSIDE LOOP")
		# Check if the R² value is higher or if the cell is empty (NaN)
		if pd.isna(master_data.at[row, "flux"]) or master_data.at[row, "R_value_used"] < R_squared[0]:
			print("INSIDE IF STATEMENT")
			master_data.at[row, "R_value_used"] = R_squared[0]
			master_data.at[row, "flux"] = flux
			master_data.at[row, "flux_error"] = flux_error
			master_data.at[row, "slope"] = slope
			master_data.at[row, "slope_error"] = slope_error
	else:
		print(gas_to_read + " not able to be run")
		return master_data
	master_data.at[row, "program_run?"] = "y"

	#test looping mechanism
	print("Running Loop Mechanism =======> \n")
	master_data.at[row, f"R_threshold_{r_2_value}"] = r_2_value
	master_data.at[row, f"flux_{r_2_value}"] = flux
	master_data.at[row, f"flux_error_{r_2_value}"] = flux_error
	master_data.at[row, f"R_value_used_{r_2_value}"] = max(max_r_2)
	master_data.at[row, f"Section_length_{r_2_value}"] = valid_section_length
	master_data.at[row, f"slope_{r_2_value}"] = slope
	master_data.at[row, f"slope_error_{r_2_value}"] = slope_error


	print("SLOPE = > ", slope)
	print("SLOPE ERROR = > ", slope_error)

	print(" ===================")


	print("SECTION LENGTH !!!! ", valid_section_length)

	print(f"Ended Loop mechanism with threshold = {r_2_value}   |   flux result = {flux}   |   uncertainty = {flux_error}   |   r_value_used = {max(max_r_2)}  \n\n\n")

	with open(os.path.join(output_folder,(sample_ID + ".txt")),'w') as f: 	
		np.savetxt(f,output_data_headers,fmt = "%s,",newline=' ')
		f.write('\n')
		np.savetxt(f, output_data, fmt = "%s,",delimiter=',', newline=' ')
		
	#edit the master data sheet with the data from the spreadsheet 
	return master_data


def compute_r2(ts_section, plot = False):
     x     = np.arange(len(ts_section))
     #removes time metadata for simplicity
     y     = np.array(ts_section)
     model = np.polyfit(x,y,1)
     slope = model[0]
     intercept = model[1]
     y_hat = slope*x + intercept # OR np.polyval(model, x)
     correlation_coefficient = np.corrcoef(y,y_hat)[0,1]
     r_square = (correlation_coefficient)**2
     if plot:
         plt.plot(y)
         plt.plot(y_hat)

     return r_square, slope



def brain(section_lengths, ts, r_2_threshold):
    print("the length of the time series:")
    max_r_2_values = []
    valid_length = 0  # Initialize valid_length with a default value
    result = None  # Initialize result with a default value
    a = []  # Initialize 'a' as an empty list to prevent UnboundLocalError
    R_squared = []  # Initialize 'R_squared' as an empty list to prevent UnboundLocalError
    output_r_squared = []  # Initialize 'output_r_squared' as an empty list to prevent UnboundLocalError
    for section_length in section_lengths:
        # print(section_length)
        r_2 = []
        slope = []
        start = []
        # end   = []
        # section_length = 210
        for i in range(len(ts)-section_length):
            ts_section = ts[i:i + section_length]
            tmp_start  = ts_section.time[0]
            tmp_end    = ts_section.time[-1]
            tmp_r2, tmp_slope = compute_r2(ts_section, plot=False)
            r_2.append(tmp_r2)
            slope.append(tmp_slope)
            start.append(tmp_start)
            # end.append(tmp_end)
        r_2 = xr.DataArray(r_2, coords = [ts[:-int(section_length)].time], dims = ['time'])
        slope = xr.DataArray(slope, coords = [ts[:-int(section_length)].time], dims = ['time'])

        # c = end.where(r_2>=r_2_threshold, drop=True)
        #
        #all of the data windows that fit the r_2 threshhold
        a = list(slope.where(r_2>=r_2_threshold, drop=True))
		#all the R_squared values that worked
        R_squared = list(r_2.where(r_2>=r_2_threshold, drop=True))
		#the maximum r_squared value
		#doesn't work if the array size is 0
        if (len(ts)-section_length) <= 0:
            max_r_sqaured = 0
        else:
            max_r_squared_index = r_2.argmax()
            max_r_squared = r_2[max_r_squared_index]
            max_r_2_values.append(max_r_squared)
        result = []
        valid_length = []
        if a:
            print("breaking out")
            # print(a)
            result = a[0].data
            valid_length = section_length
            # print('starting time stamp' + a[0].time)
            break
		#check to see if there are any r^2 values
    if not max_r_2_values:
        output_r_squared = 0
    else:
        output_r_squared = max(max_r_2_values)
		
    return valid_length, result, a, R_squared, output_r_squared

def get_slope_error(ts_section, plot = True):
     x     = np.arange(len(ts_section))
     #removes time metadata for simplicity
     y     = np.array(ts_section)
     model, M = np.polyfit(x,y,1, cov = True)
     slope = model[0]
     slope_error = np.sqrt(M[0][0])
     intercept = model[1]
     y_hat = slope*x + intercept # OR np.polyval(model, x)

     if plot:
            print('Slope error = %.6f ppm/s' %slope_error)

     return slope, slope_error, ts_section, y, y_hat