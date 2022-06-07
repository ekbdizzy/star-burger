from operator import itemgetter

from geopy import distance

from address.services import get_or_fetch_coordinates


def filter_restaurants_by_products(order, restaurants):
    """Return list of restaurants where products can be cooked."""
    product_ids = {product.product_id for product in order.items.all()}
    order_rests = [restaurant
                   for restaurant, rest_products
                   in restaurants.items()
                   if product_ids.issubset(rest_products)]
    return order_rests


def add_distance_to_order(order, restaurants: list[tuple]) -> list[tuple]:
    order_coords = (order.coord_lon, order.coord_lat)
    order_coords = (order_coords
                    if all(order_coords)
                    else get_or_fetch_coordinates(order.address))
    restaurants_with_distance = []
    for rest_name, rest_address, rest_coords in restaurants:
        rest_coords = (rest_coords
                       if all(rest_coords)
                       else get_or_fetch_coordinates(rest_address))
        if rest_coords:
            restaurants_with_distance.append(
                (rest_name, round(distance.distance(rest_coords, order_coords).km, 2)))
    return sorted(restaurants_with_distance, key=itemgetter(1))


def filter_by_product_and_add_distance(order, restaurants):
    restaurants = filter_restaurants_by_products(order, restaurants)
    restaurants_with_distance = add_distance_to_order(order, restaurants)
    return restaurants_with_distance
