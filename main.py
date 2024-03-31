import telebot
from telebot import types
import mysql.connector

bot = telebot.TeleBot('6603229406:AAEepixn5mb0HjCSpsDYy07b-7zxXCp6yj4')

db = mysql.connector.connect(
host = "localhost",
user = "root",
passwd = "cport2003",
port = "3306",
database = "kursach_bd"
)


cursor = db.cursor()

cursor.execute("USE kursach_bd")

# # Пример вставки новой записи
# insert_query = "INSERT INTO buyers(id_buyer, fio, date_birth, number, email, adress) VALUES (%s, %s, %s, %s, %s, %s)"
# data_to_insert = (5, 'Степанов Степан Степаныч', '12.04.2003', '8-111-124-12-52', 'step@gmail.com', 'Москва')

# # Выполнение запроса
# cursor.execute(insert_query, data_to_insert)

# # Фиксация изменений
# db.commit()


# print(cursor.execute("SELECT * FROM buyers"))
#result = cursor.fetchall()

# # Вывод результата
# print(result)

#Начало работы
@bot.message_handler(commands=['start'])
def main(us):
    bot.send_message(us.chat.id, '<b>Привет!</b>\nЯ твой бот помощник управления бизнесом автосалона.\n Со мной ты сможешь выполнить различные действия с базой данных, или получить какую то информацию оттуда. Можешь посмотреть доступные команды, и воспользоваться тем, что вам нужно.', parse_mode="html")

#Работа с информацией о покупателях
@bot.message_handler(commands=['buyer'])
def main(us):
    mark = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Посмотреть', callback_data='view_buyers')
    btn2 = types.InlineKeyboardButton('Изменить', callback_data='edit_buyers')
    mark.row(btn1, btn2)
    bot.send_message(us.chat.id, '<b>Вы попали в раздел с работой с покупателями</b>\n Выберите вы хотите изменить или просто посмотреть какую либо информацию о покупателях?', parse_mode="html", reply_markup=mark)

#Работа с информацией о автомобилях
@bot.message_handler(commands=['cars'])
def main(us):
    mark = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Посмотреть', callback_data='view_cars')
    btn2 = types.InlineKeyboardButton('Изменить', callback_data='edit_cars')
    mark.row(btn1, btn2)
    bot.send_message(us.chat.id, '<b>Вы попали в раздел с работой с автомобилями</b>\n Выберите вы хотите изменить или просто посмотреть какую либо информацию об автомобилях?', parse_mode="html", reply_markup=mark)


#Преобразует из кортежа в красивый столбец
def transform_hash(hash):
    rez = ""
    p = 0
    for i in hash:
        p += 1
        rez += f"{p}. " + str(i)[2:-3] + "\n"
    return rez

#Преобразует из кортежа большого, в красивый столбец
def transform_hash_big(hash):
    rez = ""
    p = 0
    for i in hash:
        p += 1
        rez += f"{p}.) " + str(i)[1:-1] + "\n"
    return rez

#Обработка кнопочек
@bot.callback_query_handler(func=lambda callback: True)
def callback_message(cal):
    mark = types.InlineKeyboardMarkup()
    bot.delete_message(cal.message.chat.id, cal.message.message_id)
    
