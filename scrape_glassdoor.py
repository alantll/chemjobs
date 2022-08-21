from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import argparse
import pandas as pd
import time

def get_jobs(keyword, num_jobs=900):
    """
    Scrape job data from Glassdoor, tabulate the information in a Pandas DataFrame, and returns a .csv file

    Args:
        keyword (str): Job title (separated by hyphen if required)
        num_jobs (int): Number of jobs to scrape. Defaults to 900 or maximum number if jobs (whichever is less)
    """
    # Get date information for csv filename
    now = datetime.now()
    date_YYYYmmdd = now.strftime('%Y%m%d') # YYYYMMDD

    options = webdriver.ChromeOptions()
    #options.add_argument('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36')
    #options.add_argument('headless') # Uncomment to scrape in headless mode
    
    # Initialize webdriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_window_size(1120, 1000)

    url = 'https://www.glassdoor.com/Job/' + keyword + '-SRCH_KO0,15.htm'
    driver.get(url)

    if num_jobs == 900:
        max_jobs = driver.find_element(By.XPATH, '//*[@data-test="jobCount-H1title"]').text
        num_jobs = int(max_jobs.split(' ')[0])
    else:
        pass

    jobs = []
    page = 1
    
    while len(jobs) < num_jobs:  # If true, will look for new jobs

        # Sleep time to let page load
        time.sleep(3)

        # Get list of jobs on page
        job_buttons = driver.find_elements(By.XPATH, '//*[@id="MainCol"]/div[1]/ul/li')

        #Iterate through jobs
        for job_button in job_buttons:

            # Print progress
            print(f'Progress: {str(len(jobs))}/{str(num_jobs)}, Page: {page}')
            if len(jobs) >= num_jobs:
                break

            job_button.click()
            time.sleep(2)

            # Search for "Sign Up" prompt and click on x to close if appears after first click
            if len(jobs) >= 1:
                pass
            else:
                try:
                    driver.find_element(By.XPATH, '//*[@id="JAModal"]/div/div[2]/span').click()
                except NoSuchElementException:
                    pass
            
            # Click on the "see more" link to reveal complete job description
            try:
                driver.find_element(By.XPATH, '//*[@id="JobDescriptionContainer"]/div[2]').click()
            except NoSuchElementException:
                pass

            job_dict = {}

            collected_successfully = False
            while not collected_successfully:

                try:
                    time_posted = job_button.find_element(By.XPATH, './/div[@data-test="job-age"]').text
                except (NoSuchElementException, StaleElementReferenceException) as e:
                    #print(f'### {e} ###')
                    time_posted = ''
                    pass

                # Get job details from header, passes if job fails to load in window
                try:
                    company_name = driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[1]/div[1]').text
                    job_title = driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[1]/div[2]').text
                    location = driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[1]/div[3]').text
                    job_description = driver.find_element(By.XPATH, '//*[@id="JobDescriptionContainer"]/div[1]/div').text

                    # Raise exception if salary estimate or rating not present
                    try:
                        salary_estimate = driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div/div/div[1]/div[4]/span').text
                    except NoSuchElementException:
                        salary_estimate = ''

                    try:
                        rating = driver.find_element(By.XPATH, '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[1]/div[1]/span').text
                    except NoSuchElementException:
                        rating = ''
 
                    collected_successfully = True

                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            # If collected successful, continue scraping relevant information and add to dictionary 
            if collected_successfully:

                job_dict = {'Job Title': job_title,
                            'Company Name': company_name,
                            'Location': location,
                            'Job Description': job_description,
                            'Salary Estimate': salary_estimate,
                            'Rating': rating,
                            'Time Posted': time_posted}

                # Extract employer information from Company Overview flexbox (some decriptors not always present)
                company_elements = driver.find_elements(By.XPATH, '//*[@id="EmpBasicInfo"]/div[1]/div/div')
                for element in company_elements:
                    try:
                        descriptor_label = element.find_element(By.XPATH, './span[1]').text
                        descriptor_text = element.find_element(By.XPATH, './span[2]').text
                        job_dict.update({descriptor_label: descriptor_text})
                    except NoSuchElementException:
                        continue

                # Append job to jobs list
                jobs.append(job_dict)

            else:
                pass

        # Click on the "next page" button when all job buttons parsed
        try:
            driver.find_element(By.XPATH, '//*[@id="MainCol"]/div[2]/div/div[1]/button[7]').click()
            page += 1
        except NoSuchElementException:
            print(f'Scraping terminated before reaching target number of jobs. Needed {num_jobs}, got {len(jobs)}.')
            break
    
    # Convert the list object into Pandas DataFrame and save as .csv
    df = pd.DataFrame(jobs)
    df.to_csv(f'gd_{keyword}_{date_YYYYmmdd}_raw.csv', index=False)

    driver.quit()

    return

def main():
    parser = argparse.ArgumentParser(description='This script scrapes job data from Glassdoor and outputs the results in a .csv file.')
    parser.add_argument('keyword', help='Job title (separated by hyphen if required).', type=str)
    parser.add_argument('num_jobs', help='Number of jobs to scrape. Defaults to 900 or maximum number if jobs (whichever is less)', type=int, default=900)
    
    args = parser.parse_args()
    
    get_jobs(args.keyword, args.num_jobs)

if __name__ == "__main__":
    main()
