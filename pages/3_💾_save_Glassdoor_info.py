import pickle
import undetected_chromedriver as uc
import streamlit as st
import time

# Initialize driver as None
if "driver" not in st.session_state:
    st.session_state.driver = None
# Set user name

user_name = st.text_input("Enter your Glassdoor username: ").strip().lower()

# Button 1: Login
if st.button("Login"):
    st.write(f"Opening Glassdoor login page for user: {user_name}...")
    if st.session_state.driver is None:
        try:
            options = uc.ChromeOptions()
            options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.popups": 1,  # Allow pop-ups
                "profile.default_content_setting_values.notifications": 1  # Allow notifications
            })

            st.session_state.driver = uc.Chrome(options=options)
            st.session_state.driver.get("https://www.glassdoor.com/profile/login_input.htm")
            st.write("Please log in on the Glassdoor page that opened.")
            st.write("After logging in, click the 'Log in manually & save cookies' button.")
        except Exception as e:
            st.error(f"Error opening Chrome: {e}")
            st.session_state.driver = None  # Reset on failure

# Button 2: Log in manually & save cookies
if st.button("Log in manually & save cookies"):
    if not user_name:
        st.warning("Please enter your Glassdoor username first.")
    elif st.session_state.driver is None:
        st.warning("Please click the 'Login' button first to open Glassdoor.")
    else:
        st.write("Checking if you are logged in and saving cookies...")
        try:
            cookies = st.session_state.driver.get_cookies()
            with open(f"{user_name}_glassdoor.pkl", "wb") as f:
                pickle.dump(cookies, f)
            st.success("✅ Cookies saved successfully!")

            # Close the browser and reset driver
            try:
                st.session_state.driver.quit()
                st.session_state.driver = None
            except Exception as e:
                st.error(f"Error while quitting driver: {e}")
        except Exception as e:
            st.error(f"❌ Error saving cookies. Ensure you are logged in: {e}")