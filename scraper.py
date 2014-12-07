import requests
import bs4
import codecs
import time
import ast
import os
import operator

proxy_dict = {"http":"10.18.0.21:3128"}
MAX_RETRIES = 10
pages_to_visit = ['http://www.hotnews.ro/',
                  'http://economie.hotnews.ro/',
                  'http://sport.hotnews.ro/',
                  'http://life.hotnews.ro/',
                  'http://science.hotnews.ro/']

EMPTY_PAGE = r'''<body></body>'''
EMPTY_SOUP = bs4.BeautifulSoup(EMPTY_PAGE)
PUNCTUATION_REPLACEMENTS = {',': '', ':': '', ';': '', '(': '', ')': '', '-':''}
WORDS_NOT_COUNTED = ['sa', 'din', 'in', 'si', 'pentru', 'deci', 'in', 'ca', 'cu', 'la', 'cat', 'cum', 'de', 'ce', 's-a', 's-au', 'o', 'un', 'niste', 'cand', 'incat',
                    'dupa', 'inainte', 'sub', 'peste', 'alaturi', 'au', 'are', 'sunt', 'este',
                    'voi', 'noi', 'ei', 'ele', 'el', 'ea', 'eu', 'tu',
                    'sunt', 'esti', 'este', 'suntem', 'sunteti', 'sunt',
                    'am', 'ai', 'are', 'avem', 'aveti', 'au', 'a', 'ati',
                    'pe', 'video', 'care', 'mai', 'fost', 'va', 'se', 'o', 'un','al', 'ar', 'fi', 'putea', 'nu', 'da']

def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text

def scrap_all_pages():
    print("scrapping all pages");
    pages = []
    for page in pages_to_visit:
        article_title_link = get_article_titles_and_links(page)
        #print(article_title_link)
        print("scraping from main page: " + str(page))
        for article_dict in article_title_link:
            link = article_dict['link']
            text = get_article_text(link)
            article_dict['text'] = text
            page_dict = {'page':page, 'content':article_dict}
            pages.append(page_dict)

    return pages

def get_content(page_address):

    retries = 0

    while retries < MAX_RETRIES:
        try:
            #req = requests.get(page_address, proxies=proxy_dict)
            req = requests.get(page_address)
            bs = bs4.BeautifulSoup(req.content)

            results = bs

            while req.status_code != 200 or not results:
                print("could not retrieve result for the request on: " + page_address)
                time.sleep(1)  # try again
                req = requests.get(page_address, proxies=proxy_dict)
                bs = bs4.BeautifulSoup(req.content)
                results = bs

            return results

        except Exception:
            print("generic exception caught while trying to connect")
            return EMPTY_SOUP

        ++retries


def get_article_titles_and_links(page_address):


    print("getting article titles and links for: " + page_address)
    results = get_content(page_address)
    divTag = results.find_all("h2", {"class":"article_title"})

    articles = []

    for tag in divTag:
        links_to_pages = tag.find_all("a")
        for a in links_to_pages:
            titleRaw = a.get('title')
            linkRaw = a.get('href')

            if titleRaw == None or titleRaw == '' or titleRaw == u'\u200b':
                continue

            if linkRaw == None or linkRaw == '' or titleRaw == u'\u200b':
                continue

            title = unicode(titleRaw)
            link = unicode(linkRaw)

            articles.append({'title':title, 'link':link})

    return articles

def get_article_text(page_address):
    print("getting article text for: " + page_address)
    results = get_content(page_address)
    divTag = results.find_all("div", {"id":"articleContent"})

    if len(divTag) > 0:
        return divTag[0].text

    return None

def save_pages_contents(pages_contents):

    for page in pages_contents:
        with codecs.open('hotnews.csv', 'a', 'utf-8') as f:
            line = unicode(page)
            f.write(line + '\n')




def process_info(page_dict):

    title_string = page_dict['content']['title']
    title_string_clean = replace_all(title_string, PUNCTUATION_REPLACEMENTS)
    title_string_clean = title_string_clean.lower()
    tokens = title_string_clean.split()
    final_tokens = {}

    for token in tokens:
        if token in WORDS_NOT_COUNTED:
            continue

        if token in final_tokens:
            final_tokens[token] += 1
        else:
            final_tokens[token] = 1

    return final_tokens


def get_page_infos():

    final_tokens = {}

    sorted_tokens = []

    with open('hotnews.csv') as f:
        for line in f:
            page_dict = ast.literal_eval(line)
            page_tokens = process_info(page_dict)
            for token in page_tokens:
                if token in final_tokens:
                    final_tokens[token] += page_tokens[token]
                else:
                    final_tokens[token] = 1

    final_tokens_sorted = sorted(final_tokens, key=final_tokens.get, reverse=True)
    for token in final_tokens_sorted:
        sorted_tokens.append({token:final_tokens[token]})

    return sorted_tokens

def get_titles_for_token(token):

    titles = []
    print("getting the titles for the token: " + token)
    with open('hotnews.csv') as f:
        for line in f:
            page_dict = ast.literal_eval(line)
            title_string = page_dict['content']['title']
            title_string = title_string.lower()
            link_string = page_dict['content']['link']

            title_tokens = title_string.split()
            if token in title_tokens:
                titles.append(link_string)

    return titles

if __name__ == '__main__':
    print("Scrape started")
    if not os.path.isfile('hotnews.csv'):
        pages_contents = scrap_all_pages()
        save_pages_contents(pages_contents)


    sorted_tokens = get_page_infos()
    for i in range(0, 5):
        print("================================================")
        print(sorted_tokens[i])

        token = sorted_tokens[i].keys()[0]
        occurences = sorted_tokens[i].values()[0]
        print("TOKEN: " + token)
        titles = get_titles_for_token(token)
        for title in titles:
            print("TITLE: " + unicode(title))

        print("================================================")





