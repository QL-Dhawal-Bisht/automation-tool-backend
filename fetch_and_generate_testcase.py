import os
import requests
import argparse
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def escape_string(s: str) -> str:
    """Escape string for use in Python code."""
    return s.replace('"', '\\"').replace("'", "\\'")

def fetch_testcase(testcase_id: int, api_url: str = "http://localhost:8000") -> dict:
    """
    Fetch a test case object from the Supabase API.
    
    Args:
        testcase_id (int): ID of the test case to fetch.
        api_url (str): Base URL of the API (default: http://localhost:8000).
    
    Returns:
        dict: Test case object from the API.
    
    Raises:
        Exception: If the API request fails or response is invalid.
    """
    try:
        endpoint = f"{api_url}/testcase/{testcase_id}"
        logger.debug(f"Fetching test case from {endpoint}")
        response = requests.get(endpoint, headers={"Accept": "application/json"}, timeout=10)
        response.raise_for_status()
        
        testcase_data = response.json()
        logger.debug(f"Received test case data: {testcase_data}")
        if not isinstance(testcase_data, dict) or 'name' not in testcase_data:
            raise ValueError("Invalid test case response: Missing 'name'")
        
        return testcase_data
    
    except requests.RequestException as e:
        logger.error(f"Failed to fetch test case: {str(e)}")
        raise Exception(f"API error: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid test case data: {str(e)}")
        raise Exception(f"Invalid data: {str(e)}")

def generate_testcase_file(testcase: dict, output_dir: str = "testcases") -> str:
    """
    Generate a Selenium test case file from a test case object.
    
    Args:
        testcase (dict): Test case object with 'name' and 'actions'.
        output_dir (str): Directory to save the file (default: testcases).
    
    Returns:
        str: Path to the generated test case file.
    
    Raises:
        Exception: If file writing fails.
    """
    try:
        # Ensure output directory exists
        logger.debug(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract test case name and actions
        test_name = testcase.get('name', 'testcase').lower().replace(' ', '_')
        actions = testcase.get('actions', [])
        logger.debug(f"Generating file for test case: {test_name}, actions: {len(actions)}")
        
        # File header and imports
        file_content = [
            f"# Selenium Test: {test_name}",
            "from selenium.webdriver.common.by import By",
            "from selenium.webdriver.support.ui import WebDriverWait",
            "from selenium.webdriver.support import expected_conditions as EC",
            "import time",
            "",
            "def run_test(driver, log_debug, print_step_result):",
            "    wait = WebDriverWait(driver, 10)",
            "    driver.implicitly_wait(5)",
            "    driver.maximize_window()",
            "",
            "    try:"
        ]

        # Generate code for each action
        for index, action in enumerate(actions, 1):
            action_type = action.get('type')
            description = escape_string(action.get('description', f"Step {index}"))
            css_selector = escape_string(action.get('element', {}).get('uniqueSelector', ''))
            xpath = escape_string(action.get('element', {}).get('xpath', ''))
            value = escape_string(str(action.get('value', '')))
            url = escape_string(action.get('url', ''))
            scroll_x = action.get('scrollX', 0)
            scroll_y = action.get('scrollY', 0)
            
            logger.debug(f"Processing action {index}: {action_type}, description: {description}")
            file_content.append(f"        # Step {index}: {description}")
            file_content.append(f"        log_debug('{description}')")
            
            if action_type == 'navigate' and url:
                file_content.extend([
                    "        try:",
                    f"            driver.get('{url}')",
                    "            time.sleep(3)",
                    f"            print_step_result({index}, '{description}', True)",
                    "        except Exception as e:",
                    f"            print_step_result({index}, '{description}', False, str(e))"
                ])
            
            elif action_type == 'change' and (css_selector or xpath) and value is not None:
                file_content.extend([
                    "        try:",
                ])
                
                if css_selector:
                    file_content.extend([
                        f"            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '{css_selector}')))",
                        "            driver.execute_script(\"arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});\", element)",
                        "            time.sleep(1)",
                        "            element.clear()",
                        f"            element.send_keys('{value}')",
                        f"            print_step_result({index}, '{description}', True)",
                    ])
                elif xpath:
                    file_content.extend([
                        f"            element = wait.until(EC.presence_of_element_located((By.XPATH, '{xpath}')))",
                        "            driver.execute_script(\"arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});\", element)",
                        "            time.sleep(1)",
                        "            element.clear()",
                        f"            element.send_keys('{value}')",
                        f"            print_step_result({index}, '{description}', True)",
                    ])
                
                file_content.extend([
                    "        except Exception as e:",
                    f"            print_step_result({index}, '{description}', False, str(e))"
                ])
            
            elif action_type == 'click' and (css_selector or xpath):
                file_content.extend([
                    "        try:",
                ])
                
                if css_selector:
                    file_content.extend([
                        f"            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '{css_selector}')))",
                        "            driver.execute_script(\"arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});\", element)",
                        "            time.sleep(1)",
                        "            element.click()",
                        f"            print_step_result({index}, '{description}', True)",
                    ])
                elif xpath:
                    file_content.extend([
                        f"            element = wait.until(EC.element_to_be_clickable((By.XPATH, '{xpath}')))",
                        "            driver.execute_script(\"arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});\", element)",
                        "            time.sleep(1)",
                        "            element.click()",
                        f"            print_step_result({index}, '{description}', True)",
                    ])
                
                file_content.extend([
                    "        except Exception as e:",
                    f"            print_step_result({index}, '{description}', False, str(e))"
                ])
            
            elif action_type == 'scroll' and (scroll_x is not None) and (scroll_y is not None):
                file_content.extend([
                    "        try:",
                    f"            driver.execute_script(f\"window.scrollTo({scroll_x}, {scroll_y})\")",
                    "            time.sleep(1)",
                    f"            print_step_result({index}, '{description}', True)",
                    "        except Exception as e:",
                    f"            print_step_result({index}, '{description}', False, str(e))"
                ])
            
            else:
                file_content.extend([
                    "        try:",
                    f"            log_debug('Unsupported action type: {action_type}')",
                    f"            print_step_result({index}, '{description}', False, 'Unsupported action type')",
                    "        except Exception as e:",
                    f"            print_step_result({index}, '{description}', False, str(e))"
                ])
            
            file_content.append("")  # Blank line between steps

        # Global error handling
        file_content.extend([
            "    except Exception as e:",
            "        log_debug(f\"Test execution aborted: {str(e)}\")",
            "        driver.save_screenshot(\"test_failure.png\")",
            "        raise"
        ])

        # Write to file
        file_name = os.path.join(output_dir, f"test_{test_name}.py")
        logger.debug(f"Writing test case file: {file_name}")
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write('\n'.join(file_content))
        
        logger.info(f"Generated test case file: {file_name}")
        return file_name
    
    except Exception as e:
        logger.error(f"Failed to generate test case file: {str(e)}")
        raise Exception(f"File generation error: {str(e)}")

def main():
    """Parse CLI arguments and generate test case file."""
    parser = argparse.ArgumentParser(description="Fetch and generate Selenium test case file.")
    parser.add_argument("--id", type=int, required=True, help="Test case ID")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", type=str, default="testcases", help="Output directory")
    args = parser.parse_args()

    try:
        testcase = fetch_testcase(args.id, args.url)
        file_path = generate_testcase_file(testcase, args.output)
        print(f"Test case file generated: {file_path}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()