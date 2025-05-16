import os
import importlib.util
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from datetime import datetime
import json
import traceback
import logging



logger = logging.getLogger(__name__)
def run_selenium_test(testcase_file, test_case_id=None, test_case_name=None):
    result = {
        "testCaseId": test_case_id or os.path.basename(testcase_file).replace('.py', ''),
        "name": test_case_name or os.path.basename(testcase_file).replace('.py', '').replace('_', ' ').title(),
        "response": {
            "steps": [],
            "summary": {
                "totalSteps": 0,
                "passed": 0,
                "failed": 0,
                "successRate": 0,
                "status": "PASSED"
            }
        }
    }

    # File existence check
    if not os.path.isfile(testcase_file):
        return create_error_result(result, f"Test case file {testcase_file} does not exist")

    # Load test case module
    try:
        spec = importlib.util.spec_from_file_location("test_case", testcase_file)
        if spec is None or spec.loader is None:
            return create_error_result(result, f"Failed to create module spec from {testcase_file}")
            
        testcase = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(testcase)
        
        if not hasattr(testcase, 'run_test'):
            return create_error_result(result, f"Test case file {testcase_file} missing 'run_test' function")
            
    except Exception as e:
        return create_error_result(result, f"Failed to load test case: {str(e)}")

    # Configure Chrome options for low resource usage
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument('--headless=new')  # Enable headless mode
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # Disable GPU for headless
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")  # Set consistent window size
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = None
    current_step_debug = []

    def log_debug(message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        current_step_debug.append(f"[{timestamp}] {message}")

    def print_step_result(step_num, description, success, error_msg=""):
        nonlocal result
        status = "PASSED" if success else "FAILED"
        error = None if success else clean_error_message(error_msg)
        
        step_result = {
            "step": step_num,
            "description": description,
            "status": status,
            "debug": current_step_debug.copy(),
            "error": error
        }
        
        result["response"]["steps"].append(step_result)
        
        if success:
            result["response"]["summary"]["passed"] += 1
        else:
            result["response"]["summary"]["failed"] += 1
            result["response"]["summary"]["status"] = "FAILED"
        
        current_step_debug.clear()

    try:
        # Initialize WebDriver
        logger.debug(f"Initializing Chrome WebDriver for test case {test_case_id}")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.implicitly_wait(5)
        
        # Run the test case
        logger.debug(f"Starting test execution: {result['name']}")
        testcase.run_test(driver, log_debug, print_step_result)

    except WebDriverException as e:
        error_msg = clean_error_message(str(e))
        logger.error(f"WebDriver error in test case {test_case_id}: {error_msg}")
        print_step_result(
            len(result["response"]["steps"]) + 1,
            "Test execution",
            False,
            error_msg
        )
        
    except Exception as e:
        error_msg = clean_error_message(traceback.format_exc())
        logger.error(f"Unexpected error in test case {test_case_id}: {error_msg}")
        print_step_result(
            len(result["response"]["steps"]) + 1,
            "Test execution",
            False,
            error_msg
        )

    finally:
        # Calculate summary
        result["response"]["summary"]["totalSteps"] = len(result["response"]["steps"])
        if result["response"]["summary"]["totalSteps"] > 0:
            result["response"]["summary"]["successRate"] = int(
                (result["response"]["summary"]["passed"] / result["response"]["summary"]["totalSteps"]) * 100
            )
        
        # Clean up WebDriver
        if driver:
            try:
                driver.quit()
                logger.debug(f"WebDriver quit for test case {test_case_id}")
            except Exception as e:
                logger.error(f"Error quitting WebDriver for test case {test_case_id}: {str(e)}")

    return json.dumps(result, indent=2)
def clean_error_message(error_msg):
    """Simplify and clean up error messages"""
    if not error_msg:
        return ""  # Return empty string instead of None
        
    # Remove stack traces for common Selenium errors
    if "Stacktrace:" in error_msg:
        error_msg = error_msg.split("Stacktrace:")[0].strip()
    
    # Remove DevTools listening messages
    if "DevTools listening on" in error_msg:
        error_msg = error_msg.split("DevTools listening on")[0].strip()
    
    # Common error pattern cleanup
    error_msg = error_msg.replace("Message:", "").strip()
    
    return error_msg[:500]  # Limit error message length

def create_error_result(result, error_message):
    """Create an error result structure"""
    result["response"]["summary"]["status"] = "ERROR"
    result["response"]["steps"].append({
        "step": 1,
        "description": "Test initialization",
        "status": "FAILED",
        "debug": [error_message],
        "error": error_message
    })
    result["response"]["summary"]["totalSteps"] = 1
    result["response"]["summary"]["failed"] = 1
    result["response"]["summary"]["successRate"] = 0
    return json.dumps(result, indent=2)