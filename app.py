import keys
import time
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def get_grade():
    url = "https://adfs.uwaterloo.ca/adfs/ls/idpinitiatedsignon.aspx?LoginToRP=urn:quest.ss.apps.uwaterloo.ca"

    # open quest window
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.get(url)
    driver.maximize_window()

    # enter username
    username_field = driver.find_element(By.ID, "userNameInput")
    username_field.send_keys("asoman@uwaterloo.ca")

    next_button = driver.find_element(By.ID, "nextButton")
    next_button.click()

    # enter password
    password_field = driver.find_element(By.ID, "passwordInput")
    password_field.send_keys("XXX") #personal password

    submit_button = driver.find_element(By.ID, "submitButton")
    submit_button.click()

    # show it's your device
    wait = WebDriverWait(driver, 30)
    trust_me_button = wait.until(ec.presence_of_element_located((By.ID, "trust-browser-button")))
    trust_me_button.click()

    # get to the grades
    grades_tile = wait.until(ec.presence_of_element_located((By.ID, "win0divPTNUI_LAND_REC_GROUPLET$0")))
    grades_tile.click()

    # get into spring 2024
    time.sleep(5)
    driver.switch_to.frame("main_target_win0")
    term_button = wait.until(ec.presence_of_element_located((By.ID, "SSR_DUMMY_RECV1$sels$1$$0")))
    term_button.click()
    continue_button = driver.find_element(By.ID, "UW_DRVD_SSS_SCT_SSR_PB_GO")
    continue_button.click()

    time.sleep(5)

    # find all the grades info (course name + grade) and print
    subj1_name = driver.find_element(By.ID, "CLS_LINK$span$0")
    subj2_name = driver.find_element(By.ID, "CLS_LINK$span$1")
    subj3_name = driver.find_element(By.ID, "CLS_LINK$span$2")
    subj4_name = driver.find_element(By.ID, "CLS_LINK$span$3")
    subj5_name = driver.find_element(By.ID, "CLS_LINK$span$4")

    subj1_grade = driver.find_element(By.ID, "STDNT_ENRL_SSV1_CRSE_GRADE_OFF$0")
    subj2_grade = driver.find_element(By.ID, "STDNT_ENRL_SSV1_CRSE_GRADE_OFF$1")
    subj3_grade = driver.find_element(By.ID, "STDNT_ENRL_SSV1_CRSE_GRADE_OFF$2")
    subj4_grade = driver.find_element(By.ID, "STDNT_ENRL_SSV1_CRSE_GRADE_OFF$3")
    subj5_grade = driver.find_element(By.ID, "STDNT_ENRL_SSV1_CRSE_GRADE_OFF$4")

    grade_dict = {subj1_name.text: subj1_grade.text,
                  subj2_name.text: subj2_grade.text,
                  subj3_name.text: subj3_grade.text,
                  subj4_name.text: subj4_grade.text,
                  subj5_name.text: subj5_grade.text
                  }
    
    driver.close()

    return grade_dict

@app.route("/sms", methods=['POST'])
def sms_reply():
    from_msg = request.form.get('Body')
    response = MessagingResponse()

    if "grades" in from_msg.lower():
        grades = get_grade()
        grades_message = "\n".join([f"{course}: {grade}" for course, grade in grades.items()])
        response.message(f"Grades:\n{grades_message}")
    else:
        response.message("Please re-enter 'grades'...")

    client = Client(keys.account_sid, keys.auth_token)

    to_message = client.messages.create(
        body=str(response),
        from_=keys.twilio_number,
        to=keys.target_number
    )

    return str(to_message)

if __name__ == "__main__":
    app.run(port=5002,debug=True)
