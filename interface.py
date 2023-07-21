# Импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import vkTools
from data_store import add_user, engine
from data_store import chek_user


class BotInterface():

    def __init__(self, comunity_token, acces_token):
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

    def process_search(self, event, params, offset):
        self.worksheets = self.vkTools.search_worksheets(self.params, self.offset
        )
        self.offset += 10
        worksheet = self.worksheets.pop()
        while chek_user(engine, event.user_id,worksheet["id"]) is True:
            if len(self.worksheets) != 0:
                worksheet = self.worksheets.pop()
                continue
            else:
                self.process_search(event, self.params, self.offset)
        else:
            self.worksheet_cheked = worksheet

    # Обработка событий / Получение сообщений
    def event_handler(self):
        longpoll = VkLongPoll(self.interface)
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''Логика для получения данных'''
                    self.params = self.vkTools.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Привет {self.params["name"]}')
                elif event.text.lower() == 'поиск':
                    '''Логика для поиска'''
                    self.process_search(event, self.params, self.offset)
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

                elif event.text.lower() == 'пока':
                    self.message_send(event.user_id, 'Пока')
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token )
    bot_interface.event_handler()
