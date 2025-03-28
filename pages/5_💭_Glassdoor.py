import pickle
import time
import os
import tempfile
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import streamlit as st
from utils.bot import ask_query
from selenium.common.exceptions import TimeoutException

def ask_llm(question,options=None):
    return ask_query(question,options).ask()

driver=None

st.title("Glassdoor Job Auto Apply Bot")
st.sidebar.header("Settings")

def load_glassdoor_session(driver,user_name):
    """Restores Glassdoor session using saved cookies."""
    # user_name=st.sidebar.text_input("User Name").lower()
    driver.get("https://www.glassdoor.com/index.htm")

    try:
        with open(f"{user_name}_glassdoor.pkl", "rb") as f:
            cookies = pickle.load(f)

        for cookie in cookies:
            driver.add_cookie(cookie)

        driver.refresh()  # Refresh after adding cookies
        print(" Glassdoor session restored successfully!")

    except Exception as e:
        print(" Error loading session:", e)

def close_modal_if_present(driver):
    """
    Detects and closes the application submission modal if it appears.
    
    :param driver: Selenium WebDriver instance.
    """
    try:
        # Wait for the modal close button to appear (if present)
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='close-modal']"))
        )
        
        # Click the close button
        driver.execute_script("arguments[0].click();", close_button)
        print(" Modal closed successfully!")
        return True

    except TimeoutException:
        print(" No modal appeared. Continuing...")
    except Exception as e:
        print(" Error closing modal:", e)
        return False

def click_easy_apply_buttons(driver):
    # Wait for "Easy Apply" buttons to be present
    easy_apply_buttons = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//button[@data-test='easyApply']"))
    )

    print(f" Found {len(easy_apply_buttons)} 'Easy Apply' buttons.")

    for index, button in enumerate(easy_apply_buttons):
        try:
            # Click using JavaScript to avoid interception issues
            driver.execute_script("arguments[0].click();", button)
            print(f" Clicked 'Easy Apply' button {index + 1}/{len(easy_apply_buttons)}")
            
            time.sleep(random.randint(3, 6))  # Mimic human behavior

            # Handle potential application pop-ups
            # click_cancel(driver)
            return True

        except Exception as btn_error:
            print(f" Error clicking 'Easy Apply' button {index + 1}: {btn_error}")
            return False

def click_cancel(driver):
    try:
        # Find cancel button
        cancel_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Cancel"]'))
        )

        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView();", cancel_button)

        # Use JavaScript click
        driver.execute_script("arguments[0].click();", cancel_button)

        print(" Cancel button clicked successfully.")
        return True

    except Exception as e:
        print("Not found or error clicking cancel button:", e)
        return False
      # Close browser after some time

def search_glassdoor_jobs(driver,job_title,location):
    try:
        # Open Glassdoor homepage
        driver.get("https://www.glassdoor.com/")
        time.sleep(random.randint(3, 6))  # Random delay

        # Click the "Jobs" link
        jobs_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Jobs')]"))
        )
        driver.execute_script("arguments[0].click();", jobs_link)  # JavaScript click
        print(" Clicked 'Jobs' link.")
        
        time.sleep(random.randint(3, 6))  # Wait for page to load

        # Find job title input field and enter job title
        job_title_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchBar-jobTitle"))
        )
        job_title_input.clear()
        for char in job_title:
            time.sleep(random.uniform(0.1, 0.3))
            job_title_input.send_keys(char)
        time.sleep(random.uniform(1, 3))  # Random delay

        # Find location input field and enter location
        location_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchBar-location"))
        )
        location_input.clear()
        for char in location:
            time.sleep(random.uniform(0.1, 0.3))
            location_input.send_keys(char)
        time.sleep(random.uniform(1, 3))  # Random delay

        # Press Enter to search
        location_input.send_keys(Keys.RETURN)

        print(" Job search executed successfully on Glassdoor.")

        # Wait for results to load
        time.sleep(random.randint(5, 8)) 

    except Exception as e:
        print(" Error searching Glassdoor jobs:", e)

def filter_jobs(driver):
    try:
        # Wait for the button to appear
        easy_apply_filter = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-test='applicationType' and contains(text(), 'Easy Apply only')]"))
        )

        # Click using JavaScript
        driver.execute_script("arguments[0].click();", easy_apply_filter)
        print(" Clicked 'Easy Apply only' filter.")

        time.sleep(random.randint(3, 6))  # Mimic human behavior
    except Exception as e:
        print(" Error clicking 'Easy Apply only' filter:", e)

