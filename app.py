import streamlit as st
import requests
from pdf2image import convert_from_bytes
import time
import json
import os
import platform
POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"
URL = "http://127.0.0.1:8000/{}"


# Use Windows poppler only if it actually exists on this machine
if platform.system() == "Windows":
    win_path = r"C:\poppler-24.08.0\Library\bin"
    POPPLER_PATH = win_path if os.path.exists(win_path) else None
else:
    POPPLER_PATH = None


st.title("Medical Data Extractor 👩‍⚕️")

file = st.file_uploader("Upload file", type="pdf")
col3, col4 = st.columns(2)

with col3:
    file_format = st.radio(label="Select type of document", options=["prescription", "patient_details"], horizontal=True)

with col4:
    if file and st.button("Upload PDF", type="primary"):
        bar = st.progress(50)
        time.sleep(3)
        bar.progress(100)

        payload = {'file_format': file_format}
        files = {'file': file.getvalue()}
        headers = {}

        try:
            response = requests.post(URL.format('extract_from_doc'), headers=headers, data=payload, files=files)
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
        else:
            if response.status_code == 200:
                try:
                    data = response.json()  # directly parse JSON response
                    if data:
                        st.session_state.update(data)
                        st.success("Data extracted successfully!")
                    else:
                        st.warning("No data returned from server.")
                except json.JSONDecodeError:
                    st.error("Failed to parse JSON from server response.")
            else:
                st.error(f"Server error: {response.status_code} - {response.reason}")
                st.write(f"Response content: {response.text}")

if file:
    pages = convert_from_bytes(file.getvalue(), poppler_path=POPPLER_PATH)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Your file")
        st.image(pages[0])

    with col2:
        if st.session_state:
            st.subheader("Details")
            if file_format == "prescription":
                name = st.text_input(label="Name", value=st.session_state.get("patient_name", ""))
                address = st.text_input(label="Address", value=st.session_state.get("patient_address", ""))
                medicines = st.text_input(label="Medicines", value=st.session_state.get("medicines", ""))
                directions = st.text_input(label="Directions", value=st.session_state.get("directions", ""))
                refill = st.text_input(label="Refill", value=st.session_state.get("refill", ""))
            elif file_format == "patient_details":
                name = st.text_input(label="Name", value=st.session_state.get("patient_name", ""))
                phone = st.text_input(label="Phone No.", value=st.session_state.get("phone_no", ""))
                vacc_status = st.text_input(label="Hepatitis B vaccination status", value=st.session_state.get("vaccination_status", ""))
                med_problems = st.text_input(label="Medical Problems", value=st.session_state.get("medical_problems", ""))
                has_insurance = st.text_input(label="Does patient have insurance?", value=st.session_state.get("has_insurance", ""))

            if st.button(label="Submit", type="primary"):
                if file_format == "patient_details":
                    post_data = {
                        'name': name,
                        'phone': phone,
                        'vacc_status': vacc_status,
                        'med_problems': med_problems,
                        'has_insurance': has_insurance
                    }
                else:  # prescription
                    post_data = {
                        'name': name,
                        'address': address,
                        'medicines': medicines,
                        'directions': directions,
                        'refill': refill
                    }

                try:
                    response = requests.post(URL.format(file_format), headers={}, data=post_data)
                    response.raise_for_status()
                    resp_json = response.json()
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to submit details: {e}")
                except json.JSONDecodeError:
                    st.error("Failed to parse response from server.")
                else:
                    if resp_json:
                        st.success('Details successfully recorded.')
                        # Clear session state after successful submission
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                    else:
                        st.error('Error saving data into Database')
