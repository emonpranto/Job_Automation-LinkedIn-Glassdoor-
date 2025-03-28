import pickle
import undetected_chromedriver as uc
import streamlit as st
import time

# Initialize driver as seasson state
if "driver" not in st.session_state:
    st.session_state.driver = None

# Set user name
user_name = st.text_input("Enter your LinkedIn username: ").strip().lower()

# Button 1: Login
if st.button("Login"):
    st.write(f"Opening LinkedIn login page for user: {user_name}...")
    if st.session_state.driver is None:
        try:
            st.session_state.driver = uc.Chrome()
            st.session_state.driver.get("https://www.linkedin.com/login")
            st.write("Please log in on the LinkedIn page that opened.")
            st.write("After logging in, click the 'Log in manually & save cookies' button.")
        except Exception as e:
            st.error(f"Error opening Chrome: {e}")
            st.session_state.driver = None  # Reset on failure

# Button 2: Log in manually & save cookies
if st.button("Log in manually & save cookies"):
    if not user_name:
        st.warning("Please enter your LinkedIn username first.")
    elif st.session_state.driver is None:
        st.warning("Please click the 'Login' button first to open LinkedIn.")
    else:
        st.write("Checking if you are logged in and saving cookies...")
        try:
            cookies = st.session_state.driver.get_cookies()
            with open(f"{user_name}_linkedin.pkl", "wb") as f:
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