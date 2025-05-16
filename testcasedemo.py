# Selenium Test: new login flow
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# Set up ChromeDriver using webdriver_manager
options = webdriver.ChromeOptions()
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 10)
driver.implicitly_wait(5)
driver.maximize_window()

passed_steps = 0
failed_steps = 0
step_results = []

def print_step_result(step_num, description, success, error_msg=""):
    if success:
        print(f"✅ Step {step_num}: {description} - PASSED")
        step_results.append(True)
    else:
        print(f"❌ Step {step_num}: {description} - FAILED ({error_msg})")
        step_results.append(False)
    return success

try:
    # Step 1: Navigate to https://practicetestautomation.com/practice-test-login/
    print("DEBUG: Navigating to https://practicetestautomation.com/practice-test-login/")
    try:
        driver.get("https://practicetestautomation.com/practice-test-login/")
        time.sleep(3)
        print_step_result(1, "Navigate to https://practicetestautomation.com/practice-test-login/", True)
    except Exception as e:
        print_step_result(1, "Navigate to https://practicetestautomation.com/practice-test-login/", False, str(e))

    # Step 2: Set username to \"student\"
    print("DEBUG: Entering value 'student' into element with selector #username or xpath //input[@id=\"username\"]")
    try:
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#username")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(1)
        element.clear()
        element.send_keys("student")
        print_step_result(2, "Set username to \"student\"", True)
    except Exception as e:
        print("DEBUG: CSS selector failed, trying XPath")
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id=\"username\"]")))
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            element.clear()
            element.send_keys("student")
            print_step_result(2, "Set username to \"student\"", True)
        except Exception as e:
            print_step_result(2, "Set username to \"student\"", False, str(e))

    # Step 3: Enter password: ***********
    print("DEBUG: Entering value 'Password123' into element with selector #password or xpath //input[@id=\"password\"]")
    try:
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#password")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(1)
        element.clear()
        element.send_keys("Password123")
        print_step_result(3, "Enter password: ***********", True)
    except Exception as e:
        print("DEBUG: CSS selector failed, trying XPath")
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id=\"password\"]")))
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            element.clear()
            element.send_keys("Password123")
            print_step_result(3, "Enter password: ***********", True)
        except Exception as e:
            print_step_result(3, "Enter password: ***********", False, str(e))

    # Step 4: Click on submit
    print("DEBUG: Clicking element with selector #submit or xpath //button[@id=\"submit\"]")
    try:
        element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#submit")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(1)
        element.click()
        print_step_result(4, "Click on submit", True)
    except Exception as e:
        print("DEBUG: CSS selector failed, trying XPath")
        try:
            element = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@id=\"submit\"]")))
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            element.click()
            print_step_result(4, "Click on submit", True)
        except Exception as e:
            print_step_result(4, "Click on submit", False, str(e))

    # Step 5: Navigated to https://practicetestautomation.com/logged-in-successfully/
    print("DEBUG: Navigating to https://practicetestautomation.com/logged-in-successfully/")
    try:
        driver.get("https://practicetestautomation.com/logged-in-successfully/")
        time.sleep(3)
        print_step_result(5, "Navigated to https://practicetestautomation.com/logged-in-successfully/", True)
    except Exception as e:
        print_step_result(5, "Navigated to https://practicetestautomation.com/logged-in-successfully/", False, str(e))

    passed_steps = sum(1 for result in step_results if result)
    failed_steps = len(step_results) - passed_steps
    print(f"\n=== TEST SUMMARY ===")
    print(f"Test Case: new login flow")
    print(f"Total Steps: {len(step_results)}")
    print(f"Passed: {passed_steps}")
    print(f"Failed: {failed_steps}")
    print(f"Success Rate: {int((passed_steps/len(step_results))*100) if len(step_results) > 0 else 0}%")
    print("="*20)
    if failed_steps == 0:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")

except Exception as e:
    print(f"❌ Test execution aborted: {str(e)}")
    driver.save_screenshot("test_failure.png")
finally:
    input("Press Enter to close the browser...")
    driver.quit()