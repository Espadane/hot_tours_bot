import config
import requests
from mongo_db import *


def get_hot_tours_list(departure_city_id):
    """получение списка горящих туров по айди города вылета"""
    hot_tour_url = f'https://tourvisor.ru/xml/modhot.php?format=json&city={departure_city_id}&regular=2&rows=33&{config.referer}'
    try:
        hot_tours_data = requests.get(hot_tour_url)
        hot_tours_list = hot_tours_data.json()
    except Exception as e:
        print(e)
        hot_tours_list = []

    return hot_tours_list['hot']


def get_depatures_list():
    """получение списка городов вылета"""
    all_data_url = f'https://tourvisor.ru/xml/listdev.php?type=departure,allcountry,country,region,subregions,operator&cndep=0&flydeparture=0&flycountry=0&moduleid=164156&format=json&{config.referer}'
    try:
        all_data = requests.get(all_data_url)
        depatures_list = all_data.json()
    except Exception as e:
        print(e)
        depatures_list = []

    return depatures_list


def write_departures_to_db():
    """запись списка городов вылета в базу данных"""
    departures_list = get_depatures_list()
    departures = departures_list['lists']['departures']['departure']
    write_cities_to_db(departures)