def fill_input_fields(driver):
    """Detect and fill out text fields dynamically using ask_llm()."""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "input"))
        )
        input_fields = driver.find_elements(By.CSS_SELECTOR, "input, textarea")
        print(f" Found {len(input_fields)} input fields.")

        for field in input_fields:
            field_id = field.get_attribute("id") or ""
            field_name = field.get_attribute("name") or ""

            # Locate the associated question text
            question_text = ""
            try:
                question_element = driver.find_element(
                    By.XPATH,
                    f"//label[@for='{field_id}']//span[contains(@class, 'css-gtr6b9')]"
                )
                question_text = question_element.text.strip()
            except:
                pass

            # If no label, fallback to using placeholder, aria-label, or name
            field_identifier = (question_text).strip().lower()
            print(f" Identified question: {field_identifier}")

            # Skip honeypot fields
            if "if you're a human" in field_identifier or "leave this blank" in field_identifier:
                print(f" Skipping honeypot field: {field_identifier}")
                continue  

            # Skip already filled fields
            if field.get_attribute("value"):
                continue

            # Scroll to field and click (in case it's required)
            driver.execute_script("arguments[0].scrollIntoView();", field)
            driver.execute_script("arguments[0].click();", field)  

            # Get AI-generated answer for this question
            answer = ask_llm(f"What should I fill for: '{question_text}'?")
            print(f" Filling '{question_text}' with: {answer}")

            # Type the answer in a human-like way
            if "optional" not in answer.lower():
                for char in answer:
                    time.sleep(random.uniform(0.1, 0.3))
                    field.send_keys(char)
            time.sleep(1)  

        print(" Successfully filled all fields.")
        return True

    except Exception as e:
        print(f" Error filling input fields: {e}")
        return False

    
def click_continue(driver):
    try:
        # Find all "Continue" buttons
        continue_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-testid='continue-button']"))
        )

        for button in continue_buttons:
            button_text = button.text.strip().lower()

            # Click "Continue" or "Review your application" button
            if "continue" in button_text or "review your application" in button_text:
                driver.execute_script("arguments[0].scrollIntoView();", button)
                driver.execute_script("arguments[0].click();", button)
                print(f" Clicked the '{button_text}' button successfully!")
                return True

        print(" No matching 'Continue' button found.")
        return True

    except Exception as e:
        print(" Error clicking the 'Continue' button:", e)
        return False


def upload_resume(driver,cv_path):
    """Uploads a resume file by finding the hidden file input field."""
    try:
        # Locate the file input field by its 'for' attribute reference
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        
        # Send the resume file path to the input field
        file_input.send_keys(cv_path)
        print(" CV uploaded successfully.")
        return True

    except Exception as e:
        print(" Error uploading CV:", e)
        return False

def click_submit_application(driver):
    try:
        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[.//span[text()='Submit your application']]"))
        )

        # Scroll into view and click using JavaScript
        driver.execute_script("arguments[0].scrollIntoView();", submit_button)
        driver.execute_script("arguments[0].click();", submit_button)

        print(" Clicked the 'Submit your application' button successfully!")
        return True

    except Exception as e:
        print(" Error clicking 'Submit your application':", e)
        return False
    
def auto_fill_checkboxes(driver):
    """
    Detects all checkbox questions, asks LLM for answers, and selects the correct checkboxes using execute_script.
    """
    try:
        # Find all checkbox-based questions
        checkbox_questions = driver.find_elements(By.XPATH, "//div[contains(@class, 'css-u74ql7')]/label")

        for question in checkbox_questions:
            question_text = question.text.strip()
            if question_text:
                print(f" Processing Question: {question_text}")

                # Ask LLM for an answer (Yes/No)
                answer = ask_llm(question_text, ["Yes", "No"]).strip().lower()

                # Find checkboxes related to this question
                checkboxes = question.find_elements(By.XPATH, ".//following-sibling::fieldset//input[@type='checkbox']")
                
                if checkboxes:
                    # Determine the correct index (0 = Yes, 1 = No)
                    index = 0 if "yes" in answer else 1
                    
                    # Click checkbox using JavaScript execution
                    driver.execute_script("arguments[0].click();", checkboxes[index])

                    print(f"✅ Selected '{answer.capitalize()}' for: {question_text}")
                else:
                    driver.execute_script("arguments[0].click();", checkboxes[0])
                    print(f"⚠️ No checkboxes found for: {question_text}")

        print(" All checkbox questions processed!")
    except Exception as e:
        print(f" Error: {e}")
