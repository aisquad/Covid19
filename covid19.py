import requests

from Covid19.worldometers import Worldometers


class GitHub:
    def __init__(self, owner, repo):
        self.__owner = owner
        self.__repo = repo
        self.__basic_url = f'https://github.com/{owner}/{repo}'
        self.__current_url = ''

    def get_raw_file(self, raw_url):
        self.__current_url = raw_url
        return requests.get(raw_url).content.decode()

    def get_file_content(self, filename, path=''):
        url = self.__basic_url + f'/raw/master/{path}{filename}'
        self.__current_url = url
        return self.get_raw_file(url)

    def get_file_list(self, path):
        url = f"https://api.github.com/repos/{self.__owner}/{self.__repo}/contents/{path}"
        self.__current_url = url
        r = requests.get(url)
        return r.json()

    def get_url(self):
        return self.__current_url or self.__basic_url


def __main():
    import argparse
    from Covid19.eclectikus import Eclectikus
    from Covid19.jhu import JHU

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-a', dest='admins', action='store_true')
    argparser.add_argument('-c', dest='country')
    argparser.add_argument('-s', dest='spain', action='store_true')
    argparser.add_argument('-u', dest='update', action='store_true')
    argparser.add_argument('-w', dest='worldometers', action='store_true')
    argparser.add_argument('-W', dest='who', action='store_true')
    args = argparser.parse_args()

    owner = "CSSEGISandData"
    repo = "COVID-19"
    covid19 = JHU(owner, repo)

    if args.update:
        covid19.update()
    elif args.admins:
        covid19.get_admins()
    elif args.country:
        covid19.load_time_series_data()
        covid19.get_country_stats(args.country)

    if args.spain:
        spain_covid19 = Eclectikus()
        spain_covid19.save_data()

    if args.who:
        covid19.download_who_time_series()

    if args.worldometers:
        worldometers = Worldometers()
        worldometers.get_tables()


if __name__ == '__main__':
    __main()
