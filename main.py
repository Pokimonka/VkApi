import sys

import requests
import time
import logging
from pprint import pprint
from requests import Response


class VKPhoto:


    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version, 'album_id': 'profile', 'extended': 1}


    def get_max_size(self, phot: dict) ->dict:
        photos_type = ['w', 'z', 'y', 'r', 'q', 'p', 'o', 'x', 'm', 's']
        for type in photos_type:
            if type in phot:
                return phot[type]


    def get_saved_photos(self, response: Response, count_to_save: str):
        saved_photos = {}
        photos = {}
        likes = []
        for item in response.json()['response']['items']:
            sizes = {}
            name = str(item['likes']['count'])
            if name in likes :
                name += f'_{time.strftime("%B_%d_%Y", time.gmtime(float(item["date"])))}'
            likes.append(name)
            for id, size in enumerate(item['sizes']):
                sizes[size['type']] = id

            photo_with_max_size = self.get_max_size(sizes)

            photos[name+'.jpg'] = item['sizes'][photo_with_max_size]
        if (int(count_to_save) > len(photos)):
            count = 5
            print("Вы запросили больше фото, чем есть в профиле. Сохранятся 5 фото.")
            logging.warning("Запрошено больше фото, чем есть. Сохранено 5 фото.")
        elif (count_to_save == ""):
            logging.info("Будет сохранено 5 фото")
            count = 5
        elif (int(count_to_save) == 0):
            return photos
        else:
            count = int(count_to_save)

        list_count_to_save = list(photos.keys())
        for n in range(count):
            saved_photos[list_count_to_save[n]] = photos[list_count_to_save[n]]
        logging.info("Успешно сформирован словарь с фото")
        return saved_photos


    def get_users_photo(self, count_to_save: str):
        url = 'https://api.vk.com/method/photos.get'
        params = {'user_id ': self.id}
        try:
            resp = requests.get(url, params={**self.params, **params})
            return self.get_saved_photos(resp, count_to_save)
        except KeyError:
            print("Недействительный токен ВК")
            logging.error("Токен ВК недействителен")
            sys.exit(1)


class YandexPhoto:

    def __init__(self, access_token, path_to_load, photos_for_download):
        self.token = access_token
        self.path = path_to_load
        self.photos = photos_for_download
        self.params = {"path": self.path}
        self.headers = {"Authorization": f"OAuth {self.token}"}

    def set_directory(self):
        url = 'https://cloud-api.yandex.net/v1/disk/resources/'
        resp = requests.get(url, params=self.params, headers=self.headers)
        #при существующей папке я решила оставлять ее и подгружать оставшиеся фото
        #можно создать копию, в условии не прописано, как делать,
        # идем по пути наименьшего сопротивления)))
        if (resp.status_code != 200):
            requests.put(url, params=self.params, headers=self.headers)
            logging.info("Папка успешно создана")

    def set_photo_in_directory(self):
        result = []
        for photo in self.photos:
            path_photo = f"/{self.params['path']}/{photo}"
            params = {
                'path': path_photo
            }
            url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            response = requests.get(url, params=params, headers=self.headers)
            if (response.status_code == 409 and response.json()['error'] == 'DiskResourceAlreadyExistsError'):
                logging.warning(f"Фото {photo} уже загружено")
                continue

            download_url = response.json()['href']
            data = requests.get(self.photos[photo]['url'])
            requests.put(download_url, data=data)
            logging.info("Фото успешно загружено на Яндекс диск")
            result.append({"file_name": photo, "size": self.photos[photo]['type']})
        if (result == []):
            print("Эти фото уже сохранены.")
            logging.info("Фото уже сохранены. Ничего нового не добавлено")
        return result


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, filename="SavePhoto.log")
    with open('SavePhoto.log', 'w'):
        pass
    logging.info(".log файл очищен")

    access_vk_token = input("Введите токен vk: ")
    # я хотела здесь проверить токен вк с помощью secure.checkToken, но не получилось, так что
    # программа будет завершаться с кодом 1 и с сообщением о невалидном токене.
    user_id_ = input("Введите VKID: ")
    access_yandex_token = input("Введите токен с Яндекс Полигона: ")
    print("Ведите количество фото, которые хотите сохранить.")
    print("Если хотите сохранить все - введите 0, ")
    number_of_photos = (input("или оставьте поле пустым и сохранятся 5 фото: "))
    logging.info(f"Пользователь запросил {number_of_photos} фото для сохранения")


    vk = VKPhoto(access_vk_token, user_id_)
    photos = vk.get_users_photo(number_of_photos)
    path = 'VkPhotos'
    yandex = YandexPhoto(access_yandex_token, path, photos)
    yandex.set_directory()
    logging.info("запрос на сохранение фото в YD")
    pprint(yandex.set_photo_in_directory())

