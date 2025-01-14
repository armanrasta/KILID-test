from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException, WebDriverException
from datetime import datetime
import json
from src.processor.celery_tasks import process_property_details
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BayutSeleniumScraper:
    def __init__(self):
        options = Options()
        options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30, poll_frequency=1)  # Increased timeout
        self.base_url = 'https://www.bayut.com/for-sale/property/dubai/?sort=date_desc'

    def scrape(self):
        try:
            self.driver.get(self.base_url)
            while True:
                # Wait for listings to load
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul li article')))
                time.sleep(2)  # Extra wait for dynamic content

                # Get all property cards
                property_cards = self.driver.find_elements(By.CSS_SELECTOR, 'ul li article')
                
                for card in property_cards:
                    try:
                        # Get basic info from card
                        property_data = self._extract_card_info(card)
                        if property_data is None:
                            continue
                        
                        # Get detail page URL
                        detail_url = card.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                        
                        # Visit detail page and get full info
                        self._get_property_details(detail_url, property_data)
                        
                    except Exception as e:
                        print(f"Error processing property card: {str(e)}")
                        continue

                # Try to go to next page
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 'a[title="Next"]')
                    if not next_button.is_enabled():
                        break
                    next_button.click()
                    time.sleep(2)
                except:
                    break

        finally:
            self.driver.quit()

    def _extract_card_info(self, card):
        """Extract information from the property card."""
        try:
            # Get JSON-LD data
            script = card.find_element(By.CSS_SELECTOR, 'script[type="application/ld+json"]').get_attribute('innerHTML')
            data = json.loads(script)
            
            # Map the fields to match the model's field names exactly
            return {
                'property_id': data['url'].split('-')[-1].replace('.html', ''),
                'property_type': data.get('@type'),
                'title': data.get('name'),
                'latitude': data['geo']['latitude'],
                'longitude': data['geo']['longitude'],
                'area': data['floorSize']['value'].replace(',', '') if data.get('floorSize', {}).get('value') else None,
                'beds': str(data['numberOfRooms']['value']) if data.get('numberOfRooms', {}).get('value') else None,
                'baths': str(data.get('numberOfBathroomsTotal')),
                'image_url': data.get('image', ''),
                'country': data['address']['addressCountry'],
                'location': data['address']['addressLocality'],
                'region': data['address']['addressRegion'],
                'crawl_timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error extracting card info: {str(e)}")
            return None

    def _get_property_details(self, url, property_data):
        """Get detailed property information from property page."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Open new tab and switch to it
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                print(f"\nProcessing URL: {url}")
                self.driver.get(url)
                
                # Wait for the page to load completely
                self.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(5)  # Additional wait for dynamic content

                # Try different selectors to ensure the page is loaded
                try:
                    # Wait for any of these elements to be present
                    selectors = [
                        'ul[aria-label="Property details"]',
                        'div._948d9e0a',  # Common class in property details
                        'h1.fcca24e0',    # Property title
                        'div[role="main"]' # Main content area
                    ]
                    
                    for selector in selectors:
                        try:
                            element = self.wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            if element:
                                print(f"Found element with selector: {selector}")
                                break
                        except:
                            continue

                except TimeoutException:
                    print("Timeout waiting for page elements")
                    retry_count += 1
                    continue

                # Extract property details
                details = {}
                
                # Get basic information
                try:
                    details['title'] = self._safe_get_text(
                        self.driver.find_element(By.CSS_SELECTOR, 'h1.fcca24e0')
                    )
                    print(f"Title: {details.get('title')}")
                except:
                    print("Could not find title")

                # Get price information
                try:
                    price_element = self.driver.find_element(
                        By.CSS_SELECTOR, 'span[aria-label="Price"], span.fcca24e0'
                    )
                    details['price'] = price_element.text
                    print(f"Price: {details.get('price')}")
                except:
                    print("Could not find price")

                # Update property data with what we found
                property_data.update(details)

                # Extract other information
                self._extract_additional_details(property_data)
                
                print("\nFinal Property Data:")
                print(json.dumps(property_data, indent=2))
                
                # Queue the data for processing
                process_property_details.delay(property_data)
                print(f"Queued property {property_data['property_id']}")
                
                break  # Success, exit retry loop

            except WebDriverException as e:
                print(f"Error processing property: {str(e)}")
                retry_count += 1
                time.sleep(2)
                
            finally:
                try:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                except:
                    pass

        if retry_count == max_retries:
            print(f"Failed to process property after {max_retries} attempts")

    def _wait_and_get_element(self, selector, timeout=10, by=By.CSS_SELECTOR):
        """Wait for element and return it when available."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            print(f"Timeout waiting for element: {selector}")
            return None
        except Exception as e:
            print(f"Error finding element {selector}: {str(e)}")
            return None

    def _wait_and_get_elements(self, selector, timeout=10, by=By.CSS_SELECTOR):
        """Wait for elements and return them when available."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, selector))
            )
        except TimeoutException:
            print(f"Timeout waiting for elements: {selector}")
            return []
        except Exception as e:
            print(f"Error finding elements {selector}: {str(e)}")
            return []

    def _safe_get_text(self, element):
        """Safely get text from element."""
        try:
            return element.text.strip() if element else None
        except:
            return None

    def _extract_property_details(self):
        """Extract all property details with proper error handling."""
        details = {}
        try:
            # Extract all labeled fields
            labeled_fields = [
                'Price', 'Beds', 'Baths', 'Area', 'Type', 'Purpose', 'Property reference',
                'Completion status', 'Reactivated date', 'Handover date', 'Permit Number',
                'BRN number', 'Currency'
            ]

            for label in labeled_fields:
                try:
                    value = self._safe_get_text(
                        self.driver.find_element(By.CSS_SELECTOR, f'*[aria-label="{label}"]')
                    )
                    if value:
                        field = label.lower().replace(' ', '_')
                        details[field] = value
                        print(f"Found {label}: {value}")
                except:
                    pass

            # Extract link information
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, 'a[aria-label]')
                for link in links:
                    name = link.get_attribute('aria-label')
                    if name:
                        details['link_name'] = name
                        print(f"Found Link name: {name}")
            except:
                pass

            # Extract guide link title
            try:
                guide_title = self.driver.find_element(
                    By.CSS_SELECTOR, 'div[aria-label="Guide link title"]'
                ).text
                if guide_title:
                    details['guide_link_title'] = guide_title
                    print(f"Found Guide link title: {guide_title}")
            except:
                pass

            return details

        except Exception as e:
            print(f"Error extracting property details: {str(e)}")
            return {}

    def _extract_contact_info(self):
        """Extract contact information."""
        contact_info = {}
        try:
            dialog = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label="Dialog"]')
            contact_info['contact_number'] = dialog.find_element(By.CSS_SELECTOR, 'span[dir="ltr"]').text
            contact_info['contact_reference'] = dialog.find_element(By.CSS_SELECTOR, 'div._460a308e').text
        except:
            pass
        return contact_info

    def _extract_agency_info(self):
        """Extract agency information."""
        agency_info = {}
        try:
            agency_section = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label="Agency info"]')
            agency_info.update({
                'agent_name': self._safe_get_text(agency_section.find_element(By.CSS_SELECTOR, 'h2')),
                'agency_name': self._safe_get_text(agency_section.find_element(By.CSS_SELECTOR, 'h3[aria-label="Agency name"]')),
                'agent_rating': self._safe_get_text(agency_section.find_element(By.CSS_SELECTOR, 'span')),
                'agency_url': agency_section.find_element(By.CSS_SELECTOR, 'a[aria-label="View all properties"]').get_attribute('href')
            })
        except:
            pass
        return agency_info

    def _set_default_values(self, property_data):
        """Set default values for missing fields."""
        defaults = {
            'price': 'Not specified',
            'purpose': 'Not specified',
            'property_type': 'Not specified',
            'completion_status': 'Not specified',
            'furnishing_status': 'Not specified',
            'property_reference': 'Not available',
            'description': 'No description available',
            'usage': 'Not specified',
            'ownership': 'Not specified',
            'developer': 'Not specified',
            'building_name': 'Not specified',
            'agency_name': 'Not specified',
            'agent_name': 'Not specified',
            'currency': 'AED',
            'permit_number': 'Not available',
            'brn_number': 'Not available',
            'guide_link_title': 'Not available'
        }
        
        for field, default in defaults.items():
            if not property_data.get(field):
                property_data[field] = default

    def _extract_features(self, property_data):
        """Extract features and amenities grouped by category."""
        features = {}
        try:
            amenities_section = self.driver.find_element(By.CSS_SELECTOR, 'div._34032b68')
            feature_elements = amenities_section.find_elements(By.CSS_SELECTOR, 'span._7181e5ac')
            if feature_elements:
                features['General'] = [element.text for element in feature_elements]
                print(f"Found {len(features['General'])} direct amenities")

            try:
                more_amenities = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label="More amenities"]')
                if more_amenities.is_displayed() and more_amenities.is_enabled():
                    more_amenities.click()
                    time.sleep(1)

                    categories = self.driver.find_elements(By.CSS_SELECTOR, 'div.da8f482a')
                    for category in categories:
                        try:
                            category_name = category.find_element(By.CSS_SELECTOR, 'div._1c78af3b').text
                            feature_elements = category.find_elements(By.CSS_SELECTOR, 'span._7181e5ac')
                            features[category_name] = [element.text for element in feature_elements]
                        except:
                            continue

                    close_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Close button"]')
                    close_button.click()
                else:
                    print("More amenities button not interactable")

            except Exception as e:
                print(f"Could not open amenities dialog: {str(e)}")

                if 'description' in property_data:
                    desc = property_data['description']
                    features_section = desc.split('Features & Amenities:')
                    if len(features_section) > 1:
                        feature_lines = [line.strip('➤ ').strip() 
                                      for line in features_section[1].split('\n') 
                                      if line.strip()]
                        if feature_lines:
                            features['From Description'] = feature_lines

            return features

        except Exception as e:
            print(f"Error extracting features: {str(e)}")
            return {}

    def _extract_additional_details(self, property_data):
        """Extract additional property details with better error handling."""
        try:
            # Extract features/amenities
            features = self._extract_features(property_data)
            if features:
                property_data['features'] = features
                print(f"Found {sum(len(v) for v in features.values())} features in {len(features)} categories")

            # Extract description
            try:
                description_element = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    'div[aria-label="Property description"] span._3547dac9'
                )
                if description_element:
                    property_data['description'] = description_element.text
                    print(f"Found description: {property_data['description'][:100]}...")
            except Exception as e:
                print(f"Error extracting description: {str(e)}")
                property_data['description'] = None

            # Extract all spans with aria-labels
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'span[aria-label], div[aria-label="Property details"] span'
            )
            
            for element in elements:
                try:
                    label = element.get_attribute('aria-label')
                    if label:
                        value = element.text
                        if value:
                            property_data[label.lower().replace(' ', '_')] = value
                            print(f"Found {label}: {value}")
                except:
                    continue

        except Exception as e:
            print(f"Error extracting additional details: {str(e)}")

if __name__ == "__main__":
    try:
        scraper = BayutSeleniumScraper()
        scraper.scrape()
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"\nScraping failed: {str(e)}")
