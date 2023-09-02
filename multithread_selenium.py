from collections.abc import Callable, Iterable, Mapping
import threading
from typing import Any
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import queue
from time import sleep
from selenium.webdriver.common.by import By
import time 

linkedInUsers = {}
linkedInQ = queue.Queue()
llm_q = queue.Queue() #once all data for a company is ready, it is added to llm q
# extracted_queue = queue.Queue() #all threads add data to this queue, one thread manages all the data and once all data for a company is ready, it is added to llm q

# class dataManager(threading.Thread):
# 	def __init__(self):
# 		threading.Thread.__init__(self)
# 	def run():
# 		#company : data
# 		pass
# 		#load model and read from queue and do stuff
linkedin_login = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'
email = ''
pw = ""

class llmThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		counter = 0
		pass
		while True:
			counter+=1
			data = llm_q.get()
			if data == ('exit','exit'):
				return
			with open(str(counter)+'.txt','w',encoding='UTF-8') as f:
				f.write(data[1])

		#load model and read from queue and do stuff

class linkedIn(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

	def run(self): #all processing has to be done here
		driver = webdriver.Chrome()
		driver.get(linkedin_login)
		WebDriverWait(driver, 3)

		username = driver.find_element(By.XPATH,'//input[@name="session_key"]')
		password = driver.find_element(By.XPATH,'//input[@name="session_password"]')
		username.send_keys(email)
		password.send_keys(pw)
		login_btn = driver.find_element(By.XPATH,"//button[@class='btn__primary--large from__button--floating']")
		WebDriverWait(driver, 3)
		login_btn.click()
		WebDriverWait(driver, 3)

		while True:
			user = linkedInQ.get()
			if user=='exit':
				driver.close()
				return 
			else:
				driver.get(user)
				last_height = driver.execute_script("return document.body.scrollHeight")
				while True:
					driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
					time.sleep(2)
					new_height = driver.execute_script("return document.body.scrollHeight")
					if new_height == last_height:
						break
					last_height = new_height   
				page_source = driver.page_source
				linkedInUsers[user]=page_source

class ScrapeThread(threading.Thread):
	def __init__(self, url):
		threading.Thread.__init__(self)
		self.url = url

	def run(self): #all processing has to be done here
		driver = webdriver.Chrome()
		WebDriverWait(driver, 3)
		driver.get(self.url)
		WebDriverWait(driver, 3)
		last_height = driver.execute_script("return document.body.scrollHeight")
		while True:
			driver.execute_script(f"window.scrollTo(0, {last_height});")
			time.sleep(1.5)
			new_height = driver.execute_script("return document.body.scrollHeight")
			if new_height == last_height:
				break
			last_height = new_height   

		#make site map and do whatever

		#ends here
		page_source = driver.page_source
		driver.close()
		data = page_source #temporary test
		company_name = self.url[-5:-1]
		llm_q.put((company_name,data))
		# print(page_source)

urls = [
	'https://en.wikipedia.org/wiki/0',
	'https://en.wikipedia.org/wiki/1',
	'https://en.wikipedia.org/wiki/2',
	'https://en.wikipedia.org/wiki/3',
	"https://python.langchain.com/docs/get_started/introduction.html",
	]

# manager = dataManager()
# manager.start()
llm = llmThread()
llm.start()

linkedinThread = linkedIn()
linkedinThread.start()

threads = []
for url in urls:
	t = ScrapeThread(url)
	t.start()
	threads.append(t)

for t in threads:
	t.join()
llm_q.put(('exit','exit'))
linkedInQ.put('exit')
linkedInQ.join()
llm.join()
# manager.join()