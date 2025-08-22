import streamlit as st
import pandas as pd
import io
import tabula
import numpy as np
import re
from datetime import datetime
import json # For parsing the service account key

# --- Firebase Admin SDK Imports ---
import firebase_admin
from firebase_admin import credentials, firestore

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="College Duty List",
    page_icon="📋",
    layout="wide"
)

# --- College Emblem URL ---
college_emblem_url = "https://www.mec.ac.in/static/media/collegelogo@2x.9167c282.png"

# --- Background Banner Image URL ---
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

# --- Firebase Initialization (Global, run only once) ---
# Check if Firebase has already been initialized to prevent multiple app instances
if not firebase_admin._apps:
    try:
        # Load the service account key from Streamlit secrets
        # The secret should be named 'FIREBASE_SERVICE_ACCOUNT_KEY' and contain the full JSON string
        # Streamlit loads TOML secrets into st.secrets, so we access it like a dictionary
        # and then parse it as JSON
        
        # Access the dictionary value from st.secrets and then convert to JSON string
        # Assuming your secrets.toml looks like:
        # [connections.firestore]
        # type = "service_account"
        # ...
        # private_key = "..."
        # ...
        
        # The key for the secrets is 'connections.firestore' as per TOML structure
        firebase_credentials_config = st.secrets["connections"]["firestore"]
        
        # We need to reconstruct the credentials dictionary if Streamlit parses it into a flat dict.
        # The firebase_admin.credentials.Certificate expects a dictionary matching the JSON structure.
        
        # Ensure the private_key includes newlines correctly, as TOML might escape them
        private_key_fixed = firebase_credentials_config["private_key"].replace("\\n", "\n")

        cred_dict = {
            "type": firebase_credentials_config["type"],
            "project_id": firebase_credentials_config["project_id"],
            "private_key_id": firebase_credentials_config["private_key_id"],
            "private_key": private_key_fixed,
            "client_email": firebase_credentials_config["client_email"],
            "client_id": firebase_credentials_config["client_id"],
            "auth_uri": firebase_credentials_config["auth_uri"],
            "token_uri": firebase_credentials_config["token_uri"],
            "auth_provider_x509_cert_url": firebase_credentials_config["auth_provider_x509_cert_url"],
            "client_x509_cert_url": firebase_credentials_config["client_x509_cert_url"],
            "universe_domain": firebase_credentials_config["universe_domain"]
        }
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        st.success("Firebase initialized successfully!")
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        st.warning("Please ensure your Streamlit Cloud secret 'connections.firestore' is correctly configured with your Firebase service account JSON in TOML format.")

# Get Firestore client
db = firestore.client()

# --- Header Banner ---
st.markdown('<div class="header-banner"></div>', unsafe_allow_html=True)

# --- Header with Emblem and Titles ---
col1, col2 = st.columns([0.15, 0.85])
with col1:
    st.image(college_emblem_url, width=100)
with col2:
    st.markdown("<h2>MODEL ENGINEERING COLLEGE</h2>", unsafe_allow_html=True)
    st.title("College Duty List Portal")
    st.write("A streamlined application to manage and search faculty duty assignments.")

