import streamlit as st
import pandas as pd
import re
from datetime import datetime
import numpy as np
import pytz

def convert_to_snake_case(text):
    # Remove any special characters except alphanumeric and spaces
    text = re.sub(r'[^\w\s]', '', text)
    # Replace spaces with underscores and convert to lowercase
    return re.sub(r'\s+', '_', text.strip().lower())

# Set up the Streamlit page
st.title('Excel Header Formatter')
st.write('Upload one or more Excel files to convert headers to snake case format')

# File uploader for multiple files
uploaded_files = st.file_uploader('Choose Excel files', type=['xlsx', 'xls'], accept_multiple_files=True)

# Add timezone selector
timezone_options = pytz.all_timezones
default_tz_index = timezone_options.index('Asia/Singapore')  # UTC+8
selected_timezone = st.selectbox(
    'Select source data timezone',
    options=timezone_options,
    index=default_tz_index,
    help='Choose the timezone that matches your source data'
)

# Add checkbox for snake case conversion
convert_to_snake = st.checkbox('Convert headers to snake case', value=True)
consolidate_files = st.checkbox('Consolidate all files into one (requires identical headers)', value=True)

# Update format_timestamp_columns function
def format_timestamp_columns(df, source_timezone):
    timestamp_pattern = r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}$'
    
    for column in df.columns:
        if df[column].dtype == 'object':
            # Replace empty strings, dashes, and whitespace-only strings with NaN
            df[column] = df[column].replace([r'^\s*$', r'^-+$', r''], np.nan, regex=True)
            
            sample_values = df[column].dropna().head()
            if any(isinstance(val, str) and (re.match(timestamp_pattern, val.strip()) or '+0000' in val) for val in sample_values):
                try:
                    # If timestamps already have timezone info, parse them directly
                    if any('+0000' in str(val) for val in sample_values if pd.notnull(val)):
                        df[column] = pd.to_datetime(df[column], format='%Y-%m-%d %H:%M:%S%z', errors='coerce')
                    else:
                        # Convert to datetime with source timezone
                        df[column] = pd.to_datetime(df[column], errors='coerce')
                        df[column] = df[column].apply(lambda x: x.tz_localize(source_timezone) if pd.notnull(x) else None)
                        # Convert to UTC
                        df[column] = df[column].apply(lambda x: x.tz_convert('UTC') if pd.notnull(x) else None)
                    
                    # Format as ISO 8601 without 'Z' suffix
                    df[column] = df[column].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S%z') if pd.notnull(x) else None)
                except Exception as e:
                    st.warning(f"Could not convert column '{column}' to timestamp format: {str(e)}")
    return df

# Update process_excel_file function
def process_excel_file(uploaded_file, convert_headers=True, timezone=None):
    df = pd.read_excel(uploaded_file)
    
    if convert_headers:
        df.columns = [convert_to_snake_case(col) for col in df.columns]
    
    df = format_timestamp_columns(df, timezone)
    
    return df

# File uploader for multiple files
uploaded_files = st.file_uploader('Choose Excel files', type=['xlsx', 'xls'], accept_multiple_files=True)

# Add checkbox for snake case conversion
convert_to_snake = st.checkbox('Convert headers to snake case', value=True)
consolidate_files = st.checkbox('Consolidate all files into one (requires identical headers)', value=True)

# Initialize session state for processed files
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = {}

def get_table_stats(df):
    stats = {
        'row_count': len(df),
        'column_count': len(df.columns),
        'headers': list(df.columns)
    }
    return stats

def validate_consolidation(individual_stats, consolidated_df):
    total_rows = sum(stats['row_count'] for stats in individual_stats.values())
    if total_rows != len(consolidated_df):
        raise ValueError(f"Row count mismatch. Individual files total: {total_rows}, Consolidated: {len(consolidated_df)}")
    
    # Validate headers
    first_file_headers = individual_stats[list(individual_stats.keys())[0]]['headers']
    if not all(stats['headers'] == first_file_headers for stats in individual_stats.values()):
        raise ValueError("Header mismatch detected in consolidation validation")

if uploaded_files:
    try:
        if st.button('Process Files'):
            st.session_state.processed_files.clear()
            st.session_state.file_stats = {}
            headers_set = set()
            
            # Create table data
            table_data = []
            
            for uploaded_file in uploaded_files:
                st.write(f'Processing: {uploaded_file.name}')
                df = process_excel_file(
                    uploaded_file, 
                    convert_headers=convert_to_snake,
                    timezone=selected_timezone
                )
                
                stats = get_table_stats(df)
                st.session_state.file_stats[uploaded_file.name] = stats
                table_data.append({
                    'File Name': uploaded_file.name,
                    'Rows': stats['row_count'],
                    'Columns': stats['column_count']
                })

                # Validate headers if consolidation is requested
                if consolidate_files:
                    current_headers = tuple(df.columns)
                    if not headers_set:
                        headers_set.add(current_headers)
                    elif current_headers not in headers_set:
                        raise ValueError(f"Headers in {uploaded_file.name} do not match other files.")
                
                st.session_state.processed_files[uploaded_file.name] = df
            
            # Display statistics table
            st.write("File Statistics:")
            stats_df = pd.DataFrame(table_data)
            st.table(stats_df)
            
            # Handle consolidated output
            if consolidate_files and st.session_state.processed_files:
                combined_df = pd.concat(st.session_state.processed_files.values(), ignore_index=True)
                validate_consolidation(st.session_state.file_stats, combined_df)
                
                total_individual_rows = sum(stats['row_count'] for stats in st.session_state.file_stats.values())
                consolidated_stats = get_table_stats(combined_df)
                
                st.write("Consolidated File Statistics:")
                consolidated_data = pd.DataFrame([{
                    'File Name': 'CONSOLIDATED FILE',
                    'Rows': f"{consolidated_stats['row_count']} / {total_individual_rows}",
                    'Columns': consolidated_stats['column_count']
                }])
                st.table(consolidated_data)
                
                if consolidated_stats['row_count'] == total_individual_rows:
                    st.success("✅ Row count validation successful")
                else:
                    st.error("❌ Row count validation failed")

                st.write('Consolidated Data Preview:')
                st.dataframe(combined_df.head())
                
                # Offer consolidated download
                csv = combined_df.to_csv(index=False)
                st.download_button(
                    label='Download Consolidated CSV',
                    data=csv,
                    file_name='consolidated_output.csv',
                    mime='text/csv',
                    key='download_consolidated'
                )
                st.divider()
            
            # Display individual files
            if not consolidate_files:
                for filename, df in st.session_state.processed_files.items():
                    st.write(f'Processed Data Preview for {filename}:')
                    st.dataframe(df.head())
                    
                    csv = df.to_csv(index=False)
                    output_filename = filename.rsplit('.', 1)[0] + '.csv'
                    st.download_button(
                        label=f'Download {output_filename}',
                        data=csv,
                        file_name=output_filename,
                        mime='text/csv',
                        key=f'download_{filename}'
                    )
                    st.divider()
                
    except ValueError as ve:
        st.error(str(ve))
    except Exception as e:
        st.error(f'Error processing files: {str(e)}')