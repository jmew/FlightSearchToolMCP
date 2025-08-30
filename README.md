# Flight Findr

Flight Findr is a powerful, AI-powered application that helps you find the best flight deals using your credit card points and airline miles. It scrapes data from popular award travel websites and provides a user-friendly chat interface to interact with the results.

## Features

- **AI-Powered Chat:** A natural language interface to search for award flights.
- **Multi-Source Scraping:** Gathers data from "seats.aero" and "pointsyeah" for comprehensive results.
- **Cash Price Enrichment:** Calculates the cents-per-point (CPP) value to help you determine the best deals.
- **Dockerized:** Easy to set up and run with Docker.

## Getting Started

### Prerequisites

- Docker
- Node.js
- Python 3.11
- An environment file `.env` with your Gemini API Key `GEMINI_API_KEY=your_api_key`

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://your-repository-url.git
   cd flight-findr
   ```
2. **Build and run the application with Docker Compose:**
   ```bash
   docker-compose up --build
   ```
The application will be available at `http://localhost:3000`.

## Usage

Once the application is running, you can open your web browser and navigate to `http://localhost:3000`. You will be greeted with a chat interface where you can ask the AI to find flight deals.

For example, you can ask:
"Find me a flight from SFO to LAX between 2025-12-01 and 2025-12-10"

## Project Structure

- **`flight-findr-mcp`:** A Python-based microservice responsible for scraping flight data from various sources.
- **`web-frontend`:** A React application that provides the user interface.
- **`web-server`:** A Node.js server that handles the backend logic, including the Gemini integration.
- **`Dockerfile`:** A multi-stage Dockerfile for building the production image.
- **`docker-compose.yml`:** A Docker Compose file for orchestrating the services.