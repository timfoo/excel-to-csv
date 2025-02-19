# Excel Header Formatter

A Streamlit web application that helps you convert Excel file headers to snake case format. This tool makes it easy to standardize your Excel column headers by converting them to lowercase and replacing spaces with underscores.

## Features

- Upload Excel files (.xlsx, .xls)
- Automatically converts headers to snake case format
- Preview processed data before downloading
- Export results to CSV format
- Simple and intuitive user interface

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/shopee-order-formatter.git
cd shopee-order-formatter
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the provided local URL (typically http://localhost:8501)

3. Use the application:
   - Click the 'Choose an Excel file' button to upload your Excel file
   - Preview the processed data with converted headers
   - Download the processed file in CSV format

## Example

Original Excel headers:
```
Product Name | Order Date | Customer ID
```

Converted headers:
```
product_name | order_date | customer_id
```

## Dependencies

- streamlit==1.32.0
- pandas==2.2.1
- openpyxl==3.1.2

## License

This project is open source and available under the MIT License.