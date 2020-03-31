import csv
import datetime
import json
import requests

from dateutil.parser import parse as date_parser

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
        r = requests.get(url)
        return r.json()

    def get_url(self):
        return self.__current_url or self.__basic_url


class Covid19(GitHub):
    def __init__(self, owner, repo):
        GitHub.__init__(self, owner, repo)
        self.categories = ('confirmed', 'deaths', 'recovered')
        self.countries = {}
        self.current_coordinates = None
        self.current_dates = {}
        path = 'dades/covid19'
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
        if not self.countries[country].get('latitude'):
            self.countries[country]['latitude'] = self.current_coordinates['lt']
            self.countries[country]['longitude'] = self.current_coordinates['ln']
            self.countries[country]['dates'] = {}
        for key in self.current_dates:
            date = datetime.datetime.strptime(key, '%m/%d/%y').strftime("%Y-%m-%d")
            if not self.countries[country]['dates'].get(date):
                self.countries[country]['dates'][date] = {}
            self.countries[country]['dates'][date].update(
                {self.current_coordinates['ct']:  int(self.current_dates.get(key))}
            )

    def __fill_province_data(self, country, province):
        if not self.countries[country][province].get('latitude'):
            self.countries[country][province]['country'] = country
            self.countries[country][province]['latitude'] = self.current_coordinates['lt']
            self.countries[country][province]['longitude'] = self.current_coordinates['ln']
            self.countries[country][province]['dates'] = {}
        for key in self.current_dates:
            date = datetime.datetime.strptime(key, '%m/%d/%y').strftime("%Y-%m-%d")
            if not self.countries[country][province]['dates'].get(date):
                self.countries[country][province]['dates'][date] = {}
            self.countries[country][province]['dates'][date].update(
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
                    if not self.countries.get(country):
                        self.countries[country] = {province: {}}
                    elif not self.countries[country].get(province):
                        self.countries[country][province] = {}
                    self.__fill_province_data(country, province)
                else:
                    if not self.countries.get(country):
                        self.countries[country] = {}
                    self.__fill_country_data(country)
        with open(self.__time_series_filename, 'w') as f:
            json.dump(self.countries, f, indent=4)

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

    def __get_data(self, filename):
        with open(filename, 'r') as f:
            return json.load(f)

    def get_time_series_data(self):
        return self.__get_data(self.__time_series_filename)

    def get_daily_reports_data(self):
        return self.__get_data(self.__daily_reports_filename)

    def compare(self):
        time_series = self.get_time_series_data()
        daily_reports = self.get_daily_reports_data()
        for country in time_series:
            if country in daily_reports:
                if time_series[country].get('dates'):
                    for date in time_series[country]['dates']:
                        if not time_series[country].get('dates'):
                            for province in time_series[country]:
                                if daily_reports[country].get(province):
                                    if date in daily_reports[country][province]['dates']:
                                        print(f"time_series country: {country} date: {date} data: {time_series[country][province]['dates'][date]}")
                                        print(f"daily_reports country: {country} date: {date} data: {daily_reports[country][province]['dates'][date]}\n")


def fix_country(admin1, admin2):
    if admin1 == "Mainland China":
        admin1 = "China"
    elif admin1 in ("Hong Kong", "Hong Kong SAR"):
        admin1, admin2 = "China", "Hong Kong"
    elif admin1 in ("Macao SAR", 'Macau'):
        admin1, admin2 = "China", "Macau"
    elif admin1 == 'US':
        admin1 = 'United States of America'
    elif admin1 == "UK":
        admin1, admin2 = "United Kingdom", ''
    elif admin1 == "Holy See":
        admin1 = "Vatican City"
    elif admin1 == 'Russian Federation':
        admin1 = "Russia"
    elif admin1 in ('Republic of Ireland', 'North Ireland'):
        admin1 = 'Ireland'
    elif admin1 == 'Republic of Moldova':
        admin1 = 'Moldova'
    elif admin1 in ('Taipei and environs', 'Taiwan*'):
        admin1 = 'Taiwan'
    elif admin1 == 'Iran (Islamic Republic of)':
        admin1 = 'Iran'
    elif admin1 in ('The Bahamas', 'Bahamas, The'):
        admin1 = 'Bahamas'
    elif admin1 in ('The Gambia', 'Gambia, The'):
        admin1 = 'Gambia'
    elif admin1 == admin2:
        admin2 = ''

    if admin1 in ('St. Martin', 'Saint Martin'):
        admin1, admin2 = 'France', 'Saint Martin'
    elif admin1 in ('Saint Barthelemy', 'French Guiana', 'Guadeloupe', 'Martinique', 'Reunion', 'Mayotte'):
        admin1, admin2 = 'France', admin1
    elif admin1 in ('Gibraltar', 'Channel Islands', 'Cayman Islands', 'Jersey'):
        admin1, admin2 = 'United Kingdom', admin1
    elif admin1 in ('Aruba', 'Curacao'):
        admin1, admin2 = 'Netherlands', admin1
    elif admin1 in ('Korea, South', 'Republic of Korea'):
        admin1, admin2 = 'South Korea', admin1
    elif admin1 in ('Faroe Islands', "Greenland"):
        admin1, admin2 = 'Denmark', admin1
    elif admin1 == "Viet Nam":
        admin1, admin2 = 'Vietnam', admin1
    elif admin1 == "East Timor":
        admin1, admin2 = 'Timor-Leste', ''
    elif admin1 == 'Cape Verde':
        admin1, admin2 = 'Cabo Verde', ''
    elif admin1 == 'Ivory Coast':
        admin1, admin2 = "Cote d'Ivoire", ''
    elif admin1 == 'Diamond Princess':
        admin1, admin2 = 'Cruise Ship', admin1
    elif admin1 == 'Burma':
        admin1, admin2 = 'Myanmar', ''
    elif admin1 == 'Others' and admin2 in ('Diamond Princess cruise ship', 'Cruise Ship'):
        admin1, admin2 = 'Cruise Ship', 'Diamond Princess'
    elif admin1 == 'MS Zaandam':
        admin1, admin2 = 'Cruise Ship', admin1

    if admin2 == 'Fench Guiana':
        admin2 = "French Guiana"
    elif admin2 == 'St Martin':
        admin2 = 'Saint Martin'
    elif admin2 == "UK":
        admin1, admin2 = "United Kingdom", ''
    elif admin2 == 'Bavaria':
        admin1, admin2 = 'Germany', ''

    if admin2 == 'None':
        admin2 = ''
    return admin1, admin2


def sanitize(old_dict):
    new_dict = {}
    for key in old_dict:
        old_dict[key] = old_dict[key].strip()
        new_key = key.replace("y_R", "y/r").replace("e_S", "e/s")
        new_key = new_key.lstrip('\ufeff').replace("_", " ").lower()
        if new_key == 'lat':
            new_key = 'latitude'
        elif new_key == 'long ':
            new_key = 'longitude'
        elif new_key == 'last update':
            old_dict[key] = date_parser(old_dict[key]).strftime("%Y-%m-%d %H:%M")
        elif new_key in ('confirmed', 'deaths', 'recovered', 'active'):
            old_dict[key] = int(old_dict[key] or 0)
        if new_key in ('latitude', 'longitude'):
            old_dict[key] = float(old_dict[key] or 0)
        new_dict[new_key] = old_dict[key]
    return new_dict


if __name__ == '__main__':
    g_owner = "CSSEGISandData"
    g_repo = "COVID-19"
    covid19 = Covid19(g_owner, g_repo)
    covid19.download_time_series()
    # covid19.download_daily_reports()

