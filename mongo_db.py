import pymongo
from config import *

db_client = pymongo.MongoClient(
    f'mongodb+srv://{db_login}:{db_pass}@cluster0.xt6ve.mongodb.net/hot_tours?retryWrites=true&w=majority')
current_db = db_client['hot_tours']


def write_cities_to_db(departures):
    """Вносит список городов отправлений в базу данных"""
    collection = current_db['cities']
    r = collection.find()
    if len(list(r)) > 0:
        print('документы есть')
    else:
        print('Документов в базе данных нет, пополняю...')
        collection.insert_many(departures)
        print(f'{len(departures)} документов добавлено')


def get_departure_city_data_from_db(departure_city_id_request):
    """получение названия города по его айди"""
    collection = current_db['cities']
    r = collection.find_one(
        {'name': {'$regex': f'(?i){departure_city_id_request}'}})

    return r


def write_user_data_to_db(user_id, user_name, city_id, city_name):
    """Внесение данных пользователя в базу данных, имя, айди, список городов которые отслеживаются имя и айди города."""
    collection = current_db['users']
    user_data = {
        'user_id': user_id,
        'user_name': user_name,
        'watch_cities': [{
            'city_id': city_id,
            'city_name': city_name
        }]
    }
    if collection.find_one({'user_id': user_id}) == None:
        result = collection.insert_one(user_data)
        answer = f'Туры с вылетом из {city_name} теперь отслеживаются'

    else:
        result = collection.update_one({'user_id': user_id}, {'$addToSet': {
                                       'watch_cities': {'city_id': city_id, 'city_name': city_name}}})
        if result.modified_count > 0:
            answer = f'Туры с вылетом из города "{city_name}" теперь отслеживаются'
        else:
            answer = f'Вы уже следите за турами с вылетом из города "{city_name}"'

    return answer


def add_hot_tours_to_db(city_name, hot_tours):
    """Внесение туров в таблицу по названию города"""
    collection = current_db[f'{city_name}']
    if list(collection.find()) == []:
        collection.insert_many(hot_tours)


def get_user_cities(user_id):
    """получение названий городов которые отслеживает пользователь"""
    user_cities = []
    collection = current_db['users']
    user_data = collection.find_one({'user_id': user_id})
    watch_cities = user_data['watch_cities']
    for i in watch_cities:
        user_cities.append(i['city_name'])

    return user_cities


def get_tours_on_date(user_city, date):
    """Получение туров по дате вылета из базы данных"""
    collection = current_db[f'{user_city}']
    tour_list_on_date = collection.find({'flydate': date})

    return list(tour_list_on_date)


def get_tours_on_destination(user_city, destination):
    """получение туров по пункту назначения по названию города, либо страны если город не найден"""
    collection = current_db[f'{user_city}']
    if collection.count_documents({'hotelregionname': {'$regex': f'(?i){destination}'}}) > 0:
        tours_list = collection.find(
            {'hotelregionname': {'$regex': f'(?i){destination}'}})
    elif collection.count_documents({'countryname': {'$regex': f'(?i){destination}'}}) > 0:
        tours_list = collection.find(
            {'countryname': {'$regex': f'(?i){destination}'}})
    else:
        tours_list = []
    return list(tours_list)


def get_all_departare_cities():
    """получения айди городов которые отслеживают все пользователи"""
    cities_id = []
    collection = current_db['users']
    try:
        watch_cities = collection.find()
        for city in watch_cities:
            for city_name in city['watch_cities']:
                cities_id.append(city_name['city_id'])
    except:
        print('Никто ничего не отслеживает')
    return set(cities_id)


