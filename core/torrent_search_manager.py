from selenium import webdriver
from selenium.webdriver.common.by import By
from config import TVROBOT
from core.selenium_fixtures import page_interactions
from core.selenium_fixtures import page_loads


SEARCH_URL = {
    'Episode': {
        'HD': "http://thepiratebay.se/search/%s/0/7/208",
        'SD': "http://thepiratebay.se/search/%s/0/7/205"
    },
    'Movie': {
        'HD': "http://thepiratebay.se/search/%s/0/7/207",
        'SD': "http://thepiratebay.se/search/%s/0/7/201"
    }
}

class TorrentSearchManager:

    def __init__(self, driver):
        self.driver = driver

    def get_magnet(self, search, media_type, sd_fallback = False):
        quality = 'HD'
        rows = self.find_rows(search, media_type, quality)
        if rows is None and sd_fallback:
            quality = 'SD'
            rows = self.find_rows(search, media_type, quality)
        if rows:
            print "%s %s results found!" % (len(rows), quality)            
            return self.get_best_row_magnet(rows)
        else:
            return rows

    def find_rows(self, search, media_type, quality):
        self.driver.get(SEARCH_URL[media_type][quality] % search)
        page_loads.wait_for_element_present(self.driver, "p#footer", By.CSS_SELECTOR, 120)
        if page_interactions.is_text_visible(self.driver, 'No hits. Try adding an asterisk in you search phrase.', 'h2'):
            #sometimes TPB likes to strip apostrophes
            if search.find('\'') > -1:
                again = self.find_rows(search.replace('\'', ''), media_type, quality)
                if again:
                    return again
            print "No results found."
            if page_interactions.is_text_visible(self.driver, 'Search engine overloaded, please try again in a few seconds', 'div#main-content'):
                print "TPB is overloaded."
                return False
            return None
        else:
            rows = self.driver.find_elements_by_css_selector('table#searchResult tbody tr')
            return rows

    def get_best_row_magnet(self, rows):
        print "checking torrent ratio..."
        done = None
        for resultrow in rows:
            seeds = float(resultrow.find_element_by_xpath('.//td[3]').text)
            leechers = float(resultrow.find_element_by_xpath('.//td[4]').text)
            print "SE: %s; LE: %s" % (seeds, leechers)
            ratio = seeds / leechers
            if ratio > TVROBOT['torrent_ratio_threshold']:
                print "ratio of %s is above threshold, downloading dat shit" % ratio
                #this is janky because htmlunit cant get the href attr for some reason. 
                #http://stackoverflow.com/questions/7263824/get-html-source-of-webelement-in-selenium-webdriver-python
                magnet_element = resultrow.find_element_by_xpath('.//td[2]')
                magnet_element_source = self.driver.execute_script('return arguments[0].innerHTML;', magnet_element)
                magnet = magnet_element_source[magnet_element_source.find('magnet:'):].split('"', 1)[0]
                print "MAGNET LINK:\n%s\n" % magnet
                return magnet
            else:
                print "ratio of %s is below threshold, trying next row." % ratio