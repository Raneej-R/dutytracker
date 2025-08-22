import streamlit as st
import pandas as pd
import io
import tabula
import numpy as np
import re # Import regex for advanced splitting

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="College Duty List",
    page_icon="📋",
    layout="wide"
)

# --- College Emblem URL ---
college_emblem_url = "https://www.mec.ac.in/static/media/collegelogo@2x.9167c282.png"

# --- Background Banner Image URL ---
# This URL is for the image you provided to be used as a background at the top.
background_banner_url = "https://media.licdn.com/dms/image/v2/C561BAQEtyyIRJA3trg/company-background_10000/company-background_10000/0/1620905018536/model_engineering_college_cover?e=1756396800&v=beta&t=sM_YWuRMFsrD0qBxeTqZJJ4s4W2K4f2QCKa1tgHEb5w"

# --- Custom CSS for Red and White Theme & Banner ---
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #F8F8F8; /* Light off-white background */
        color: #333333; /* Dark grey text for readability */
    }}
    .stSidebar {{
        background-color: #E0E0E0; /* Slightly darker sidebar for contrast */
        color: #333333;
    }}
    .css-1d391kg {{ /* Target for the main Streamlit container background */
        background-color: #FFFFFF; /* Pure white content area */
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: #D32F2F; /* Deep red for headers */
    }}
    .stButton>button {{
        background-color: #D32F2F; /* Deep red buttons */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }}
    .stButton>button:hover {{
        background-color: #B71C1C; /* Darker red on hover */
    }}
    .stTextInput>div>div>input {{
        border-radius: 8px;
        border: 1px solid #D32F2F; /* Red border for text inputs */
        padding: 8px 12px;
    }}
    .stFileUploader>div>div>button {{
        background-color: #D32F2F;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }}
    .stFileUploader>div>div>button:hover {{
        background-color: #B71C1C;
    }}
    .stSuccess {{
        background-color: #E8F5E9; /* Light green for success messages */
        color: #2E7D32; /* Dark green text */
        border-left: 5px solid #4CAF50;
        border-radius: 5px;
        padding: 10px;
    }}
    .stError {{
        background-color: #FFEBEE; /* Light red for error messages */
        color: #D32F2F; /* Deep red text */
        border-left: 5px solid #F44336;
        border-radius: 5px;
        padding: 10px;
    }}
    .stWarning {{
        background-color: #FFF3E0; /* Light orange for warning messages */
        color: #EF6C00; /* Dark orange text */
        border-left: 5px solid #FF9800;
        border-radius: 5px;
        padding: 10px;
    }}
    /* Style for the dataframe output */
    .stDataFrame {{
        border: 1px solid #D32F2F;
        border-radius: 8px;
        overflow: auto; /* Ensures scroll if table is wide */
    }}
    /* Custom banner div style */
    .header-banner {{
        background-image: url("{background_banner_url}");
        background-size: cover;
        background-position: center;
        height: 150px; /* Adjust height as needed */
        width: 100%;
        margin-bottom: 20px; /* Space below the banner */
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white; /* Text color on banner, assuming image is dark enough */
        font-size: 2em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }}
    .footer {{
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #D32F2F;
        text-align: center;
        color: #555555;
        font-size: 0.9em;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header Banner ---
# This div will display the background image at the top of the page.
st.markdown('<div class="header-banner"></div>', unsafe_allow_html=True)

# --- Header with Emblem and Titles ---
col1, col2 = st.columns([0.15, 0.85])
with col1:
    st.image(college_emblem_url, width=100)
with col2:
    # "MODEL ENGINEERING COLLEGE" as a heading in red
    st.markdown("<h2>MODEL ENGINEERING COLLEGE</h2>", unsafe_allow_html=True)
    st.title("College Duty List Portal")
    st.write("A streamlined application to manage and search faculty duty assignments.") # Tagline added

# --- Data Normalization Function ---
def normalize_duty_data(df_raw):
    """
    Normalizes the raw DataFrame extracted from Excel/CSV.
    Assumes a fixed header structure based on the provided Excel screenshot and CSV data:
    - Row 0: Dates (e.g., '21 Aug,1')
    - Row 1: Day names (e.g., 'Thursday')
    - Row 2: Times (e.g., '9:45 AM')
    - Column 1: Staff Names ('Name')
    """
    normalized_data = []

    # Fixed header row indices based on common structure of your Excel/CSV
    date_header_row_idx = 0
    day_header_row_idx = 1
    time_header_row_idx = 2

    # Fixed name column index
    name_col_idx = 1
    # Data columns (duties) start after the name column
    data_start_col = 2

    # Basic validation that these header rows and columns exist in the raw DataFrame
    required_rows_for_headers = max(date_header_row_idx, day_header_row_idx, time_header_row_idx) + 1
    if len(df_raw) < required_rows_for_headers or name_col_idx >= len(df_raw.columns):
        st.error(f"Error: Raw data does not match the expected header structure. Expected at least {required_rows_for_headers} rows for headers and column {name_col_idx} for names. "
                 f"Raw data shape: {df_raw.shape}. Please check the uploaded file's format.")
        return pd.DataFrame()

    # Extract raw header data as lists of strings
    try:
        # Convert to string and handle potential NaN values explicitly
        dates_raw = df_raw.iloc[date_header_row_idx].astype(str).fillna('').tolist()
        days_raw = df_raw.iloc[day_header_row_idx].astype(str).fillna('').tolist()
        times_raw = df_raw.iloc[time_header_row_idx].astype(str).fillna('').tolist()
    except IndexError as e:
        st.error(f"Internal Error: Failed to access expected header rows based on fixed indices. Error: {e}")
        return pd.DataFrame()

    # Step 2: Construct `combined_headers_map` (maps raw_df_column_index -> "Date Time" string)
    combined_headers_map = {}

    # Regex to extract clean date (e.g., "21 Aug") from "21 Aug,1", "21 Aug,2" or just "21 Aug"
    clean_date_pattern = r'(\d{1,2}\s+[A-Za-z]{3})'
    # Regex for time patterns (e.g., "9:45 AM")
    time_pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM))'

    current_base_date = "" # To carry over date for columns where it might be empty (e.g., merged cells)

    # Determine the maximum column index to iterate through for headers
    max_col_in_headers = max(len(dates_raw), len(days_raw), len(times_raw))

    for col_idx in range(data_start_col, max_col_in_headers):
        # Get raw cell values, handling potential IndexError if rows are shorter than expected
        date_cell_val = dates_raw[col_idx].replace('\n', ' ').strip() if col_idx < len(dates_raw) else ""
        # day_cell_val is present but not used directly in combined header for simplicity
        time_cell_val = times_raw[col_idx].replace('\n', ' ').strip() if col_idx < len(times_raw) else ""

        # Update current_base_date if a new date is found in the date header row
        date_match = re.search(clean_date_pattern, date_cell_val, re.IGNORECASE)
        if date_match:
            current_base_date = date_match.group(1).strip() # Extract "21 Aug" from "21 Aug,1"

        # Extract time from the time header row
        time_match = re.search(time_pattern, time_cell_val, re.IGNORECASE)

        # Only form a combined header if both a base date and a time are found for this column
        if current_base_date and time_match:
            combined_headers_map[col_idx] = f"{current_base_date} {time_match.group(0).strip()}"
        else:
            # If no valid date/time combination, assign a placeholder.
            # These columns will be ignored when processing actual duty data.
            combined_headers_map[col_idx] = f"COL_{col_idx}_UNMATCHED_HEADER"


    # Determine the row where actual staff duty data begins (after the time header row)
    actual_data_start_row = time_header_row_idx + 1

    # Step 3: Process each staff member's row for duty entries
    for r_idx in range(actual_data_start_row, len(df_raw)):
        row_data = df_raw.iloc[r_idx]

        # Get the person's name from the identified name column
        # Ensure name_col_idx is within the bounds of row_data for this specific row
        if name_col_idx >= len(row_data) or pd.isna(row_data.iloc[name_col_idx]):
            continue # Skip if name column is out of bounds for this row or cell is empty/NaN

        person_name_raw = str(row_data.iloc[name_col_idx]).replace('\n', ' ').strip()

        # Skip rows that don't look like actual staff entries (e.g., empty, headers, footers, numbers)
        if not person_name_raw or \
           person_name_raw.lower() in ["nan", "", "name", "model engineering college", "principal", "total"] or \
           re.fullmatch(r'^\d+$', person_name_raw.replace('"', '')) or \
           'exam cell' in person_name_raw.lower():
            continue

        # Clean name (remove extra details like '(Exam Cell)' and surrounding quotes if present)
        person_name = person_name_raw.split('(')[0].replace('"', '').strip()
        if not person_name: # Handle cases where name becomes empty after stripping
            continue

        # Iterate through the duty columns, using the refined `combined_headers_map`
        for c_idx in range(data_start_col, len(row_data)):
            # Ensure the column index is within our generated headers map and has a valid Date_Time string
            if c_idx not in combined_headers_map or combined_headers_map[c_idx].startswith("COL_"):
                continue # Skip if no valid Date_Time was derived for this column

            duty_value_raw = str(row_data.iloc[c_idx]).strip().upper()

            # Check for 'X' (Duty) or 'C' (Paper Collection) in the duty cell
            if 'X' in duty_value_raw or 'C' in duty_value_raw:
                date_time_slot = combined_headers_map[c_idx]

                duty_type_str = ""
                if 'C' in duty_value_raw:
                    duty_type_str += "Paper Collection "
                if 'X' in duty_value_raw:
                    duty_type_str += "Duty"
                duty_type_str = duty_type_str.strip()

                normalized_data.append({
                    'Name': person_name,
                    'Date_Time': date_time_slot,
                    'Duty_Type': duty_type_str
                })
    return pd.DataFrame(normalized_data)


# --- Admin Password Check and File Upload ---
def check_password():
    """Returns `True` if the user enters the correct password."""
    password = st.sidebar.text_input("Admin Password (Upload Only)", type="password")
    # >>>>>> IMPORTANT: CHANGE "your_secret_password_for_upload" TO YOUR DESIRED PASSWORD! <<<<<<
    if password == "mee":
        return True
    return False

# Display the admin section only if the password is correct
if check_password():
    st.sidebar.success("Admin access granted! You can now upload files.")
    st.sidebar.header("Admin Panel: Upload Duty List")
    uploaded_file = st.sidebar.file_uploader("Upload an Excel (.xlsx) or CSV (.csv) file for best results. PDF (.pdf) can be unstable.", type=["xlsx", "csv", "pdf"])

    if uploaded_file:
        st.sidebar.info(f"Processing '{uploaded_file.name}'...")
        try:
            if uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                # Read Excel directly into a DataFrame without a header initially.
                df_raw = pd.read_excel(uploaded_file, header=None)
                st.sidebar.success("Excel file raw data loaded.")
                st.sidebar.subheader("Raw Data from Excel (for debug)")
                st.sidebar.dataframe(df_raw.head(50)) # Show first 50 rows for debugging
                st.sidebar.dataframe(df_raw.tail(50)) # Show last 50 rows
            elif uploaded_file.type == "text/csv":
                df_raw = pd.read_csv(uploaded_file, header=None)
                st.sidebar.success("CSV file raw data loaded.")
                st.sidebar.subheader("Raw Data from CSV (for debug)")
                st.sidebar.dataframe(df_raw.head(50)) # Show first 50 rows for debugging
                st.sidebar.dataframe(df_raw.tail(50)) # Show last 50 rows
            elif uploaded_file.type == "application/pdf":
                st.sidebar.warning("PDF upload detected. For best results, please convert your PDF to Excel or CSV externally and upload that file instead. PDF parsing can be unreliable.")
                pdf_bytes = io.BytesIO(uploaded_file.read())

                # Basic tabula-py call for PDF - may or may not work reliably for complex layouts
                df_list = tabula.read_pdf(pdf_bytes, pages='all', multiple_tables=True, lattice=True)

                if df_list:
                    df_raw = pd.concat(df_list, ignore_index=True)
                    st.sidebar.success("PDF file raw tables extracted (note: reliability varies).")
                    st.sidebar.subheader("Raw Data from PDF (for debug)")
                    st.sidebar.dataframe(df_raw.head(50))
                    st.sidebar.dataframe(df_raw.tail(50))
                else:
                    st.sidebar.warning("No tables found in the PDF. Please check the PDF format or try uploading an Excel/CSV file.")
                    df_raw = pd.DataFrame()

            if not df_raw.empty:
                st.sidebar.info("Normalizing data...")
                df_normalized = normalize_duty_data(df_raw)

                if not df_normalized.empty:
                    st.session_state['duty_data'] = df_normalized.to_json(orient='split')
                    st.sidebar.success("Duty list data prepared and normalized for searching!")
                    st.sidebar.dataframe(df_normalized.head()) # Show a preview of normalized data
                    st.sidebar.dataframe(df_normalized.tail())
                else:
                    st.session_state['duty_data'] = None
                    st.sidebar.error("Data normalization failed. Please ensure your Excel/CSV file matches the expected header patterns (Dates in row 0, Days in row 1, Times in row 2, Name in column 1).")
            else:
                st.session_state['duty_data'] = None
        except Exception as e:
            st.sidebar.error(f"Error processing file: {e}")
            st.sidebar.warning("An unexpected error occurred during file processing. Please ensure the file is valid and formatted as expected.")
            st.session_state['duty_data'] = None
else:
    st.sidebar.warning("Enter admin password to enable file upload.")


# --- Main Application Content (Search Section) ---
st.header("Search Duty List")

if 'duty_data' not in st.session_state or st.session_state['duty_data'] is None:
    st.info("No duty list loaded. Please upload a file using the Admin Panel in the sidebar.")
else:
    df_normalized = pd.read_json(st.session_state['duty_data'], orient='split')

    st.success("Duty list loaded. You can now perform searches.")

    # Create tabs for search functionality
    tab1, tab2 = st.tabs(["Search by Staff Name", "Search by Date"])

    with tab1:
        st.subheader("Search by Staff Name")
        name_query = st.text_input("Enter staff member's name:", key="name_search_tab") # Unique key for tab
        if name_query:
            name_results = df_normalized[df_normalized['Name'].str.contains(name_query, case=False, na=False)]

            if not name_results.empty:
                st.write(f"Duties for '{name_query}':")
                name_results_sorted = name_results.sort_values(by='Date_Time')
                for index, row in name_results_sorted.iterrows():
                    st.write(f"- **{row['Date_Time']}**: {row['Duty_Type']}")
            else:
                st.warning(f"No duties found for '{name_query}'. Please try another name.")

    with tab2:
        st.subheader("Search by Date")
        date_query = st.text_input("Enter a date (e.g., '21 Aug', '25 Aug'):", key="date_search_tab") # Unique key for tab
        if date_query:
            df_normalized['Date_Only'] = df_normalized['Date_Time'].apply(
                lambda x: ' '.join(x.split(' ')[:2]) if len(x.split(' ')) >= 2 else x
            )
            date_results = df_normalized[df_normalized['Date_Only'].str.contains(date_query, case=False, na=False)]

            if not date_results.empty:
                st.write(f"Staff on duty on '{date_query}':")
                for date_time_slot in sorted(date_results['Date_Time'].unique()):
                    st.markdown(f"#### {date_time_slot}")
                    staff_for_slot = date_results[date_results['Date_Time'] == date_time_slot].sort_values(by='Name')
                    for index, row in staff_for_slot.iterrows():
                        st.write(f"- {row['Name']} ({row['Duty_Type']})")
            else:
                st.warning(f"No duties found for '{date_query}'. Please try another date format (e.g., '21 Aug').")

# --- Footer ---
st.markdown(
    """
    <div class="footer">
        <p>&copy; 2025 Model Engineering College. All rights reserved.</p>
        <p>Contact: info@mec.ac.in</p>
    </div>
    """,
    unsafe_allow_html=True
)
