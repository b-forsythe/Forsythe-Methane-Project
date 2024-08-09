import pandas as pd

# Path to the new file
new_file_path = r'C:\Users\busin\Desktop\MethaneProject\PyFluxModel.v3-bf_test\inputs\lgr\micro_2023-08-23_f0000.txt'

# Load the new LGR data file
new_lgr_data = pd.read_csv(new_file_path, delimiter=',', header=1)

# Function to clean and convert the index to datetime
def clean_and_convert_to_datetime(index):
    # Attempt to convert the index to datetime, coercing errors to NaT
    cleaned_index = pd.to_datetime(index, errors='coerce')
    
    # Find any NaT values (which were originally invalid strings)
    invalid_dates = cleaned_index.isna()
    if invalid_dates.any():
        print("Found invalid date values in index. They will be dropped:")
        print(index[invalid_dates])
        
    # Drop invalid dates
    cleaned_index = cleaned_index.dropna()
    
    return cleaned_index

# Clean the index of new_lgr_data and convert to datetime
new_lgr_data.index = clean_and_convert_to_datetime(new_lgr_data['Time'])

# Remove the original 'Time' column as it's now the index
new_lgr_data.drop(columns=['Time'], inplace=True)

# Ensure the index conversion didn't result in any dropped data
if new_lgr_data.index.isna().any():
    print("There are still NaT values in the index after cleaning. Check your data.")
else:
    print("Index successfully converted to DatetimeIndex.")
    
# Display the cleaned data
print(new_lgr_data.head())
