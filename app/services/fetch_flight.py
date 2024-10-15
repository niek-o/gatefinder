import logging

from fastapi import HTTPException
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.cache.cache import add_to_cache, get_from_cache

logger = logging.getLogger('uvicorn.error')


async def fetch_flight(flight_number=None, data_target=None, i=0):
    logger.debug("Checking if departure gate is in cache")
    departure_gate_from_cache = get_from_cache(flight_number)
    if departure_gate_from_cache is not None:
        logger.info(f"Found valid departure gate in cache: {departure_gate_from_cache}")
        return departure_gate_from_cache

    if i > 0 and i >= 2:
        logger.warning(f'Too many retries: {i}...')
        raise HTTPException(status_code=404, detail="Gate not found")

    url = ""

    if flight_number is not None:
        logger.debug(f"Finding flight with flight number {flight_number}")
        url = f"https://www.flightaware.com/live/flight/{flight_number}"
    else:
        if data_target is not None:
            logger.debug(f"Finding flight with index {i}")
            url = f"https://www.flightaware.com{data_target}"

    logger.debug(f"Finding flight on url {url}")

    logger.debug("Starting webdriver")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    dr = webdriver.Remote(command_executor="http://selenium-hub:4444", options=options)
    logger.debug("Started webdriver")

    logger.debug("Fetching url using webdriver")
    try:
        dr.get(url)
        WebDriverWait(dr, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'flightPageAirportGate')))
    except:
        logger.warning('Flight not found')
        raise HTTPException(status_code=404, detail="Flight not found")
    logger.debug("Fetched url using webdriver")

    logger.debug("Starting soup using lxml format")
    soup = BeautifulSoup(dr.page_source, "lxml")
    logger.debug("Soup started")

    logger.debug("Finding span element with class 'flightPageAirportGate'")
    flight_page_origin_airport_gate = soup.find("span", {"class": "flightPageAirportGate"})
    logger.debug("Found span element")

    logger.debug("Finding strong element within span 'flightPageAirportGate'")
    gate = flight_page_origin_airport_gate.find("strong")
    logger.debug("Found strong element")

    if gate is None or "Gate" not in flight_page_origin_airport_gate.text:
        logger.debug("Gate does not exist or is not valid")

        logger.debug("Finding all historical flight rows with class 'flightPageDataRowTall' and data-type 'past'")
        flight_history = soup.find_all("div", {"class": "flightPageDataRowTall", "data-type": "past"})
        logger.debug("Found all historical flight rows")

        if not flight_history or len(flight_history) == 0:
            logger.warning('No entries in historical flight table found')
            raise HTTPException(status_code=404, detail="Gate not found")

        if i > len(flight_history):
            logger.warning(f'The current index {i} is higher than amount of historic flights {len(flight_history)}')
            raise HTTPException(status_code=404, detail="Gate not found")

        logger.debug(f"Selecting flight from flight history with an index of {i}")
        previous_flight = flight_history[i]
        logger.debug(f"Selected flight with an index of {i}")

        logger.warning(f'Gate not found on historical flight from flight history with an index of {i}, trying again...')
        return await fetch_flight(data_target=previous_flight["data-target"], i=i + 1)

    logger.debug("Finding valid departure gate")
    departure_gate = gate.text

    logger.info(f"Found valid departure gate: {departure_gate}")

    logger.debug("Adding departure gate to cache")
    add_to_cache(flight_number, departure_gate)
    logger.debug("Added departure gate to cache")

    return departure_gate
