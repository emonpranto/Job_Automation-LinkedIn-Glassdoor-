import streamlit as st
import os 

st.set_page_config(
    page_title="Job Application Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('Job Application Bot/Home Page')

user_name = st.text_input("Enter your user name", key="user_name_input")
job_title = st.text_input("Enter the job title you're looking for", key="job_title_input")
location = st.sidebar.text_input("Location", key="location_input")
apply_limit = st.sidebar.number_input("Number of Jobs to Apply", min_value=1, max_value=6, key="apply_limit_input")
cv = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"], accept_multiple_files=False, key="cv_upload")
cv_path = r"D:\Job Automation Bot\temp"

save_dir = r"D:\Job Automation Bot\temp"

# Ensure the directory exists
os.makedirs(save_dir, exist_ok=True)

# File uploader in Streamlit


if cv is not None:
    # Extract the file name
    cv_filename = cv.name

    # Create the full save path
    path = os.path.join(save_dir, cv_filename)

    # Save the file to the local directory
    with open(path, "wb") as f:
        f.write(cv.read())
# Store inputs in session state

# Store inputs in session state
if user_name and job_title and location and apply_limit and cv:
    st.session_state.user_name = user_name
    st.session_state.job_title = job_title
    st.session_state.location = location
    st.session_state.apply_limit = apply_limit
    if cv:
        cv_path = os.path.join(cv_path, cv.name)
        st.session_state.cv_path = cv_path

if st.button("Go to LinedIn Page"):
    st.session_state.page = "4_💼_LinkedIn"
    st.rerun()


# Navigation to the next page
if st.button("Go to Glassdoor Page"):
    st.session_state.page = "5_💭_Glassdoor"
    st.rerun()