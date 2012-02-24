"""
This module contains a set of methods that can be used for loading pages and
waiting for elements to come in.

The default option we use to search for elements is CSS Selector.
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

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.errorhandler import ElementNotVisibleException
from selenium.webdriver.remote.errorhandler import NoSuchElementException


def wait_for_element_present(driver, selector,
                             by=By.CSS_SELECTOR, timeout=30):
    """
    Searches for the specified element by the given selector.  Returns the
    element object if the element is present on the page.  The element can be
    invisible.  Raises an exception if the element does not appear in the
    specified timeout.
    @Params
    driver - the webdriver object
    selector - the locator that is used (required)
    by - the method to search for hte locator (Default- By.CSS_SELECTOR)
    timeout - the time to wait for the element in seconds (Default- 30 seconds)

    @returns
    A web element object
    """

    element = None
    for x in range(timeout):
        try:
            element = driver.find_element(by=by, value=selector)
            return element
        except Exception:
            time.sleep(1)
    if not element:
        raise NoSuchElementException("Element %s was not present in %s" %
                                     (selector, timeout))

def wait_for_element_visible(driver, selector,
                             by=By.CSS_SELECTOR, timeout=30):
    """
    Searches for the specified element by the given selector.  Returns the
    element object if the element is present and visible on the page.
    Raises an exception if the element does not appear in the
    specified timeout.
    @Params
    driver - the webdriver object (required)
    selector - the locator that is used (required)
    by - the method to search for hte locator (Default- By.CSS_SELECTOR)
    timeout - the time to wait for the element in seconds (Default- 30 seconds)

    @returns
    A web element object
    """

    element = None
    for x in range(timeout):
        try:
            element = driver.find_element(by=by, value=selector)
            if element.is_displayed():
                return element
            else:
                element = None
            time.sleep(1)
        except Exception:
            time.sleep(1)
    if not element:
        raise ElementNotVisibleException("Element %s was not present in %s"\
                                         % (selector, timeout))

def wait_for_text_visible(driver, text, selector,
                          by=By.CSS_SELECTOR, timeout=30):
    """
    Searches for the specified element by the given selector. Returns the 
    element object if the text is present in the element and visible 
    on the page. Raises an exception if the text or element do not appear 
    in the specified timeout.
    @Params
    driver - the webdriver object (required)
    text - the text that is being searched for in the element (required)
    selector - the locator that is used (required)
    by - the method to search for hte locator (Default- By.CSS_SELECTOR)
    timeout - the time to wait for the element in seconds (Default- 30 seconds)

    @returns
    A web element object that contains the text searched for
    """

    element = None
    for x in range(timeout):
        try:
            element = driver.find_element(by=by, value=selector)
            if element.is_displayed():
                if text in element.text:
                    return element
                else:
                    element = None
            time.sleep(1)
        except Exception:
            time.sleep(1)
    if not element:
        raise ElementNotVisibleException("Element %s was not present in %s"\
                                         % (selector, timeout))

def wait_for_element_absent(driver, selector,
                             by=By.CSS_SELECTOR, timeout=30):
    """
    Searches for the specified element by the given selector. Returns void when
    element is no longer present on the page. Raises an exception if the 
    element does still exist after the specified timeout.
    @Params
    driver - the webdriver object
    selector - the locator that is used (required)
    by - the method to search for hte locator (Default- By.CSS_SELECTOR)
    timeout - the time to wait for the element in seconds (Default- 30 seconds)
    """

    for x in range(timeout + 1):
        try:
            driver.find_element(by=by, value=selector)
            time.sleep(1)
        except Exception:
            return
    raise Exception("Element %s was still present after %s" %
                    (selector, timeout))

def wait_for_element_not_visible(driver, selector,
                             by=By.CSS_SELECTOR, timeout=30):
    """
    Searches for the specified element by the given selector. Returns void when
    element is no longer visible on the page (or if the element is not 
    present). Raises an exception if the element is still visible after the 
    specified timeout.
    @Params
    driver - the webdriver object (required)
    selector - the locator that is used (required)
    by - the method to search for hte locator (Default- By.CSS_SELECTOR)
    timeout - the time to wait for the element in seconds (Default - 30 seconds)
    """

    for x in range(timeout + 1):
        try:
            element = driver.find_element(by=by, value=selector)
            if element.is_displayed():
                time.sleep(1)
            else:
                return
            time.sleep(1)
        except Exception:
            return
    raise Exception("Element %s was still present after %s"\
                                     % (selector, timeout))