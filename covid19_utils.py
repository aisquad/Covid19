from dateutil.parser import parse as date_parser


"""
    These function has been created to clean any results because of any items in downloaded files have
    a lot of inconsistencies.
    
    fix_country() fix the name of the country because of a same region can be named with several names: we can find
    Hong Kong or Hong Kong SAR as a country or as dependent of China and several other similar cases.
    
    sanitize() pretends regularize the name of the keys. We can find Long_ and Longitude for longitude
"""

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