#Отдель с автомобилями
    #Обработка кнопки изменить что-то связанное с автомобилями
    if cal.data == 'edit_cars':
        btn1 = types.InlineKeyboardButton('Добавить новый авто.', callback_data='add_car')
        btn2 = types.InlineKeyboardButton('Удаление просроченных покупок.', callback_data='del_pur')
        mark.add(btn1)
        mark.add(btn2)
        bot.send_message(cal.message.chat.id, "<b>Что именно вас интересует?</b>", parse_mode="html", reply_markup=mark)
    
    #Удаление лишних записей в покупках
    def check_pur(mes):
        dmg = mes.text
        sql_txt = f"SELECT * FROM purchases WHERE DATE_ADD(STR_TO_DATE(purchases.date_buy, '%d.%m.%Y') , INTERVAL purchases.period_quar YEAR) <= STR_TO_DATE('{dmg}', '%d.%m.%Y'); "
        cursor.execute(sql_txt)
        rez = cursor.fetchall()
        if rez == []:
            bot.send_message(cal.message.chat.id, 'Никакие сроки гарантии ещё не закончились.')
        else:
            bot.send_message(cal.message.chat.id, 'Сроки гарантии закончились у следующих покупок, далее будет информация в виде n.) ФИО - vin авто которое было куплено.\n\n Данные о данных покупках были удалены, автомобили так же убраны из базы данных', parse_mode="html")
            n = 0
            for r in rez:
                n += 1
                sql_txt = f"SELECT fio FROM buyers WHERE id_buyer = {r[1]}"
                cursor.execute(sql_txt)
                fio = cursor.fetchall()
                #Удаляю авто из автомобилей
                sql_txt = f"DELETE FROM purchases WHERE id_car = {r[2]}"
                cursor.execute(sql_txt)
                sql_txt = f"DELETE FROM cars WHERE id_car = {r[2]}"
                cursor.execute(sql_txt) 

                bot.send_message(cal.message.chat.id, f'{n}.) {str(fio)[2:-3]} - {r[2]}')
        db.commit()



    if cal.data == 'del_pur':
        msg = bot.send_message(cal.message.chat.id, "<b>Вы запустили функцию обработки покупок, после данной процедуры все покупки у которых истёк срочк гарантии будут удалены, вместе с информацией об автомобиле и информацией о покупателе.</b>\nВам следует ввести \n\n Введите через запятую: \n текущую дату", parse_mode="html")
        bot.register_next_step_handler(msg, check_pur)

    
    #Добавление нового авто
    def mes_add_car(mes):
        result_array = list(map(str, mes.text.split(', ')))
        if len(result_array) != 6:
            bot.send_message(cal.message.chat.id, '<b>В вашем сообщение либо слишком много данных, либо слишком мало, попробуйте снова.</b>', parse_mode="html")
        else:
            try:
                sql_txt = f"(SELECT id_brand FROM cars_brands WHERE name_brand = '{result_array[1]}')"
                cursor.execute(sql_txt)
                id_brand = int(str(cursor.fetchall())[2:-3])
                
                sql_txt = f"(SELECT id_model FROM cars_models WHERE name_model = '{result_array[2]}')"
                cursor.execute(sql_txt)
                id_model = int(str(cursor.fetchall())[2:-3])
                
                sql_txt = f"SELECT * FROM brands_models WHERE id_brand = {id_brand} AND id_model = {id_model};"
                cursor.execute(sql_txt)
                
                rez = cursor.fetchall()
                if rez == []:
                    bot.send_message(cal.message.chat.id, '<b>Скорее всего вы ввели модель авто которая не принадлежит введённой марке.</b>', parse_mode="html")
                else:
                    #Добавляю в таблицу автомобилей
                    sql_txt = f"INSERT INTO cars(id_car, id_brand, id_model, status, box_type, equip, price) VALUES ({result_array[0]} , {id_brand}, {id_model}, 0, '{result_array[3]}', '{result_array[4]}', {result_array[5]});"
                    cursor.execute(sql_txt)
                    db.commit()
            except:
                bot.send_message(cal.message.chat.id, '<b>Какие то данные неверного типа или не верно введены, попробуйте снова.</b>', parse_mode="html")
    if cal.data == 'add_car':
        msg = bot.send_message(cal.message.chat.id, "<b>Далее введите через запятую следующие данные про автомобиль:</b>\n vin-номер(id_car), бренд, модель, тип коробки, комплектация, цена", parse_mode="html")
        bot.register_next_step_handler(msg, mes_add_car)
    
    #Обработка кнопки Посмотреть что-то связанное с автомобилями
    if cal.data == 'view_cars':
        btn1 = types.InlineKeyboardButton('Список всех авто.', callback_data='all_cars')
        btn2 = types.InlineKeyboardButton('Список покупателей заказавших авто.', callback_data='order_car')
        mark.add(btn1)
        mark.add(btn2)
        bot.send_message(cal.message.chat.id, "<b>Что именно вас интересует?</b>", parse_mode="html", reply_markup=mark)
    
    #Обработка кнопки просмотра заказанных авто
    if cal.data == 'order_car':
        sql_txt = """ SELECT
                Buyers.fio AS buyer_name,
                Buyers.date_birth,
                Buyers.number AS buyer_number,
                Buyers.email,
                Buyers.adress AS buyer_address,
                Cars.box_type,
                Cars.equip,
                Cars.price,
                Cars_Brands.name_brand,
                Cars_Models.name_model,
                Cars_Ordered.delivery_time
            FROM
                Kursach_BD.Buyers
            JOIN
                Kursach_BD.Cars_Ordered ON Buyers.id_buyer = Cars_Ordered.id_buyer
            JOIN
                Kursach_BD.Cars ON Cars_Ordered.id_car = Cars.id_car
            JOIN
                Kursach_BD.Cars_Brands ON Cars.id_brand = Cars_Brands.id_brand
            JOIN
                Kursach_BD.Cars_Models ON Cars.id_model = Cars_Models.id_model;"""
        print("ASDasd")
        cursor.execute(sql_txt)
        rez = cursor.fetchall()
        if rez == []:
            bot.send_message(cal.message.chat.id, f"Заказанных автомобилей нет.")
        else:
            rez = transform_hash_big(rez)
            bot.send_message(cal.message.chat.id, f"Самая последняя цифра - срок доставки в днях \n\n {rez}")


    #Обработка кнопки просмотра всех авто
    if cal.data == 'all_cars':
        sql_txt = "SELECT Cars.id_car, Cars.status, Cars.box_type, Cars.equip, Cars.price, Cars_Brands.name_brand, Cars_Models.name_model FROM Kursach_BD.Cars LEFT JOIN  Kursach_BD.Cars_Brands ON Cars.id_brand = Cars_Brands.id_brand LEFT JOIN  Kursach_BD.Cars_Models ON Cars.id_model = Cars_Models.id_model;"
        cursor.execute(sql_txt)
        rez = cursor.fetchall()
        if rez == []:
            bot.send_message(cal.message.chat.id, f"Автомобилей вообще нет на складе.")
        else:
            rez = transform_hash_big(rez)
            bot.send_message(cal.message.chat.id, f"Обратите внимание на вторую циферку.(0-машина свободна, 1 - машина куплена, -1 - машина заказана)цифра после комплектации-цена\n\n{rez}")