# --- Data Normalization Function ---
def normalize_duty_data(df_raw, exam_type, upload_date):
    """
    Normalizes the raw DataFrame extracted from Excel/CSV and adds exam type and upload date.
    Assumes a fixed header structure based on the provided Excel screenshot and CSV data:
    - Row 0: Dates (e.g., '21 Aug,1')
    - Row 1: Day names (e.g., 'Thursday')
    - Row 2: Times (e.g., '9:45 AM')
    - Column 1: Staff Names ('Name')
    """
    normalized_data = []

    date_header_row_idx = 0
    day_header_row_idx = 1
    time_header_row_idx = 2

    name_col_idx = 1
    data_start_col = 2

    required_rows_for_headers = max(date_header_row_idx, day_header_row_idx, time_header_row_idx) + 1
    if len(df_raw) < required_rows_for_headers or name_col_idx >= len(df_raw.columns):
        st.error(f"Error: Raw data does not match the expected header structure. Expected at least {required_rows_for_headers} rows for headers and column {name_col_idx} for names. "
                 f"Raw data shape: {df_raw.shape}. Please check the uploaded file's format.")
        return pd.DataFrame()

    try:
        dates_raw = df_raw.iloc[date_header_row_idx].astype(str).fillna('').tolist()
        days_raw = df_raw.iloc[day_header_row_idx].astype(str).fillna('').tolist()
        times_raw = df_raw.iloc[time_header_row_idx].astype(str).fillna('').tolist()
    except IndexError as e:
        st.error(f"Internal Error: Failed to access expected header rows based on fixed indices. Error: {e}")
        return pd.DataFrame()

    combined_headers_map = {}
    clean_date_pattern = r'(\d{1,2}\s+[A-Za-z]{3})'
    time_pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM))'

    current_base_date = ""
    max_col_in_headers = max(len(dates_raw), len(days_raw), len(times_raw))

    for col_idx in range(data_start_col, max_col_in_headers):
        date_cell_val = dates_raw[col_idx].replace('\n', ' ').strip() if col_idx < len(dates_raw) else ""
        time_cell_val = times_raw[col_idx].replace('\n', ' ').strip() if col_idx < len(times_raw) else ""

        date_match = re.search(clean_date_pattern, date_cell_val, re.IGNORECASE)
        if date_match:
            current_base_date = date_match.group(1).strip()

        time_match = re.search(time_pattern, time_cell_val, re.IGNORECASE)

        if current_base_date and time_match:
            combined_headers_map[col_idx] = f"{current_base_date} {time_match.group(0).strip()}"
        else:
            combined_headers_map[col_idx] = f"COL_{col_idx}_UNMATCHED_HEADER"

    actual_data_start_row = time_header_row_idx + 1

    for r_idx in range(actual_data_start_row, len(df_raw)):
        row_data = df_raw.iloc[r_idx]

        if name_col_idx >= len(row_data) or pd.isna(row_data.iloc[name_col_idx]):
            continue

        person_name_raw = str(row_data.iloc[name_col_idx]).replace('\n', ' ').strip()

        if not person_name_raw or \
           person_name_raw.lower() in ["nan", "", "name", "model engineering college", "principal", "total"] or \
           re.fullmatch(r'^\d+$', person_name_raw.replace('"', '')) or \
           'exam cell' in person_name_raw.lower():
            continue

        person_name = person_name_raw.split('(')[0].replace('"', '').strip()
        if not person_name:
            continue

        for c_idx in range(data_start_col, len(row_data)):
            if c_idx not in combined_headers_map or combined_headers_map[c_idx].startswith("COL_"):
                continue

            duty_value_raw = str(row_data.iloc[c_idx]).strip().upper()

            if 'X' in duty_value_raw or 'C' in duty_value_raw:
                date_time_slot_str = combined_headers_map[c_idx]
                
                try:
                    dt_object = pd.to_datetime(date_time_slot_str, format='%d %b %H:%M %p', errors='coerce')
                    if pd.isna(dt_object): # If year isn't explicitly in the string, assume current year
                        current_year = datetime.now().year
                        date_time_slot_with_year_str = f"{date_time_slot_str} {current_year}"
                        dt_object = pd.to_datetime(date_time_slot_with_year_str, format='%d %b %Y %I:%M %p', errors='coerce')

                    if pd.notna(dt_object):
                        duty_month = dt_object.strftime("%B")
                        duty_year = dt_object.year
                    else:
                        st.warning(f"Could not parse date/time '{date_time_slot_str}'. Month/Year filtering might be inaccurate for this entry.")
                        duty_month = "Unknown"
                        duty_year = "Unknown"
                except Exception as e:
                    st.warning(f"Error processing date '{date_time_slot_str}': {e}. Setting Month/Year to Unknown.")
                    duty_month = "Unknown"
                    duty_year = "Unknown"

                duty_type_str = ""
                if 'C' in duty_value_raw:
                    duty_type_str += "Paper Collection "
                if 'X' in duty_value_raw:
                    duty_type_str += "Duty"
                duty_type_str = duty_type_str.strip()

                normalized_data.append({
                    'Name': person_name,
                    'Date_Time': date_time_slot_str,
                    'Duty_Type': duty_type_str,
                    'Exam_Type': exam_type,
                    'Upload_Date': upload_date.strftime("%Y-%m-%d %H:%M:%S"),
                    'Duty_Month': duty_month,
                    'Duty_Year': duty_year
                })
    return pd.DataFrame(normalized_data)


