import scrapy
import json
import sys

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
    # parse ()
    #===========================================================================
    def parse(self, response):
        yield scrapy.Request(response.url, self.parse_api_directory_page)

    #===========================================================================
    # parse_api_directory_page ()
    #===========================================================================
    def parse_api_directory_page(self, response):
        # Parse current directory page
        for tr in response.xpath("//tr[@class='list-api-row']"):
            url = tr.xpath("td[2]/a/@href").extract()[0]
            fullurl = response.urljoin(url)
            yield scrapy.Request(fullurl, self.parse_api_page)

    #===========================================================================
    # parse_api_page ()
    #===========================================================================
    def parse_api_page(self, response):
        print response.url
        return
        d = dict()
        for div in response.xpath("//div[@id='tabs-content']/div[2]/div[@class='field']"):
            key = str(div.xpath("label/text()").extract()[0])
            try:
                value = str(div.xpath("span/a/text()").extract()[0])
            except:
                value = str(div.xpath("span/text()").extract()[0])
            d[key] = value
        print json.dumps(d, sort_keys=True)
