"""
Service for fetching real estate properties.
Uses mock data for now, can be replaced with actual database queries.
"""

import random
from datetime import datetime, timedelta


# Mock neighborhoods in Toulon with market data
NEIGHBORHOODS = {
    "Mourillon": {"avg_price_m2": 5200, "properties": []},
    "Cap Brun": {"avg_price_m2": 4800, "properties": []},
    "Centre": {"avg_price_m2": 5500, "properties": []},
    "Saint-Jean": {"avg_price_m2": 4500, "properties": []},
    "Ouest": {"avg_price_m2": 4200, "properties": []},
}


def generate_mock_properties(neighborhood: str, count: int = 10) -> list:
    """Generate mock properties for a given neighborhood"""
    properties = []
    avg_price_m2 = NEIGHBORHOODS.get(neighborhood, {}).get("avg_price_m2", 5000)
    
    for i in range(count):
        surface = random.choice([45, 55, 65, 75, 85, 95, 110, 125])
        rooms = random.choice([1, 2, 2, 3, 3, 3, 4])
        
        # Price with some variation
        price_m2 = avg_price_m2 * random.uniform(0.85, 1.15)
        price = int(surface * price_m2)
        
        # Check if undervalued (20% below market)
        is_undervalued = random.random() < 0.2
        if is_undervalued:
            price = int(price * 0.80)
        
        properties.append({
            "address": f"{random.randint(1, 200)} Rue de {neighborhood}",
            "neighborhood": neighborhood,
            "type": random.choice(["T2", "T3", "T4", "Maison"]),
            "surface": surface,
            "rooms": rooms,
            "price": price,
            "price_per_m2": int(price / surface),
            "market_price_per_m2": int(avg_price_m2),
            "is_undervalued": is_undervalued,
            "source": random.choice(["SeLoger", "LeBonCoin", "Immo24"]),
            "ref": f"REF{random.randint(100000, 999999)}",
            "days_on_market": random.randint(5, 90),
            "description": f"Beau {random.choice(['T2', 'T3', 'T4'])} de {surface}m² en bon état à {neighborhood}",
        })
    
    return properties


def fetch_properties(
    location: str = "Toulon",
    budget_max: float = 450000,
    surface_min: float = None,
    rooms_min: int = None,
    top_n: int = 5
) -> list:
    """
    Fetch properties matching criteria.
    
    Args:
        location: Neighborhood or city name
        budget_max: Maximum budget
        surface_min: Minimum surface in m²
        rooms_min: Minimum number of rooms
        top_n: Number of top results to return
    
    Returns:
        List of properties matching the criteria
    """
    
    # Determine neighborhood(s) to search
    if location.lower() in [n.lower() for n in NEIGHBORHOODS.keys()]:
        neighborhoods = [n for n in NEIGHBORHOODS if n.lower() == location.lower()]
    elif location.lower() == "toulon":
        neighborhoods = list(NEIGHBORHOODS.keys())
    else:
        # Default to all neighborhoods if not recognized
        neighborhoods = list(NEIGHBORHOODS.keys())
    
    # Generate/fetch properties for each neighborhood
    all_properties = []
    for neighborhood in neighborhoods:
        props = generate_mock_properties(neighborhood, count=15)
        all_properties.extend(props)
    
    # Filter by criteria
    filtered = all_properties
    
    if budget_max:
        filtered = [p for p in filtered if p["price"] <= budget_max]
    
    if surface_min:
        filtered = [p for p in filtered if p["surface"] >= surface_min]
    
    if rooms_min:
        filtered = [p for p in filtered if p["rooms"] >= rooms_min]
    
    # Sort by undervalued status first, then by price per m²
    filtered.sort(
        key=lambda p: (not p["is_undervalued"], p["price_per_m2"])
    )
    
    return filtered[:top_n]
