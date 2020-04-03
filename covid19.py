import csv
import datetime
import json
import requests

from Covid19.utils import date_parser, sanitize, fix_country
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


class Covid19(GitHub):
    def __init__(self, owner, repo):
        GitHub.__init__(self, owner, repo)
        self.categories = ('confirmed', 'deaths', 'recovered')
        self.__time_series_data = {}
        self.__daily_reports_data = {}
        self.current_coordinates = None
        self.current_dates = {}
        path = './data'
        self.__time_series_filename = f'{path}/covid19_time_series.json'
        self.__daily_reports_filename = f'{path}/covid19_daily_reports.json'

    def __get_time_series_file(self, category):
        path = 'csse_covid_19_data/csse_covid_19_time_series/'
        filename = f'time_series_covid19_{category}_global.csv'
        return self.get_file_content(filename, path)

    def __get_daily_reports_files(self):
        path = 'csse_covid_19_data/csse_covid_19_daily_reports'
        return self.get_file_list(path)

    def __fill_country_data(self, country):
        if not self.__time_series_data[country].get('latitude'):
            self.__time_series_data[country]['latitude'] = self.current_coordinates['lt']
            self.__time_series_data[country]['longitude'] = self.current_coordinates['ln']
            self.__time_series_data[country]['dates'] = {}
        for key in self.current_dates:
            date = datetime.datetime.strptime(key, '%m/%d/%y').strftime("%Y-%m-%d")
            if not self.__time_series_data[country]['dates'].get(date):
                self.__time_series_data[country]['dates'][date] = {}
            self.__time_series_data[country]['dates'][date].update(
                {self.current_coordinates['ct']:  int(self.current_dates.get(key))}
            )

    def __fill_province_data(self, country, province):
        if not self.__time_series_data[country][province].get('latitude'):
            self.__time_series_data[country][province]['country'] = country
            self.__time_series_data[country][province]['latitude'] = self.current_coordinates['lt']
            self.__time_series_data[country][province]['longitude'] = self.current_coordinates['ln']
            self.__time_series_data[country][province]['dates'] = {}
        for key in self.current_dates:
            date = datetime.datetime.strptime(key, '%m/%d/%y').strftime("%Y-%m-%d")
            if not self.__time_series_data[country][province]['dates'].get(date):
                self.__time_series_data[country][province]['dates'][date] = {}
            self.__time_series_data[country][province]['dates'][date].update(
                {self.current_coordinates['ct']:  int(self.current_dates.get(key))}
            )

    def download_time_series(self):
        for category in self.categories:
            csv_dict = csv.DictReader(self.__get_time_series_file(category).splitlines())
            print(category, self.get_url())
            for keys in csv_dict:
                lat = keys.pop('Lat')
                long = keys.pop('Long')
                province = keys.pop('Province/State') or None
                country = keys.pop('Country/Region')
                self.current_coordinates = {'ct': category, 'lt': float(lat), 'ln': float(long)}
                self.current_dates = keys
                if province:
                    if not self.__time_series_data.get(country):
                        self.__time_series_data[country] = {province: {}}
                    elif not self.__time_series_data[country].get(province):
                        self.__time_series_data[country][province] = {}
                    self.__fill_province_data(country, province)
                else:
                    if not self.__time_series_data.get(country):
                        self.__time_series_data[country] = {}
                    self.__fill_country_data(country)
        with open(self.__time_series_filename, 'w') as f:
            json.dump(self.__time_series_data, f, indent=4)

    def download_daily_reports(self):
        places = {}
        for file in covid19.__get_daily_reports_files():
            if file['name'].endswith('.csv'):
                csv_dict = csv.DictReader(covid19.get_raw_file(file['download_url']).splitlines())
                date = date_parser(file['name'].split('.')[0]).strftime('%Y-%m-%d')
                print(date, self.get_url())
                for keys in csv_dict:
                    new_dict = sanitize(keys)
                    admin1 = new_dict.get('country/region')
                    admin2 = new_dict.get('province/state')
                    admin3 = new_dict.get('admin2')
                    confirmed = new_dict['confirmed']
                    deaths = new_dict['deaths']
                    recovered = new_dict['recovered']
                    active = new_dict.get('active', 0)
                    latitude = new_dict.get('latitude', 0)
                    longitude = new_dict.get('longitude', 0)
                    last_update = new_dict['last update']
                    data = {
                        'last update': last_update,
                        'confirmed': confirmed,
                        'deaths': deaths,
                        'recovered': recovered,
                        'active': active
                    }
                    admin1, admin2 = fix_country(admin1, admin2)
                    if admin3:
                        if places.get(admin1) and places[admin1].get(admin2):
                            if places[admin1][admin2].get(admin3):
                                places[admin1][admin2][admin3]['dates'][date] = data
                            else:
                                places[admin1][admin2][admin3] = {
                                    'admin1': admin1,
                                    'admin2': admin2,
                                    'admin3': admin3,
                                    'latitude': latitude,
                                    'longitude': longitude,
                                    'dates': {date: data}
                                }
                    elif admin2:
                        if not places.get(admin1):
                            places[admin1] = {}
                        if not places[admin1].get(admin2):
                            places[admin1][admin2] = {}
                        if not places[admin1][admin2].get('dates'):
                            places[admin1][admin2] = {
                                'admin1': admin1,
                                'admin2': admin2,
                                'latitude': latitude,
                                'longitude': longitude,
                                'dates': {date: data}
                            }
                        else:
                            if places[admin1][admin2].get('latitude') == 0 and float(latitude):
                                places[admin1][admin2]['latitude'] = latitude
                                places[admin1][admin2]['longitude'] = longitude
                            if places[admin1][admin2]['dates'].get(date):
                                for item in data:
                                    places[admin1][admin2]['dates'][date][item] += data[item]
                            else:
                                places[admin1][admin2]['dates'][date] = data
                    elif admin1:
                        if not places.get(admin1):
                            places[admin1] = {
                                'admin1': admin1,
                                'latitude': latitude,
                                'longitude': longitude,
                                'dates': {date: data}
                            }
                        else:
                            if places[admin1].get('latitude') == 0 and float(latitude):
                                places[admin1]['latitude'] = latitude
                                places[admin1]['longitude'] = longitude
                            if not places[admin1].get('dates'):
                                if len(places[admin1]) == 0:
                                    places[admin1] = {
                                        'admin1': admin1,
                                        'latitude': latitude,
                                        'longitude': longitude,
                                        'dates': {date: data}
                                    }
                                else:
                                    places[admin1]['latitude'] = latitude
                                    places[admin1]['longitude'] = longitude
                                    places[admin1]['dates'] = {date: data}
                            else:
                                places[admin1]['dates'][date] = data
        with open(self.__daily_reports_filename, 'w') as f:
            f.write(json.dumps(places, indent=2))
        self.__daily_reports_data = places

    def __get_data(self, filename):
        with open(filename, 'r') as f:
            return json.load(f)

    def get_time_series_data(self):
        return self.__get_data(self.__time_series_filename)

    def get_daily_reports_data(self):
        return self.__get_data(self.__daily_reports_filename)

    def __load_data(self):
        self.__daily_reports_data = self.get_daily_reports_data()
        self.__time_series_data = self.get_time_series_data()

    def load_time_series_data(self):
        self.__time_series_data = self.get_time_series_data()

    def update(self):
        self.download_time_series()
        self.download_daily_reports()

    def get_admins(self):
        self.__load_data()
        categories = ('latitude', 'longitude', 'dates', 'admin1', 'admin2')
        admin1_stack = []
        admin2_stack = []
        admin3_stack = []
        for admin1 in self.__daily_reports_data:
            admin1_stack.append(admin1)
            self.get_country_stats(admin1)
            admin2_list = [a for a in self.__daily_reports_data[admin1] if a not in categories]
            for admin2 in admin2_list:
                admin2_stack.append(admin2)
                admin3_list = [a for a in self.__daily_reports_data[admin1][admin2] if a not in categories]
                for admin3 in admin3_list:
                    admin3_stack.append(admin3)
        print (len(admin1_stack), admin1_stack)
        print (len(admin2_stack), admin2_stack)
        print (len(admin3_stack), admin3_stack)

    def get_country_stats(self, target):
        if self.__time_series_data.get(target):
            country = self.__time_series_data[target]
            if country.get('dates'):
                for date in country['dates']:
                    data = country['dates'][date]
                    print(f"\t{date}: {data}")
        else:
            print(f"unknown country ({target})")

def __main():
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-a', dest='admins', action='store_true')
    argparser.add_argument('-c', dest='country')
    argparser.add_argument('-u', dest='update', action='store_true')
    argparser.add_argument('-w', dest='worldometers', action='store_true')
    args = argparser.parse_args()

    if args.update:
        covid19.update()
    elif args.admins:
        covid19.get_admins()
    elif args.country:
        covid19.load_time_series_data()
        covid19.get_country_stats(args.country)
    if args.worldometers:
        worldometers = Worldometers()
        worldometers.get_tables()


if __name__ == '__main__':
    g_owner = "CSSEGISandData"
    g_repo = "COVID-19"
    covid19 = Covid19(g_owner, g_repo)
    __main()
