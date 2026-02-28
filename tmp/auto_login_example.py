from selenium import webdriver  # 모듈 사용

url = "https://nid.naver.com/nidlogin.login?mode=form&url=https%3A%2F%2Fwww.naver.com" # 네이버 로그인 URL

driver = webdriver.Chrome("c:/chromedriver.exe") #크로 드라이버 경로 , 드라이버라는 변수에 저장

driver.get(url) #네이버 URL 입력 

#아이디 입력 코드

id = driver.find_element("xpath",'//*[@id="id"]') # 아이디 변수 만들기

id.click() # 아이디 창 클릭
id.send_keys("ffff") # 아이디 입력키 보내기 ("본인 아이디")

#비밀번호 입력 코드

pw = driver.find_element("xpath",'//*[@id="pw"]')

pw.click() # 비밀번호 창 클릭
pw.send_keys("ffffff") # 비밀번호 입력키 보내기 ("본인 비번")

# 로그인 코드 입력

button = driver.find_element("xpath",'//*[@id="log.login"]') # 로그인 버튼을 button 함수로 변경

button.click() #로그인 버튼 클릭