def compare_tours(new_tours, city_id):
    """сравнение списка айди туров, новых, тех которые надо удалить из базы и туров с изменением цены"""
    new_tours_ids_list = get_new_tours_ids(new_tours)
    old_tours_ids_list = get_old_tours_ids(city_id)
    new_tours_list = list(set(new_tours_ids_list) - set(old_tours_ids_list))
    tours_to_delete_list = list(
        set(old_tours_ids_list) - set(new_tours_ids_list))
    tours_to_check_list = list(
        set(new_tours_ids_list) & set(old_tours_ids_list))

    return new_tours_list, tours_to_delete_list, tours_to_check_list


def get_new_tours_ids(new_tours):
    """получение списка айди новых туров"""
    new_tours_ids_list = []
    for new_tour in new_tours:
        new_tours_ids_list.append(new_tour['tourid'])

    return new_tours_ids_list


def get_old_tours_ids(city_id):
    """получение списка айди устаревших туров"""
    old_tours_ids_list = []
    collection_cities = current_db['cities']
    city_name = collection_cities.find_one({'id': city_id})['name']
    collection_tours = current_db[f'{city_name}']
    old_tours = collection_tours.find()
    for old_tour in old_tours:
        old_tours_ids_list.append(old_tour['tourid'])

    return old_tours_ids_list


def delete_old_tours(tours_to_delete_list, city_id):
    """удаление старых туров из базы данных, по списку айди"""
    collection_cities = current_db['cities']
    city_name = collection_cities.find_one({'id': city_id})['name']
    collection_tours = current_db[f'{city_name}']
    for tour_id in tours_to_delete_list:
        collection_tours.find_one_and_delete({'tourid': tour_id})
    print(f'Удалено - {len(tours_to_delete_list)}')


def write_new_tour_to_db(new_tours, new_tours_list_id, city_id):
    """запись новых туров в базу данных по айди из списка """
    added_tours = []
    collection_cities = current_db['cities']
    city_name = collection_cities.find_one({'id': city_id})['name']
    collection = current_db[f'{city_name}']
    for new_tour_id in new_tours_list_id:
        for tour in new_tours:
            if new_tour_id == tour['tourid']:
                collection.insert_one(tour)
                added_tours.append(tour)

    print(f'Добавленно {len(new_tours_list_id)} туров в городе {city_name}')
    return added_tours


def check_tour_data(new_tours, tours_to_check_list, city_id):
    """Получение туров с изменением цены, а так же новый, старые цены и процентную разницу между ними"""
    new_price_tours = []
    collection_cities = current_db['cities']
    city_name = collection_cities.find_one({'id': city_id})['name']
    collection = current_db[f'{city_name}']
    for new_tour in new_tours:
        for tour in tours_to_check_list:
            if new_tour['tourid'] == tour:
                tour_in_db = collection.find_one({'tourid': tour})
                new_price = int(new_tour['price'])
                old_price = int(tour_in_db['price'])
                persent = int((old_price - new_price)/(old_price/100))
                if persent > 7 or persent < -7:
                    collection.find_one_and_update(
                        {'tourid': tour}, {'$set': {'price': new_price}})
                    new_price_tour = collection.find_one({'tourid': tour})
                    new_price_tours.append(
                        [new_price_tour, old_price, new_price, persent])

    return new_price_tours


def get_city_id_from_user(city_id):
    """получение списка пользовательских айди которые отслеживают город вылета"""
    user_id_list = []
    collection = current_db['users']
    users = collection.find()
    for user in users:
        cities = user['watch_cities']
        for city in cities:
            if city['city_id'] == city_id:
                user_id_list.append(user['user_id'])

    return user_id_list


def delete_watched_city(user_id, city_name):
    """удаление города из списка отслеживаемых пользователем"""
    collection = current_db['users']
    user_data = collection.find_one({'user_id': user_id})
    cities = list(user_data['watch_cities'])
    for city in cities:
        if city['city_name'] == city_name:
            collection.update_one({'user_id': user_id}, {
                                  '$pull': {'watch_cities': {'city_name': city_name}}})
            answer = f'{city_name} удален из отслеживаемых'
        else:
            answer = f'Вы не следите за городом {city_name}'

    return answer
