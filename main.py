from fastmcp import FastMCP
import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("mcp-linkedin")
logger = logging.getLogger(__name__)

def get_client():
    """Returns an httpx client configured for the LinkedIn Data API"""
    headers = {
        'x-rapidapi-key': os.getenv("RAPIDAPI_KEY"),
        'x-rapidapi-host': "linkedin-data-api.p.rapidapi.com"
    }
    return httpx.Client(headers=headers)

@mcp.tool()
def search_jobs(keywords: str, limit: int = 10, location: str = 'Israel', format_output: bool = True) -> dict:
    """
    Search for jobs on LinkedIn and return as a dictionary.
    
    :param keywords: Job search keywords
    :param limit: Maximum number of job results
    :param location: Location filter
    :param format_output: Whether to return formatted string or raw dictionary
    :return: Dictionary of job listings or formatted string
    """
    client = get_client()
    
    location = search_locations(location)

    # Format the query parameters
    encoded_keywords = keywords.replace(" ", "%20")
    encoded_location = location.replace(" ", "%20")
    
    url = f"https://linkedin-data-api.p.rapidapi.com/search-jobs?keywords={encoded_keywords}&locationId={encoded_location}&datePosted=pastMonth&sort=mostRelevant"
    
    try:
        response = client.get(url)
        print(f"Status code: {response.status_code}")
        
        data = response.json()
        
        if not data.get("success"):
            error_msg = f"API Error: {data.get('message', 'Unknown error')}"
            return {"error": error_msg} if not format_output else error_msg
        
        # Store jobs in a list of dictionaries
        jobs_list = []
        for job in data.get("data", [])[:limit]:
            job_dict = {
                "id": job.get("id"),
                "title": job.get("title", "Unknown Title"),
                "company": job.get("company", {}).get("name", "Unknown Company"),
                "company_logo": job.get("company", {}).get("logo"),
                "location": job.get("location", "Unknown Location"),
                "url": job.get("url", ""),
                "post_date": job.get("postAt", "Unknown Date"),
                "reference_id": job.get("referenceId")
            }
            jobs_list.append(job_dict)
        
        result = {
            "query": {
                "keywords": keywords,
                "location": location
            },
            "count": len(jobs_list),
            "jobs": jobs_list
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error: {e}")
        error_msg = f"Error searching jobs: {e}"
        return {"error": error_msg} if not format_output else error_msg
    

@mcp.tool()
def get_job_details(job_id: str) -> str:
    """
    Get detailed information about a specific LinkedIn job posting.
    
    :param job_id: The LinkedIn job ID
    :return: Detailed job information
    """
    client = get_client()
    
    url = f"https://linkedin-data-api.p.rapidapi.com/get-job-details?id={job_id}"
    
    try:
        response = client.get(url)
        print(f"Status code: {response.status_code}")
        
        data = response.json()
        if not data.get("success"):
            return f"API Error: {data.get('message', 'Unknown error')}"
        
        job_data = data.get("data", {})
        return job_data
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error fetching job details: {e}"
    
@mcp.tool()
def search_locations(keyword: str) -> str:
    """
    Search for LinkedIn location IDs by keyword.
    
    :param keyword: Location keyword to search for
    :return: ID of the first matching location
    """
    client = get_client()
    
    # Format the query parameter
    encoded_keyword = keyword.replace(" ", "%20")
    
    url = f"https://linkedin-data-api.p.rapidapi.com/search-locations?keyword={encoded_keyword}"
    
    try:
        response = client.get(url)
        print(f"Status code: {response.status_code}")
        
        data = response.json()
        
        if not data.get("success"):
            return f"API Error: {data.get('message', 'Unknown error')}"
        
        items = data.get("data", {}).get("items", [])
        
        if not items:
            return f"No locations found matching '{keyword}'"
        
        # Get the first location's ID
        first_location = items[0]
        full_id = first_location.get("id", "")
        
        # Extract the numeric ID from "urn:li:geo:104243116" format
        if ":" in full_id:
            location_id = full_id.split(":")[-1]
        else:
            location_id = full_id
        print(f"Location ID: {location_id}")
        return location_id
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error searching locations: {e}"
    
if __name__ == "__main__":
    mcp.run(transport='stdio')
