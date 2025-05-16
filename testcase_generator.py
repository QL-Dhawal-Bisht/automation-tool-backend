import os
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
logger = logging.getLogger(__name__)

def escape_string(s: str) -> str:
    return s.replace('"', '\\"').replace("'", "\\'")

def generate_testcase_file(testcase: dict, output_dir: str = "testcases") -> str:
    try:
        os.makedirs(output_dir, exist_ok=True)
        test_name = testcase.get('name', 'testcase').lower().replace(' ', '_')
        actions = testcase.get('actions', [])

        # Find the login page URL from change or click actions
        login_url = None
        for action in actions:
            if action.get('type') in ['change', 'click'] and action.get('url'):
                login_url = action.get('url')
                break

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

        step_index = 1

        # Add initial navigation to login page if found
        if login_url:
            login_url = escape_string(login_url)
            file_content.extend([
                f"        # Step {step_index}: Navigate to login page",
                f"        log_debug('Navigate to login page')",
                "        try:",
                f"            driver.get('{login_url}')",
                "            time.sleep(3)",
                f"            print_step_result({step_index}, 'Navigate to login page', True)",
                "        except Exception as e:",
                f"            print_step_result({step_index}, 'Navigate to login page', False, str(e))",
                ""
            ])
            step_index += 1

        # Process non-navigate actions
        for action in actions:
            action_type = action.get('type')
            if action_type == 'navigate':
                continue  # Skip navigate actions to avoid incorrect navigation

            description = escape_string(action.get('description', f"Step {step_index}"))
            css_selector = escape_string(action.get('element', {}).get('uniqueSelector', ''))
            xpath = escape_string(action.get('element', {}).get('xpath', ''))
            value = escape_string(str(action.get('value', '')))
            scroll_x = action.get('scrollX', 0)
            scroll_y = action.get('scrollY', 0)

            file_content.append(f"        # Step {step_index}: {description}")
            file_content.append(f"        log_debug('{description}')")

            if action_type == 'change' and (css_selector or xpath) and value is not None:
                file_content.extend(["        try:"])
                if css_selector:
                    file_content.extend([
                        f"            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '{css_selector}')))",
                        "            driver.execute_script(\"arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});\", element)",
                        "            time.sleep(1)",
                        "            element.clear()",
                        f"            element.send_keys('{value}')",
                        f"            print_step_result({step_index}, '{description}', True)",
                    ])
                elif xpath:
                    file_content.extend([
                        f"            element = wait.until(EC.presence_of_element_located((By.XPATH, '{xpath}')))",
                        "            driver.execute_script(\"arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});\", element)",
                        "            time.sleep(1)",
                        "            element.clear()",
                        f"            element.send_keys('{value}')",
                        f"            print_step_result({step_index}, '{description}', True)",
                    ])
                file_content.extend([
                    "        except Exception as e:",
                    f"            print_step_result({step_index}, '{description}', False, str(e))"
                ])
            elif action_type == 'click' and (css_selector or xpath):
                file_content.extend(["        try:"])
                if css_selector:
                    file_content.extend([
                        f"            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '{css_selector}')))",
                        "            driver.execute_script(\"arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});\", element)",
                        "            time.sleep(1)",
                        "            element.click()",
                        f"            print_step_result({step_index}, '{description}', True)",
                    ])
                elif xpath:
                    file_content.extend([
                        f"            element = wait.until(EC.element_to_be_clickable((By.XPATH, '{xpath}')))",
                        "            driver.execute_script(\"arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});\", element)",
                        "            time.sleep(1)",
                        "            element.click()",
                        f"            print_step_result({step_index}, '{description}', True)",
                    ])
                file_content.extend([
                    "        except Exception as e:",
                    f"            print_step_result({step_index}, '{description}', False, str(e))"
                ])
            elif action_type == 'scroll':
                file_content.extend([
                    "        try:",
                    f"            driver.execute_script(f\"window.scrollTo({scroll_x}, {scroll_y})\")",
                    "            time.sleep(1)",
                    f"            print_step_result({step_index}, '{description}', True)",
                    "        except Exception as e:",
                    f"            print_step_result({step_index}, '{description}', False, str(e))"
                ])
            else:
                file_content.extend([
                    "        try:",
                    f"            log_debug('Unsupported action type: {action_type}')",
                    f"            print_step_result({step_index}, '{description}', False, 'Unsupported action type')",
                    "        except Exception as e:",
                    f"            print_step_result({step_index}, '{description}', False, str(e))"
                ])
            file_content.append("")
            step_index += 1

        file_content.extend([
            "    except Exception as e:",
            "        log_debug(f\"Test execution aborted: {str(e)}\")",
            "        driver.save_screenshot(\"test_failure.png\")",
            "        raise"
        ])

        file_name = os.path.join(output_dir, f"test_{test_name}.py")
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write('\n'.join(file_content))

        logger.info(f"Generated test case file: {file_name}")
        return file_name

    except Exception as e:
        logger.error(f"Failed to generate test case file: {str(e)}")
        raise