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

        cursor = self.connection.cursor()
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

    def add_db_entry(self, record: tuple, verbose=False):
        """"Record tuple format (timestamp, entry_id, temp_in, temp_out, humidity_in, dew_point_in,
            batt_volt, batt_curr, air_pressure, light_intensity"""
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

        cursor = self.connection.cursor()
        cursor.execute(query)

        if verbose:
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

    def retrieve_latest_entries_from_ts(self, **kwargs):
        """Retrieve latest records from ThingSpeak channel and update records in local DB"""
        result = self.get_ts_data(**kwargs)
        for i in result:
            self.add_db_entry(i)

        if self.verbose:
            print(f"{len(result)} records updated in local DB.")

    def get_all_data(self):
        """Return all stored data as Pandas DataFrame"""
        import pandas as pd

        query = f"""SELECT time_stamp, temp_inside, temp_outside, humidity_inside, dew_point_inside, air_pressure, 
                            light_intensity, battery_voltage, battery_current, battery_power
                    FROM greenhouse_src_data
                    ORDER by time_stamp
                    ;"""

        cursor = self.connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()

        df = pd.DataFrame(result)
        df.index = df[0]
        df.drop([0, ], axis=1, inplace=True)

        df.columns = ["Temperature in [°C]", "Temperature out [°C]", "Humidity in [%]", "Dew point in [°C]",
                      "Air pressure [hPa]", "Light intensity [lux]",
                      "Battery voltage [V]", "Battery current [mA]", "Battery power [mW]"]
        return df
