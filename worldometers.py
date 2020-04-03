import json
import locale
import requests

from datetime import date, timedelta
from bs4 import BeautifulSoup


class Worldometers:
    def __init__(self):
        locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF8')
        page = requests.get('https://www.worldometers.info/coronavirus/')
        self.soup = BeautifulSoup(page.content, 'html.parser')

    def get_table(self, name):
        data = []
        table = self.soup.find('table', {'id': f'main_table_countries_{name}'})
        cols = [th.text for th in table.find_all('th')]
        for row in [tr for tr in table.find_all('tr')]:
            row_dict = dict(zip(cols, [td.text for td in row.find_all('td')]))
            if not row_dict:
                continue
            data.append(_clean_dict(row_dict))
        return data

    def today_table(self):
        return self.get_table('today')

    def yesterday_table(self):
        return self.get_table('yesterday')

    def save(self):
        today = date.today()
        filename = today.strftime("./data/%Y-%m-%d.json")
        data = self.today_table()
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        yesterday = date.today() - timedelta(days=1)
        data = self.yesterday_table()
        filename = yesterday.strftime("./data/%Y-%m-%d.json")
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)


def _clean_dict(d):
    for key, value in d.items():
        if key in ('TotalCases', 'TotalDeaths', 'TotalRecovered', 'ActiveCases', 'Serious,Critical', 'Tot\xa0Cases/1M pop', 'Deaths/1M pop'):
            if value.strip() == '':
                d[key] = 0
            elif not '.' in value:
                d[key] = locale.atoi(value.strip())
            else:
                d[key] = locale.atof(value.strip())
        elif key in ('NewCases', 'NewDeaths'):
            if value == '':
                d[key] = 0
            else:
                d[key] = locale.atoi(value.lstrip('+').strip())
    return d


if __name__ == "__main__":
    worldmeters = Worldometers()
    worldmeters.save()
