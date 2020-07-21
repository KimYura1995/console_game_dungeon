# -*- coding: utf-8 -*-

import csv
import re
import json
import datetime

from decimal import Decimal


class DnD:
    """
    DnD на минималках
    """
    re_location = re.compile(r'Location_\w+_tm(\d+\.?\d*)')
    re_mob = re.compile(r'\w+exp(\d+)_tm(\d+)')
    re_hatch = re.compile(r'Hatch_tm(\d+\.?\d*)')

    def __init__(self, map_dungeon, remaining_time, field_names, output_csv_name):
        self.map_dungeon = map_dungeon
        self.remaining_time_const = Decimal(remaining_time)
        self.remaining_time = None
        self.map_data = None
        self.experience = 0
        self.max_experience = 280
        self.end_game_trigger = False
        self.field_names = field_names
        self.output_csv_name = output_csv_name
        self.total_time_spent = datetime.timedelta()
        self.data_for_csv = []

    def initial_conditions(self):
        """
        Возвращает параметры в дефолтное значение
        :return: None
        """
        self.end_game_trigger = False
        self.remaining_time = self.remaining_time_const
        self.total_time_spent = datetime.timedelta()
        self.experience = 0
        self.data_for_csv = []

    def start_game(self):
        """
        Содержит основной цикл игры
        :return: None
        """
        self.initial_conditions()
        with open(self.map_dungeon, mode="r") as map_dungeon_file:
            self.map_data = json.load(map_dungeon_file)
            while self.remaining_time > 0:
                location, content_map = list(self.map_data.items())[0]
                self.data_generation_csv(location)
                player_action = self.io_display(location, content_map)
                self.selection_processing(player_action, content_map)
                if self.end_game_trigger:
                    break
            else:
                print(
                    "Вы не успели открыть люк!!! НАВОДНЕНИЕ!!!"
                    "\nУ вас темнеет в глазах... прощай, принцесса..."
                    "\nНо что это?! Вы воскресли у входа в пещеру... Не зря матушка дала вам оберег"
                    "\nНу, на этот-то раз у вас все получится! Трепещите, монстры!"
                    "\nВы осторожно входите в пещеру..."
                )

    def extract_dict_key(self, item):
        """
        Вытаскивает ключ из словаря, если это словарь
        :param item: словарь
        :return: либо сам item, либо ключ
        """
        if isinstance(item, dict):
            item = list(item.keys())[0]
        return item

    def counting_time(self, spent_time):
        """
        Подсчет времени в данже
        :param spent_time: понраченное время в секундах (Decimal)
        :return: None
        """
        current_spent_time = datetime.timedelta(seconds=float(spent_time))
        self.total_time_spent += current_spent_time

    def data_generation_csv(self, location):
        """
        Формирует данные для csv
        :param location: str текущая локация
        :return: None
        """
        current_datetime = datetime.datetime.now()
        current_datetime_str = current_datetime.strftime("%d.%m.%Y %H:%M:%S.%f")
        line_information = [location, self.experience, current_datetime_str]
        line_information_dict = dict(zip(self.field_names, line_information))
        self.data_for_csv.append(line_information_dict)

    def io_display(self, location, content):
        """
        Вывод на консосль сообщений для игрока, ввод следующего шага
        :param location: тукущая локация
        :param content: наполнение локации (монстры, следующие локации)
        :return: player_action-выбранное действие игрока
        """
        print(f"\nВы находитесь в {location}")
        print(f"У вас {self.experience} опыта и осталось {self.remaining_time} до наводнения")
        print(f"Прошло времени в подземелье {self.total_time_spent}")

        # Выводим, содержание комнаты
        print("Внутри вы видите:")
        for item in content:
            item = self.extract_dict_key(item)
            if re.search(DnD.re_mob, item):
                print(f"- Монстра {item}")
            else:
                print(f"- Вход в локацию: {item}")

        # Выводим, возможные дейтсвия
        print("Выберите действие:")
        index = 0
        for index, item in enumerate(content):
            item = self.extract_dict_key(item)
            if re.search(DnD.re_mob, item):
                print(f"{index + 1}. Убить монстра {item}")
            else:
                print(f"{index + 1}. Перейти в локацию {item}")
        index = index + 1 if content else 0
        print(f"{index + 1}. Сдаться и выйти из игры")
        while True:
            try:
                player_action = int(input("Введите номер действия:")) - 1
                if (player_action < 0) or (player_action > index):
                    raise IndexError
                return player_action
            except IndexError:
                print(f"\nВведите число от 1 до {index + 1}")
            except ValueError:
                print(f"\nВведите число")

    def selection_processing(self, player_action, content):
        """
        Обработка действий игрока в зависимости от выбранного item
        :param player_action: действие игрока
        :param content: список, включающий в себя содержимое локации
        :return: None
        """
        try:
            current_item = content.pop(player_action)
            item = self.extract_dict_key(current_item)
            coincidence_mob = re.search(DnD.re_mob, item)
            coincidence_location = re.search(DnD.re_location, item)
            coincidence_hatch = re.search(DnD.re_hatch, item)
            if coincidence_mob:
                print("\nВы выбрали сражаться с монстром")
                exp = int(coincidence_mob.group(1))
                spent_time = coincidence_mob.group(2)
                self.experience += exp
            elif coincidence_location:
                print(f"\nВы выбрали переход в локацию {item}")
                spent_time = coincidence_location.group(1)
                self.map_data = current_item
            elif coincidence_hatch:
                if self.experience >= self.max_experience:
                    self.end_game_trigger = True
                    print("\nПоздравляем, вы прошли все подземелье и нашли выход!")
                else:
                    print("\nО нет! Для того что бы открыть люк нужно 280 очков опыта!")
                    content.append(current_item)
                spent_time = coincidence_hatch.group(1)
            self.remaining_time -= Decimal(spent_time)
            self.counting_time(spent_time=spent_time)
        except IndexError:
            self.end_game_trigger = True
            print("\nК сожалению вы не станете великим героем :(")

    def write_csv(self):
        """
        Записывает данные в csv файл
        :return: None
        """
        with open(self.output_csv_name, mode="w", newline="") as out_csv:
            writter = csv.DictWriter(out_csv, delimiter=",", fieldnames=self.field_names)
            writter.writeheader()
            for row in self.data_for_csv:
                writter.writerow(row)


def run_game(game_session):
    """Цикл игры и запись информации в csv файл"""
    while not game_session.end_game_trigger:
        game_session.start_game()
        game_session.write_csv()


remaining_time = '123456.0987654321'
# если изначально не писать число в виде строки - теряется точность!
field_names = ['current_location', 'current_experience', 'current_date']
if __name__ == '__main__':
    my_game = DnD(
        map_dungeon="rpg.json",
        remaining_time=remaining_time,
        field_names=field_names,
        output_csv_name="dungeon.csv")
    run_game(game_session=my_game)