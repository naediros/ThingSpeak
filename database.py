class Database:

    def __init__(self, verbose=False):
        import sqlite3
        import dotenv
        import os

        dotenv.load_dotenv()

        self.connection = sqlite3.connect("data.db")
        self.verbose = verbose
        self.TS_READ_KEY = os.environ["READ_KEY"]
        self.TS_CHANNEL_ID = os.environ["CHANNEL_ID"]


    def __str__(self):
        return "SQLite database interface for greenhouse weather station"

    def create_src_data_table(self):
        query = f"""CREATE TABLE IF NOT EXISTS greenhouse_src_data (
                        time_stamp REAL PRIMARY KEY,
                        entry_id INTEGER,
                        temp_inside REAL,
                        temp_outside REAL,
                        humidity_inside INTEGER,
                        dew_point_inside REAL,
                        battery_voltage REAL,
                        battery_current REAL,
                        air_pressure INTEGER,
                        light_intensity INTEGER,
                        battery_power REAL
                        );
                        """

        with self.connection as cursor:
            cursor.execute(query)

    def get_ts_data(self, record_count=8000):
        import requests

        r = requests.get(
            f'https://api.thingspeak.com/channels/{self.TS_CHANNEL_ID}/feeds.csv?api_key={self.TS_READ_KEY}&results={record_count}')
        result = r.text.split("\n")
        result = [tuple(i.split(",")) for i in result if i]
        result = result[1:]

        if self.verbose:
            print(f"{len(result)} records retrieved from ThingSpeak server")

        return result

    def add_db_entry(self, record:tuple):
        """"Record tuple format (timestamp, entry_id, temp_in, temp_out, humidity_in, dew_point_in, batt_volt, batt_curr, air_pressure, light_intensity"""
        timestamp = record[0]
        entry_id = int(record[1])
        temp_in = float(record[2])
        temp_out = float(record[3])
        humidity_in = int(record[4])
        dew_point_in = float(record[5])
        voltage = float(record[6])
        current = int(record[7])
        power = voltage * current
        air_pressure = int(record[8])
        light_intensity = int(record[9])

        query = f"""INSERT OR REPLACE INTO greenhouse_src_data 
                   VALUES ("{timestamp}", {entry_id}, {temp_in}, {temp_out}, {humidity_in}, {dew_point_in}, 
                            {voltage}, {current}, {air_pressure}, {light_intensity}, {power})
                    ;"""

        with self.connection:
            self.connection.execute(query)

        if self.verbose:
            print(f"""Entry number: {entry_id} recorded on: {timestamp}
                      Inside: 
                              Temperature: {temp_in} deg.C
                              Humidity:     {humidity_in} %
                              Dew point:   {dew_point_in} deg. C

                      Outside:
                              Temperature:     {temp_out} deg.C
                              Air pressure:    {air_pressure} hPa
                              Light intensity: {light_intensity} lux

                      Battery:
                              Voltage: {voltage} V
                              Current: {current} mA
                              Power:   {power:.0f} mW """)


def test():
    db = Database(verbose=False)
    # db.create_src_data_table()
    result = db.get_ts_data()


    for i in result:
        db.add_db_entry(i)

test()