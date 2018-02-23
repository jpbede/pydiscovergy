class Meter:
    def __init__(self, serialNumber, type, measurementType, location, *args, **kwargs):
        """Represents a meter"""
        self.serial_number = serialNumber
        self.type = type
        self.measurement_type = measurementType
        self.location = Location(**location)

    def get_meter_id(self):
        return self.type + "_" + self.serial_number


class Location:
    def __init__(self, city, street, zip, streetNumber, country, *args, **kwargs):
        """Represents a smart meter location"""
        self.city = city
        self.street = street
        self.zip = zip
        self.street_number = streetNumber
        self.country = country