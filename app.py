import streamlit as st
import pandas as pd
import re

def convert_to_snake_case(text):
    # Remove any special characters except alphanumeric and spaces
    text = re.sub(r'[^\w\s]', '', text)
    # Replace spaces with underscores and convert to lowercase
    return re.sub(r'\s+', '_', text.strip().lower())

def process_excel_file(uploaded_file, convert_headers=True):
    # Read the Excel file
    df = pd.read_excel(uploaded_file)
    
    # Convert headers to snake case if option is selected
    if convert_headers:
        df.columns = [convert_to_snake_case(col) for col in df.columns]
    
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