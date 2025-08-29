from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time

def scrape_seats_aero(origin, destination, start_date, end_date, programs=None, alliances=None, transfer_partners=None, points_min=None, points_max=None, days=None):
    """
    Scrapes seats.aero for flight deals.

    Args:
        origin (str): The origin airport IATA code.
        destination (str): The destination airport IATA code.
        start_date (str): The start date of the travel date range in YYYY-MM-DD format.
        end_date (str): The end date for the travel date range in YYYY-MM-DD format.
        programs (list, optional): List of frequent flyer programs to filter by. Defaults to None.
        alliances (list, optional): List of airline alliances to filter by. Defaults to None.
        transfer_partners (list, optional): List of transfer partners to filter by. Defaults to None.
        points_min (int, optional): Minimum points required for a deal. Defaults to None.
        points_max (int, optional): Maximum points required for a deal. Defaults to None.
        days (int, optional): Number of days to search around the specified date. Defaults to None.

    Returns:
        list: A list of flight options, where each option is a dictionary.
    """
    url = f"https://seats.aero/search?min_seats=1&applicable_cabin=any&max_fees=40000&disable_live_filtering=false&date={start_date}&origins={origin}&destinations={destination}"
    if days and days > 0:
        url += f"&additional_days_num={days}"

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
            
            # Apply filters via UI interaction
            if programs:
                page.click('button:has-text("Programs")')
                page.wait_for_selector('.custom-dropdown-menu')
                for program in programs:
                    page.check(f'label:has-text("{program}")')
                    time.sleep(0.5) # Wait for live update
                page.click('button:has-text("Programs")') # Close dropdown
            
            if alliances:
                page.click('button:has-text("Alliances")')
                page.wait_for_selector('.custom-dropdown-menu')
                for alliance in alliances:
                    page.check(f'label:has-text("{alliance}")')
                    time.sleep(0.5)
                page.click('button:has-text("Alliances")')

            if transfer_partners:
                page.click('button:has-text("Transfer Partners")')
                page.wait_for_selector('.custom-dropdown-menu')
                for partner in transfer_partners:
                    page.check(f'label:has-text("{partner}")')
                    time.sleep(0.5)
                page.click('button:has-text("Transfer Partners")')

            if points_min or points_max:
                page.click('button:has-text("Points")')
                if points_min:
                    page.fill('input[placeholder="Min"]', str(points_min))
                if points_max:
                    page.fill('input[placeholder="Max"]', str(points_max))
                page.click('button:has-text("Points")')

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
    origin = "JFK"
    destination = "LHR"
    start_date = "2025-09-01"
    end_date = "2025-09-10"
    
    deals = scrape_seats_aero(origin, destination, start_date, end_date, days=3)
    
    if deals:
        for deal in deals:
            print(deal)
    else:
        print("No deals found.")
