import os
import pandas as pd
import random
import requests
import string
from datetime import datetime
from time import sleep

from robocorp.tasks import task
from RPA.Browser.Selenium import Selenium


 # Global variables 
SITE_URL = "https://www.aljazeera.com/"
SEARCH_PHRASE = "Israel"

def _search():
    """
    Searches for news via the 'SEARCH_PHRASE' on aljazeera.com .

    Returns:
    obj: A page object with the news articles searched for.
    """
    browser = Selenium(auto_close=False)
    browser.open_browser(SITE_URL,browser='firefox')
    browser.maximize_browser_window()
    browser.click_button('//*[@id="root"]/div/div[1]/div[1]/div/header/div[4]/div[2]/button')
    browser.press_key('//*[@id="root"]/div/div[1]/div[2]/div/div/form/div[1]/input',SEARCH_PHRASE)
    browser.click_button('//*[@id="root"]/div/div[1]/div[2]/div/div/form/div[2]/button')
    return browser

def _find_element_from_page(obj,loc) -> list:
    """
    Finds elements specified from the page.

    Parameters:
    obj (object): A page object.
    loc (locator): An element locator e.g. 'class:container' .

    Returns:
    list: A list of elements by locator name.
    """
    news_value = obj.find_elements(loc)
    news_list = [ item.text for item in news_value ]
    return  news_list

def clean_date(lst):
    """
    Clean the date from the format Last updated 24 Apr 2024 Last updated 24 Apr 2024.
    If a date doesn't exist the article is from today.

    Parameter:
    lst (list): A list of returns from date element class search

    Returns:
    list: A list of well formatted dates.
    """
    clean_date_list = []
    for dat in lst:
        if len(dat) == 0:
            today  = datetime.today()
            formated_date = today.strftime('%d %b %Y')
            clean_date_list.append(formated_date)
        else:
            one_date = dat.split('\n')[-1]
            last_date = one_date.replace('Last update ','')
            clean_date_list.append(last_date)
    return clean_date_list

def download_image(url, file_name):
    """
    Downloads images from image urls.
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_name, 'wb') as f:
                f.write(response.content)
            print("Download complete!")
        else:
            print(f"Failed to download image. Status code: {response.status_code}")
    except Exception as e:
        return e

def image_names(obj, output_path):
    """
    Create random names for the images.

    Parameters:
    obj (object): A browser page object.
    output_path: A path to save the file

    Returns:
    list: A list of image names following the same index pattern
    """
    image_names = []
    for img in obj:
        image_link = img.get_attribute('src')
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        image_name = f"{output_path}/image_{random_string}.jpg"
        image_names.append(random_string)
        clean_links = image_link.strip('"')
        download_image(clean_links,image_name)
    return image_names

def count_search_matches(list1 , list2):
    """
    Matches the search phase and count the number of matches in 
    titles as well as summary and sum them together. It returns
    a list of total matched words.

    Parameters:
    list1 (lst): List of title elements
    list2 (lst): List of summary elements

    Returns:
    lst: A list of total matched search phrase per article.
    """
    title_matches = [string.count(SEARCH_PHRASE) for string in list1]
    summary_matches = [string.count(SEARCH_PHRASE) for string in list2]
    # Add the items
    result = [x + y for x, y in zip(title_matches, summary_matches)]
    return result

@task
def get_news_task():
    """ 
    Main function that searches a word on aljazeera.com 
    It then returns the files of excel file of:
    title, summary, date, count and image name
    """
    browser = _search()

    # To allow site to load
    sleep(20)

    # Getting data
    titles = _find_element_from_page(browser,'class:gc__title')
    news_summary = _find_element_from_page(browser,'class:gc__excerpt')
    news_date = _find_element_from_page(browser,'class:gc__meta')

    #cleaning data of the '\xad' added by browser  reCAPTCHA
    clean_titles = [ title.replace('\xad','') for title in titles ]
    clean_summary = [ summary.replace('\xad','') for summary in news_summary]
    cleaned_date = clean_date(news_date)

    #file path
    output_path = os.path.join(os.getcwd(),'output')

    # Download & save images
    image = browser.find_elements('class:article-card__image')
    photo_names = image_names(image,output_path=output_path)
    photo_names = []

    # Count search word matches
    number_of_words = count_search_matches(clean_titles, clean_summary)

    news_dict = {
        'titles': clean_titles,
        'summary': clean_summary,
        'date': cleaned_date,
        'image': photo_names,
        'Word match': number_of_words
        }
    
    # Saving to excel
    df = pd.DataFrame(news_dict,index=None)
    df.to_excel(f"{output_path}/data.xlsx",index=False)

    # close the browser
    browser.close_browser()


if __name__ == "__main__":
    get_news_task()

