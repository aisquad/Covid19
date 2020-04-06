import csv
import json

from datetime import datetime
from re import match

from Covid19.covid19 import GitHub


class Eclectikus(GitHub):
    def __init__(self, owner='Eclectikus', repo='COVID-19'):
        GitHub.__init__(self, owner, repo)
        self.autonomies = set()

    def download_data(self):
        path = 'data/'
        dates = {}
        for file in self.get_file_list(path):
            if match(r'covi\d+\.csv', file['name']):
                csv_reader = csv.DictReader(self.get_raw_file(file['download_url']).splitlines())
                date = datetime.strptime(file['name'], 'covi%d%m.csv').replace(year=2020).strftime("%Y-%m-%d")
                dates.update({date: {}})
                cases_amt = 0
                acc_inc_amt = 0
                uci_amt = 0
                deaths_amt = 0
                hosp_amt = 0
                new_amt = 0
                recovered_amt = 0
                for row_dict in csv_reader:
                    cases = int(row_dict['Casos'])
                    acc_inc = float(row_dict['IA'])
                    uci = int(row_dict['UCI'])
                    deaths = int(row_dict['Fallecidos'])
                    hosp = int(row_dict.get('Hospitalizados', 0))
                    new = int(row_dict.get('Nuevos', 0))
                    recovered = int(row_dict.get('Curados', 0))
                    dates[date][row_dict['ID']] = {
                        'id': int(row_dict['ID']),
                        'ca': row_dict['CCAA'],
                        'cases': cases,
                        'acc_inc': acc_inc,
                        'uci': uci,
                        'deaths': deaths,
                        'hosp': hosp,
                        'new': new,
                        'recovered': recovered
                    }
                    cases_amt += cases
                    acc_inc_amt += acc_inc
                    uci_amt += uci
                    deaths_amt += deaths
                    hosp_amt += hosp
                    new_amt += new
                    recovered_amt += recovered
                dates[date]['Total'] = {
                    'cases': cases_amt,
                    'acc_inc': acc_inc_amt,
                    'uci': uci_amt,
                    'deaths': deaths_amt,
                    'hosp': hosp_amt,
                    'new': new_amt,
                    'recovered': recovered_amt
                }
        self.autonomies = [dates[date][c]['ca'] for c in dates[date] if c != 'Total']
        return dates

    def save_data(self):
        data = self.download_data()
        places = {}
        for aut in self.autonomies:
            places[aut] = {'dates': {}}
        places['Total'] = {'dates': {}}
        for date in data:
            for aut in data[date]:
                if data[date][aut].get('ca'):
                    aut_name = data[date][aut]['ca']
                    places[aut_name]['dates'][date] = dict(
                        filter(lambda item: isinstance(item[1], (float,int)), data[date][aut].items())
                    )
            places['Total']['dates'][date] = data[date]['Total']
        with open('./data/spain.json', 'w') as f:
            json.dump(places, f, indent=4, sort_keys=True)


