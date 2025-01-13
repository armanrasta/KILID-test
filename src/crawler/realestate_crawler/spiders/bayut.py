import scrapy
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from src.processor.celery_tasks import process_property_details

class BayutSpider(CrawlSpider):
    name = 'bayut'
    allowed_domains = ['bayut.com']
    start_urls = ['https://www.bayut.com/for-sale/property/dubai/?sort=date_desc']
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 3,
        'COOKIES_ENABLED': False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_run_time = datetime.now()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        # Update the path to the actual location of your chromedriver
        self.driver = webdriver.Chrome(service=Service('C:/path/to/your/chromedriver.exe'), options=chrome_options)
        
    def parse_start_url(self, response):
        return self.parse_listings(response)

    def parse_listings(self, response):
        listings = response.css('ul li article')
        for listing in listings:
            json_ld = listing.css('script[type="application/ld+json"]::text').get()
            if json_ld:
                data = json.loads(json_ld)
                property_id = data['url'].split('-')[-1].replace('.html', '')
                property_data = {
                    'property_id': property_id,
                    'property_type': data['@type'],
                    'title': data['name'],
                    'latitude': data['geo']['latitude'],
                    'longitude': data['geo']['longitude'],
                    'area_sqft': float(data['floorSize']['value'].replace(',', '')),
                    'bedrooms': int(data['numberOfRooms']['value']),
                    'bathrooms': int(data['numberOfBathroomsTotal']),
                    'image_url': data.get('image', ''),
                    'country': data['address']['addressCountry'],
                    'location': data['address']['addressLocality'],
                    'region': data['address']['addressRegion'],
                    'crawl_timestamp': datetime.now().isoformat()
                }
                yield scrapy.Request(
                    url=f"https://www.bayut.com/property/details-{property_id}.html",
                    callback=self.parse_property,
                    meta={'property_data': property_data},
                    dont_filter=True  # Allow revisiting to check for updates
                )

        # Follow next page if we haven't seen these listings before
        if self._has_new_listings(listings):
            next_page = response.css('a[title="Next"]::attr(href)').get()
            if next_page:
                yield response.follow(next_page, self.parse_listings)

    def parse_property(self, response):
        property_data = response.meta['property_data']
        
        # Extract TruCheck status using the specific XPath
        self.driver.get(response.url)
        try:
            tru_check_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//*[@id="body-wrapper"]/main/div[3]/div[2]/div[2]/div[2]/div[1]/div[2]/div/ul/li[14]/article/div[2]/div[3]/div[1]/div/div'
                ))
            )
            property_data['tru_check'] = bool(tru_check_element)
        except:
            property_data['tru_check'] = False

        # Extract additional property details
        json_ld = response.css('script[type="application/ld+json"]::text').get()
        if json_ld:
            data = json.loads(json_ld)
            main_entity = data.get('mainEntity', {})
            if main_entity.get('@type') == 'Product':
                property_data.update({
                    'price': main_entity['offers'][0]['priceSpecification']['price'],
                    'price_currency': main_entity['offers'][0]['priceCurrency'],
                    'description': main_entity['description'],
                    'agent_name': main_entity['offers'][0]['offeredBy']['name'],
                    'agent_image': main_entity['offers'][0]['offeredBy']['image'],
                    'agent_organization': main_entity['offers'][0]['offeredBy']['parentOrganization']['name'],
                    'agent_organization_url': main_entity['offers'][0]['offeredBy']['parentOrganization']['url']
                })

        # Queue for async processing
        process_property_details.delay(property_data)

    def _has_new_listings(self, listings):
        """Check if we have new listings by comparing timestamps."""
        if not listings:
            return False
        
        try:
            latest_listing_time = self._extract_listing_time(listings[0])
            return latest_listing_time > self.last_run_time
        except:
            return True

    def _extract_listing_time(self, listing):
        """Extract the timestamp from a listing."""
        timestamp = listing.css('time::attr(datetime)').get()
        if timestamp:
            return datetime.fromisoformat(timestamp.rstrip('Z'))
        return datetime.now()

    def closed(self, reason):
        self.driver.quit()