#Отдел с покупателями
    #Обработка кнопки Посмотреть что-то связанное с покупателями
    if cal.data == 'view_buyers':
        btn1 = types.InlineKeyboardButton('Список ФИО всех покупателей', callback_data='all_buyers')
        btn2 = types.InlineKeyboardButton('Список ФИО всех покупателей из выбранного далее города', callback_data='all_buyers_from_city')
        mark.add(btn1)
        mark.add(btn2)
        bot.send_message(cal.message.chat.id, "<b>Что именно вас интересует?</b>", parse_mode="html", reply_markup=mark)
    
    #Обработка кнопки Изменить что-то связанное с покупателями
    if cal.data == 'edit_buyers':
        btn1 = types.InlineKeyboardButton('Добавить нового покупателя', callback_data='add_buyer')
        btn2 = types.InlineKeyboardButton('Изменить адрес покупателя', callback_data='change_adress')
        mark.add(btn1)
        mark.add(btn2)
        bot.send_message(cal.message.chat.id, "<b>Что именно вас интересует?</b>", parse_mode="html", reply_markup=mark)
    
    #Изменение адреса покупателя
    def change_adress(mes):
        result_array = list(map(str, mes.text.split(', ')))
        if len(result_array) != 2:
            bot.send_message(cal.message.chat.id, '<b>В вашем сообщение либо слишком много данных, либо слишком мало, попробуйте снова.</b>', parse_mode="html")
        else:
            try:
                sql_txt = f"UPDATE buyers SET adress = '{result_array[1]}' WHERE fio = '{result_array[0]}'"
                cursor.execute(sql_txt)
                db.commit()
            except:
                bot.send_message(cal.message.chat.id, '<b>Какие то данные неверного типа или не верно введены, попробуйте снова.</b>', parse_mode="html")
    if cal.data == 'change_adress':
        msg = bot.send_message(cal.message.chat.id, "<b>Далее введите через запятую.</b>ФИО покупателя, Новый город покупателя\n ", parse_mode="html")
        bot.register_next_step_handler(msg, change_adress)

    #Добавление покупателя
    def mes_add_buyer(mes):
        result_array = list(map(str, mes.text.split(', ')))
        print(result_array)
        if len(result_array) != 8:
            bot.send_message(cal.message.chat.id, '<b>В вашем сообщение либо слишком много данных, либо слишком мало, попробуйте снова.</b>', parse_mode="html")
        else:
            sql_txt = f"(SELECT status FROM cars WHERE id_car = {result_array[0]})"
            cursor.execute(sql_txt)
            rez = cursor.fetchall()
            if int(str(rez)[2:-3]) != 0:
                bot.send_message(cal.message.chat.id, '<b>Авто с таким айди к сожалению уже куплен, или авто с таким айди не существует в салоне.</b>', parse_mode="html")
            else:
                try:
                    cursor.execute("(SELECT MAX(id_buyer) + 1 FROM buyers)")
                    rez = cursor.fetchall()
                    rez = str(rez)[2:-3]
                    #Добавляю в таблицу покупателей
                    sql_txt = f"INSERT INTO buyers(id_buyer, fio, date_birth, number, email, adress) VALUES ({rez} , '{result_array[1]}', '{result_array[2]}', '{result_array[3]}', '{result_array[4]}', '{result_array[5]}');"
                    cursor.execute(sql_txt)
                    #Обновляю информацию о том что авто куплен
                    sql_txt = f"UPDATE cars SET status = 1 WHERE id_car = '{result_array[0]}';"
                    cursor.execute(sql_txt)
                    #Добавлю покупку в таблицу покупок
                    cursor.execute("(SELECT MAX(id_purchase) + 1 FROM purchases)")
                    rez2 = int(str(cursor.fetchall())[2:-3])
                    sql_txt = f"INSERT INTO purchases(id_purchase, id_buyer, id_car, date_buy, period_quar) VALUES ({rez2},{rez},{result_array[0]},'{result_array[6]}',{result_array[7]});"
                    cursor.execute(sql_txt)
                    db.commit()
                except:
                    bot.send_message(cal.message.chat.id, '<b>Какие то данные неверного типа или не верно введены, попробуйте снова.</b>', parse_mode="html")
    if cal.data == 'add_buyer':
        msg = bot.send_message(cal.message.chat.id, "<b>Далее введите через запятую следующие данные Покупателя:</b>\n id покупаемого авто, ФИО, Дата рождения, Телефон, Почта, Адрес, Дату покупки, Период гарантии\n\n(Дата в формате день.месяц.год)", parse_mode="html")
        bot.register_next_step_handler(msg, mes_add_buyer)


    #Обработка просмотра списка ФИО всех покупателей
    if cal.data == 'all_buyers':
        cursor.execute("SELECT fio FROM buyers")
        rez = cursor.fetchall()
        bot.send_message(cal.message.chat.id, f'{transform_hash(rez)}')
    
    #Обработка просмотра списка ФИО по выбранному городу
    def mes_city(mes):
        sql_txt = f"SELECT fio FROM buyers WHERE adress = '{mes.text}'"
        cursor.execute(sql_txt)
        rez = cursor.fetchall()
        if rez == []:
            bot.send_message(mes.chat.id, "Покупателей из этого города нет.")
        else:
            bot.send_message(mes.chat.id, f'{transform_hash(rez)}')
    if cal.data == 'all_buyers_from_city':
        msg = bot.send_message(cal.message.chat.id, '<b>Введите из какого города стоит искать покупателей?</b>', parse_mode="html")
        bot.register_next_step_handler(msg, mes_city)



bot.polling(none_stop=True)