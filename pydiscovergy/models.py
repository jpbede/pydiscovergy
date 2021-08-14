class ConsumerToken:
    """Represents a consumer token pair"""

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret


class RequestToken:
    def __init__(self, token, token_secret):
        self.token = token
        self.token_secret = token_secret


class AccessToken(RequestToken):
    """Represents a access token pair"""


class Meter:
    def __init__(self, serialNumber, type, measurementType, location, **kwargs):
        """Represents a meter"""
        self.serial_number = serialNumber
        self.type = type
        self.measurement_type = measurementType
        self.location = Location(**location)
        self.additional = kwargs

    def get_meter_id(self):
        return self.type + "_" + self.serial_number


class Location:
    def __init__(self, city, street, zip, streetNumber, country):
        """Represents a smart meter location"""
        self.city = city
        self.street = street
        self.zip = zip
        self.street_number = streetNumber
        self.country = country


class Reading:
    def __init__(self, time, values):
        """Represents a reading"""
        self.time = time
        self.values = values
