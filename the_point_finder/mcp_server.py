import asyncio
from fastmcp import FastMCP
from fastmcp.tools import Tool
from scrapers import seats_aero, pointsyeah
import json
from typing import List, Optional
from fast_flights import get_flights, FlightData, Passengers

PROGRAM_MAPPING = {
    "Virgin": "Virgin Atlantic",
    "Virgin Atlantic Flying Club": "Virgin Atlantic",
    "Delta SkyMiles": "Delta",
    "Delta": "Delta",
    "American Airlines AAdvantage": "American Airlines",
    "Alaska Atmos Rewards": "Alaska Airlines",
    "Qantas Frequent Flyer": "Qantas",
    "Qantas": "Qantas",
}

def normalize_program_name(program_name: Optional[str]) -> Optional[str]:
    """Normalizes airline program names for consistent matching."""
    if not program_name:
        return None
    return PROGRAM_MAPPING.get(program_name, program_name)

class FlightSearchMCP(FastMCP):
    def __init__(self):
        super().__init__()
        tool = Tool.from_function(
            self.check_flight_points_prices,
            description="Finds the best flight deals using points from various sources.",
        )
        self.add_tool(tool)

    async def get_flight_cash_prices(self, deal: dict, cabin: str) -> None:
        """Gets cash prices for a given deal and cabin, and calculates CPP."""
        if not deal.get(cabin) or not deal[cabin].get('points'):
            return

        try:
            origin, destination = deal['route'].split(' -> ')
            flight_data = [
                FlightData(date=deal['date'], from_airport=origin, to_airport=destination)
            ]
            passengers = Passengers(adults=1)

            seat_map = {
                'economy': 'economy',
                'premium': 'premium-economy',
                'business': 'business',
                'first': 'first'
            }
            seat_type = seat_map.get(cabin)
            if not seat_type:
                return

            cash_result = get_flights(
                flight_data=flight_data,
                trip="one-way",
                passengers=passengers,
                seat=seat_type,
                fetch_mode="fallback",
            )

            if cash_result and cash_result.flights:
                # Cheapest cash price is the first result
                cheapest_flight = cash_result.flights[0]
                cheapest_price_str = cheapest_flight.price.replace('$', '').replace(',', '')
                cheapest_price = float(cheapest_price_str)
                points = deal[cabin]['points']
                cheapest_cpp = (cheapest_price / points) * 100 if points > 0 else 0
                deal[cabin]['cheapest_cash_price'] = cheapest_price
                deal[cabin]['cheapest_cpp'] = round(cheapest_cpp, 2)

                # Find exact match
                exact_match_flight = None
                award_flight_numbers = deal[cabin].get('flight_numbers')
                award_departure_time = deal[cabin].get('departure_time')

                for flight in cash_result.flights:
                    # Attempt to match by flight number if available
                    if award_flight_numbers and flight.name in " ".join(award_flight_numbers):
                        exact_match_flight = flight
                        break
                    # Fallback to matching by departure time
                    elif award_departure_time and flight.departure and award_departure_time in flight.departure:
                        exact_match_flight = flight
                        break
                
                if exact_match_flight:
                    exact_price_str = exact_match_flight.price.replace('$', '').replace(',', '')
                    exact_price = float(exact_price_str)
                    exact_cpp = (exact_price / points) * 100 if points > 0 else 0
                    deal[cabin]['exact_cash_price'] = exact_price
                    deal[cabin]['exact_cpp'] = round(exact_cpp, 2)
                else:
                    deal[cabin]['exact_cash_price'] = 'N/A'
                    deal[cabin]['exact_cpp'] = 'N/A'

        except Exception as e:
            print(f"Error getting cash price for {deal['route']} ({cabin}): {e}")

    async def check_flight_points_prices(
        self,
        origin_airports: List[str],
        destination_airports: List[str],
        start_date: str,
        end_date: str,
        programs: Optional[List[str]] = None,
        alliances: Optional[List[str]] = None,
        transfer_partners: Optional[List[str]] = None,
        points_min: Optional[int] = None,
        points_max: Optional[int] = None,
        days: Optional[int] = None,
    ) -> str:
        """
        Checks for flight points prices across different platforms.

        Args:
            origin_airports: List of origin airport IATA codes (e.g., ["SFO", "JFK"]).
            destination_airports: List of destination airport IATA codes (e.g., ["LAX", "LHR"]).
            start_date: Start date for the travel search in YYYY-MM-DD format.
            end_date: End date for the travel date range in YYYY-MM-DD format.
            programs: List of frequent flyer programs to filter by.
            alliances: List of airline alliances to filter by.
            transfer_partners: List of transfer partners to filter by.
            points_min: Minimum points required for a deal.
            points_max: Maximum points required for a deal.
            days: Number of days to search around the specified date.

        Returns:
            A JSON string with all available deals and the cheapest deal found.
        """
        loop = asyncio.get_event_loop()
        origin_str = ",".join(origin_airports)
        dest_str = ",".join(destination_airports)

        print(f"Searching for flights from {origin_str} to {dest_str} between {start_date} and {end_date}...")

        # Run scrapers in parallel
        seats_aero_task = loop.run_in_executor(
            None,
            seats_aero.scrape_seats_aero,
            origin_str,
            dest_str,
            start_date,
            end_date,
            programs,
            alliances,
            transfer_partners,
            points_min,
            points_max,
            days,
        )
        pointsyeah_task = loop.run_in_executor(
            None, pointsyeah.scrape_pointsyeah, origin_str, dest_str, start_date, end_date
        )

        all_deals = []
        try:
            seats_aero_deals = await seats_aero_task
            for deal in seats_aero_deals:
                deal["source"] = "seats.aero"
            all_deals.extend(seats_aero_deals)
            print(f"Found {len(seats_aero_deals)} deals on seats.aero")
        except Exception as e:
            print(f"Error scraping seats.aero: {e}")

        try:
            pointsyeah_deals = await pointsyeah_task
            for deal in pointsyeah_deals:
                deal["source"] = "pointsyeah"
            all_deals.extend(pointsyeah_deals)
            print(f"Found {len(pointsyeah_deals)} deals on pointsyeah")
        except Exception as e:
            print(f"Error scraping pointsyeah: {e}")

        if not all_deals:
            return json.dumps({"all_deals": [], "cheapest_deal": None}, indent=2)

        # Deduplicate and merge deals
        merged_deals = {}
        for deal in all_deals:
            normalized_program = normalize_program_name(deal.get("program"))
            if not normalized_program:
                continue  # Skip deals without a program name

            deal_id = (deal.get("date"), deal.get("route"), normalized_program)

            if deal_id not in merged_deals:
                deal["program"] = normalized_program
                merged_deals[deal_id] = deal
            else:
                existing_deal = merged_deals[deal_id]
                # Merge cabin data, keeping the best (lowest points)
                for cabin in ["economy", "premium", "business", "first"]:
                    new_cabin_data = deal.get(cabin)
                    if not new_cabin_data or not new_cabin_data.get("points"):
                        continue

                    existing_cabin_data = existing_deal.get(cabin)
                    if (
                        not existing_cabin_data
                        or not existing_cabin_data.get("points")
                        or new_cabin_data["points"] < existing_cabin_data["points"]
                    ):
                        existing_deal[cabin] = new_cabin_data
                        # If sources differ, mark as 'multiple'
                        if "source" in existing_deal and existing_deal["source"] != deal.get("source"):
                            existing_deal["source"] = "multiple"
        
        unique_deals = list(merged_deals.values())

        # Enrich deals with cash prices and CPP
        cash_price_tasks = []
        for deal in unique_deals:
            for cabin in ['economy', 'premium', 'business', 'first']:
                cash_price_tasks.append(self.get_flight_cash_prices(deal, cabin))
        
        await asyncio.gather(*cash_price_tasks)

        def get_best_points(deal):
            for cabin in ['economy', 'premium', 'business', 'first']:
                if deal.get(cabin) and deal[cabin].get('points'):
                    return deal[cabin]['points']
            return float('inf')

        unique_deals.sort(key=get_best_points)
        
        cheapest_deal = unique_deals[0] if unique_deals else None

        result = {
            "all_deals": unique_deals,
            "cheapest_deal": cheapest_deal,
        }

        return json.dumps(result, indent=2)

mcp_server = FlightSearchMCP()

def run():
    mcp_server.run(transport="stdio")

if __name__ == "__main__":
    run()