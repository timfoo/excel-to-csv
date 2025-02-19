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
    for column in df.columns:
        # Check if column contains datetime-like values
        if df[column].dtype == 'datetime64[ns]' or (
            df[column].dtype == 'object' and 
            df[column].notna().any() and 
            isinstance(df[column].iloc[df[column].first_valid_index()], (str, datetime))
        ):
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
st.write('Upload an Excel file to convert headers to snake case format')

# File uploader
uploaded_file = st.file_uploader('Choose an Excel file', type=['xlsx', 'xls'])

# Add checkbox for snake case conversion
convert_to_snake = st.checkbox('Convert headers to snake case', value=True)

if uploaded_file is not None:
    try:
        # Add button to trigger conversion
        if st.button('Process File'):
            # Process the file
            df = process_excel_file(uploaded_file, convert_headers=convert_to_snake)
            
            # Display the processed dataframe
            st.write('Processed Data Preview:')
            st.dataframe(df.head())
            
            # Convert to CSV and offer download
            csv = df.to_csv(index=False)
            original_filename = uploaded_file.name
            output_filename = original_filename.rsplit('.', 1)[0] + '.csv'
            st.download_button(
                label='Download CSV',
                data=csv,
                file_name=output_filename,
                mime='text/csv'
            )
            
    except Exception as e:
        st.error(f'Error processing file: {str(e)}')