def auto_fill_radio_buttons(driver):
    """
    Detects all radio button questions, asks LLM for answers, and selects the correct radio option using execute_script.
    """
    try:
        # Find all radio button groups
        radio_groups = driver.find_elements(By.XPATH, "//fieldset[@role='radiogroup']")

        for group in radio_groups:
            # Extract question text
            question_element = group.find_element(By.XPATH, ".//legend")
            question_text = question_element.text.strip() if question_element else "Unknown Question"
            
            print(f" Processing Question: {question_text}")

            # Ask LLM for an answer (Yes/No)
            answer = ask_llm(question_text, ["Yes", "No"]).strip().lower()

            # Find corresponding radio buttons
            radio_buttons = group.find_elements(By.XPATH, ".//input[@type='radio']")
            
            if radio_buttons:
                # Determine correct index (0 = Yes, 1 = No)
                index = 0 if "yes" in answer else 1

                # Click the radio button using JavaScript
                driver.execute_script("arguments[0].click();", radio_buttons[index])

                print(f" Selected '{answer.capitalize()}' for: {question_text}")
            else:
                print(f" No radio buttons found for: {question_text}")

        print(" All radio button questions processed!")
        return True
    except Exception as e:
        print(f" No radio button found : {e}")
        return False
def click_recaptcha(driver):
    try:
        # Switch to the reCAPTCHA iframe
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@title, 'reCAPTCHA')]"))
        )

        # Locate the reCAPTCHA checkbox
        recaptcha_checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "recaptcha-checkbox-border"))
        )

        # Click using JavaScript
        driver.execute_script("arguments[0].click();", recaptcha_checkbox)

        print(" Clicked the reCAPTCHA checkbox using JavaScript!")
        driver.switch_to.default_content()  # Switch back to the main page
        return True

    except Exception as e:
        print(" Failed to click reCAPTCHA:", e)
        return False
    

def fill_dropdowns(driver):
    wait=WebDriverWait(driver, 10)
    """Finds all dropdowns, extracts questions and options, queries the LLM, and selects answers."""
    try:
        dropdowns = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "select")))
        print(f" Found {len(dropdowns)} dropdowns.")

        for dropdown in dropdowns:
            question_text = ""

            # Find associated question (label, aria-labelledby, or nearby text)
            label = driver.find_elements(By.CSS_SELECTOR, f"label[for='{dropdown.get_attribute('id')}']")
            if label:
                question_text = label[0].text.strip()

            if not question_text:
                aria_labelledby = dropdown.get_attribute("aria-labelledby")
                aria_describedby = dropdown.get_attribute("aria-describedby")

                if aria_labelledby:
                    labelled_element = driver.find_element(By.ID, aria_labelledby)
                    question_text = labelled_element.text.strip()
                elif aria_describedby:
                    described_element = driver.find_element(By.ID, aria_describedby)
                    question_text = described_element.text.strip()

            if not question_text:
                parent = dropdown.find_element(By.XPATH, "./ancestor::*[self::div or self::form]")
                question_candidates = parent.find_elements(By.XPATH, ".//span | .//p | .//div")
                for elem in question_candidates:
                    if elem.text.strip():
                        question_text = elem.text.strip()
                        break

            question_text = question_text if question_text else "Question not found"

            # Extract options
            options = [option.text.strip() for option in dropdown.find_elements(By.TAG_NAME, "option") if option.text.strip()]

            # Send question & options to LLM
            llm_answer = ask_llm(question_text, options)

            print(f"\n Question: {question_text}")
            print(f" Available Options: {options}")
            print(f" LLM Answer: {llm_answer}")

            # Match the answer to available options
            if llm_answer in options:
                best_answer = llm_answer
            else:
                print(f"⚠ LLM Answer '{llm_answer}' not found in options. Selecting first valid option.")
                best_answer = options[19] if len(options) > 19 else options[0]

            # Scroll into view before selection
            driver.execute_script("arguments[0].scrollIntoView();", dropdown)
            time.sleep(0.5)  # Allow smooth scrolling

            # Open dropdown menu
            dropdown.click()
            time.sleep(0.5)  # Allow menu to open

            # Select the best answer using keyboard input
            dropdown.send_keys(best_answer)
            dropdown.send_keys(Keys.RETURN)  # Confirm selection
            print(f"✔ Selected: {best_answer}")

            time.sleep(1)  # Wait for selection to register

        print(" Successfully filled all dropdowns.")
        return True
    except Exception as e:
        print(f" Failed to fill dropdowns: {e}")
        return False
def scroll_until_jobs_load(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.randint(5, 10))  # Wait for new jobs to load

        # Get new scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")

        # Break if no new jobs are loaded
        if new_height == last_height:
            print("No more new jobs are loading.")
            break

        last_height = new_height  # Update last height

def handle_uploaded_resume(cv_path):
    if cv_path is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(cv_path.read())
            return tmp_file.name
    return None


