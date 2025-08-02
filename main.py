from logger import app_logger
from job_searcher import JobSearcher

if __name__ == "__main__":
    # Add your subject and expertise here
    app_logger.info(f"Searching for jobs")
    fact_generator = JobSearcher()
    fact_generator.get_fact()
