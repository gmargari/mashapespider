import scrapy
import json
import sys
from selenium import webdriver
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

#===============================================================================
# MashapeWebSpider
#===============================================================================
class MashapeWebSpider(scrapy.Spider):
    name = 'Mashape'
    start_urls = [
        'https://market.mashape.com/explore?tags=Education&page=1',
    ]

    # scrapy parameter: seconds between successive page crawls
    download_delay = 0.25

    #===========================================================================
    # __init__ ()
    #===========================================================================
    def __init__(self):
        self.api_varnames_xpaths = {
            'name': "//h1[contains(@class,'name')]",
            'owner': "//div[contains(@class,'owner')]",
            'website': "//div[contains(@class,'website')]",
            'tags': "//div[contains(@class,'tags')]",
            'description': "//span[contains(@class,'more-contaner')]",
        }

        self.endpoints_xpath = "//section[@class='endpoint']"
        self.endpoint_varnames_xpaths = {
            'name': ".//div[@class='request']/div[@class='endpoint-name']/span",
            'description': ".//div[@class='request']/div[@class='description']",
            'method': ".//div[@class='response']/pre/div/span[@class='verb']",
            'host': ".//div[@class='response']/pre/div/span/span[@class='host']",
            'route': ".//div[@class='response']/pre/div/span/span[@class='route']",
        }

        self.params_xpath = ".//div[@class='request']/div[contains(@class, 'parameter') and contains(@class, 'typed')]"
        self.param_varnames_xpaths = {
            'name': ".//span[contains(@class, 'name')]",
            'type': ".//span[contains(@class, 'type')]",
            'description': ".//p",
        }

        # Initialized our headless browser
        self.browser = webdriver.PhantomJS()

        # Function to be called when spider terminates
        dispatcher.connect(self.quit, signals.spider_closed)

    #===========================================================================
    # quit ()
    #===========================================================================
    def quit(self):
        self.browser.quit()

    #===========================================================================
    # parse ()
    #===========================================================================
    def parse(self, response):
        yield scrapy.Request(response.url, self.parse_api_directory_page)

    #===========================================================================
    # parse_api_directory_page ()
    #===========================================================================
    def parse_api_directory_page(self, response):
        table_rows = response.xpath("//tr[@class='list-api-row']")
        # Page does not contain an API, thus is a 404
        if (table_rows == []):
            return

        # For each API link found in current directory page call parse_api_page
        for tr in table_rows:
            url = tr.xpath("td[2]/a/@href").extract()[0]
            fullurl = response.urljoin(url)
            yield scrapy.Request(fullurl, self.parse_api_page)

        # Recursive call this function for the next page
        yield scrapy.Request(self.get_next_url(response.url), self.parse_api_directory_page)

    #===========================================================================
    # parse_api_page ()
    #===========================================================================
    def parse_api_page(self, response):
        self.browser.get(response.url)

        # Get API description
        api = dict()
        api['mashape_url'] = response.url
        self.add_elements_to_dict_if_existing(api, self.browser, self.api_varnames_xpaths)

        # Get API endpoints
        api['endpoints'] = list()
        for elem_endpoint in self.browser.find_elements_by_xpath(self.endpoints_xpath):

            # Get endpoint description
            endpoint = dict()
            self.add_elements_to_dict_if_existing(endpoint, elem_endpoint, self.endpoint_varnames_xpaths)

            # Get endpoint params
            endpoint['params'] = list()
            for elem_param in elem_endpoint.find_elements_by_xpath(self.params_xpath):
                param = dict()
                self.add_elements_to_dict_if_existing(param, elem_param, self.param_varnames_xpaths)
                param['required'] = "true" if "required" in elem_param.get_attribute("class") else "false"
                endpoint['params'].append(param)
            api['endpoints'].append(endpoint)

        print json.dumps(api, sort_keys=True)

    #===========================================================================
    # add_elements_to_dict_if_existing ()
    #===========================================================================
    def add_elements_to_dict_if_existing(self, dictionary, dom_element, varnames_xpaths):
        for varname, xpath in varnames_xpaths.items():
            try:
                dictionary[varname] = dom_element.find_elements_by_xpath(xpath)[0].text
            except:
                pass

    #===========================================================================
    # get_next_url ()
    #===========================================================================
    def get_next_url(self, url):
        pos = url.rfind("=")
        num = int(url[pos+1:])
        return url[:pos+1] + str(num + 1)
