import streamlit as st
import pandas as pd
import re
from datetime import datetime
import numpy as np

def convert_to_snake_case(text):
    # Remove any special characters except alphanumeric and spaces
    text = re.sub(r'[^\w\s]', '', text)
    # Replace spaces with underscores and convert to lowercase
    return re.sub(r'\s+', '_', text.strip().lower())

def format_timestamp_columns(df):
    timestamp_pattern = r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}$'
    
    for column in df.columns:
        if df[column].dtype == 'object':  # Only check string columns
            # Replace dash-only values with NaN
            df[column] = df[column].replace('^-+$', np.nan, regex=True)
            
            sample_values = df[column].dropna().head()
            if any(isinstance(val, str) and re.match(timestamp_pattern, val.strip()) for val in sample_values):
                try:
                    # Convert to datetime and handle timezone
                    df[column] = pd.to_datetime(df[column], utc=True)
                    # Format as ISO 8601 string compatible with timestamptz
                    df[column] = df[column].dt.strftime('%Y-%m-%d %H:%M:%S%z')
                except Exception as e:
                    st.warning(f"Could not convert column '{column}' to timestamp format: {str(e)}")
    return df

def process_excel_file(uploaded_file, convert_headers=True):
    # Read the Excel file
    df = pd.read_excel(uploaded_file)
    
    # Convert headers to snake case if option is selected
    if convert_headers:
        df.columns = [convert_to_snake_case(col) for col in df.columns]
    
    # Format timestamp columns
    df = format_timestamp_columns(df)
    
    return df

# Set up the Streamlit page
st.title('Excel Header Formatter')
st.write('Upload one or more Excel files to convert headers to snake case format')

# File uploader for multiple files
uploaded_files = st.file_uploader('Choose Excel files', type=['xlsx', 'xls'], accept_multiple_files=True)

# Add checkbox for snake case conversion
convert_to_snake = st.checkbox('Convert headers to snake case', value=True)

if uploaded_files:
    try:
        # Add button to trigger conversion
        if st.button('Process Files'):
            for uploaded_file in uploaded_files:
                st.write(f'Processing: {uploaded_file.name}')
                
                # Process the file
                df = process_excel_file(uploaded_file, convert_headers=convert_to_snake)
                
                # Display the processed dataframe
                st.write('Processed Data Preview:')
                st.dataframe(df.head())
                
                # Convert to CSV and offer download
                csv = df.to_csv(index=False)
                output_filename = uploaded_file.name.rsplit('.', 1)[0] + '.csv'
                st.download_button(
                    label=f'Download {output_filename}',
                    data=csv,
                    file_name=output_filename,
                    mime='text/csv'
                )
                st.divider()
                
    except Exception as e:
        st.error(f'Error processing files: {str(e)}')