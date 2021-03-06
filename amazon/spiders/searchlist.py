import scrapy
from scrapy.loader import ItemLoader
#from scrapy.crawler import CrawlerProcess
#from twisted.internet import reactor, defer
#from scrapy.crawler import CrawlerRunner
#from scrapy.utils.log import configure_logging
from w3lib.html import remove_tags
import sys
sys.path.append('..')
from items import *

class searchquery(scrapy.Spider):
	name = 'listing'

	searchitem = 'Shaver'
	
	start_urls =['https://www.amazon.com/s?k='+searchitem.replace(' ','+').strip()]
	
	
	def replacenewspace(self,value):
		return value.replace('\n',"").strip()

	def getweight(self,value):
		return value.split(" inches; ")	
	
	def parse(self,response):
		for products in response.css('div.s-result-item.s-asin'):
			a = ItemLoader(item=AmazonItem(),selector=products)
			a.add_css('url','a.a-link-normal.a-text-normal::attr(href)')
			a.add_css('img','img::attr(src)')
			a.add_css('ASIN','div.s-result-item.s-asin::attr(data-asin)')
			yield scrapy.Request('https://www.amazon.com'+ products.css('a.a-link-normal.a-text-normal::attr(href)').get(), callback=self.parse_2, meta={'loader': a},)

		next_page = response.css("li.a-last").css("a::attr(href)").get()

		if next_page:
			yield scrapy.Request('https://www.amazon.com'+next_page, callback=self.parse)
			
			
			
	def parse_2(self,response):
		l = ItemLoader(item=AmazonItem(),selector=response, parent=response.meta['loader'])
		l.add_value('rating',response.css('span.reviewCountTextLinkedHistogram.noUnderline::attr(title)').get())
		l.add_css('reviews','span[id="acrCustomerReviewText"]')
		
		l.add_css('title','span[id="productTitle"]')
		
		if len(response.css('span[id="newBuyBoxPrice"]'))>0:
			l.add_css('price','span[id="newBuyBoxPrice"]')
		elif len(response.css('span.a-size-medium.a-color-price.offer-price.a-text-normal')) >0:
			l.add_css('price','span.a-size-medium.a-color-price.offer-price.a-text-normal')
		else:
			l.add_css('price','span[id="price_inside_buybox"]')

		l.add_css('brand','a[id="bylineInfo"]')
		l.add_value('description',''.join(list(map(lambda a : a.encode('ascii', errors='ignore').decode('utf-8'),response.css('ul.a-unordered-list.a-vertical.a-spacing-mini').css('span.a-list-item::text').getall()))))

		if len(response.xpath('//*[@id="sellerProfileTriggerId"]')) >0:
			l.add_css('buybox','a[id="sellerProfileTriggerId"]')
		else:
			l.add_css('buybox','span.tabular-buybox-text')

		l.add_xpath('activeseller','//*[@id="olp_feature_div"]/div[2]')
		
		if len(response.css('div.a-row.a-spacing-base').css('tr')) > 0:

			for infoss in response.css('div.a-row.a-spacing-base').css('tr'):
				c = ItemLoader(item=AmazonItem(),selector=infoss, parent=response.meta['loader'])
				if 'Weight' in self.replacenewspace(infoss.get()):
					c.add_css('weight_lbs','td')
				elif 'inches' in self.replacenewspace(infoss.get()):
					c.add_css('Dimensions','td')
				elif 'Date First' in self.replacenewspace(infoss.get()):
					c.add_css('firstdate','td')
				elif 'Sellers' in self.replacenewspace(infoss.get()):
					c.add_value('bestseller',infoss.get())
			yield c.load_item()

		elif len(response.css('ul.a-unordered-list.a-nostyle.a-vertical.a-spacing-none.detail-bullet-list').css('li')) > 0:
			for info in response.css('ul.a-unordered-list.a-nostyle.a-vertical.a-spacing-none.detail-bullet-list').css('li'):
				d = ItemLoader(item=AmazonItem(),selector=info, parent=response.meta['loader'])

				if 'inches' in self.replacenewspace(info.get()) or 'inches;' in self.replacenewspace(info.get()) and 'Ounces' in self.replacenewspace(info.get()) or 'pounds' in self.replacenewspace(info.get()) or 'Pounds' in self.replacenewspace(info.get()):

					d.add_value('weight_lbs',self.getweight(remove_tags(info.css('span').get()))[1])
					d.add_value('Dimensions',self.getweight(remove_tags(info.css('span').get()))[0])

				elif 'Date First' in self.replacenewspace(info.get()):
					d.add_value('firstdate',info.get())
				elif 'Sellers' in self.replacenewspace(info.get()):
					d.add_value('bestseller',info.get())
			yield d.load_item()
