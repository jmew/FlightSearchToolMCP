# The Point Finder

**The Point Finder** is a powerful flight deal scraper that finds the best award travel options using points. It scrapes popular services like `seats.aero` and `pointsyeah` and exposes the results through a simple and efficient MCP (Machine-Readable Command Post) server.

This tool is perfect for travel enthusiasts and developers who want to automate their search for the best flight deals.

## Features

- **Multi-Source Scraping**: Gathers flight deals from both `seats.aero` and `pointsyeah`.
- **MCP Server**: Exposes a simple API endpoint to check for flight point prices.
- **Best Deal Identification**: Automatically identifies and highlights the cheapest deal found.
- **Easy to Install**: Packaged for simple local installation via `pip`.

## Installation

Follow these steps to set up The Point Finder on your local machine.

### Prerequisites

- Python 3.8 or higher
- `git` for cloning the repository

### 1. Clone the Repository

```bash
git clone <repository-url>
cd flight-search-mcp
```

### 2. Set Up a Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the Package

Install the tool and all its dependencies with a single command:

```bash
pip install .
```

### 4. Install Playwright Browsers

The Point Finder uses Playwright for web scraping, which requires browser binaries to be installed.

```bash
playwright install
```

## Usage

Once installed, you can run the MCP server with the following command:

```bash
the-point-finder-server
```

The server will start on `http://0.0.0.0:8080`.

## API Reference

The MCP server provides one primary tool: `check_flight_points_prices`.

### `check_flight_points_prices`

This tool searches for the best flight deals using points from various sources.

#### Request

You can send a POST request to the `/tools/check_flight_points_prices/call` endpoint. Here is an example using `curl`:

```bash
curl -X POST http://localhost:8080/tools/check_flight_points_prices/call \
-H "Content-Type: application/json" \
-d '{
    "origin_airports": ["SFO", "JFK"],
    "destination_airports": ["LAX", "LHR"],
    "start_date": "2025-10-01",
    "end_date": "2025-10-05"
}'
```

#### Parameters

- `origin_airports` (required, List[str]): A list of one or more origin airport IATA codes.
- `destination_airports` (required, List[str]): A list of one or more destination airport IATA codes.
- `start_date` (required, str): The start date for the search in `YYYY-MM-DD` format.
- `end_date` (required, str): The end date for the search in `YYYY-MM-DD` format.
- `programs` (optional, List[str]): A list of frequent flyer programs to filter by.
- `alliances` (optional, List[str]): A list of airline alliances to filter by.
- `transfer_partners` (optional, List[str]): A list of transfer partners to filter by.
- `points_min` (optional, int): The minimum number of points for a deal.
- `points_max` (optional, int): The maximum number of points for a deal.
- `days` (optional, int): The number of days to search around the specified date.

#### Response

The tool returns a JSON object containing all the deals found and the cheapest deal.

```json
{
  "all_deals": [
    {
      "date": "2025-10-02",
      "program": "United MileagePlus",
      "route": "SFO -> LAX",
      "economy": {
        "points": 5000,
        "fees": "$5.60 USD"
      },
      "source": "seats.aero"
    }
  ],
  "cheapest_deal": {
    "date": "2025-10-02",
    "program": "United MileagePlus",
    "route": "SFO -> LAX",
    "economy": {
      "points": 5000,
      "fees": "$5.60 USD"
    },
    "source": "seats.aero"
  }
}
```
