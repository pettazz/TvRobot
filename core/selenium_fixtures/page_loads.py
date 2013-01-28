"""
This module contains a set of methods that can be used for loading pages and
waiting for elements to come in.

Locators can be Locator instances or specific webdriver "find_element" selectors.

The default option we use to search for elements using selectors is CSS_SELECTOR.
This can be changed by setting the by paramter.  The enum class for options is:
from selenium.webdriver.common.by import By

Options are
By.CSS_SELECTOR
By.CLASS_NAME
By.ID
By.NAME
By.LINK_TEXT
By.XPATH
By.TAG_NAME
By.PARTIAL_LINK_TEXT


"""
import time

from ..locators_manager import Locator

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

class PageLoads:
    def __init__(self, webdriver):
        self.driver = webdriver

    def wait_for_element_present(self, selector,
                                 by=By.CSS_SELECTOR, timeout=30):
        """
        Searches for the specified element by the given selector.  Returns the
        element object if the element is present on the page.  The element can be
        invisible.  Raises an exception if the element does not appear in the
        specified timeout.
        @Params
        selector - the locator that is used, can be either a Locator instance or a
                    webdriver find value (required)
        by - the method to search for the locator, unused when selector is a
                    Locator instance (Default- By.CSS_SELECTOR)
        timeout - the time to wait for the element in seconds (Default- 30 seconds)

        @returns
        A web element object
        """

        if isinstance(selector, Locator):
            wait_function = lambda driver : selector.find()
        else:
            wait_function = lambda driver : driver.find_element(by=by, value=selector)

        return WebDriverWait(self.driver, timeout).until(wait_function,
            "Element %s was not present in %s seconds" % (selector, timeout))
            

    def wait_for_element_visible(self, selector,
                                 by=By.CSS_SELECTOR, timeout=30):
        """
        Searches for the specified element by the given selector.  Returns the
        element object if the element is present and visible on the page.
        Raises an exception if the element does not appear in the
        specified timeout.
        @Params
        selector - the locator that is used, can be either a Locator instance or a
                    webdriver find value (required)
        by - the method to search for the locator, unused when selector is a
                    Locator instance (Default- By.CSS_SELECTOR)
        timeout - the time to wait for the element in seconds (Default- 30 seconds)

        @returns
        A web element object
        """

        if isinstance(selector, Locator):
            wait_function = lambda driver : (selector.find_one() and 
                                             selector.find_one().is_displayed())
        else:
            wait_function = lambda driver : driver.find_element(by=by, value=selector).is_displayed()

        return WebDriverWait(self.driver, timeout).until(wait_function,
            "Element %s was not present in %s seconds" % (selector, timeout))

    def wait_for_text_visible(self, text, selector,
                              by=By.CSS_SELECTOR, timeout=30):
        """
        Searches for the specified element by the given selector. Returns the 
        element object if the text is present in the element and visible 
        on the page. Raises an exception if the text or element does not appear 
        in the specified timeout.
        @Params
        text - the text that is being searched for in the element (required)
        selector - the locator that is used, can be either a Locator instance or a
                    webdriver find value (required)
        by - the method to search for the locator, unused when selector is a
                    Locator instance (Default- By.CSS_SELECTOR)
        timeout - the time to wait for the element in seconds (Default- 30 seconds)

        @returns
        A web element object that contains the text searched for
        """

        if isinstance(selector, Locator):
            wait_function = lambda driver : (selector.find_one() and 
                                             selector.find_one().is_displayed() and 
                                             text in selector.find_one().text)
        else:
            
            wait_function = lambda driver : (driver.find_element(by=by, value=selector).is_displayed() and 
                                             text in driver.find_element(by=by, value=selector).text)

        return WebDriverWait(self.driver, timeout).until(wait_function, 
            "Text %s was not found in %s seconds" % (text, timeout))

    def wait_for_element_absent(self, selector,
                                 by=By.CSS_SELECTOR, timeout=30):
        """
        Searches for the specified element by the given locator. Returns None when
        element is no longer present on the page. Raises an exception if the 
        element does still exist after the specified timeout.
        @Params
        selector - the locator that is used, can be either a Locator instance or a
                    webdriver find value (required)
        by - the method to search for the locator, unused when selector is a
                    Locator instance (Default- By.CSS_SELECTOR)
        timeout - the time to wait for the element in seconds (Default- 30 seconds)
        """

        if isinstance(selector, Locator):
            wait_function = lambda driver : (not selector.find_one())
        else:
            wait_function = lambda driver : (not driver.find_element(by=by, value=selector))

        return WebDriverWait(self.driver, timeout).until(wait_function, 
            "Element %s was still present after %s seconds" % (selector, timeout))                    

    def wait_for_element_not_visible(self, selector,
                                 by=By.CSS_SELECTOR, timeout=30):
        """
        Searches for the specified element by the given locator. Returns None when
        element is no longer visible on the page (or if the element is not 
        present). Raises an exception if the element is still visible after the 
        specified timeout.
        @Params
        selector - the locator that is used, can be either a Locator instance or a
                    webdriver find value (required)
        by - the method to search for the locator, unused when selector is a
                    Locator instance (Default- By.CSS_SELECTOR)
        timeout - the time to wait for the element in seconds (Default - 30 seconds)
        """

        if isinstance(selector, Locator):        
            wait_function = lambda driver : (selector.find_one() and selector.find_one().is_displayed())
        else:
            wait_function = lambda driver : (driver.find_element(by=by, value=selector).is_displayed())

        return WebDriverWait(self.driver, timeout).until_not(wait_function, 
            "Element %s was still present after %s seconds" % (selector, timeout))