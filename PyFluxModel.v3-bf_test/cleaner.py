import pandas as pd

# Specify the file path
lgr_file_path = r'C:\Users\busin\Desktop\MethaneProject\PyFluxModel.v3-bf_test\inputs\lgr\micro_2023-08-23_f0000.txt'

# Load the LGR data
lgr_data = pd.read_csv(lgr_file_path, delimiter=',', header=0)

# Display the columns to understand the structure
print("Columns in the DataFrame:")
print(lgr_data.columns)

# # If the correct column is not 'SysTime', replace 'SysTime' with the correct column name
# time_column = 'SysTime'  # Replace with the actual column name if different

# # Function to clean and convert the index to datetime
# def clean_and_convert_to_datetime(index):
#     # Attempt to convert the index to datetime, coercing errors to NaT
#     cleaned_index = pd.to_datetime(index, errors='coerce')
    
#     # Find any NaT values (which were originally invalid strings)
#     invalid_dates = cleaned_index.isna()
#     if invalid_dates.any():
#         print("Found invalid date values in index. They will be dropped:")
#         print(index[invalid_dates])
        
#     # Drop invalid dates
#     cleaned_index = cleaned_index.dropna()
    
#     return cleaned_index

# # Clean the index of lgr_data and convert to datetime
# lgr_data.index = clean_and_convert_to_datetime(lgr_data[time_column])

# # Remove the original time column as it's now the index
# lgr_data.drop(columns=[time_column], inplace=True)

# # Ensure the index conversion didn't result in any dropped data
# if lgr_data.index.isna().any():
#     print("There are still NaT values in the index after cleaning. Check your data.")
# else:
#     print("Index successfully converted to DatetimeIndex.")
    
# # Display the cleaned data
# print(lgr_data.head())
