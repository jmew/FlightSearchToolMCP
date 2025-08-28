import argparse
from scrapers import seats_aero
from api_clients import amadeus
import sys

def main():
    """
    Main function to run the flight deal finder.
    """
    parser = argparse.ArgumentParser(description="Find the best flight deals using points or cash.")
    parser.add_argument("origin", help="Origin airport IATA code (e.g., SFO)")
    parser.add_argument("destination", help="Destination airport IATA code (e.g., LAX)")
    parser.add_argument("start_date", help="Start date for the travel search in YYYY-MM-DD format.")
    parser.add_argument("end_date", help="End date for the travel search in YYYY-MM-DD format.")
    
    args = parser.parse_args()
    
    print(f"Searching for flights from {args.origin} to {args.destination} between {args.start_date} and {args.end_date}...")
    
    try:
        # Scrape for points deals
        points_deals = seats_aero.scrape_seats_aero(args.origin, args.destination, args.start_date, args.end_date)
    except Exception as e:
        print(f"Error scraping seats.aero: {e}", file=sys.stderr)
        points_deals = []

    try:
        # Get cash prices from Amadeus
        cash_prices = amadeus.get_flight_offers(args.origin, args.destination, args.start_date)
    except Exception as e:
        print(f"Error getting cash prices from Amadeus: {e}", file=sys.stderr)
        cash_prices = []

    # In the future, this is where the combination, VPP calculation, and ranking will happen.
    
    print("Search complete.")

if __name__ == "__main__":
    main()
