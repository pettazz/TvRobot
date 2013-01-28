from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class Locator:
    def __init__(self, webdriver, key_name, locator, by=By.CSS_SELECTOR):
        self.driver = webdriver
        self.key_name = key_name
        self.locator = locator
        self.by = by

    def __str__(self):
        return "%s (%s)" % (self.key_name, self.locator)

    def find(self):
        return self.driver.find_elements(getattr(By, self.by), self.locator)
    
    def find_one(self):
        results = self.driver.find_elements(getattr(By, self.by), self.locator)
        if len(results) == 0:
            raise NoSuchElementException('Locator `%s` (%s) not found.' % (self.key_name, self.locator))
        return results[0]


class LocatorsManager:

    def __init__(self, driver, locators_dict=None):
        self.driver = driver
        self.locators = {}
        if locators_dict is not None:
            self.add_locators(locators_dict)

    def __getattr__(self, name):
        if name in self.locators.keys():
            return self.locators[name]
        else:
            raise Exception('Locator `%s` not found' % name)

    def add_locators(self, locators_dict):
        for x in locators_dict:
            self.add_locator(x, locators_dict[x])

    def add_locator(self, name, locator, locator_type=None):
        if name in self.locators.keys():
            raise Exception('There is an existing locator with the name: %s' % name)
        if locator_type is None:
            if isinstance(locator, tuple):
                locator_type = locator[0]
                locator = locator[1]
            else:
                locator_type = 'CSS_SELECTOR'

        if not hasattr(By, locator_type):
            raise Exception('Unrecognized locator type: %s' % locator_type)

        self.locators[name] = Locator(self.driver, name, locator, locator_type)

    def find_one(self, locator):
        results = self.find(locator)
        if len(results) == 0:
            raise Exception('Locator `%s` not found' % locator)
        return results[0]

    def find(self, locator):
        if type(locator) == str:
            # a string definition key was passed in
            if locator in self.locators.keys():
                # we have a definition for this locator key
                #return self.driver.find_elements(getattr(By, self.locators[locator].by), self.locators[locator].locator)
                return self.locators[locator].find()
            else:
                # default to By.CSS_SELECTOR if we don't recognize it
                return self.find(('CSS_SELECTOR', locator))
        else:
            # a tuple definition was passed in
            return self.driver.find_elements(getattr(By, obj[0]), obj[1])

    def find_child(self, webelement, locator):
        results = self.find_children(webelement, locator)
        if len(results) == 0:
            raise Exception('Locator `%s` not found' % locator)
        return results[0]

    def find_children(self, webelement, locator):
        if type(locator) == str:
            # a string definition key was passed in
            if locator in self.locators.keys():
                # we have a definition for this locator key
                return webelement.find_elements(getattr(By, self.locators[locator].by), self.locators[locator].locator)
            else:
                # default to By.CSS_SELECTOR if we don't recognize it
                return self.find_children(webelement, ('CSS_SELECTOR', locator))
        else:
            # a tuple definition was passed in
            return webelement.find_elements(getattr(By, obj[0]), obj[1])

    def get_locator(self, name):
        return self.locators[name].locator