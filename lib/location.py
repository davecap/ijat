import string
from geopy import geocoders

def main():
    print 'This is a library!'

def find_city(s):
    api_key="ABQIAAAAQN5WZaHJfVndvygpt7fxMBRuX0AyuVcJAqNrjtVavPDeXaL5lRS8b8glZc1oa6rjD_F5V7tgfVGm2g"
    g = geocoders.Google(api_key)
    try:
        res = g.geocode(s, exactly_one=False)
    except:
        return None
    return res

def find_restaurant(s):
    return None

if __name__=='__main__':
    main()
