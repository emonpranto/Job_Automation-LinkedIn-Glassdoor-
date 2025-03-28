import pickle
import time
import os 
import random
import openai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from dotenv import load_dotenv
import streamlit as st
import undetected_chromedriver as uc
from utils.bot import ask_query
load_dotenv()


st.title("LinkedIn Job Auto Apply Bot")
st.sidebar.header("Settings")


driver=None
    

def query_gpt(question, options=None):
    answer = ask_query(question,options).ask()
    return answer


# Load LinkedIn session
def load_linkedin_session(driver,user_name):
    """Restores LinkedIn session using saved cookies."""
    driver.get("https://www.linkedin.com/")
    try:
        for cookie in pickle.load(open(f"{user_name}_linkedin.pkl", "rb")):
            driver.add_cookie(cookie)
        driver.get("https://www.linkedin.com/feed/")
        st.success("LinkedIn session restored!")
    except Exception as e:
        print(" Error loading session:", e)
        driver.quit()

# Set up pdf reader
# import pdfplumber

# def extract_cv_text(cv_path):
#     """Extracts text from a PDF CV."""
#     with pdfplumber.open(cv_path) as pdf:
#         text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
#     return text
# cv_path = r"D:\Smart Job Apply Assistant\Resume.pdf"
# cv_text = extract_cv_text(cv_path)
# # Generate answer from gpt
# # import generate

# # generate.api_key = os.getenv("OPENAI_API_KEY")
# openai.api_key=os.getenv('OPENAI_API_KEY')

# def query_gpt(question, cv_text, options=None):
#     """Generates an answer based on the given question and CV text."""

#     prompt = f"""
#             You are a CV analysis expert. Your task is to extract or infer answers to given questions based on the CV text provided. 

#             ### **Instructions:**
#             1. **Detect answer type:**
#             - If the question is about **experience, salary, years, age,notice period,education or any numerical data**, return an **integer** (default to `0` if not found).
#             - Otherwise, return a **short text answer**.
            
#             2. **Answering the question:**
#             - If the answer exists in the CV, return it.
#             - If not found:
#                 - Return `"N/A"` for text-based questions.
#                 - Return `0` for numerical questions (like `experience in years`, `salary`,`Notice period`,`Education` etc.).
            
#             3. **Handling Multiple-choice Questions:**
#             - If **options are provided**, return the closest matching answer from the option.
#             - If no exact match is found in the CV, return random answer from the option.

#             ---

#             ### **CV TEXT:**
#             {cv_text}

#             ### **QUESTION:**
#             {question}

#             ### **OPTIONS:**
#             {options}

#             ### **ANSWER:**
#             """

#     response = openai.chat.completions.create(  #  Correct new API call
#         model="gpt-4",
#         messages=[
#             {"role": "system", "content": "You are a CV analysis expert. Answer accurately and concisely."},
#             {"role": "user", "content": prompt}
#         ]
#     )
    
#     return response.choices[0].message.content.strip()
# # Function to query GPT-4 for answers
# cv_text= extract_cv_text(cv_path)
def fill_input_fields(driver):
    """Detect and fill out text fields dynamically based on CV content."""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "input"))
        )
        input_fields = driver.find_elements(By.CSS_SELECTOR, "input, textarea")
        print(input_fields)

        for field in input_fields:
            placeholder = field.get_attribute("placeholder") or ""
            aria_label = field.get_attribute("aria-label") or ""
            name_attr = field.get_attribute("name") or ""
            field_id = field.get_attribute("id") or ""

            try:
                label = field.find_element(By.XPATH, "./preceding-sibling::label").text
            except:
                label = ""

            field_identifier = (placeholder + " " + aria_label + " " + name_attr + " " + label + " " + field_id).strip().lower()
            print(field_identifier)

            # Skip already filled fields
            if field.get_attribute("value"):
                continue

            # Scroll to field, click to activate (if needed), and fill in value
            driver.execute_script("arguments[0].scrollIntoView();", field)
            field.click()
            field.clear()
            
            # Get value from GPT-4 based on field identifier
            answer = query_gpt(field_identifier)  
            print(f" Identified field: {field_identifier} -> Filling with: {answer}")

            field.send_keys(answer)
            field.send_keys(Keys.RETURN)
            time.sleep(1)  # Allow time for input field to register change

        # Special handling for mobile phone number field
        phone_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-required='true']"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", phone_field)
        phone_field.click()
        phone_field.clear()
        phone_field.send_keys("1712345678")  # Example Bangladeshi number without country code

        print(" Successfully filled all fields.")

    except Exception as e:
        print(" Error filling input fields :", e)



