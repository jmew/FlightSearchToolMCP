import argparse
from scrapers import seats_aero, pointsyeah
import sys
import json

def main():
    """
    Main function to run the flight deal finder.
    """
    parser = argparse.ArgumentParser(description="Find the best flight deals using points.")
    parser.add_argument("origin", nargs='+', help="One or more origin airport IATA codes (e.g., SFO JFK)")
    parser.add_argument("destination", nargs='+', help="One or more destination airport IATA codes (e.g., LAX LHR)")
    parser.add_argument("start_date", help="Start date for the travel search in YYYY-MM-DD format.")
    parser.add_argument("end_date", help="End date for the travel search in YYYY-MM-DD format.")
    
    # Optional filter arguments
    parser.add_argument("--programs", nargs='+', help="List of frequent flyer programs to filter by.")
    parser.add_argument("--alliances", nargs='+', help="List of airline alliances to filter by.")
    parser.add_argument("--transfer_partners", nargs='+', help="List of transfer partners to filter by.")
    parser.add_argument("--points_min", type=int, help="Minimum points required for a deal.")
    parser.add_argument("--points_max", type=int, help="Maximum points required for a deal.")
    parser.add_argument("--days", type=int, help="Number of days to search around the specified date.")
    parser.add_argument("--source", default="seats.aero", choices=["seats.aero", "pointsyeah"], help="The data source to use.")

    args = parser.parse_args()
    
    origin_airports = ",".join(args.origin)
    destination_airports = ",".join(args.destination)

    print(f"Searching for flights from {origin_airports} to {destination_airports} between {args.start_date} and {args.end_date} using {args.source}...")
    
    deals = []
    try:
        if args.source == "seats.aero":
            deals = seats_aero.scrape_seats_aero(
                origin_airports, 
                destination_airports, 
                args.start_date, 
                args.end_date,
                programs=args.programs,
                alliances=args.alliances,
                transfer_partners=args.transfer_partners,
                points_min=args.points_min,
                points_max=args.points_max,
                days=args.days
            )
        elif args.source == "pointsyeah":
            deals = pointsyeah.scrape_pointsyeah(
                origin_airports, 
                destination_airports, 
                args.start_date, 
                args.end_date
            )

    except Exception as e:
        print(f"Error scraping {args.source}: {e}", file=sys.stderr)
        deals = []

    if not deals:
        print("No deals found.")
        return

    # Deduplicate deals
    unique_deals = []
    seen_deals = set()
    for deal in deals:
        deal_id = (deal['date'], deal['route'], deal['program'])
        if deal_id not in seen_deals:
            unique_deals.append(deal)
            seen_deals.add(deal_id)

    # Sort deals from best to worst based on lowest points in any cabin
    def get_best_points(deal):
        # Check cabins in order of preference
        for cabin in ['economy', 'premium', 'business', 'first']:
            if deal.get(cabin) and deal[cabin].get('points'):
                return deal[cabin]['points']
        return float('inf')  # Put deals with no points at the end

    unique_deals.sort(key=get_best_points)

    for i, deal in enumerate(unique_deals):
        print(f"--- Deal #{i+1} ---")
        print(f"  Date: {deal['date']}")
        print(f"  Program: {deal['program']}")
        print(f"  Route: {deal['route']}")
        for cabin in ['economy', 'premium', 'business', 'first']:
            if deal.get(cabin):
                print(f"  {cabin.capitalize()}:")
                print(f"    Points: {deal[cabin]['points']}")
                print(f"    Fees: {deal[cabin]['fees']}")
        print("-" * 16)

    print("Search complete.")

if __name__ == "__main__":
    main()
