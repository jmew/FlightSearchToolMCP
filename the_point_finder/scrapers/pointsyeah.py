from playwright.sync_api import sync_playwright, TimeoutError
import json
import time

def scrape_pointsyeah(origin, destination, start_date, end_date):
    """
    Scrapes pointsyeah.com for flight deals by logging in and intercepting API calls.

    Args:
        origin (str): The origin airport IATA code.
        destination (str): The destination airport IATA code.
        start_date (str): The start date of the travel date range in YYYY-MM-DD format.
        end_date (str): The end date for the travel date range in YYYY-MM-DD format.

    Returns:
        list: A list of flight options, where each option is a dictionary.
    """
    all_deals = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Headed mode is more reliable for this site
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        # --- Login ---
        try:
            print("Navigating to login page...")
            page.goto("https://www.pointsyeah.com/login", timeout=60000)
            page.wait_for_load_state("networkidle")
            
            page.wait_for_selector('input[name="username"]', state="visible", timeout=15000)
            
            print("Entering credentials...")
            page.fill('input[name="username"]', "jepara2048@mogash.com")
            page.fill('input[name="password"]', "Password1!")
            
            submit_button = page.locator('button[type="submit"].amplify-button--primary')
            current_url = page.url
            submit_button.click()

            try:
                # Wait for the URL to change from the login page URL.
                page.wait_for_url(lambda url: url != current_url, timeout=3000)
            except TimeoutError:
                print("URL did not change after 3 seconds. Retrying click...")
                time.sleep(1)
                submit_button.click()
                # On retry, wait a bit longer for the URL to change.
                page.wait_for_url(lambda url: url != current_url, timeout=3000)

        except Exception as e:
            print(f"An error occurred during login: {e}")
            page.screenshot(path="error_login.png")
            browser.close()
            return []

        # --- Intercept API Responses ---
        def handle_response(response):
            if "flight/search/fetch_result" in response.url:
                try:
                    data = response.json()
                    results = data.get("data", {}).get("result")
                    if data.get("success") and results:
                        print(f"  -> Intercepted {len(results)} deals.")
                        all_deals.extend(results)
                    else:
                        status = data.get("data", {}).get("status", "unknown")
                        print(f"  -> Intercepted empty/processing response (status: {status}).")
                except Exception as e:
                    print(f"  -> Could not parse JSON from response: {e}")

        page.on("response", handle_response)

        # --- Perform Search ---
        multiday = "false"
        depart_date_sec = start_date
        if start_date != end_date:
            multiday = "true"
            depart_date_sec = end_date

        search_url = (
            f"https://www.pointsyeah.com/search?cabins=Economy%2CPremium+Economy%2CBusiness%2CFirst"
            f"&cabin=Economy"
            f"&banks=Amex%2CBilt%2CCapital+One%2CChase%2CCiti%2CWF"
            f"&airlineProgram=AR%2CAM%2CAC%2CKL%2CAS%2CAA%2CAV%2CDL%2CEK%2CEY%2CAY%2CIB%2CB6%2CLH%2CQF%2CSK%2CSQ%2CNK%2CTP%2CTK%2CUA%2CVS%2CVA"
            f"&tripType=1"
            f"&adults=1"
            f"&children=0"
            f"&departure={origin}"
            f"&arrival={destination}"
            f"&departDate={start_date}"
            f"&departDateSec={depart_date_sec}"
            f"&multiday={multiday}"
        )
        print(f"Navigating to search URL: {search_url}")
        page.goto(search_url, timeout=60000)

        print("Waiting for search results to load...")
        try:
            page.wait_for_selector('#nprogress', state='attached', timeout=20000)
            print("Loading bar detected.")
            page.wait_for_selector('#nprogress', state='detached', timeout=90000)
            print("Loading bar has disappeared.")
            
            print("Waiting for network to settle...")
            page.wait_for_load_state("networkidle", timeout=15000)
            print("Network has settled. Search complete.")
        except TimeoutError as e:
            print(f"Timed out waiting for results: {e}. Results may be incomplete.")
            page.screenshot(path="error_search.png")
        
        print("Finished waiting for results.")
        browser.close()

    # --- Process Data ---
    best_deals = {}
    for deal in all_deals:
        if not deal.get("routes"):
            continue
        program_name = deal.get("program")
        deal_date = deal.get("date")
        route_str = f"{deal.get('departure')} -> {deal.get('arrival')}"
        deal_key = (program_name, deal_date, route_str)
        if deal_key not in best_deals:
            best_deals[deal_key] = {
                "program": program_name,
                "route": route_str,
                "date": deal_date,
                "economy": None,
                "premium": None,
                "business": None,
                "first": None,
            }
        for route in deal["routes"]:
            payment = route.get("payment", {})
            cabin = payment.get("cabin", "").lower()
            points = payment.get("miles")
            if not cabin or points is None:
                continue
            if "premium" in cabin: cabin_key = "premium"
            elif "business" in cabin: cabin_key = "business"
            elif "first" in cabin: cabin_key = "first"
            else: cabin_key = "economy"
            current_best = best_deals[deal_key].get(cabin_key)
            if current_best is None or points < current_best['points']:
                best_deals[deal_key][cabin_key] = {
                    "points": points,
                    "fees": f"${payment.get('tax')} {payment.get('currency')}",
                    "seats": payment.get("seats"),
                    "direct": len(route.get("segments", [])) == 1
                }
    processed_deals = list(best_deals.values())
            
    return processed_deals

if __name__ == '__main__':
    deals = scrape_pointsyeah("JFK", "SFO", "2025-10-10", "2025-10-12")
    if deals:
        print(json.dumps(deals, indent=2))
    else:
        print("No deals found.")