def fill_radio_buttons(driver):
    """Detects and answers radio button questions using GPT while following structured detection."""
    try:
        print("Trying to fill radio button questions...")

        # Wait for radio button fields to load
        radio_fieldsets = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//fieldset[@data-test-form-builder-radio-button-form-component='true']"))
        )

        for fieldset in radio_fieldsets:
            try:
                # Extract the question text
                question_element = fieldset.find_element(By.XPATH, ".//legend/span")
                question_text = question_element.text.strip().lower()
                print(f"Found question: {question_text}")

                # Extract radio options
                radio_labels = fieldset.find_elements(By.TAG_NAME, "label")
                radio_options = [label.text.lower().strip('') for label in radio_labels]

                # Handle LinkedIn Yes/No buttons (special case)
                yes_no_options = fieldset.find_elements(By.XPATH, ".//div[@data-test-text-selectable-option]")
                if yes_no_options:
                    print("Detected Yes/No format")
                    radio_options = ["yes, no"]

                print(f"Available options: {radio_options}")

                if not radio_options:
                    print("No options found for this question. Skipping...")
                    continue

                # Get the best answer from GPT
                best_answer = query_gpt(question_text, radio_options)
                best_answer = best_answer.lower().strip('')
                print(f"GPT Answer: {best_answer}")

                # Try to find the correct option using the first code's logic
                to_select = None
                i = 0

                for radio in radio_labels:
                    if best_answer in radio.text.lower():
                        to_select = radio_labels[i]
                    i += 1

                if to_select is None:
                    to_select = radio_labels[-1]  # Fallback to last option

                # Scroll and click the selected radio button
                driver.execute_script("arguments[0].scrollIntoView();", to_select)
                to_select.click()
                print(f"Selected: {to_select.text}")

                # Handle LinkedIn Yes/No case separately
                if yes_no_options:
                    yes_no_map = {"yes": "0", "no": "1"}
                    option_value = yes_no_map.get(best_answer, "1")  # Default to "no" if unsure
                    yes_no_button = fieldset.find_element(By.XPATH, f".//div[@data-test-text-selectable-option='{option_value}']")

                    driver.execute_script("arguments[0].scrollIntoView();", yes_no_button)
                    yes_no_button.click()
                    print(f"Selected: {best_answer}")

            except Exception as e:
                print(f"Error processing radio button fieldset: {e}")

    except Exception as e:
        print(f"No radio button fieldsets found or error occurred: {e}")

def click_button_with_js(driver, aria_label):
    """Clicks a button using JavaScript execution in Selenium, using aria-label."""
    script = f"document.querySelector(\"button[aria-label='{aria_label}']\").click();"
    driver.execute_script(script)

def fill_dropdowns(cv_text):
    """Detect and fill dropdown fields dynamically based on CV content."""
    try:
        dropdown_containers = driver.find_elements(By.CSS_SELECTOR, "div[data-test-text-entity-list-form-component]")
        
        for container in dropdown_containers:
            try:
                # Extract the question text from the label
                label_element = container.find_element(By.TAG_NAME, "label")
                question_text = label_element.text.strip()
            except:
                print(" Could not find label for dropdown.")
                continue  # Skip this dropdown if label is missing

            print(f" Dropdown Question: {question_text}")

            # Find the <select> element inside this container
            select_element = container.find_element(By.TAG_NAME, "select")

            # Extract the options available in the dropdown
            options = select_element.find_elements(By.TAG_NAME, "option")
            option_texts = [option.text.strip() for option in options if option.text.strip() != "Select an option"]

            print(f" Available options: {option_texts}")

            # Query the LLM for the best answer
            best_answer = query_gpt(question_text, cv_text,option_texts)

            # Select the best answer if available
            if best_answer in option_texts:
    # Scroll into view before selecting
                driver.execute_script("arguments[0].scrollIntoView();", select_element)
                
                # Open dropdown menu
                select_element.click()
                
                # Select the best answer
                select_element.send_keys(best_answer)
                select_element.send_keys(Keys.RETURN)  # Confirm selection if needed
                print(f"Selected option: {best_answer}")
            else:
                print(f"Best answer '{best_answer}' not found in options. Selecting first valid option.")
                
                # Scroll and open dropdown
                driver.execute_script("arguments[0].scrollIntoView();", select_element)
                select_element.click()

                # Select the first available option
                select_element.send_keys(option_texts[1])
                select_element.send_keys(Keys.RETURN) # Default to the first valid option

            time.sleep(1)  # Give time for selection to register

        print(" Successfully filled all dropdowns.")

    except Exception as e:
        print(" Error filling dropdowns:", e)
