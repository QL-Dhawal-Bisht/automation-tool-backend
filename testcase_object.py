import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from testcase_generator import generate_testcase_file
from app import run_selenium_test
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Test Case API",
    description="API for managing test cases stored in Supabase.",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update to specific frontend URL in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize Supabase client
SUPABASE_URL = "https://mggvulbvgteamxghjoce.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1nZ3Z1bGJ2Z3RlYW14Z2hqb2NlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2OTkxMjcsImV4cCI6MjA2MDI3NTEyN30.0mByptXZXPckzwAlEfnIFKAK219lUQ2OZLQwZH9hE4Y"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Pydantic model for action objects within actions list
class Action(BaseModel):
    url: Optional[str] = None
    type: Optional[str] = None
    tabId: Optional[int] = None
    value: Optional[str] = None
    element: Optional[Dict[str, Any]] = None
    sequence: Optional[int] = None
    timestamp: Optional[int] = None
    description: Optional[str] = None
    uniqueId: Optional[str] = None
    previousUrl: Optional[str] = None

# Pydantic model for test case
class TestCase(BaseModel):
    testcaseId: int = Field(..., alias="id")
    title: Optional[str] = Field(None, alias="name")
    description: Optional[str] = None
    input: Optional[str] = None
    expected_output: Optional[str] = None
    actions: Optional[List[Action]] = None
    response: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True

# Pydantic model for test case response
class TestCaseResponse(BaseModel):
    success: bool
    data: TestCase

# Root endpoint
@app.get(
    "/",
    summary="API Root",
    description="Returns a welcome message indicating the API is running."
)
async def root():
    return {"message": "Test Case API is running"}

# Get test case by ID and run test
@app.get(
    "/testcase/{testcaseId}",
    response_model=TestCaseResponse,
    summary="Run Test Case by ID",
    description="Runs a test case by ID and stores the result in test_cases.response."
)
async def get_testcase(testcaseId: int):
    try:
        # Fetch test case from Supabase
        response = supabase.table("test_cases").select("*").eq("id", testcaseId).execute()
        logger.debug(f"Supabase response: {response.data}")
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Test case not found")
        if len(response.data) > 1:
            raise HTTPException(status_code=500, detail="Multiple test cases found for the given ID")

        testcase = response.data[0]

        # Generate test case file
        try:
            output_path = generate_testcase_file(testcase, output_dir="testcases")
            logger.info(f"Test case file generated at: {output_path}")
        except Exception as e:
            logger.error(f"Failed to generate test case: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate test case file: {str(e)}")

        # Run the test case using run_selenium_test from app.py
        try:
            json_result = run_selenium_test(
                testcase_file=output_path,
                test_case_id=str(testcase["id"]),
                test_case_name=testcase.get("name", f"Test Case {testcaseId}")
            )
            logger.info(f"Test case {testcaseId} executed successfully")
            
            # Parse the JSON result
            try:
                result_data = json.loads(json_result)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse test result JSON: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Invalid test result format: {str(e)}")
            
            # Store the parsed result in test_cases.response
            try:
                supabase.table("test_cases").update({
                    "response": result_data
                }).eq("id", testcaseId).execute()
                logger.info(f"Test result stored in test_cases.response for testcase_id: {testcaseId}")
            except Exception as e:
                logger.error(f"Failed to update test_cases.response: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to store test result: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to run test case {testcaseId}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to run test case: {str(e)}")

        # Fetch updated test case to return
        updated_response = supabase.table("test_cases").select("*").eq("id", testcaseId).execute()
        if not updated_response.data:
            raise HTTPException(status_code=404, detail="Test case not found after update")
        
        return {"success": True, "data": updated_response.data[0]}

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid test case data: {str(e)}")
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get test result by testcase ID
@app.get(
    "/testresult/{testcaseId}",
    summary="Get Test Result",
    description="Retrieve the JSON test result for a specific test case ID from test_cases.response."
)
async def get_test_result(testcaseId: int):
    
    try:
        response = supabase.table("test_cases").select("response").eq("id", testcaseId).execute()
        logger.debug(f"Supabase test result response: {response.data}")
        
        if not response.data or not response.data[0]["response"]:
            raise HTTPException(status_code=404, detail="Test result not found for this test case ID")
        
        return response.data[0]["response"]
    
    except Exception as e:
        logger.error(f"Error retrieving test result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get(
    "/testcases/run-all",
    summary="Run All Test Cases",
    description="Runs all test cases in parallel with optimized resource usage."
)
async def run_all_testcases():
    try:
        # Fetch all test cases from Supabase
        response = supabase.table("test_cases").select("*").execute()
        logger.debug(f"Supabase response: {response.data}")
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No test cases found")

        testcases = response.data
        results = []

        # Determine max workers based on CPU cores (leave 1 core free)
        max_workers = max(1, multiprocessing.cpu_count() - 1)
        max_workers = min(max_workers, len(testcases))  # Don't exceed number of test cases

        logger.info(f"Running {len(testcases)} test cases with {max_workers} workers")

        # Run test cases in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all test cases
            future_to_testcase = {
                executor.submit(run_single_testcase, testcase): testcase
                for testcase in testcases
            }

            # Collect results
            for future in as_completed(future_to_testcase):
                testcase = future_to_testcase[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Test case {testcase['id']} failed: {str(e)}")
                    results.append({
                        "testcaseId": testcase["id"],
                        "success": False,
                        "error": str(e)
                    })

        return {
            "success": True,
            "data": results,
            "summary": {
                "total": len(testcases),
                "successful": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"])
            }
        }

    except Exception as e:
        logger.error(f"Error running all test cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Helper function to run a single test case
def run_single_testcase(testcase):
    try:
        testcase_id = testcase["id"]
        
        # Generate test case file
        output_path = generate_testcase_file(testcase, output_dir="testcases")
        logger.info(f"Test case file generated at: {output_path}")

        # Run the test case
        json_result = run_selenium_test(
            testcase_file=output_path,
            test_case_id=str(testcase_id),
            test_case_name=testcase.get("name", f"Test Case {testcase_id}")
        )

        # Parse the JSON result
        result_data = json.loads(json_result)

        # Store the result in Supabase
        supabase.table("test_cases").update({
            "response": result_data
        }).eq("id", testcase_id).execute()

        return {
            "testcaseId": testcase_id,
            "success": True,
            "data": result_data
        }

    except Exception as e:
        logger.error(f"Failed to run test case {testcase.get('id')}: {str(e)}")
        return {
            "testcaseId": testcase.get("id"),
            "success": False,
            "error": str(e)
        }