# --- Admin Password Check and File Upload ---
def check_password():
    """Returns `True` if the user enters the correct password."""
    password = st.sidebar.text_input("Admin Password (Upload Only)", type="password")
    # >>>>>> IMPORTANT: CHANGE "your_secret_password_for_upload" TO YOUR DESIRED PASSWORD! <<<<<<
    if password == "your_secret_password_for_upload":
        return True
    return False

# Display the admin section only if the password is correct
if check_password():
    st.sidebar.success("Admin access granted! You can now upload files.")
    st.sidebar.header("Admin Panel: Upload Duty List")

    exam_type_selection = st.sidebar.selectbox(
        "Select Exam Type for Uploaded File:",
        ["University Exam", "Internal Exam"],
        key="exam_type_upload"
    )

    uploaded_file = st.sidebar.file_uploader("Upload an Excel (.xlsx) or CSV (.csv) file for best results. PDF (.pdf) can be unstable.", type=["xlsx", "csv", "pdf"])

    if uploaded_file:
        st.sidebar.info(f"Processing '{uploaded_file.name}'...")
        try:
            if uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                df_raw = pd.read_excel(uploaded_file, header=None)
                st.sidebar.success("Excel file raw data loaded.")
                st.sidebar.subheader("Raw Data from Excel (for debug)")
                st.sidebar.dataframe(df_raw.head(50))
            elif uploaded_file.type == "text/csv":
                df_raw = pd.read_csv(uploaded_file, header=None)
                st.sidebar.success("CSV file raw data loaded.")
                st.sidebar.subheader("Raw Data from CSV (for debug)")
                st.sidebar.dataframe(df_raw.head(50))
            elif uploaded_file.type == "application/pdf":
                st.sidebar.warning("PDF upload detected. For best results, please convert your PDF to Excel or CSV externally and upload that file instead. PDF parsing can be unreliable.")
                pdf_bytes = io.BytesIO(uploaded_file.read())
                df_list = tabula.read_pdf(pdf_bytes, pages='all', multiple_tables=True, lattice=True)
                if df_list:
                    df_raw = pd.concat(df_list, ignore_index=True)
                    st.sidebar.success("PDF file raw tables extracted (note: reliability varies).")
                    st.sidebar.subheader("Raw Data from PDF (for debug)")
                    st.sidebar.dataframe(df_raw.head(50))
                else:
                    st.sidebar.warning("No tables found in the PDF. Please check the PDF format or try uploading an Excel/CSV file.")
                    df_raw = pd.DataFrame()

            if not df_raw.empty:
                st.sidebar.info("Normalizing data and adding exam details...")
                current_upload_date = datetime.now()
                df_normalized = normalize_duty_data(df_raw, exam_type_selection, current_upload_date)

                if not df_normalized.empty:
                    st.sidebar.info("Saving data to Firestore...")
                    
                    # Store data in Firestore
                    batch = db.batch()
                    collection_ref = db.collection('duty_lists')
                    
                    docs_added = 0
                    for index, row in df_normalized.iterrows():
                        # Firestore automatically assigns an ID if you use .add() or .document()
                        # Using .document().set() gives you control over the doc ID if needed,
                        # but auto-ID is fine for simple additions.
                        doc_ref = collection_ref.document()
                        batch.set(doc_ref, row.to_dict())
                        docs_added += 1

                    batch.commit()
                    st.sidebar.success(f"Successfully uploaded {docs_added} duty entries to Firestore for {exam_type_selection}!")
                    
                    # Invalidate session_state cache to force reload from Firestore for immediate display
                    if 'duty_data' in st.session_state:
                        del st.session_state['duty_data']

                else:
                    st.sidebar.error("Data normalization failed. No data to save.")
            else:
                st.sidebar.error("No data extracted from the uploaded file.")
        except Exception as e:
            st.sidebar.error(f"Error processing file or saving to Firestore: {e}")
            st.sidebar.warning("An unexpected error occurred. Please ensure Firebase is set up correctly and the file is valid.")