def find_and_select_dropdowns(driver):
    # Find all <select> elements (dropdowns) on the page
    select_elements = driver.find_elements(By.TAG_NAME, "select")

    if not select_elements:  # Ensure dropdowns exist
        print("No dropdowns found on the page.")
        return False

    for select_element in select_elements:
        # Get the ID of the dropdown (if available)
        dropdown_id = select_element.get_attribute('id')

        # Find the associated label safely
        question = None
        label_elements = driver.find_elements(By.XPATH, f"//label[@for='{dropdown_id}']")
        
        if label_elements:
            question = label_elements[0].text.strip()

        # If no label found, use the dropdown ID as a fallback
        if not question:
            question = f"Question for dropdown with ID: {dropdown_id or 'unknown'}"

        # Get all available options
        available_options = [option.text.strip() for option in select_element.find_elements(By.TAG_NAME, "option")]

        if not available_options:
            print(f"No options found for dropdown: {dropdown_id}")
            continue

        # Use GPT to find the correct option based on the question
        gpt_answer = query_gpt(question, available_options)

        # If GPT provided a valid answer, select the option
        if gpt_answer and gpt_answer in available_options:
            select = Select(select_element)
            try:
                select.select_by_visible_text(gpt_answer)
                print(f"Selected: {gpt_answer} for dropdown {dropdown_id}")
            except Exception as e:
                print(f"Error selecting option: {e}")
        else:
            print(f"No valid option found for question: {question}")

    return True  # Return True after processing all dropdowns
# Function to upload resume
def upload_resume(driver,cv_path):
    """Uploads a resume file if required."""
    try:
        upload_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
        if upload_inputs:
            upload_inputs[0].send_keys(cv_path)
            print(" CV uploaded successfully.")
        else:
            print(" No upload field found.")
    except Exception as e:
        print(" Error uploading CV:", e)

# Function to handle clicking Next/Submit buttons
def click_next_button(driver):
    """Clicks 'Next', 'Submit', or 'Done' if found, ensuring fields are completed."""
    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            if any(text in button.text for text in ["Next", "Continue","Not now","Close","Review","Not now"]):
                button.click()
                print(f" Clicked '{button.text}' button.")
                time.sleep(random.randint(2, 5))
                return True
        
        print(" No valid button found to click.")
        return False

    except Exception as e:
        print(" Error clicking button:", e)
        return False

# Easy apply function 
def click_easy_apply(driver):
    try:
        # Wait until Easy Apply button is visible and clickable
        easy_apply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jobs-apply-button') and span[text()='Easy Apply']]"))
        )
        
        # Click the button
        easy_apply_button.click()
        print(" Clicked 'Easy Apply' button.")
        time.sleep(random.randint(3, 7))  # Add delay to simulate human behavior
        return True
    except Exception as e:
        print(" Could not click 'Easy Apply' button:", e)
        return False


# Close pop up

