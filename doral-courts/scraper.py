import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, time

@dataclass
class Court:
    name: str
    sport_type: str
    location: str
    surface_type: str
    availability_status: str
    date: str
    time_slot: str
    price: Optional[str] = None

class DoralCourtsScraper:
    def __init__(self):
        self.base_url = "https://fldoralweb.myvscloud.com/webtrac/web/search.html"
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        })

    def _get_csrf_token(self) -> str:
        """Extract CSRF token from the initial page load."""
        response = self.session.get(self.base_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_input = soup.find('input', {'name': '_csrf_token'})
        return csrf_input['value'] if csrf_input else ""

    def _build_search_params(self, date: str = None, begin_time: str = "08:00 am", page: int = 1) -> dict:
        """Build search parameters for the court availability request."""
        if not date:
            from datetime import datetime
            date = datetime.now().strftime("%m/%d/%Y")
            
        csrf_token = self._get_csrf_token()
        
        return {
            'Action': 'Start',
            'SubAction': '',
            '_csrf_token': csrf_token,
            'date': date,
            'begintime': begin_time,
            'type': ['Pickleball Court', 'Tennis Court'],
            'subtype': '',
            'category': '',
            'features': '',
            'keyword': '',
            'keywordoption': 'Match One',
            'blockstodisplay': '24',
            'frheadcount': '0',
            'primarycode': '',
            'features1': '',
            'features2': '',
            'features3': '',
            'features4': '',
            'features5': '',
            'features6': '',
            'features7': '',
            'features8': '',
            'display': 'Detail',
            'search': 'yes',
            'page': str(page),
            'module': 'fr',
            'multiselectlist_value': '',
            'frwebsearch_buttonsearch': 'yes'
        }

    def _parse_court_data(self, soup: BeautifulSoup) -> List[Court]:
        """Parse court data from the HTML response."""
        courts = []
        
        # Find all court entries in the search results
        court_entries = soup.find_all('div', class_='search-result-item') or soup.find_all('tr', class_='search-result')
        
        for entry in court_entries:
            try:
                # Extract court information from the HTML structure
                name_elem = entry.find('td', class_='facility-name') or entry.find('div', class_='facility-name')
                name = name_elem.get_text(strip=True) if name_elem else "Unknown Court"
                
                # Determine sport type from the name or other indicators
                sport_type = "Tennis" if "tennis" in name.lower() else "Pickleball"
                
                # Extract location information
                location_elem = entry.find('td', class_='location') or entry.find('div', class_='location')
                location = location_elem.get_text(strip=True) if location_elem else "Doral"
                
                # Extract surface type if available
                surface_elem = entry.find('td', class_='surface') or entry.find('div', class_='surface')
                surface_type = surface_elem.get_text(strip=True) if surface_elem else "Hard Court"
                
                # Extract availability status
                status_elem = entry.find('td', class_='availability') or entry.find('div', class_='availability')
                availability_status = status_elem.get_text(strip=True) if status_elem else "Available"
                
                # Extract date and time information
                date_elem = entry.find('td', class_='date') or entry.find('div', class_='date')
                date = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%m/%d/%Y")
                
                time_elem = entry.find('td', class_='time') or entry.find('div', class_='time')
                time_slot = time_elem.get_text(strip=True) if time_elem else "Unknown"
                
                # Extract price if available
                price_elem = entry.find('td', class_='price') or entry.find('div', class_='price')
                price = price_elem.get_text(strip=True) if price_elem else None
                
                court = Court(
                    name=name,
                    sport_type=sport_type,
                    location=location,
                    surface_type=surface_type,
                    availability_status=availability_status,
                    date=date,
                    time_slot=time_slot,
                    price=price
                )
                
                courts.append(court)
                
            except Exception as e:
                print(f"Error parsing court entry: {e}")
                continue
                
        return courts

    def fetch_courts(self, date: str = None, sport_filter: str = None) -> List[Court]:
        """Fetch court availability data from the website."""
        all_courts = []
        page = 1
        
        while True:
            params = self._build_search_params(date=date, page=page)
            
            try:
                response = self.session.get(self.base_url, params=params)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                courts = self._parse_court_data(soup)
                
                if not courts:
                    break
                    
                all_courts.extend(courts)
                
                # Check if there's a next page
                next_page = soup.find('a', text='Next') or soup.find('a', class_='next-page')
                if not next_page:
                    break
                    
                page += 1
                
            except requests.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                break
                
        # Apply sport filter if specified
        if sport_filter:
            all_courts = [court for court in all_courts if court.sport_type.lower() == sport_filter.lower()]
            
        return all_courts