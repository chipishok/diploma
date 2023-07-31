# Импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import vkTools
from data_store import add_user, engine, chek_user


class BotInterface():

    def __init__(self, comunity_token, acces_token):
        self.worksheet_cheked = None
        self.interface = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.interface)
        self.vkTools = vkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.interface.method('messages.send',
                              {'user_id': user_id,
                               'message': message,
                               'attachment': attachment,
                               'random_id': get_random_id()
                               }
                              )

    def process_search(self, event):
        self.worksheets = self.vkTools.search_worksheets(self.params[str(event.user_id)], self.offset
                                                         )
        self.offset += 10
        worksheet = self.worksheets.pop()
        while chek_user(engine, event.user_id, worksheet["id"]) is True:
            if len(self.worksheets) != 0:
                worksheet = self.worksheets.pop()
                continue
            else:
                self.process_search(event)
        else:
            self.worksheet_cheked = worksheet

    # Обработка событий / Получение сообщений
    def event_handler(self):
        longpoll = VkLongPoll(self.interface)
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    if event.text.lower() == 'привет':
                        '''Логика для получения данных'''
                        self.params[str(event.user_id)] = self.vkTools.get_profile_info(event.user_id)
                        self.message_send(event.user_id, f'Привет {self.params[str(event.user_id)]["name"]}')
                        if (self.params[str(event.user_id)]['year'] is None
                                and self.params[str(event.user_id)]['city'] is None):
                            self.message_send(event.user_id, 'Я вижу, что у тебя не указан город и возраст. Исправь это,'
                                                             'введя команду Город <Название твоего города>.\n'
                                                             'И команду Возраст <твой возраст числом>')

                        elif self.params[str(event.user_id)]['year'] is None:
                            self.message_send(event.user_id, 'Я вижу, что у тебя не указан возраст. Исправь это,'
                                                             'введя команду Возраст <твой возраст числом>')

                        elif self.params[str(event.user_id)]['city'] is None:
                            self.message_send(event.user_id, 'Я вижу, что у тебя не указан город. Исправь это,'
                                                             'введя команду Город <Название твоего города>.\n')
                        else:
                            self.message_send(event.user_id, 'Твои данные:\n'
                                                             f'Имя и Фамилия: {self.params[str(event.user_id)]["name"]}\n'
                                                             f'Город: {self.params[str(event.user_id)]["city"]}\n'
                                                             f'Возраст: {self.params[str(event.user_id)]["year"]}\n')
                            self.message_send(event.user_id, 'Если что, ты можешь исправить город и возраст с помощью'
                                                             ' команд:\nГород <Название твоего города>\n '
                                                             'Возраст <твой возраст числом>')

                    elif event.text.lower() == 'поиск':
                        '''Логика для поиска'''
                        self.process_search(event)
                        if (self.params[str(event.user_id)]['year'] is None or
                                self.params[str(event.user_id)]['city'] is None):
                            self.message_send(event.user_id, 'Данные о тебе не полные, добавь недостающие данные и запускай'
                                                             'поиск')

                        else:
                            if self.worksheets:
                                worksheet = self.worksheets.pop()
                                photos = self.vkTools.get_photos(worksheet['id'])
                                photo_string = ''
                                for photo in photos:
                                    photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                                add_user(engine, event.user_id, self.worksheet_cheked["id"])

                            else:
                                self.worksheets = self.vkTools.search_worksheets(self.params, self.offset)
                                worksheet = self.worksheets.pop()
                                photos = self.vkTools.get_photos(worksheet['id'])
                                photo_string = ''
                                for photo in photos:
                                    photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                                self.offset += 10

                            self.message_send(
                                event.user_id,
                                f'имя: {worksheet["name"]} \n ссылка: vk.com/id{worksheet["id"]}',
                                attachment=photo_string
                            )

                    elif event.text.lower() == 'город':
                        self.message_send(event.user_id,
                                          'Вы должны ввести город  в следующем формате: город <название города>. '
                                          'Например: город Москва')

                    elif event.text.lower().startswith('город '):
                        city = event.text.lower().split('город ')[1]
                        user_city = city  # Сохраняем введенный город в переменной user_city
                        self.params[str(event.user_id)]['city'] = user_city
                        self.message_send(event.user_id, f'Ваш город: {user_city.capitalize()}')

                    elif event.text.lower().startswith('возраст '):
                        age_str = event.text.lower().split('возраст ')[1]
                        if not age_str == None:
                            user_age = int(age_str)  # Сохраняем введенный возраст в переменную user_age
                            self.message_send(event.user_id, f'Ваш возраст: {user_age}')
                            self.params[str(event.user_id)]['year'] = user_age
                        else:
                            self.message_send(event.user_id,
                                              'Некорректный формат возраста. '
                                              'Пожалуйста, введите возраст в виде целого числа.')
                    elif event.text.lower() == 'пока':
                        self.message_send(event.user_id, 'Пока')
                    else:
                        self.message_send(
                            event.user_id, 'Неизвестная команда')
                except Exception as e:
                    print(e)


if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()
