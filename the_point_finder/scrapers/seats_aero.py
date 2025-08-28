from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

def scrape_seats_aero(origin, destination, start_date, end_date):
    """
    Scrapes seats.aero for flight deals.

    Args:
        origin (str): The origin airport IATA code.
        destination (str): The destination airport IATA code.
        start_date (str): The start date of the travel date range in YYYY-MM-DD format.
        end_date (str): The end date of the travel date range in YYYY-MM-DD format.

    Returns:
        list: A list of flight options, where each option is a dictionary.
    """
    url = f"https://seats.aero/search?min_seats=1&applicable_cabin=any&additional_days_num=1&max_fees=40000&disable_live_filtering=false&date={start_date}&origins={origin}&destinations={destination}"
    print(f"Scraping {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        try:
            page.goto(url, timeout=60000)
            print("Page loaded.")
            
            # Check for the "no results" message
            if page.locator("text=our cached data does not track any flights between them").is_visible():
                print("No cached data available for this route.")
                return []

            print("Waiting for results...")
            page.wait_for_selector('table.dataTable tbody tr', timeout=10000) # Reduced timeout
            print("Results found.")
            
            html = page.content()
        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path="error.png")
            print("Screenshot saved to error.png")
            html = ""
        finally:
            browser.close()

    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    results_table = soup.find('table', class_='dataTable')
    
    if not results_table:
        print("No results table found.")
        return []

    deals = []
    for row in results_table.find('tbody').find_all('tr'):
        cols = row.find_all('td')
        
        date = cols[0].text.strip()
        last_seen = cols[1].text.strip()
        program = cols[2].text.strip()
        departs = cols[3].text.strip()
        arrives = cols[4].text.strip()

        def get_cabin_data(col):
            badge = col.find('span', class_='badge')
            if badge and "Not Available" not in badge.text:
                tooltip = badge.get('data-bs-original-title', '')
                points_match = re.search(r'(\d{1,3}(,\d{3})*)\s*pts', tooltip)
                fees_match = re.search(r'\+\s*([€$]\d+\.\d{2}\s*[A-Z]{3})', tooltip)
                seats_match = re.search(r'(\d+)\s*seats', tooltip)
                direct_match = "Direct" in tooltip
                
                return {
                    "points": int(points_match.group(1).replace(',', '')) if points_match else None,
                    "fees": fees_match.group(1) if fees_match else None,
                    "seats": int(seats_match.group(1)) if seats_match else None,
                    "direct": direct_match
                }
            return None

        economy = get_cabin_data(cols[5])
        premium = get_cabin_data(cols[6])
        business = get_cabin_data(cols[7])
        first = get_cabin_data(cols[8])

        deals.append({
            "date": date,
            "last_seen": last_seen,
            "program": program,
            "route": f"{departs} -> {arrives}",
            "economy": economy,
            "premium": premium,
            "business": business,
            "first": first,
        })

    return deals

if __name__ == '__main__':
    # Example usage for testing
    origin = "BRU"
    destination = "SEA"
    start_date = "2025-09-26"
    end_date = "2025-09-26"
    
    deals = scrape_seats_aero(origin, destination, start_date, end_date)
    
    if deals:
        for deal in deals:
            print(deal)
    else:
        print("No deals found.")