else:
    st.sidebar.warning("Enter admin password to enable file upload.")


# --- Main Application Content (Search Section) ---
st.header("Search Duty List")

# --- Load data from Firestore if not already in session_state ---
# This block runs every time the app loads or relevant state changes, but only fetches from DB if needed
if 'duty_data' not in st.session_state or st.session_state['duty_data'] is None:
    st.info("Loading duty data from database...")
    try:
        docs = db.collection('duty_lists').stream()
        firestore_data = []
        for doc in docs:
            doc_dict = doc.to_dict()
            firestore_data.append(doc_dict)
        
        if firestore_data:
            df_normalized = pd.DataFrame(firestore_data)
            # Ensure 'Duty_Year' is integer for sorting
            df_normalized['Duty_Year'] = pd.to_numeric(df_normalized['Duty_Year'], errors='coerce').fillna(0).astype(int)
            st.session_state['duty_data'] = df_normalized.to_json(orient='split')
            st.success("Duty list loaded from Firestore. You can now perform searches.")
        else:
            st.info("No duty data found in the database. Admin can upload a duty list using the sidebar.")
            # Initialize with an empty DataFrame to prevent further errors
            st.session_state['duty_data'] = pd.DataFrame(columns=['Name', 'Date_Time', 'Duty_Type', 'Exam_Type', 'Upload_Date', 'Duty_Month', 'Duty_Year'])
    except Exception as e:
        st.error(f"Error loading data from Firestore: {e}")
        st.warning("Could not retrieve duty list from the database. Please check Firebase configuration.")
        st.session_state['duty_data'] = pd.DataFrame(columns=['Name', 'Date_Time', 'Duty_Type', 'Exam_Type', 'Upload_Date', 'Duty_Month', 'Duty_Year'])


# Proceed with search if data is available (even if empty, the DataFrame will be initialized)
df_normalized = pd.read_json(st.session_state['duty_data'], orient='split')

