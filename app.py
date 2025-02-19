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

def replace_empty_fields(df):
    df = df.replace(r'^\s*$', "NULL", regex=True)
    df = df.fillna("NULL")
    return df

def format_timestamp_columns(df, source_timezone):
    timestamp_columns = [
        'estimated_ship_out_date', 'ship_time', 'order_creation_date',
        'order_paid_time', 'order_complete_time'
    ]
    
    for column in df.columns:
        if column in timestamp_columns:
            try:
                df[column] = pd.to_datetime(df[column], errors='coerce')
                df[column] = df[column].dt.strftime('%Y-%m-%d %H:%M:%S%z')
            except Exception as e:
                st.warning(f"Could not convert column '{column}' to timestamp format: {str(e)}")
    
    return df

def process_excel_file(uploaded_file, convert_headers=True, timezone=None):
    df = pd.read_excel(uploaded_file)
    
    if convert_headers:
        df.columns = [convert_to_snake_case(col) for col in df.columns]
    
    df = format_timestamp_columns(df, timezone)
    df = replace_empty_fields(df)
    
    return df

def get_table_stats(df):
    return {
        'row_count': len(df),
        'column_count': len(df.columns),
        'headers': list(df.columns)
    }

def validate_consolidation(individual_stats, consolidated_df):
    total_rows = sum(stats['row_count'] for stats in individual_stats.values())
    if total_rows != len(consolidated_df):
        raise ValueError(f"Row count mismatch. Individual files total: {total_rows}, Consolidated: {len(consolidated_df)}")
    
    first_file_headers = individual_stats[list(individual_stats.keys())[0]]['headers']
    if not all(stats['headers'] == first_file_headers for stats in individual_stats.values()):
        raise ValueError("Header mismatch detected in consolidation validation")

# Set up the Streamlit page
st.title('Excel Header Formatter')
st.write('Upload one or more Excel files to convert headers to snake case format')

uploaded_files = st.file_uploader(
    'Choose Excel files', 
    type=['xlsx', 'xls'], 
    accept_multiple_files=True,
    key='excel_files'
)

timezone_options = pytz.all_timezones
default_tz_index = timezone_options.index('Asia/Singapore')
selected_timezone = st.selectbox(
    'Select source data timezone',
    options=timezone_options,
    index=default_tz_index,
    help='Choose the timezone that matches your source data'
)

convert_to_snake = st.checkbox('Convert headers to snake case', value=True)
consolidate_files = st.checkbox('Consolidate all files into one (requires identical headers)', value=True)

if 'processed_files' not in st.session_state:
    st.session_state.processed_files = {}

if uploaded_files:
    try:
        if st.button('Process Files'):
            st.session_state.processed_files.clear()
            st.session_state.file_stats = {}
            headers_set = set()
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

                if consolidate_files:
                    current_headers = tuple(df.columns)
                    if not headers_set:
                        headers_set.add(current_headers)
                    elif current_headers not in headers_set:
                        raise ValueError(f"Headers in {uploaded_file.name} do not match other files.")
                
                st.session_state.processed_files[uploaded_file.name] = df
            
            st.write("File Statistics:")
            stats_df = pd.DataFrame(table_data)
            st.table(stats_df)
            
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
                
                csv = combined_df.to_csv(index=False)
                st.download_button(
                    label='Download Consolidated CSV',
                    data=csv,
                    file_name='consolidated_output.csv',
                    mime='text/csv',
                    key='download_consolidated'
                )
                st.divider()
            
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