def main():
    # st.set_page_config(page_title="Glassdoor Job Automation", layout="wide")
    # st.header("Automate Glassdoor Job Applications")
    
    
    if 'user_name' in st.session_state and 'job_title' in st.session_state and 'location' in st.session_state and 'apply_limit' in st.session_state and 'cv_path' in st.session_state:
        user_name = st.session_state.user_name
        job_title = st.session_state.job_title
        location = st.session_state.location
        apply_limit = st.session_state.apply_limit
        cv_path = st.session_state.cv_path

    if st.button("Submit & Apply Jobs"):
        options = uc.ChromeOptions()
        options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.popups": 1,  # Allow pop-ups
                "profile.default_content_setting_values.notifications": 1  # Allow notifications
            })

        if 'driver' not in st.session_state:
            st.session_state.driver = uc.Chrome(options=options)
        driver=st.session_state.driver
        load_glassdoor_session(driver,user_name)
        with st.spinner("Processing..."):
            if not cv_path:
                st.error(" No resume uploaded. Exiting...")
                return
            search_glassdoor_jobs(driver, job_title, location)
            applied_count = 0
            count=0
            while applied_count < apply_limit:
                click_cancel(driver)
                time.sleep(random.randint(2, 3))
                filter_jobs(driver)

                jobs = driver.find_elements(By.CLASS_NAME, "JobCard_jobCardContainer__arQlW")
                if not jobs:
                    print(" No jobs found. Exiting...")
                    break

                for job in jobs:
                    if applied_count >= apply_limit:
                        st.success(f"Successfully applied {apply_limit} jobs")
                        break

                    try:
                        job.click()  # Click on job listing
                        time.sleep(random.randint(2, 3))
                        click_cancel(driver)

                        if not click_easy_apply_buttons(driver):
                            print(" 'Easy Apply' button not found. Skipping job...")
                            continue
                        
                        # **Wait for new tab to open**
                        browser_windows = driver.window_handles
                        if len(browser_windows) > 1:
                            print(" New tab opened. Switching to it...")
                            driver.switch_to.window(browser_windows[1])
                            time.sleep(random.randint(2, 3))
                            fill_input_fields(driver)
                            upload_resume(driver,cv_path)

                            while True:
                                if click_continue(driver):
                                    upload_resume(driver,cv_path)
                                    # time.sleep(random.randint(1,2))
                                    fill_input_fields(driver)
                                    # time.sleep(random.randint(1,2))
                                    auto_fill_checkboxes(driver)
                                    # time.sleep(random.randint(1,2))
                                    auto_fill_radio_buttons(driver)
                                    # time.sleep(random.randint(1,2))
                                    fill_dropdowns(driver)
                                elif click_recaptcha(driver):
                                    time.sleep(random.randint(1,2))
                                    if click_submit_application(driver):
                                        applied_count += 1
                                        print(f" Applied to job {applied_count}/{apply_limit}")
                                        time.sleep(random.randint(5, 7))
                                        click_cancel(driver)
                                        close_modal_if_present(driver)
                                        driver.close()
                                        driver.switch_to.window(browser_windows[0])
                                        break
                                elif click_submit_application(driver):
                                    time.sleep(10)
                                    applied_count += 1
                                    print(f" Applied to job {applied_count}/{apply_limit}")
                                    close_modal_if_present(driver)
                                    click_cancel(driver)
                                    break 
                                else:
                                    print(" Error applying to job. Retrying...")
                                    break  # Prevent infinite loops

                        else:
                            print(" No new tab opened.")
                            time.sleep(random.randint(2, 3))
                            fill_input_fields(driver)
                            upload_resume(driver,cv_path)

                            while True:
                                if click_continue(driver):
                                    # time.sleep(random.randint(1,2))
                                    upload_resume(driver,cv_path)
                                    # time.sleep(random.randint(1,2))
                                    fill_input_fields(driver)
                                    # time.sleep(random.randint(1,2))
                                    auto_fill_checkboxes(driver)
                                    # time.sleep(random.randint(1,2))
                                    fill_dropdowns(driver)
                                    # time.sleep(random.randint(1,2))
                                    auto_fill_radio_buttons(driver)
                                    # time.sleep(random.randint(1,2))
                                elif click_recaptcha(driver):
                                    time.sleep(random.randint(1,2))
                                    if click_submit_application(driver):
                                        time.sleep(10)
                                        applied_count += 1
                                        print(f" Applied to job {applied_count}/{apply_limit}")
                                        close_modal_if_present(driver)
                                        click_cancel(driver)
                                        break
                                    
                                elif click_submit_application(driver):
                                    time.sleep(10)
                                    applied_count += 1
                                    print(f" Applied to job {applied_count}/{apply_limit}")
                                    close_modal_if_present(driver)
                                    click_cancel(driver)
                                    break          
                                else:
                                    print(" Error applying to job. Retrying...")
                                    break # Prevent infinite loops
                            
                    
                    except Exception as e:
                        print(f"Easy Apply Not Found. Finding Next Job {e}")
                        click_cancel(driver)
                        
                continue
            

            st.success(" Successfully applied to all jobs.")
            driver.quit()


if __name__ == "__main__":
    main()

