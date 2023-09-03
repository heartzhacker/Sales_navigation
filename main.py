from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import threading
import time 
import requests
from bs4 import BeautifulSoup
import difflib
from selenium.webdriver.common.by import By

global visited
visited = set() # set of visited sites
global res # final text 
res = []
global thread_list
thread_list = []


#keywords given priority TODO generate from gpt
keywords = ["linkedin","about","contact","info","github","wikipedia","facebook","instagram","twitter","docs"] # including docs

email = ""
pw = ""
def contains_key(url):
    for i in range(len(keywords)):
        if keywords[i] in url:
            return i
    return -1

def link_relevance(base_url,new_url):
    url_similarity = difflib.SequenceMatcher(None, base_url, new_url).ratio() # similarity to base url
    link_depth = (20 - new_url.count('/') - new_url.count('?'))/20 # give priority to lesser deep links
    len_score = (100-min(100,len(new_url)))/100 # give priority to short urls (long urls with random session id may form substring with base url)
    keyword_score = 0.3 if any(key in new_url for key in keywords) else 0  # give score on the basis of prominent keywords
    return url_similarity + link_depth + len_score + keyword_score

def linkedin_fetch(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') 
    with webdriver.Chrome(options=options) as driver:
        driver.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin') # linked in login
        WebDriverWait(driver, 3)
        username = driver.find_element(By.XPATH,'//input[@name="session_key"]')
        password = driver.find_element(By.XPATH,'//input[@name="session_password"]')
        username.send_keys(email)
        password.send_keys(pw)
        login_btn = driver.find_element(By.XPATH,"//button[@class='btn__primary--large from__button--floating']")
        WebDriverWait(driver, 3)
        login_btn.click()
        WebDriverWait(driver, 10)
        time.sleep(10)
        
        if url.index("/company")!=-1: # fetch company's profile
            url = url + "/about"
        driver.get(url)
        
        WebDriverWait(driver, 10)

        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            
            driver.execute_script(f"window.scrollTo(0, {last_height});")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
        page_source = driver.page_source
        soup = BeautifulSoup(page_source,'lxml')

        
        if url.index("/company")!=-1: # fetch company's profile
            element = soup.find("section",{"class":"org-about-module__margin-bottom"})
            if not element:
                return
            text = " ".join(element.get_text().replace('\n', ' ').replace('\r', '').split())
            res.append(text)
            #print(text)
        else:
            aboutid = soup.find("div",{"id":"about"})
            head = aboutid.find_next_sibling("div")
            about = head.find_next_sibling("div")
            if head:
                text = about.get_text() # TODO remove multiple \n 
                #print(text)
                res.append(text)

def selenium_fetch(url,depth):
    if (depth==0):
        return
    if (contains_key(url)!=-1):
        #print("contains url ",contains_key(url) )
        if (contains_key(url)==0): # linked in
            linkedin_fetch(url)
            return
        #return
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # run in headless mode to avoid opening a GUI
    with webdriver.Chrome(options=options) as driver:
        driver.get(url)
        WebDriverWait(driver, 3)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script(f"window.scrollTo(0, {last_height});")
            time.sleep(1.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
        page_source = driver.page_source
        soup = BeautifulSoup(page_source,'html.parser')
        text = soup.get_text() # TODO remove multiple \n 

        arr = soup.find_all('a',href=True)
        consider = 5*depth
        count_slenium_fetch = consider//10 # count of urls to be opened in selenium 10%

        # some url do not have https:// or http:// e.g. -> /pages/terms?otracker=undefined_footer_navlinks
            # add baseurl to them
        for i in range(len(arr)):
            tempurl = arr[i]['href']
            if tempurl[0]=='/':
                if (url[-1]=='/'): # removing starting /
                    tempurl = url + tempurl[1:]
                else:
                    tempurl = url + tempurl
                arr[i]['href'] = tempurl


        arr = sorted(arr, key=lambda link: link_relevance(url, link['href']), reverse=True)

        for i in range(min(len(arr),consider)):
            newurl = arr[i]['href']
            if len(newurl)==0 or newurl.find('http')==-1:
                continue
            if newurl[len(newurl)-1]=='/': # remove additional /
                newurl = newurl[:-1]
            if newurl in visited: # check if already visited site
                continue

            visited.add(newurl)
            #print(newurl)
            #print(link_relevance(url,newurl))

            if i<count_slenium_fetch:
                selenium_fetch(newurl,depth-1)
            else:
                recur_fetch(newurl,1,depth-1)
        
            # now visit the site
            #recur_fetch(newurl,depth-1)
        #print(text)
        driver.close()
        # add to result
        res.append(text)

def recur_fetch(url,method,depth): # method selenium or bs4
    global res,visited
    if depth==0:
        return
    consider = depth*5 # how many links to consider  10->for d=2  5->for d=1
    if (method==0): #selenium
        #print(url)
        thread = threading.Thread(target=selenium_fetch,args=(url,depth,))
        thread.start()
        thread_list.append(thread)
        #thread.join()
    else: # beautiful soup
        response = requests.get(url)
        if response.status_code!=200:
            return
        soup = BeautifulSoup(response.content,'html.parser')
        text = soup.get_text()
        res.append(text) # add it to result
        #consider=100
        arr = soup.find_all('a',href=True)
        
        # some url do not have https:// or http:// e.g. -> /pages/terms?otracker=undefined_footer_navlinks
            # add baseurl to them
        for i in range(len(arr)):
            tempurl = arr[i]['href']
            if tempurl[0]=='/':
                if (url[-1]=='/'): # avoiding double //
                    tempurl = url + tempurl[1:]
                else:
                    tempurl = url + tempurl
                arr[i]['href'] = tempurl
            

        arr = sorted(arr, key=lambda link: link_relevance(url, link['href']), reverse=True)
        for i in range(min(len(arr),consider)):
            newurl = arr[i]['href']
            if len(newurl)==0 or newurl.find('http')==-1:
                continue

            if newurl[len(newurl)-1]=='/': # remove additional /
                newurl = newurl[:-1]
            
            if newurl in visited: # check if already visited site
                continue

            visited.add(newurl)
            #print(newurl)
            #print(link_relevance(url,newurl))
        
            # now visit the site
            recur_fetch(newurl,depth-1)
    return

def google_fetch(url):
    queries = ["https://google.com/search?q="+url+"+wikipedia",
    #"https://google.com/search?q="+url+"+linkedin",
    "https://google.com/search?q="+url+"+about"]
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    for  query in queries:
        driver.get(query)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = soup.find_all('div', class_="yuRUbf")
        #print(results)
        if (len(results)>0):
            result = results[0].a.get('href')
            # selenium fetch this with depth 1 if not visited in new thread
            if result not in visited:
                visited.add(result)
                thread = threading.Thread(target=selenium_fetch,args=(result,1,))
                thread.start()
                thread_list.append(thread)
        info = soup.find_all('span',class_="hgKElc")
        for ele in info:
            # add ele.text to result
            res.append(ele.text)
    driver.close()

def fetch(url):
    global res,visited
    # set visited to empty
    # set res to empty
    res = []
    visited.clear()
    depth = 1
    recur_fetch(url,0,depth)
    #google_fetch(url)
    for thread in thread_list:
        thread.join()
    return res

#print(fetch("https://www.flipkart.com/"))
#print(fetch("https://www.langchain.com"))
#print(fetch("https://www.langchain.com"))
#fetch("https://www.linkedin.com/in/sumithbangarwa/")
#fetch("https://www.linkedin.com/in/shaleen-badola/")
fetch("https://www.linkedin.com/company/flipkart/")
#fetch("https://www.linkedin.com/company/lucid-growth/")
