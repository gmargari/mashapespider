# -*- coding: utf-8 -*-
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
        'https://market.mashape.com/explore?tags=Tools&page=1',
        'https://market.mashape.com/explore?tags=Education&page=1',
        'https://market.mashape.com/explore?tags=Devices&page=1',
        'https://market.mashape.com/explore?tags=Finance&page=1',
        'https://market.mashape.com/explore?tags=Advertising&page=1',
        'https://market.mashape.com/explore?tags=Commerce&page=1',
        'https://market.mashape.com/explore?tags=Other&page=1',
        'https://market.mashape.com/explore?tags=Location&page=1',
        'https://market.mashape.com/explore?tags=Business&page=1',
        'https://market.mashape.com/explore?tags=Social&page=1',
        'https://market.mashape.com/explore?tags=Communication&page=1',
        'https://market.mashape.com/explore?tags=Entertainment&page=1',
        'https://market.mashape.com/explore?tags=Media&page=1',
        'https://market.mashape.com/explore?tags=Medical&page=1',
        'https://market.mashape.com/explore?tags=Sports&page=1',
        'https://market.mashape.com/explore?tags=Reward&page=1',
        'https://market.mashape.com/explore?tags=Data&page=1',
        'https://market.mashape.com/explore?tags=Travel&page=1',
    ]

    # scrapy parameter: seconds between successive page crawls
    #download_delay = 0.25  # Disabled since each request already required multiple seconds

    #===========================================================================
    # __init__ ()
    #===========================================================================
    def __init__(self):
        self.api_varnames_xpaths = {
            'name': "//h1[contains(@class,'name')]",
            'owner': "//div[contains(@class,'owner')]",
            'website': [ "//div[contains(@class,'website')]", "get_attribute", "href" ],
            'tags': [ "//div[contains(@class,'tags')]/a", "concat", ", " ],
            'description': "//p[contains(@class,'description')]",
            'auth_info': "//div[@class='request'][1]/div[@class='authentication-details']//following-sibling::div[@class='description']",
        }

        # Authentication parameters
        self.auth_params_xpath = "//h4[contains(., 'Authentication parameters')]//following-sibling::div[contains(@class, 'parameter') and contains(@class, 'authentication')]"
        self.auth_params_varnames_xpaths = {
            'name': ".//div[1]/span",
            'description': ".//div[2]/span",
        }

        # Authentication headers
        self.auth_headers_xpath = "//h4[contains(., 'Authentication headers')]//following-sibling::div[contains(@class, 'parameter') and contains(@class, 'authentication')]"
        self.auth_headers_varnames_xpaths = {
            'name': ".//div[1]/span",
            'description': ".//div[2]/span",
        }

        # Default Mashape authentication headers
        self.auth_mashape_default_headers = {
            'name': "X-Mashape-Key",
            'description': "Sign up to Mashape.com to get your key",
        }

        # All sections with class "endpoint" that also have attribute id
        # (if all endpoints require an auth header as in https://market.mashape.com/drillster/drillster-1-0,
        # this information is contained in an "endpoint" class without id. don't select these)
        self.endpoints_xpath = "//section[@class='endpoint' and @id]"
        self.endpoint_varnames_xpaths = {
            'name': ".//div[@class='request']/div[@class='endpoint-name']/span",
            'description': ".//div[@class='request']/div[@class='description']",
            'method': ".//div[@class='response']/pre/div/span[@class='verb']",
            'host': ".//div[@class='response']/pre/div/span/span[@class='host']",
            'route': ".//div[@class='response']/pre/div/span/span[@class='route']",
            'curl_example': ".//div[@class='code-snippet']",
            'response': ".//div[@class='response']//div[@class='model-name']/span[contains(@class, 'code')] | " + \
                        ".//div[@class='response']//div[@class='model-name']/pre[contains(@class, 'code')]",
            'response_name': ".//div[@class='response']//div[@class='model-name']/span[@class='name truncate']",
            'response_example': ".//div[@class='response']//pre[contains(@class, 'model-preview')]",
        }

        # All parameter divs after <h4>Request Headers</h4> with class "parameter typed authorization"
        self.request_headers_xpath = ".//div[@class='request']/h4[contains(., 'Request Headers')][1]/following-sibling::div[contains(@class, 'parameter') and contains(@class, 'typed') and contains(@class, 'authorization')]"
        self.request_headers_varnames_xpaths = {
            'name': ".//span[contains(@class, 'name')]",
            'type': ".//span[contains(@class, 'type')]",
            'description': ".//p",
        }

        # All parameter divs after <h4>URL Parameters</h4> and before the 2nd <h4> (Url params is always the first <h4> within request div)
        self.url_params_xpath = ".//div[@class='request']/h4[contains(., 'URL Parameters')][1]/following-sibling::div[contains(@class, 'parameter') and contains(@class, 'typed')][count(preceding-sibling::h4)=1]"
        self.url_param_varnames_xpaths = {
            'name': ".//span[contains(@class, 'name')]",
            'type': ".//span[contains(@class, 'type')]",
            'description': ".//p",
        }

        # The single div after <h4>Request Payload</h4>
        self.request_payload_xpath = ".//div[@class='request']/h4[contains(., 'Request Payload')][1]/following-sibling::div[@class='parameter model']"
        self.request_payload_varnames_xpaths = {
            'name': ".//div[contains(@class, 'model-name')]/span[contains(@class,'name')]",
            'type': ".//div[contains(@class, 'model-name')]/span[contains(@class,'code')]",
            'description': ".//div[contains(@class, 'model-description')]/span",
            'example': ".//pre[contains(@class, 'model-preview')]/div",
        }

        # All parameter divs after <h4>Form Encoded Parameters</h4> (Form encoded params is always the last <h4> within request div)
        self.body_params_xpath = ".//div[@class='request']/h4[contains(., 'Form Encoded Parameters')][1]/following-sibling::div[contains(@class, 'parameter') and contains(@class, 'typed')]"
        self.body_param_varnames_xpaths = {
            'name': ".//span[contains(@class, 'name')]",
            'type': ".//span[contains(@class, 'type')]",
            'description': ".//p",
        }

        # Initialized our headless browser
        self.browser = webdriver.PhantomJS()

        # Function to be called when spider terminates
        dispatcher.connect(self.quit, signals.spider_closed)

        self.apis_extracted = 0

        print "["

    #===========================================================================
    # quit ()
    #===========================================================================
    def quit(self):
        print "]"
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

        # Get API authentication parameters
        api['auth_params'] = list()
        for elem_param in self.browser.find_elements_by_xpath(self.auth_params_xpath):
            param = dict()
            self.add_elements_to_dict_if_existing(param, elem_param, self.auth_params_varnames_xpaths)
            api['auth_params'].append(param)

        # Get API authentication headers
        api['auth_headers'] = list()
        for elem_param in self.browser.find_elements_by_xpath(self.auth_headers_xpath):
            param = dict()
            self.add_elements_to_dict_if_existing(param, elem_param, self.auth_headers_varnames_xpaths)
            api['auth_params'].append(param)
        api['auth_headers'].append(self.auth_mashape_default_headers)

        # Get API endpoints
        api['endpoints'] = list()
        for elem_endpoint in self.browser.find_elements_by_xpath(self.endpoints_xpath):

            # Get endpoint description
            endpoint = dict()
            self.add_elements_to_dict_if_existing(endpoint, elem_endpoint, self.endpoint_varnames_xpaths)

            # Get endpoint request payload params
            endpoint['payload'] = list()
            for elem_param in elem_endpoint.find_elements_by_xpath(self.request_payload_xpath):
                param = dict()
                self.add_elements_to_dict_if_existing(param, elem_param, self.request_payload_varnames_xpaths)
                endpoint['payload'].append(param)

            # Get endpoint request headers
            endpoint['request_headers'] = list()
            for elem_param in elem_endpoint.find_elements_by_xpath(self.request_headers_xpath):
                param = dict()
                self.add_elements_to_dict_if_existing(param, elem_param, self.request_headers_varnames_xpaths)
                endpoint['request_headers'].append(param)

            # Get endpoint URL params
            endpoint['url_params'] = list()
            for elem_param in elem_endpoint.find_elements_by_xpath(self.url_params_xpath):
                param = dict()
                self.add_elements_to_dict_if_existing(param, elem_param, self.url_param_varnames_xpaths)
                param['required'] = "true" if "required" in elem_param.get_attribute("class") else "false"
                endpoint['url_params'].append(param)

            # Get endpoint body params
            endpoint['body_params'] = list()
            for elem_param in elem_endpoint.find_elements_by_xpath(self.body_params_xpath):
                param = dict()
                self.add_elements_to_dict_if_existing(param, elem_param, self.body_param_varnames_xpaths)
                param['required'] = "true" if "required" in elem_param.get_attribute("class") else "false"
                endpoint['body_params'].append(param)

            # Remove empty lists
            self.remove_empty_lists(endpoint)

            api['endpoints'].append(endpoint)

        # Remove empty lists
        self.remove_empty_lists(api)

        print "%s%s" % ("," if self.apis_extracted > 0 else "", json.dumps(api, sort_keys=True))
        self.apis_extracted += 1

    #===========================================================================
    # add_elements_to_dict_if_existing ()
    #===========================================================================
    def add_elements_to_dict_if_existing(self, dictionary, dom_element, varnames_xpaths):
        for key in varnames_xpaths.keys():
            varname = key
            if (isinstance(varnames_xpaths[key], basestring)):
                xpath = varnames_xpaths[key]
                try:
                    dictionary[varname] = self.strip_tags(dom_element.find_elements_by_xpath(xpath)[0].get_attribute("innerHTML"))
                except:
                    pass

            elif (isinstance(varnames_xpaths[key], list)):
                xpath = varnames_xpaths[key][0]
                operation = varnames_xpaths[key][1]

                if (operation == "concat"):
                    delim = varnames_xpaths[key][2]
                    if dom_element.find_elements_by_xpath(xpath):
                        dictionary[varname] = delim.join(map(lambda x: x.text, dom_element.find_elements_by_xpath(xpath)))

                if (operation == "get_attribute"):
                    attr = varnames_xpaths[key][2]
                    if dom_element.find_elements_by_xpath(xpath):
                        dictionary[varname] = dom_element.find_elements_by_xpath(xpath)[0].get_attribute(attr)

    #===========================================================================
    # get_next_url ()
    #===========================================================================
    def get_next_url(self, url):
        pos = url.rfind("=")
        num = int(url[pos+1:])
        return url[:pos+1] + str(num + 1)

    #===========================================================================
    # remove_empty_lists ()
    #===========================================================================
    def remove_empty_lists(self, dictionary):
        for key in dictionary.keys():
            if (isinstance(dictionary[key], list) and dictionary[key] == []):
                dictionary.pop(key, None)

    #===========================================================================
    # MLStripper ()
    #===========================================================================
    # from http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
    class MLStripper(HTMLParser):
        def __init__(self):
            self.reset()
            self.fed = []
        def handle_data(self, d):
            self.fed.append(d)
        def handle_entityref(self, name):
            self.fed.append('&%s;' % name)
        def get_data(self):
            return ''.join(self.fed)

    #===========================================================================
    # strip_tags ()
    #===========================================================================
    # from http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
    def strip_tags(self, html):
        #parser = HTMLParser()
        #html = parser.unescape(html)
        s = self.MLStripper()
        s.feed(html)
        return s.get_data()