def close_pop_up(driver):
    try:
        # Locate the modal overlay
        modal_overlay = driver.find_element(By.CLASS_NAME, "artdeco-modal-overlay")

        # Method 1: Click outside the pop-up modal
        ActionChains(driver).move_to_element_with_offset(modal_overlay, -50, -50).click().perform()
        print("Clicked outside the modal.")
        time.sleep(2)

        # Check if modal is still present
        if driver.find_elements(By.CLASS_NAME, "artdeco-modal-overlay"):
            # Method 2: Click the dismiss button (X)
            try:
                dismiss_button = driver.find_element(By.CLASS_NAME, "artdeco-modal__dismiss")
                dismiss_button.click()
                print("Clicked the dismiss button.")
                time.sleep(2)
            except:
                print("Dismiss button not found.")
        
        # Final fallback: Method 3 - Press 'Esc' key
        if driver.find_elements(By.CLASS_NAME, "artdeco-modal-overlay"):
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            print("Pressed the 'Esc' key.")
            time.sleep(2)
        return True

    except:
        print("No pop-up modal found or already closed.")
        return False
def click_submit_button(driver):
    """Find and click the 'Submit application' button."""
    try:
        # Wait for the Submit button to appear
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Submit application' or contains(span/text(), 'Submit ')]"))
        )

        # Scroll into view and click the button
        driver.execute_script("arguments[0].scrollIntoView();", submit_button)
        submit_button.click()
        
        print(" Successfully clicked 'Submit application' button.")
        return True

    except Exception as e:
        print(" Error clicking 'Submit application' button:", e)
        return False

def random_delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))
def click_cancel_button(driver):
    """Finds and clicks the 'Cancel' button on LinkedIn forms."""
    try:
        # Wait for the button to be clickable
        cancel_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Cancel']]"))
        )
        
        # Scroll into view and click
        driver.execute_script("arguments[0].scrollIntoView();", cancel_button)
        cancel_button.click()
        print(" Clicked 'Cancel' button.")
        return True

    except Exception as e:
        print(f" Error clicking 'Cancel' button: {e}")
        return False
    
def auto_fill_checkboxes(driver):
    """
    Detects all checkbox questions using the correct XPath structure, 
    asks the LLM for answers, and selects the correct checkboxes dynamically.
    """
    try:
        # Wait for all fieldsets that contain checkboxes
        fieldsets = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//fieldset[@data-test-checkbox-form-component='true']"))
        )

        for fieldset in fieldsets:
                # Get question text dynamically
                question_element = fieldset.find_element(By.XPATH, ".//legend/div[@data-test-checkbox-form-title='true']")
                question_text = question_element.text.strip() if question_element else "Unknown Question"

                print(f"Processing Question: {question_text}")

                # Ask LLM for an answer (Yes/No)
                answer = query_gpt(question_text, ["Yes", "No"]).strip().lower()

                # Find all checkboxes inside this fieldset
                checkboxes = fieldset.find_elements(By.XPATH, ".//input[@type='checkbox']")
                
                if checkboxes:
                    # Determine the correct index (0 = Yes, 1 = No)
                    index = 0 if "yes" in answer else 1

                    # Click checkbox using JavaScript execution
                    driver.execute_script("arguments[0].click();", checkboxes[index])

                    print(f" Selected '{answer.capitalize()}' for: {question_text}")
                else:
                    print(f" No checkboxes found for: {question_text}")

        print(" All checkbox questions processed successfully!")
    
    except Exception as e:
        print(f" Error: {e}")

def select_and_click_checkboxes(driver):
    try:    # Open the page you want to check

        try:# Find all div elements with the data-test-text-selectable-option attribute
            div_elements = driver.find_elements_by_xpath("//div[contains(@data-test-text-selectable-option, '')]")

            # Create a list to hold checkbox IDs
            checkbox_ids = []

            # Iterate through all div elements and get their associated checkbox IDs
            for div in div_elements:
                checkbox = div.find_elements(By.XPATH, ".//input[@type='checkbox']")
                checkbox_id = checkbox.get_attribute('id')
                checkbox_ids.append(checkbox_id)

            # Sort the checkbox IDs
            checkbox_ids.sort()

            # Now click each checkbox one by one based on the sorted ID
            for checkbox_id in checkbox_ids:
                checkbox = driver.find_elements(By.ID,checkbox_id)
                if not checkbox.is_selected():  # Check if the checkbox is already selected
                    checkbox.click()
                    print(f"Clicked checkbox with ID: {checkbox_id}")
            return True
        except Exception as e:
            div_elements = driver.find_elements(By.XPATH,"//div[contains(@data-test-text-selectable-option, '')]")

        # Create a list to hold div elements (for sorting by the data-test-text-selectable-option attribute)
            div_elements_sorted = sorted(div_elements, key=lambda div: div.get_attribute("data-test-text-selectable-option"))

            # Now, click each checkbox inside the sorted divs
            for div in div_elements_sorted:
                # Find the checkbox inside the div
                checkbox = div.find_elements(By.XPATH,".//input[@type='checkbox']")
                
                # Click the checkbox if it's not already selected
                if not checkbox.is_selected():
                    checkbox.click()
                    print(f"Clicked checkbox with ID: {checkbox.get_attribute('id')}")

            print(" All checkbox questions processed successfully!")   
            return True

    except Exception as e:
            print(f" Error: {e}")
            return False
            

