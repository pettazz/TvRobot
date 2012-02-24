from selenium import webdriver
from selenium.webdriver.common.by import By
from core.selenium_fixtures import page_interactions
from core.selenium_fixtures import page_loads


SEARCH_URL = {
    'TV': {
        'HD': "http://thepiratebay.se/search/%s/0/7/208",
        'SD': "http://thepiratebay.se/search/%s/0/7/205"
    },
    'MOVIE': {
        'HD': "http://thepiratebay.se/search/%s/0/7/207",
        'SD': "http://thepiratebay.se/search/%s/0/7/201"
    }
}

class TorrentSearchManager:

    def __init__(self, driver):
        self.driver = driver

    def get_magnet(self, search, media_type, sd_fallback = False):
        self.driver.get(SEARCH_URL[media_type]['HD'] % search)
        page_loads.wait_for_element_present(self.driver, "p#footer", By.CSS_SELECTOR, 120)
        if page_interactions.is_text_visible(self.driver, 'No hits. Try adding an asterisk in you search phrase.', 'h2'):
            if sd_fallback:
                self.driver.get(SEARCH_URL[media_type]['SD'] % search)
                page_loads.wait_for_element_present(self.driver, "p.footer", By.CSS_SELECTOR, 120)
                if page_interactions.is_text_visible(self.driver, 'No hits. Try adding an asterisk in you search phrase.', 'h2'):
                    magnet_link = None
                else:
                    print "SD RESULTS!"
                    magnet_link = self.driver.find_element_by_css_selector('table#searchResult tr:first-child a[title="Download this torrent using magnet"]').get_attribute('href')
            else:
                magnet_link = None
        else:
            print "HD RESULTS!"
            magnet_link = self.driver.find_element_by_css_selector('table#searchResult tr:first-child a[title="Download this torrent using magnet"]').get_attribute('href')
        return magnet_link