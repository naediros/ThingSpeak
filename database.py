class Database:

    def __init__(self, verbose=False):
        import sqlite3
        import dotenv
        import os

        dotenv.load_dotenv()

        self.connection = sqlite3.connect("data.db")
        self.verbose = verbose
        self.GREENHOUSE_TS_READ_KEY = os.environ["GREENHOUSE_READ_KEY"]
        self.GREENHOUSE_TS_CHANNEL_ID = os.environ["GREENHOUSE_CHANNEL_ID"]

        self.DOOM_TS_READ_KEY = os.environ["DOOM_READ_KEY"]
        self.DOOM_TS_CHANNEL_ID = os.environ["DOOM_CHANNEL_ID"]

    def __del__(self):
        self.connection.close()

    def __str__(self):
        return "SQLite database interface for greenhouse weather station"

    def create_src_data_tables(self):
        query = f"""CREATE TABLE IF NOT EXISTS greenhouse_src_data (
                        time_stamp REAL PRIMARY KEY,
                        time_stamp_unix INTEGER,
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

        query = f"""CREATE TABLE IF NOT EXISTS doom_src_data (
                        time_stamp REAL PRIMARY KEY,
                        time_stamp_unix INTEGER,
                        entry_id INTEGER,
                        temp_livingroom REAL,
                        temp_heater_inlet REAL,
                        temp_heater_outlet REAL,
                        well_emergency_discharge REAL
                        );
                        """

        cursor = self.connection.cursor()
        cursor.execute(query)


    def convert_time_stamp(self, time_stamp:str):
        """Return UNIX epoch timestamp"""
        import time

        time_stamp = time_stamp[:-4]
        ts = time.strptime(time_stamp, '%Y-%m-%d  %H:%M:%S')
        time_stamp = time.mktime(ts)
        return int(time_stamp)

    def get_ts_data(self, channel_id, read_api_key, record_count=8000):
        import requests

        r = requests.get(
            f'https://api.thingspeak.com/channels/{channel_id}/feeds.csv?api_key={read_api_key}&results={record_count}')
        result = r.text.split("\n")
        result = [tuple(i.split(",")) for i in result if i]
        result = result[1:]

        if self.verbose:
            print(f"{len(result)} records retrieved from ThingSpeak server for channel ID {channel_id}")

        return result

    def add_db_entry_greenhouse(self, record: tuple, verbose=False):
        """"Record tuple format (timestamp, entry_id, temp_in, temp_out, humidity_in, dew_point_in,
            batt_volt, batt_curr, air_pressure, light_intensity"""
        time_stamp = record[0]
        time_stamp_unix = self.convert_time_stamp(time_stamp)
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
                   VALUES ("{time_stamp}", {time_stamp_unix}, {entry_id}, {temp_in}, {temp_out}, {humidity_in}, {dew_point_in}, 
                            {voltage}, {current}, {air_pressure}, {light_intensity}, {power})
                    ;"""

        cursor = self.connection.cursor()
        cursor.execute(query)

        if verbose:
            print(f"""Entry number: {entry_id} recorded on: {time_stamp}
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

    def add_db_entry_doom(self, record: tuple, verbose=False):
        """"Record tuple format (timestamp, entry_id, temp_livingroom, temp_heater_inlet, temp_heater_outlet, well_discharge"""

        time_stamp = record[0]
        time_stamp_unix = self.convert_time_stamp(time_stamp)
        entry_id = int(record[1])

        try:
            temp_living_room = float(record[2])
        except ValueError:
            temp_living_room = "NULL"

        try:
            temp_heater_inlet = float(record[3])
        except ValueError:
            temp_heater_inlet = "NULL"

        try:
            temp_heater_outlet = float(record[4])
        except ValueError:
            temp_heater_outlet = "NULL"

        try:
            well_discharge = float(record[5])
        except ValueError:
            well_discharge = "NULL"

        query = f"""INSERT OR REPLACE INTO doom_src_data 
                   VALUES ("{time_stamp}", {time_stamp_unix}, {entry_id}, {temp_living_room}, {temp_heater_inlet}, {temp_heater_outlet}, {well_discharge})
                    ;"""

        cursor = self.connection.cursor()
        cursor.execute(query)

        if verbose:
            print(f"""Entry number: {entry_id} recorded on: {time_stamp}
                      Living room: 
                              Temperature: {temp_living_room} deg.C
                              
                      Heater:
                              Inlet temperature:     {temp_heater_inlet} deg.C
                              Outlet temperature:    {temp_heater_outlet} deg. C

                      Well discharged volume: {well_discharge} l
                    """)

    def retrieve_latest_entries_from_ts(self):
        """Retrieve latest records from ThingSpeak channel and update records in local DB"""
        result = self.get_ts_data(channel_id=self.GREENHOUSE_TS_CHANNEL_ID, read_api_key=self.GREENHOUSE_TS_READ_KEY)
        for i in result:
            self.add_db_entry_greenhouse(i)
        self.connection.commit()

        if self.verbose:
            print(f"{len(result)} greenhouse weather station records received.")

        result = self.get_ts_data(channel_id=self.DOOM_TS_CHANNEL_ID, read_api_key=self.DOOM_TS_READ_KEY)
        for i in result:
            self.add_db_entry_doom(i)
        self.connection.commit()

        if self.verbose:
            print(f"{len(result)} home sensors records received.")

    def get_all_data_greenhouse(self):
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
