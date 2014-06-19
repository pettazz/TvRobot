import re

import requests
from bs4 import BeautifulSoup

from config import TVROBOT


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

    def get_magnet(self, search, media_type, sd_fallback = False):
        quality = 'HD'
        search = re.sub('[^A-Z a-z0-9]+', '', search)
        rows = self._find_rows(search, media_type, quality)
        if rows is None and sd_fallback:
            quality = 'SD'
            rows = self._find_rows(search, media_type, quality)
        if rows:
            print "%s %s results found!" % (len(rows), quality)            
            return self._get_best_row_magnet(rows)
        else:
            return rows

    def _find_rows(self, search, media_type, quality):
        r = requests.get(SEARCH_URL[media_type][quality] % search)
        soup = BeautifulSoup(r.text)
        if soup.h2.text == 'No hits. Try adding an asterisk in you search phrase.':
            #sometimes TPB likes to strip apostrophes
            if search.find('\'') > -1:
                again = self._find_rows(search.replace('\'', ''), media_type, quality)
                if again:
                    return again
            print "No results found."
            if soup.find(id='main-content').text == 'Search engine overloaded, please try again in a few seconds':
                print "TPB is overloaded."
                return False
            return None
        else:
            rows = soup.select('table#searchResult > tr')
            return rows

    def _get_best_row_magnet(self, rows):
        print "checking torrent ratio..."
        done = None
        for resultrow in rows:
            cols = resultrow.find_all('td')
            seeds = float(cols[2].text)
            leechers = float(cols[3].text)
            print "SE: %s; LE: %s" % (seeds, leechers)
            if leechers == 0:
                ratio = -1
            else:
                ratio = seeds / leechers
            if ratio > TVROBOT['torrent_ratio_threshold']:
                print "ratio of %s is above threshold, downloading dat shit" % ratio
                magnet = cols[1].find_all(title='Download this torrent using magnet')[0]['href']
                print "MAGNET LINK:\n%s\n" % magnet
                return magnet
            else:
                print "ratio of %s is below threshold, trying next row." % ratio