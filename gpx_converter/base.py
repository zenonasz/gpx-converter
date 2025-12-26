"""Top-level package for gpx_converter."""

import gpxpy
import pandas as pd
import numpy as np
import glob
import os

from xml.etree import ElementTree

try:
    # Load LXML or fallback to cET or ET
    import lxml.etree as mod_etree  # type: ignore
except:
    try:
        import xml.etree.cElementTree as mod_etree # type: ignore
    except:
        import xml.etree.ElementTree as mod_etree # type: ignore

GPXTPX_NS = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
# Custom namespace for WunderLINQ/bike fields.
# Can be any stable URI-like string; keep it stable once you start generating files.
WLINQ_NS = "https://wunderlinq.local/ns/1"


class Converter(object):
    """main class converter that holds all conversion methods"""

    def __init__(self, input_file=None):

        if not input_file:
            raise Exception("You need to provide an input file!")
        else:
            input_file_abs_path = os.path.abspath(input_file)
            input_file_exists = os.path.exists(input_file_abs_path)

            if not input_file_exists:
                raise Exception(f"The file {input_file} does not exist.")

            self.input_file = input_file_abs_path
            self.input_extension = os.path.splitext(input_file)[1].lower()
            # print(self.extension)


    def _gpx_to_dict(self, lats_colname="latitude", longs_colname="longitude", times_colname="time", alts_colname="altitude", sats_colname="satellites", export_extensions=True):
        longs, lats, times, alts, sats, ext = [], [], [], [], [], []
        ext_tags=[]

        with open(self.input_file, 'r') as gpxfile:
            gpx = gpxpy.parse(gpxfile)
            items = dir(gpx.tracks[0].segments[0].points[0].__class__)
            items = [item for item in items if not item.startswith('__') and not callable(getattr(gpx.tracks[0].segments[0].points[0], item)) and type(item)!=list]
            items_delete = ['extensions','gpx_10_fields','gpx_11_fields','time','longitude','latitude','elevation']

            # Keep order of items and delete unecessary items
            for item in items.copy():
                if item in items_delete:
                    items.remove(item)

            items = ['time','longitude','latitude','elevation']+items


            for item in items:
                print(type(getattr(gpx.tracks[0].segments[0].points[0],item)))
            print(items)
            gpx_data = dict((item, []) for item in items)
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        for item in items:
                            gpx_data[item] += [getattr(point, item)]
                        if export_extensions == True:
                            for extension in point.extensions:
                                ext_tags+=[extension.tag]


            #gpx_data = {times_colname: times, lats_colname: lats, longs_colname: longs, alts_colname: alts, sats_colname: sats}
            if export_extensions == True:
                ext_tags=set(ext_tags)
                extensions=dict((ext_tag, []) for ext_tag in ext_tags)
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            for ext_tag in ext_tags:
                                extensions[ext_tag]+=[None]
                            for extension in point.extensions:
                                extensions[extension.tag][-1]=extension.text
                gpx_data = {**gpx_data, **extensions}


        gpx_data['altitude'] = gpx_data['elevation']
        del gpx_data['elevation']
        for column in gpx_data.copy().keys():
            if not any(gpx_data[column]):
                del gpx_data[column]

        return gpx_data

    def gpx_to_dictionary(self, latitude_key="latitude", longitude_key="longitude", time_key="time", altitude_key="altitude", satellites_key="satellites",export_extensions=True):
        return self._gpx_to_dict(lats_colname=latitude_key, longs_colname=longitude_key, times_colname=time_key, alts_colname=altitude_key, sats_colname=satellites_key, export_extensions=export_extensions)

    def gpx_to_dataframe(self, lats_colname="latitude", longs_colname="longitude", times_colname="time", alts_colname="altitude", sats_colname="satellites",export_extensions=True):
        """
        convert gpx file to a pandas dataframe
        lats_colname: name of the latitudes column
        longs_colname: name of the longitudes column
        times_colname: name of the times column
        alts_colname: name of the altitude column
        sats_colname: name of the satellites column
        """
        if self.input_extension != ".gpx":
            raise TypeError(f"input file must be a GPX file")

        if not lats_colname or not longs_colname:
            raise TypeError("you must provide the column names of the longitude and latitude")

        df = pd.DataFrame.from_dict(self._gpx_to_dict(lats_colname=lats_colname,
                                                      longs_colname=longs_colname,
                                                      times_colname=times_colname,
                                                      alts_colname=alts_colname,
                                                      sats_colname=sats_colname,
                                                      export_extensions=export_extensions))
        return df

    def gpx_to_numpy_array(self,export_extensions=True):
        df = self.gpx_to_dataframe(export_extensions=export_extensions)
        return df.to_numpy()

    def gpx_to_csv(self, lats_colname="latitude", longs_colname="longitude", times_colname="time", alts_colname="altitude", sats_colname="satellites", output_file=None, export_extensions=True):
        """
        convert a gpx file to a csv
        lats_colname: name of the latitudes column
        longs_colname: name of the longitudes column
        times_colname: name of the times column
        alts_colname: name of the altitude column
        sats_colname: name of the satellites column
        output_file: output file where the csv file will be saved
        """
        if self.input_extension != ".gpx":
            raise TypeError(f"input file must be a GPX file")

        if not output_file:
            raise Exception("you need to provide an output file!")

        output_extension = os.path.splitext(output_file)[1]
        if output_extension != ".csv":
            raise TypeError(f"output file must be a csv file")

        df = self.gpx_to_dataframe(lats_colname=lats_colname,
                                   longs_colname=longs_colname,
                                   times_colname=times_colname,
                                   alts_colname=alts_colname,
                                   sats_colname=sats_colname)

        df.to_csv(output_file, index=False)
        return True

    def gpx_to_excel(self, lats_colname="latitude", longs_colname="longitude", times_colname="time", alts_colname="altitude", sats_colname="satellites", output_file=None, export_extensions=True):
        """
        convert a gpx file to a excel
        lats_colname: name of the latitudes column
        longs_colname: name of the longitudes column
        times_colname: name of the times column
        alts_colname: name of the altitude column
        sats_colname: name of the satellites column
        output_file: output file where the csv file will be saved
        """
        if self.input_extension != ".gpx":
            raise TypeError(f"input file must be a GPX file")

        if not output_file:
            raise Exception("you need to provide an output file!")

        output_extension = os.path.splitext(output_file)[1]
        if output_extension != ".xlsx":
            raise TypeError(f"output file must be a excel file (xlsx extension)")

        df = self.gpx_to_dataframe(lats_colname=lats_colname,
                                   longs_colname=longs_colname,
                                   times_colname=times_colname,
                                   alts_colname=alts_colname,
                                   sats_colname=sats_colname,
                                   export_extensions=export_extensions)
        if times_colname:
            df[times_colname] = df[times_colname].dt.tz_localize(None)
        df.to_excel(output_file, index=False)
        return True

    def gpx_to_json(self, lats_keyname="latitude", longs_keyname="longitude", times_keyname="time", alts_keyname="altitude", sats_keyname="satellites" ,output_file=None, export_extensions=True):
        """
        convert a gpx file to json
        lats_keyname: name of the key which will hold all latitude values
        longs_keyname: name of the key which will hold all longitude values
        times_keyname: name of the key which will hold all time values
        alts_keyname: name of the key which will hold all the altitude values
        sats_keyname: name of the key which will hold all the satellites values
        output_file: output file where the csv file will be saved
        """
        if self.input_extension != ".gpx":
            raise TypeError(f"input file must be a GPX file")

        if not output_file:
            raise Exception("you need to provide an output file!")

        output_extension = os.path.splitext(output_file)[1]
        if output_extension != ".json":
            raise TypeError(f"output file must be a json file ")

        df = self.gpx_to_dataframe(lats_colname=lats_keyname,
                                   longs_colname=longs_keyname,
                                   times_colname=times_keyname,
                                   alts_colname=alts_keyname,
                                   sats_colname=sats_keyname,
                                   export_extensions=export_extensions)


        df.to_json(output_file,date_format='iso')

        return True

    @staticmethod
    def dataframe_to_gpx(input_df, lats_colname='latitude', longs_colname='longitude',
                                                            times_colname=None,
                                                            alts_colname=None,
                                                            speed_colname=None,
                                                            symbol_colname=None,
                                                            comment_colname=None,
                                                            name_colname=None,
                                                            horizontal_dilution_colname=None,
                                                            vertical_dilution_colname=None,
                                                            position_dilution_colname=None,
                                                            gps_speed_colname=None,
                                                            gear_colname=None,
                                                            engine_temp_colname=None,
                                                            ambient_temp_colname=None,
                                                            front_tire_pr_colname=None,
                                                            rear_tire_pr_colname=None,
                                                            odo_colname=None,
                                                            bt_volt_colname=None,
                                                            throttle_colname=None,
                                                            front_brakes_colname=None,
                                                            rear_brakes_colname=None,
                                                            shifts_colname=None,
                                                            vin_colname=None,
                                                            ambient_light_colname=None,
                                                            trip1_colname=None,
                                                            trip2_colname=None,
                                                            trip_auto_colname=None,
                                                            avg_speed_colname=None,
                                                            crnt_consumption_colname=None,
                                                            fuel1_economy_colname=None,
                                                            fuel2_economy_colname=None,
                                                            fuel_range_colname=None,
                                                            lean_angle_mobile_colname=None,
                                                            g_force_colname=None,
                                                            bearing_colname=None,
                                                            barometer_kpa_colname=None,
                                                            rpm_colname=None,
                                                            lean_angle_colname=None,
                                                            rear_wheel_speed_colname=None,
                                                            device_batt_colname=None,
                                                             # NEW: optional explicit time parsing
                                                            time_format=None,
                                                            time_utc=False,
                                                            output_file=None):
        """
        convert pandas dataframe to gpx
        input_df: pandas dataframe
        lats_colname: name of the latitudes column
        longs_colname: name of the longitudes column
        times_colname: name of the time column
        alts_colname: name of the altitudes column
        sats_colname: name of the satellites column
        gps_speed_colname=None,
        gear_colname=None,
        engine_temp_colname=None,
        ambient_temp_colname=None,
        front_tire_pr_colname=None,
        rear_tire_pr_colname=None,
        odo_colname=None,
        bt_volt_colname=None,
        throttle_colname=None,
        front_brakes_colname=None,
        rear_brakes_colname=None,
        shifts_colname=None,
        vin_colname=None,
        ambient_light_colname=None,
        trip1_colname=None,
        trip2_colname=None,
        trip_auto_colname=None,
        avg_speed_colname=None,
        crnt_consumption_colname=None,
        fuel1_economy_colname=None,
        fuel2_economy_colname=None,
        fuel_range_colname=None,
        lean_angle_mobile_colname=None,
        g_force_colname=None,
        barometer_kpa_colname=None,
        rpm_colname=None,
        lean_angle_colname=None,
        rear_wheel_speed_colname=None,
        device_batt_colname=None,
        output_file: path of the output file
        """
        if not output_file:
            raise Exception("you need to provide an output file!")

        output_extension = os.path.splitext(output_file)[1]
        if output_extension != ".gpx":
            raise TypeError(f"output file must be a gpx file")

        import gpxpy.gpx
        gpx = gpxpy.gpx.GPX()

        # Register custom namespace for our fields
        # gpxpy will emit this in root element.
        gpx.nsmap["wlinq"] = WLINQ_NS

        # Create first track in our GPX:(and half of export)
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)



        # Prepare time parsing once (vectorized)
        if times_colname and times_colname in input_df.columns:
            if time_format:
                input_df[times_colname] = pd.to_datetime(
                    input_df[times_colname], format=time_format, errors="coerce", utc=time_utc
                )
            else:
                input_df[times_colname] = pd.to_datetime(
                    input_df[times_colname], errors="coerce", utc=time_utc
                )

        def _get(df, idx, col):
            if not col:
                return None
            if col not in df.columns:
                return None
            v = df.at[idx, col]
            if v is None:
                return None
            if isinstance(v, float) and np.isnan(v):
                return None
            return v

        def _add_ext(point, tag, value):
            if value is None:
                return
            el = ElementTree.Element(f"{{{WLINQ_NS}}}{tag}")
            el.text = str(value)
            point.extensions.append(el)


        # Create points
        for idx in input_df.index:
            lat = _get(input_df, idx, lats_colname)
            lon = _get(input_df, idx, longs_colname)
            if lat is None or lon is None:
                # Skip invalid points
                continue

            t = _get(input_df, idx, times_colname)
            if isinstance(t, pd.Timestamp):
                time_val = t.to_pydatetime()
            else:
                time_val = None

            ele = _get(input_df, idx, alts_colname)

            p = gpxpy.gpx.GPXTrackPoint(
                lat,
                lon,
                time=time_val,
                elevation=ele,
                # Keep these as you had them (even if not all tools use them)
                speed=_get(input_df, idx, speed_colname),
                symbol=_get(input_df, idx, symbol_colname),
                comment=_get(input_df, idx, comment_colname),
                name=_get(input_df, idx, name_colname),
                horizontal_dilution=_get(input_df, idx, horizontal_dilution_colname),
                vertical_dilution=_get(input_df, idx, vertical_dilution_colname),
                position_dilution=_get(input_df, idx, position_dilution_colname),
            )

            # Custom bike telemetry extensions (units encoded in tag names)
            _add_ext(p, "speed_kmh", _get(input_df, idx, speed_colname))
            _add_ext(p, "gps_speed_kmh", _get(input_df, idx, gps_speed_colname))
            # same value as GPX <ele>, but also exported in wlinq namespace
            _add_ext(p, "altitude_m", ele)
            _add_ext(p, "gear", _get(input_df, idx, gear_colname))
            _add_ext(p, "engine_temp_c", _get(input_df, idx, engine_temp_colname))
            _add_ext(p, "ambient_temp_c", _get(input_df, idx, ambient_temp_colname))
            _add_ext(p, "front_tire_pressure_bar", _get(input_df, idx, front_tire_pr_colname))
            _add_ext(p, "rear_tire_pressure_bar", _get(input_df, idx, rear_tire_pr_colname))
            _add_ext(p, "odometer_km", _get(input_df, idx, odo_colname))
            _add_ext(p, "battery_voltage_v", _get(input_df, idx, bt_volt_colname))
            _add_ext(p, "throttle_pct", _get(input_df, idx, throttle_colname))
            _add_ext(p, "front_brakes", _get(input_df, idx, front_brakes_colname))
            _add_ext(p, "rear_brakes", _get(input_df, idx, rear_brakes_colname))
            _add_ext(p, "shifts", _get(input_df, idx, shifts_colname))
            _add_ext(p, "vin", _get(input_df, idx, vin_colname))
            _add_ext(p, "ambient_light", _get(input_df, idx, ambient_light_colname))
            _add_ext(p, "trip1_km", _get(input_df, idx, trip1_colname))
            _add_ext(p, "trip2_km", _get(input_df, idx, trip2_colname))
            _add_ext(p, "trip_auto_km", _get(input_df, idx, trip_auto_colname))
            _add_ext(p, "avg_speed_kmh", _get(input_df, idx, avg_speed_colname))
            _add_ext(p, "current_consumption_l_per_100km", _get(input_df, idx, crnt_consumption_colname))
            _add_ext(p, "fuel_economy_1_l_per_100km", _get(input_df, idx, fuel1_economy_colname))
            _add_ext(p, "fuel_economy_2_l_per_100km", _get(input_df, idx, fuel2_economy_colname))
            _add_ext(p, "fuel_range_km", _get(input_df, idx, fuel_range_colname))
            _add_ext(p, "lean_angle_mobile_deg", _get(input_df, idx, lean_angle_mobile_colname))
            _add_ext(p, "g_force", _get(input_df, idx, g_force_colname))
            _add_ext(p, "bearing_deg", _get(input_df, idx, bearing_colname))
            _add_ext(p, "barometer_kpa", _get(input_df, idx, barometer_kpa_colname))
            _add_ext(p, "rpm", _get(input_df, idx, rpm_colname))
            _add_ext(p, "lean_angle_deg", _get(input_df, idx, lean_angle_colname))
            _add_ext(p, "rear_wheel_speed_kmh", _get(input_df, idx, rear_wheel_speed_colname))
            _add_ext(p, "device_battery_pct", _get(input_df, idx, device_batt_colname))

            gpx_segment.points.append(p)

        with open(output_file, 'w') as f:
            f.write(gpx.to_xml())
        return gpx.to_xml()

    def csv_to_gpx(self, lats_colname='latitude', longs_colname='longitude',
                                                times_colname=None,
                                                alts_colname=None,
                                                speed_colname=None,
                                                symbol_colname=None,
                                                comment_colname=None,
                                                name_colname=None,
                                                horizontal_dilution_colname=None,
                                                vertical_dilution_colname=None,
                                                position_dilution_colname=None,
                                                gps_speed_colname=None,
                                                gear_colname=None,
                                                engine_temp_colname=None,
                                                ambient_temp_colname=None,
                                                front_tire_pr_colname=None,
                                                rear_tire_pr_colname=None,
                                                odo_colname=None,
                                                bt_volt_colname=None,
                                                throttle_colname=None,
                                                front_brakes_colname=None,
                                                rear_brakes_colname=None,
                                                shifts_colname=None,
                                                vin_colname=None,
                                                ambient_light_colname=None,
                                                trip1_colname=None,
                                                trip2_colname=None,
                                                trip_auto_colname=None,
                                                avg_speed_colname=None,
                                                crnt_consumption_colname=None,
                                                fuel1_economy_colname=None,
                                                fuel2_economy_colname=None,
                                                fuel_range_colname=None,
                                                lean_angle_mobile_colname=None,
                                                g_force_colname=None,
                                                bearing_colname=None,
                                                barometer_kpa_colname=None,
                                                rpm_colname=None,
                                                lean_angle_colname=None,
                                                rear_wheel_speed_colname=None,
                                                device_batt_colname=None,
                                                # NEW: optional explicit time parsing
                                                time_format=None,
                                                time_utc=False,
                                                output_file=None):
        """
        convert csv file to gpx
        lats_colname: name of the latitudes column
        longs_colname: name of the longitudes column
        times_colname: name of the time column
        alts_colname: name of the altitudes column
        sats_colname: name of the satellites column
        output_file: path of the output file
        gps_speed_colname=None,
        gear_colname=None,
        engine_temp_colname=None,
        ambient_temp_colname=None,
        front_tire_pr_colname=None,
        rear_tire_pr_colname=None,
        odo_colname=None,
        bt_volt_colname=None,
        throttle_colname=None,
        front_brakes_colname=None,
        rear_brakes_colname=None,
        shifts_colname=None,
        vin_colname=None,
        ambient_light_colname=None,
        trip1_colname=None,
        trip2_colname=None,
        trip_auto_colname=None,
        avg_speed_colname=None,
        crnt_consumption_colname=None,
        fuel1_economy_colname=None,
        fuel2_economy_colname=None,
        fuel_range_colname=None,
        lean_angle_mobile_colname=None,
        g_force_colname=None,
        bearing_colname=None,
        barometer_kpa_colname=None,
        rpm_colname=None,
        lean_angle_colname=None,
        rear_wheel_speed_colname=None,
        device_batt_colname=None,
        """
        if not output_file:
            raise Exception("you need to provide an output file!")

        if self.input_extension != ".csv":
            raise TypeError(f"input file must be a CSV file")

        df = pd.read_csv(self.input_file)
        self.dataframe_to_gpx(input_df=df,
                              lats_colname=lats_colname,
                              longs_colname=longs_colname,
                              times_colname=times_colname,
                              alts_colname=alts_colname,
                              speed_colname=speed_colname,
                              symbol_colname=symbol_colname,
                              comment_colname=comment_colname,
                              name_colname=name_colname,
                              horizontal_dilution_colname=horizontal_dilution_colname,
                              vertical_dilution_colname=vertical_dilution_colname,
                              position_dilution_colname=position_dilution_colname,
                              gps_speed_colname=gps_speed_colname,
                              gear_colname=gear_colname,
                              engine_temp_colname=engine_temp_colname,
                              ambient_temp_colname=ambient_temp_colname,
                              front_tire_pr_colname=front_tire_pr_colname,
                              rear_tire_pr_colname=rear_tire_pr_colname,
                              odo_colname=odo_colname,
                              bt_volt_colname=bt_volt_colname,
                              throttle_colname=throttle_colname,
                              front_brakes_colname=front_brakes_colname,
                              rear_brakes_colname=rear_brakes_colname,
                              shifts_colname=shifts_colname,
                              vin_colname=vin_colname,
                              ambient_light_colname=ambient_light_colname,
                              trip1_colname=trip1_colname,
                              trip2_colname=trip2_colname,
                              trip_auto_colname=trip_auto_colname,
                              avg_speed_colname=avg_speed_colname,
                              crnt_consumption_colname=crnt_consumption_colname,
                              fuel1_economy_colname=fuel1_economy_colname,
                              fuel2_economy_colname=fuel2_economy_colname,
                              fuel_range_colname=fuel_range_colname,
                              lean_angle_mobile_colname=lean_angle_mobile_colname,
                              g_force_colname=g_force_colname,
                              bearing_colname=bearing_colname,
                              barometer_kpa_colname=barometer_kpa_colname,
                              rpm_colname=rpm_colname,
                              lean_angle_colname=lean_angle_colname,
                              rear_wheel_speed_colname=rear_wheel_speed_colname,
                              device_batt_colname=device_batt_colname,
                              output_file=output_file)
        return True

    def excel_to_gpx(self, lats_colname='latitude', longs_colname='longitude',
                                                    times_colname=None,
                                                    alts_colname=None,
                                                    sats_colname=None,
                                                    speed_colname=None,
                                                    symbol_colname=None,
                                                    comment_colname=None,
                                                    name_colname=None,
                                                    horizontal_dilution_colname=None,
                                                    vertical_dilution_colname=None,
                                                    position_dilution_colname=None,
                                                    output_file=None):
        """
        convert csv file to gpx
        lats_colname: name of the latitudes column
        longs_colname: name of the longitudes column
        times_colname: name of the time column
        alts_colname: name of the altitudes column
        sats_colname: name of the satellites column
        output_file: path of the output file
        """
        if not output_file:
            raise Exception("you need to provide an output file!")

        if self.input_extension != ".xlsx":
            raise TypeError(f"input file must be a Excel file")

        df = pd.read_excel(self.input_file)
        self.dataframe_to_gpx(input_df=df,
                              lats_colname=lats_colname,
                              longs_colname=longs_colname,
                              times_colname=times_colname,
                              alts_colname=alts_colname,
                              sats_colname=sats_colname,
                              speed_colname=speed_colname,
                              symbol_colname=symbol_colname,
                              comment_colname=comment_colname,
                              name_colname=name_colname,
                              horizontal_dilution_colname=horizontal_dilution_colname,
                              vertical_dilution_colname=vertical_dilution_colname,
                              position_dilution_colname=position_dilution_colname,
                              output_file=output_file)
        return True

    def json_to_gpx(self, lats_colname='latitude', longs_colname='longitude',
                                                    times_colname=None,
                                                    alts_colname=None,
                                                    speed_colname=None,
                                                    symbol_colname=None,
                                                    comment_colname=None,
                                                    name_colname=None,
                                                    horizontal_dilution_colname=None,
                                                    vertical_dilution_colname=None,
                                                    position_dilution_colname=None,
                                                    output_file=None):
        """
        convert csv file to gpx
        lats_colname: name of the latitudes column
        longs_colname: name of the longitudes column
        times_colname: name of the time column
        alts_colname: name of the altitudes column
        output_file: path of the output file
        """
        if not output_file:
            raise Exception("you need to provide an output file!")

        if self.input_extension != ".json":
            raise TypeError(f"input file must be a json file")
        df = pd.read_json(self.input_file)
        self.dataframe_to_gpx(input_df=df,
                              lats_colname=lats_colname,
                              longs_colname=longs_colname,
                              times_colname=times_colname,
                              alts_colname=alts_colname,
                              speed_colname=speed_colname,
                              symbol_colname=symbol_colname,
                              comment_colname=comment_colname,
                              name_colname=name_colname,
                              horizontal_dilution_colname=horizontal_dilution_colname,
                              vertical_dilution_colname=vertical_dilution_colname,
                              position_dilution_colname=position_dilution_colname,
                              output_file=output_file)
        return True

    @staticmethod
    def convert_multi_csv_to_gpx(dirpath, lats_colname='latitude', longs_colname='longitude',
                                                                    times_colname=None,
                                                                    alts_colname=None,
                                                                    speed_colname=None,
                                                                    symbol_colname=None,
                                                                    comment_colname=None,
                                                                    name_colname=None,
                                                                    horizontal_dilution_colname=None,
                                                                    vertical_dilution_colname=None,
                                                                    position_dilution_colname=None,
                                                                    output_file=None):
        """
        convert multiple csv file from directory to gpx
        dirpath: directory path where the csv files are
        lats_colname: name of the latitudes columns
        longs_colname: name of the longitudes columns
        times_colname: name of the time columns
        alts_colname: name of the altitudes columns
        """
        all_files = glob.glob(dirpath + '/*.csv')
        for f in all_files:
            gpx_path = f.replace('csv', 'gpx')
            df = pd.read_csv(f)
            Converter.dataframe_to_gpx(input_df=df,
                                       lats_colname=lats_colname,
                                       longs_colname=longs_colname,
                                       times_colname=times_colname,
                                       alts_colname=alts_colname,
                                       speed_colname=speed_colname,
                                       symbol_colname=symbol_colname,
                                       comment_colname=comment_colname,
                                       name_colname=name_colname,
                                       horizontal_dilution_colname=horizontal_dilution_colname,
                                       vertical_dilution_colname=vertical_dilution_colname,
                                       position_dilution_colname=position_dilution_colname,
                                       output_file=gpx_path)

    @staticmethod
    def spline_interpolation(cv, n=100, degree=3, periodic=False):
        """ Calculate n samples on a bspline

            cv :      Array of control vertices
            n  :      Number of samples to return
            degree:   Curve degree
            periodic: True - Curve is closed
                      False - Curve is open
        """

        # If periodic, extend the point array by count+degree+1
        import scipy.interpolate as si

        cv = np.asarray(cv)
        count = len(cv)

        if periodic:
            factor, fraction = divmod(count + degree + 1, count)
            cv = np.concatenate((cv,) * factor + (cv[:fraction],))
            count = len(cv)
            degree = np.clip(degree, 1, degree)

        # If opened, prevent degree from exceeding count-1
        else:
            degree = np.clip(degree, 1, count - 1)

        # Calculate knot vector
        kv = None
        if periodic:
            kv = np.arange(0 - degree, count + degree + degree - 1, dtype='int')
        else:
            kv = np.concatenate(([0] * degree, np.arange(count - degree + 1), [count - degree] * degree))

        # Calculate query range
        u = np.linspace(periodic, (count - degree), n)

        # Calculate result
        mat = si.splev(u, (kv, cv.T, degree))
        return np.array(mat).T

    def __repr__(self):
        return "class converter that contains all conversion methods."
