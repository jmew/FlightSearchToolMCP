import argparse
from scrapers import seats_aero
import sys
import json
import re

# Placeholder for cash price. In the future, this will be retrieved from a reliable source.
CASH_PRICE = 1000 

def parse_fees(fees_str):
    if fees_str is None:
        return 0.0
    
    fees_str = fees_str.replace('$', '').replace('€', '').replace('USD', '').replace('EUR', '').strip()
    try:
        return float(fees_str)
    except (ValueError, TypeError):
        return 0.0

def deduplicate_deals(deals):
    unique_deals = []
    seen_deals = set()

    for deal in deals:
        for cabin in ['economy', 'premium', 'business', 'first']:
            if deal[cabin]:
                points = deal[cabin].get('points')
                route = deal.get('route')
                date = deal.get('date')
                
                deal_id = (date, route, points, cabin)
                if deal_id not in seen_deals:
                    unique_deals.append(deal)
                    seen_deals.add(deal_id)
    return unique_deals

def main():
    """
    Main function to run the flight deal finder.
    """
    parser = argparse.ArgumentParser(description="Find the best flight deals using points or cash.")
    parser.add_argument("origin", help="Origin airport IATA code (e.g., SFO)")
    parser.add_argument("destination", help="Destination airport IATA code (e.g., LAX)")
    parser.add_argument("start_date", help="Start date for the travel search in YYYY-MM-DD format.")
    parser.add_argument("end_date", help="End date for the travel search in YYYY-MM-DD format.")
    
    # Optional filter arguments
    parser.add_argument("--programs", nargs='+', help="List of frequent flyer programs to filter by.")
    parser.add_argument("--alliances", nargs='+', help="List of airline alliances to filter by.")
    parser.add_argument("--transfer_partners", nargs='+', help="List of transfer partners to filter by.")
    parser.add_argument("--points_min", type=int, help="Minimum points required for a deal.")
    parser.add_argument("--points_max", type=int, help="Maximum points required for a deal.")
    parser.add_argument("--days", type=int, help="Number of days to search around the specified date.")

    args = parser.parse_args()
    
    print(f"Searching for flights from {args.origin} to {args.destination} between {args.start_date} and {args.end_date}...")
    
    try:
        # Scrape for points deals
        points_deals = seats_aero.scrape_seats_aero(
            args.origin, 
            args.destination, 
            args.start_date, 
            args.end_date,
            programs=args.programs,
            alliances=args.alliances,
            transfer_partners=args.transfer_partners,
            points_min=args.points_min,
            points_max=args.points_max,
            days=args.days
        )
    except Exception as e:
        print(f"Error scraping seats.aero: {e}", file=sys.stderr)
        points_deals = []

    if not points_deals:
        print("No deals found.")
        return

    processed_deals = []
    for deal in points_deals:
        for cabin in ['economy', 'premium', 'business', 'first']:
            if deal[cabin]:
                points = deal[cabin].get('points')
                fees_str = deal[cabin].get('fees')
                fees = parse_fees(fees_str)

                if points and points > 0:
                    vpp = (CASH_PRICE - fees) / points
                    
                    processed_deal = {
                        "date": deal['date'],
                        "program": deal['program'],
                        "route": deal['route'],
                        "cabin": cabin,
                        "points": points,
                        "fees": fees_str,
                        "vpp": round(vpp, 4)
                    }
                    processed_deals.append(processed_deal)

    # Sort deals by VPP in descending order (best value first)
    sorted_deals = sorted(processed_deals, key=lambda x: x['vpp'], reverse=True)

    # Deduplicate deals
    unique_deals = []
    seen_deals = set()
    for deal in sorted_deals:
        deal_id = (deal['date'], deal['route'], deal['points'], deal['cabin'])
        if deal_id not in seen_deals:
            unique_deals.append(deal)
            seen_deals.add(deal_id)


    for i, deal in enumerate(unique_deals):
        print(f"--- Deal #{i+1} ---")
        print(f"  Date: {deal['date']}")
        print(f"  Program: {deal['program']}")
        print(f"  Route: {deal['route']}")
        print(f"  Cabin: {deal['cabin'].capitalize()}")
        print(f"  Points: {deal['points']}")
        print(f"  Fees: {deal['fees']}")
        print(f"  VPP: {deal['vpp']}")
        print("-" * 16)


    print("Search complete.")

if __name__ == "__main__":
    main()