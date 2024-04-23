import os
import pandas as pd
import random
import requests
import string
from datetime import datetime
from time import sleep

from robocorp.tasks import task
from RPA.Browser.Selenium import Selenium


SITE_URL = "https://www.aljazeera.com/"
SEARCH_PHRASE = "Israel"


def _search():
    """
    Opens the browser to the search page and
    searches for th SEARCH_PHRASE to return an page object. 
    """

    browser = Selenium(auto_close=False)
    browser.open_browser(SITE_URL,browser='firefox')
    browser.maximize_browser_window()
    browser.click_button('//*[@id="root"]/div/div[1]/div[1]/div/header/div[4]/div[2]/button')
    browser.press_key('//*[@id="root"]/div/div[1]/div[2]/div/div/form/div[1]/input',SEARCH_PHRASE)
    browser.click_button('//*[@id="root"]/div/div[1]/div[2]/div/div/form/div[2]/button')
    sleep(10)
    button_visibility = browser.does_page_contain_button('//*[@id="main-content-area"]/div[2]/div[2]/button')
    #browser.scroll_element_into_view('//*[@id="main-content-area"]/div[2]/div[2]/button')
    print(button_visibility)
    while button_visibility:
        print(f'-----{button_visibility}')
        try:
            print('Scroll')
            #browser.scroll_element_into_view('//*[@id="main-content-area"]/div[2]/div[2]/button')
            print('Before button click')
            sleep(5)
            browser.click_button_when_visible('id:onetrust-accept-btn-handler')
            browser.click_button('//*[@id="main-content-area"]/div[2]/div[2]/button')
            print('After button click')
            
            print('Button clicked')
            button_visibility = browser.does_page_contain_button('//*[@id="main-content-area"]/div[2]/div[2]/button')
        except Exception as e:
            print(e)
            pass

    return browser



def _find_element_from_page(obj,loc) -> list:
    """
    Takes a page object and a locator and returns a list of the 
    elements located.
    """
    news_value = obj.find_elements(loc)
    news_list = [ item.text for item in news_value ]
    return  news_list

def clean_date(lst):
    """
    Takes one arg as list of dates and formats the date correctly.
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
    Takes an image url and a file_name then downloads the image.
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
    Takes an object & file path and create a random name. 
    It then returns a list of image names.
    """
    image_names = []
    for img in obj:
        image_link = img.get_attribute('src')
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        print(random_string)
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

    news_dict = {
        'titles': clean_titles,
        'summary': clean_summary,
        'date': cleaned_date,
        'image': photo_names
        }
    
    # Saving to excel
    df = pd.DataFrame(news_dict,index=None)
    df.to_excel(f"{output_path}/data.xlsx",index=False)

    # close the browser
    browser.close_browser()

if __name__ == "__main__":
    get_news_task()

