#!/usr/bin/python
# -*- coding: utf-8 -*-
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
import emoji
from parse_hot import *
import config
import re


bot = Bot(token=config.bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
@dp.message_handler(commands=['старт'])
async def start_command(msg: types.Message):
    """Обработчик команды '/start'"""
    await msg.answer(emoji.emojize(f"Привет, {msg.from_user.first_name}!\nОтслеживаю :fire: туры\nПожалуйста, если у тебя есть пожелания напиши: t.me/espadane"), disable_web_page_preview=True)


@dp.message_handler(commands=['help'])
@dp.message_handler(commands=['помощь'])
async def help_command(msg: types.Message):
    '''Обработчик команды помощи'''
    await msg.answer('Для того чтобы начать отслеживать горящие туры с вылетом из определенного города напиши /отселживать -название города-\nБот будет присылать туры когда они появятся на сайте. Цена за тур указана за одного человека, но на сайте за двоих. Так же имей ввиду, что присылать он будет их кучами, так что не остлеживай много городов и убирай уведомления.\nЧтобы перестать отслеживать напиши /отменить -название города-\nТак же ты можешь смотреть все актуальные туры по дате, просто введи ее в формате 11.11.2011.\nКроме того ты можешь посмотреть туры с вылетом из отслеживаемых городов по названию страны или города. Просто напиши их мне.')


@dp.message_handler(commands=['отслеживать'])
async def watch_city(msg: types.Message):
    """Команда вносит в базу данных название города туры с вылетами из которого пользователь хочется отслеживать."""
    user_id = msg.from_user.id
    user_name = msg.from_user.first_name
    city = msg.text.replace('/отслеживать', '').strip()
    city_data = get_departure_city_data_from_db(city)
    if city_data != None:
        city_id = city_data['id']
        city_name = city_data['name']
        answer = write_user_data_to_db(user_id, user_name, city_id, city_name)
        await msg.answer(answer)
        hot_tours = get_hot_tours_list(city_id)
        add_hot_tours_to_db(city_name, hot_tours)
    else:
        await msg.answer('Туров с вылетом из данного города не найдено. Возможно вы ошиблись в написании. Попробуйте написать город по другому или введите ближайший крупый город.')


@dp.message_handler(commands=['отменить'])
async def unwatch_city(msg: types.Message):
    """Команда прекращает отслеживание туров и удаляет город из базы данных"""
    user_id = msg.from_user.id
    city_name = msg.text.replace('/отменить', '').strip()
    answer = delete_watched_city(user_id, city_name)
    await msg.answer(answer)


@dp.message_handler(commands=['write_departures'])
async def write_departures(msg: types.Message):
    """Команда для администратора для принудительного скачивания списка городов отправления, на случай изменения на сайте."""
    if str(msg.from_user.id) == config.admin_id:
        write_departures_to_db()
    else:
        await msg.answer(emoji.emojize(':stop_sign:ТЫ НЕ ПРОЙДЕШЬ!!!:stop_sign:'))


@dp.message_handler(commands=['get_tours'])
async def write_tours(msg: types.Message):
    """Команда для принудительного получения списка туров, только по городам которые добавили пользователи. Для администратора на всякий случай."""
    if str(msg.from_user.id) == config.admin_id:
        check_new_tours()
    else:
        await msg.answer(emoji.emojize(':stop_sign:ТЫ НЕ ПРОЙДЕШЬ!!!:stop_sign:'))


@dp.message_handler(Text)
async def get_tours_request(msg: types.Message):
    """Получение отчета по турам по дате или пункту назначения."""
    user_id = msg.from_user.id
    if re.fullmatch(r'(\d\d).(\d\d).(\d\d\d\d)', msg.text):
        date = msg.text
        answer = get_tours_on_date_message(user_id, date)
        if answer == '':
            await msg.answer('На эту дату туров нет. Попробуйте другую, или спросите позже.')
        else:
            await msg.answer(answer, disable_web_page_preview=True, parse_mode='HTML')
    else:
        destination = msg.text
        answer = get_tours_on_destination_message(user_id, destination)
        if answer == '':
            await msg.answer(emoji.emojize('Простите, я не понял что вы у меня спрашивали. Такого населенного пункта, города или страны я не знаю. Уточните свой запрос или спросите позже. Вот вам котик чтобы вы не расстраивались - :cat:'))
        else:
            await msg.answer(answer, disable_web_page_preview=True, parse_mode='HTML')


def get_tours_on_date_message(user_id, date):
    """Создание сообщения с турами основанными на дате вылета"""
    user_cities = get_user_cities(user_id)
    answer = []
    for user_city in user_cities:
        tour_list_on_date = get_tours_on_date(user_city, date)
        if tour_list_on_date == []:
            continue
        else:
            for tour in tour_list_on_date:
                stars = int(tour['hotelstars']) * emoji.emojize(':star:')
                text = f"{stars}\nИз {tour['departurefrom']} в {tour['countryname']} - {tour['hotelregionname']} за {tour['price']} руб. на {tour['nights']} ночей с {tour['meal']}"
                string = f"<a href='https://tourvisor.ru/search.php#tvtourid={tour['tourid2']}'>{text}</a>\n" + \
                    '\n===============\n'
                answer.append(string)
    answer = ''.join(answer)

    return answer


def get_tours_on_destination_message(user_id, destination):
    """Формирования сообщения пользователю на основе пункта назначения"""
    user_cities = get_user_cities(user_id)
    answer = []
    for user_city in user_cities:
        tours_list = get_tours_on_destination(user_city, destination)
        if tours_list == []:
            continue
        else:
            for tour in tours_list:
                stars = int(tour['hotelstars']) * emoji.emojize(':star:')
                text = f"{stars}\nИз {tour['departurefrom']} в {tour['countryname']} - {tour['hotelregionname']} за {tour['price']} руб. на {tour['nights']} ночей с {tour['meal']} вылет {tour['flydate']}"
                string = f"<a href='https://tourvisor.ru/search.php#tvtourid={tour['tourid2']}'>{text}</a>\n" + \
                    '\n===============\n'
                answer.append(string)
    answer = ''.join(answer)

    return answer


async def check_new_tours():
    """Проверка новых туров на сайте. Новые туры заносит в базу и отправляет пользователю, на основе отслеживаемых городов. Старые удаляет из базы. Туры у которых изменилась цена на 7% и более процентов в обе стороны обновляет и присылает информацию пользователю"""
    while True:
        watched_cities_id = get_all_departare_cities()
        for city_id in watched_cities_id:
            new_tours = get_hot_tours_list(city_id)
            new_tours_list_id, tours_to_delete_list, tours_to_check_list = compare_tours(
                new_tours, city_id)
            delete_old_tours(tours_to_delete_list, city_id)
            new_tours_to_user = write_new_tour_to_db(
                new_tours, new_tours_list_id, city_id)
            changed_tours_to_user = check_tour_data(
                new_tours, tours_to_check_list, city_id)
            user_ids = get_city_id_from_user(city_id)
            for user_id in user_ids:
                if len(new_tours_to_user) > 0:
                    answer = create_new_tours_message(new_tours_to_user)
                    await bot.send_message(user_id, answer, parse_mode='HTML')
                for changed_tour in changed_tours_to_user:
                    yesterday_price = changed_tour[1]
                    today_price = changed_tour[2]
                    persentage = changed_tour[3]
                    price_old = int(changed_tour[0]['priceold'])
                    price = int(changed_tour[0]['price'])
                    discount = int((price_old - price)/(price_old/100))
                    stars = int(
                        changed_tour[0]['hotelstars']) * emoji.emojize(':star:')
                    await bot.send_message(user_id, emoji.emojize(f"Цена на тур изменилась:\nБыла - {yesterday_price} руб., а стала - {today_price} руб. Разница {persentage} %\n{changed_tour[0]['countryname']} - {changed_tour[0]['hotelregionname']}\nОтель {stars} {changed_tour[0]['meal']}\n:airplane: из {changed_tour[0]['departurefrom']} :spiral_calendar: {changed_tour[0]['flydate']}\n{changed_tour[0]['nights']} ночей - <b>{price} ₽</b> за чел.\Первоначальная цена - {price_old} ₽ Скидка: {discount} %\n<a href='https://tourvisor.ru/search.php#tvtourid={changed_tour[0]['tourid2']}'>Подробнее</a>"), disable_web_page_preview=True, parse_mode='HTML')

        await asyncio.sleep(300)


def create_new_tours_message(new_tours_to_user):
    depurture_city_from = new_tours_to_user[0]['departurefrom']
    destinations = []
    prices = []
    counter = []
    dates = []
    for new_tour in new_tours_to_user:
        destination = f'{new_tour["countryname"]}/{new_tour["hotelregionname"]}'
        min_price = new_tour['price']
        date = new_tour['flydate']
        if destination in destinations:
            double_index = destinations.index(destination)
            if min_price < prices[double_index]:
                prices[double_index] = min_price
            counter[double_index] += 1
            dates[double_index] = date
        else:
            destinations.append(destination)
            prices.append(min_price)
            counter.append(1)
            dates.append(date)
    new_tours_list = []
    for d, p, c, dt in zip(destinations, prices, counter, dates):
        new_tours_list.append(
            f'<b>{d}</b> - {c}\nМин: {p} руб. {dt}\n==============\n')

    answer = f'Появились новые туры с вылетом из {depurture_city_from}:\n\n{"".join(new_tours_list)}'

    return answer


if __name__ == '__main__':
    write_departures_to_db()
    loop = asyncio.get_event_loop()
    loop.create_task(check_new_tours())
    executor.start_polling(dp)
