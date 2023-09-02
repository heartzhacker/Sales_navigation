import multiprocessing
from selenium import webdriver

def scrape(url):
	driver = webdriver.Chrome()
	driver.get(url)
	page_source = driver.page_source
	driver.close()
	# do something with the page source

urls = [
	'https://en.wikipedia.org/wiki/0',
	'https://en.wikipedia.org/wiki/1',
	'https://en.wikipedia.org/wiki/2',
	'https://en.wikipedia.org/wiki/3',
]

processes = []
for url in urls:
	p = multiprocessing.Process(target=scrape, args=(url,))
	p.start()
	processes.append(p)

for p in processes:
	p.join()
