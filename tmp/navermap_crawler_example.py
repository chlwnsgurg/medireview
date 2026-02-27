from selenium.webdriver.common.by import By
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from openpyxl import Workbook
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import time
import datetime
import requests
from selenium.webdriver.chrome.service import Service

# url
url = 'https://m.place.naver.com/restaurant/1085956231/review/visitor?entry=ple&reviewSort=recent'

# Webdriver headless mode setting
options = webdriver.ChromeOptions()
# options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")

# BS4 setting for secondary access
session = requests.Session()
headers = {
    "User-Agent": "user value"}

retries = Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504])

session.mount('http://', HTTPAdapter(max_retries=retries))

# New xlsx file
now = datetime.datetime.now()
xlsx = Workbook()
list_sheet = xlsx.create_sheet('output')
list_sheet.append(['nickname', 'content', 'date', 'revisit'])

# Start crawling/scraping!
try:
    # driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    res = driver.get(url)
    driver.implicitly_wait(30)

    # Pagedown
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)

    try:
        for i in range(30):  # 최대 30번 반복
            driver.find_element(By.XPATH, '//*[@id="app-root"]/div/div/div/div[6]/div[2]/div[3]/div[2]/div/a').click()
            time.sleep(0.4)
    except Exception as e:
        print('finish')
    else :
        print('30times_finish')

    time.sleep(25)
    html = driver.page_source
    bs = BeautifulSoup(html, 'lxml')
    reviews = bs.select('li.pui__X35jYm.EjjAW')

    for r in reviews:
        # nickname
        nickname = r.select_one('div.pui__JiVbY3 > span.pui__uslU0d')

        # content
        content = r.select_one('div.pui__vn15t2 > a.pui__xtsQN-')

        # date
        date_elements = r.select('div.pui__QKE5Pr > span.pui__gfuUIT > time')
        date = date_elements[0] if date_elements else 'N/A'

        # revisit
        revisit_span = r.select('div.pui__QKE5Pr > span.pui__gfuUIT')
        revisit = revisit_span[1] if len(revisit_span) > 1 else 'N/A'

        # exception handling
        nickname = nickname.text if nickname else ''
        content = content.text if content else ''
        date = date.text if date else ''
        revisit = revisit.text if revisit else ''
        time.sleep(0.06)

        # append sheet
        print(nickname, '/', content, '/', date, '/', revisit)
        list_sheet.append([nickname, content, date, revisit])
        time.sleep(0.06)
    # Save the file
    file_name = 'naver_review_' + now.strftime('%Y-%m-%d_%H-%M-%S') + '.xlsx'
    xlsx.save(file_name)

except Exception as e:
    print(e)
    # Save the file(temp)
    file_name = 'naver_review_' + now.strftime('%Y-%m-%d_%H-%M-%S') + '.xlsx'
    xlsx.save(file_name)
출처: https://jinooh.tistory.com/89 [글쎄요, 아직 잘 모릅니다.:티스토리]