if not df_normalized.empty:
    # Extract unique months and years for filters
    # Convert month names to datetime objects for proper sorting, handling "Unknown"
    month_order = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December", "Unknown"]
    available_months = ["All"] + sorted(df_normalized['Duty_Month'].unique().tolist(), 
                                        key=lambda x: month_order.index(x) if x in month_order else 99)
    available_years = ["All"] + sorted(df_normalized['Duty_Year'].unique().tolist(), reverse=True)


    # Create tabs for search functionality
    tab1, tab2 = st.tabs(["Search by Staff Name", "Search by Date"])

    with tab1:
        st.subheader("Search by Staff Name")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)

        with col_s1:
            name_query = st.text_input("Enter staff member's name:", key="name_search_tab")
        with col_s2:
            filter_exam_type_name = st.selectbox(
                "Filter by Exam Type:",
                ["All", "University Exam", "Internal Exam"],
                key="filter_exam_type_name"
            )
        with col_s3:
            filter_month_name = st.selectbox(
                "Filter by Month:",
                available_months,
                key="filter_month_name"
            )
        with col_s4:
            filter_year_name = st.selectbox(
                "Filter by Year:",
                available_years,
                key="filter_year_name"
            )
        
        filtered_df_name = df_normalized.copy()

        if name_query:
            filtered_df_name = filtered_df_name[filtered_df_name['Name'].str.contains(name_query, case=False, na=False)]
        if filter_exam_type_name != "All":
            filtered_df_name = filtered_df_name[filtered_df_name['Exam_Type'] == filter_exam_type_name]
        if filter_month_name != "All":
            filtered_df_name = filtered_df_name[filtered_df_name['Duty_Month'] == filter_month_name]
        if filter_year_name != "All":
            filtered_df_name = filtered_df_name[filtered_df_name['Duty_Year'] == filter_year_name]


        if name_query or filter_exam_type_name != "All" or filter_month_name != "All" or filter_year_name != "All":
            if not filtered_df_name.empty:
                st.write(f"Duties found:")
                for name in sorted(filtered_df_name['Name'].unique()):
                    st.markdown(f"**{name}**")
                    staff_duties = filtered_df_name[filtered_df_name['Name'] == name].sort_values(by=['Duty_Year', 'Duty_Month', 'Date_Time'])
                    for index, row in staff_duties.iterrows():
                        st.write(f"  - **{row['Date_Time']}** ({row['Exam_Type']}): {row['Duty_Type']}")
            else:
                st.warning("No duties found matching your criteria. Please adjust your filters.")

    with tab2:
        st.subheader("Search by Date")
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)

        with col_d1:
            date_query = st.text_input("Enter a date (e.g., '21 Aug', '25 Aug'):", key="date_search_tab")
        with col_d2:
            filter_exam_type_date = st.selectbox(
                "Filter by Exam Type:",
                ["All", "University Exam", "Internal Exam"],
                key="filter_exam_type_date"
            )
        with col_d3:
            filter_month_date = st.selectbox(
                "Filter by Month:",
                available_months,
                key="filter_month_date"
            )
        with col_d4:
            filter_year_date = st.selectbox(
                "Filter by Year:",
                available_years,
                key="filter_year_date"
            )

        filtered_df_date = df_normalized.copy()

        if date_query:
            filtered_df_date['Date_Only'] = filtered_df_date['Date_Time'].apply(
                lambda x: ' '.join(x.split(' ')[:2]) if len(x.split(' ')) >= 2 else x
            )
            filtered_df_date = filtered_df_date[filtered_df_date['Date_Only'].str.contains(date_query, case=False, na=False)]
        
        if filter_exam_type_date != "All":
            filtered_df_date = filtered_df_date[filtered_df_date['Exam_Type'] == filter_exam_type_date]
        if filter_month_date != "All":
            filtered_df_date = filtered_df_date[filtered_df_date['Duty_Month'] == filter_month_date]
        if filter_year_date != "All":
            filtered_df_date = filtered_df_date[filtered_df_date['Duty_Year'] == filter_year_date]

        if date_query or filter_exam_type_date != "All" or filter_month_date != "All" or filter_year_date != "All":
            if not filtered_df_date.empty:
                st.write(f"Staff on duty:")
                for date_time_slot in sorted(filtered_df_date['Date_Time'].unique()):
                    st.markdown(f"#### {date_time_slot}")
                    slot_duties = filtered_df_date[filtered_df_date['Date_Time'] == date_time_slot].sort_values(by='Name')
                    for index, row in slot_duties.iterrows():
                        st.write(f"- {row['Name']} ({row['Exam_Type']}): {row['Duty_Type']}")
            else:
                st.warning("No duties found matching your criteria. Please adjust your filters.")
else:
    st.info("No duty data available for searching. The Admin needs to upload a duty list first.")


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