def main():
    
    if 'user_name' in st.session_state and 'job_title' in st.session_state and 'location' in st.session_state and 'apply_limit' in st.session_state and 'cv_path' in st.session_state:
        user_name = st.session_state.user_name
        job_title = st.session_state.job_title
        location = st.session_state.location
        apply_limit = st.session_state.apply_limit
        cv_path = st.session_state.cv_path
    """Automates job applications for a specific role and location."""
    if st.button("Submit & Apply Jobs"):
        if 'driver' not in st.session_state:
            st.session_state.driver = uc.Chrome()
        driver=st.session_state.driver
        with st.spinner("Processing..."):
            load_linkedin_session(driver,user_name)


            driver.get(f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}")
            time.sleep(random.randint(5, 10))  # Simulate human behavior
            click_button_with_js(driver, "Easy Apply filter.")
            
            applied_count = 0
            
            while applied_count < apply_limit:
                applied_count = 0
                jobs = driver.find_elements(By.CLASS_NAME, "job-card-container__link")  # Find job listings
                if not jobs:
                    print(" No jobs found. Exiting...")
                    break

                for job in jobs:
                    if applied_count >= apply_limit:
                        break  # Stop when apply limit is reached

                    try:
                        job.click()
                        time.sleep(random.randint(3, 7))

                        # Step 1: Click Easy Apply button
                        if not click_easy_apply(driver):
                            print(" 'Easy Apply' button not found. Skipping job...")
                            continue

                        # Fill application form (first page)
                        fill_input_fields(driver)
                        upload_resume(driver,cv_path)
                        fill_dropdowns(driver)
                        fill_radio_buttons(driver)
                        auto_fill_checkboxes(driver)
                        find_and_select_dropdowns(driver)
                        select_and_click_checkboxes(driver)

                        # Step 2: Keep clicking "Next" until "Submit" appears
                        while True:
                            if click_next_button(driver):  # Click "Next" and continue filling fields
                                print(" Clicked 'Next' button, moving to the next page...")
                                click_cancel_button(driver)
                                fill_input_fields(driver)
                                upload_resume(driver,cv_path)
                                fill_dropdowns(driver)
                                fill_radio_buttons(driver)
                                click_next_button(driver)
                                auto_fill_checkboxes(driver)
                                find_and_select_dropdowns(driver)
                                select_and_click_checkboxes(driver)
                                time.sleep(5)  # Allow next page to load
                            elif click_submit_button(driver): # If "Submit" appears, submit and close modal
                                applied_count += 1  
                                print(f" Successfully applied to {applied_count}/{apply_limit} jobs.")
                                print(" Found 'Submit' button, applying now...")
                                time.sleep(6)
                                close_pop_up(driver)  
                                click_next_button(driver) 
                                break  # Stop loop after submitting
                            else:
                                # close_pop_up(driver)  
                                # click_next_button(driver) 
                                applied_count += 1  
                                print(f" Successfully applied to {applied_count}/{apply_limit} jobs.")
                                break  # Exit if neither button is found

                    except Exception as e:
                        print(" Error applying:", e)
                        continue

                # Scroll down to load more jobs
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                time.sleep(random.randint(5, 10))

            print(f" Finished applying to {applied_count} jobs.")
            driver.quit()


if __name__ == "__main__":
    main()