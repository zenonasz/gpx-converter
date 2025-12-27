WunderLINQ integration and custom extensions
===========================================

This fork of ``gpx_converter`` adds first-class support for WunderLINQ TripLog CSV files and arbitrary GPX extension namespaces.

1. **Convert WunderLINQ CSV to GPX**

   The script ``run/wlinq_csv_to_gpx.py`` reads the WunderLINQ CSV format, validates required columns, and writes a GPX file with custom extension tags prefixed by the ``wlinq`` namespace. Tags include speed, RPM, gear, tyre pressures, temperatures, trip counters and more. Units are encoded in the tag names (for example ``_kmh``, ``_deg``, ``_bar``).

2. **Custom GPX namespace registration**

   When exporting a GPX from a DataFrame (using ``dataframe_to_gpx``), the ``wlinq`` namespace is registered and all extension values are written under this namespace. This makes the output GPX self-describing and avoids collisions with existing GPX tags.

3. **Generic extension support**

   If you’re using a different device, you can emit your own ``<vendor:tag>`` elements in the CSV headers and extend the ``WLINQ_COLS`` mapping and ``_add_ext`` helper to write them into the GPX. Unknown namespaces are preserved in the extension dictionary, so adding support for new devices requires minimal code changes.

4. **Part of the overlay workflow**

   The primary motivation for these changes is to feed the generated GPX files into our fork of the `gopro-dashboard-overlay <https://github.com/zenonasz/gopro-dashboard-overlay>`_ project to render bike telemetry on top of GoPro videos.

   The workflow is as follows:

   1. Export your WunderLINQ TripLog as a CSV.
   2. Run ``run/wlinq_csv_to_gpx.py`` to convert it to a GPX with custom ``<wlinq:*>`` extension tags.
   3. Pass the resulting GPX file to ``gopro-dashboard.py`` (from the GoPro overlay project) as the ``--gpx`` argument.

   See the gopro-dashboard-overlay README for more details on generating videos with custom layouts and how the GPX extension data is visualized.

Local development with uv
-------------------------

To set up a local development environment:

.. code-block:: bash

   git clone git@github.com:zenonasz/gpx-converter.git
   cd gpx-converter
   uv venv --python 3.8
   uv pip install -e .

Example: Convert WunderLINQ CSV to GPX
-------------------------------------

Using uv (recommended):

.. code-block:: bash

   uv run python run/wlinq_csv_to_gpx.py \
     <path_to_csv_file>/<wlinq_csv_file.csv> \
     --output-gpx-path <output_gpx_path>/<output_gpx_file.gpx>

Optional flags:

.. code-block:: bash

   --time-format "%Y%m%d-%H:%M:%S.%f"   # Custom timestamp format
   --time-utc                           # Treat timestamps as UTC
   --local-tz Asia/Nicosia              # Timezone of CSV timestamps

Timestamp and timezone handling
-------------------------------

WunderLINQ CSV timestamps are recorded in local device time without timezone
metadata (for example: ``20250615-18:24:20.306``).

To correctly align WunderLINQ telemetry with GoPro GPS data, timestamps should
be converted to UTC before generating the GPX file.

The conversion script supports this via the following options:

- ``--time-format``
  Specifies the input timestamp format used in the CSV.

- ``--local-tz``
  Specifies the IANA timezone in which the CSV timestamps should be interpreted
  (for example ``Asia/Nicosia``).

- ``--time-utc``
  Converts timestamps from the specified local timezone to UTC and writes
  UTC-normalised timestamps into the GPX file.

Example:

.. code-block:: bash

   uv run python run/wlinq_csv_to_gpx.py trip.csv \
     --time-format "%Y%m%d-%H:%M:%S.%f" \
     --local-tz Asia/Nicosia \
     --time-utc \
     --output-gpx-path trip.gpx

When ``--time-utc`` is enabled, all timestamps written to the GPX are UTC and
safe to merge with GoPro GPS tracks or other time-aware data sources.

=============
gpx-converter
=============

.. image:: https://github.com/nidhaloff/gpx-converter/blob/master/assets/icon.png
    :width: 100
    :align: center
    :alt: gpx-converter-icon

|



.. image:: https://img.shields.io/pypi/v/gpx-converter.svg
        :target: https://pypi.python.org/pypi/gpx-converter

.. image:: https://img.shields.io/travis/nidhaloff/gpx-converter.svg
        :target: https://travis-ci.com/nidhaloff/gpx-converter

.. image:: https://readthedocs.org/projects/gpx-converter/badge/?version=latest
        :target: https://gpx-converter.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status
.. image:: https://img.shields.io/pypi/wheel/gpx-converter
        :alt: PyPI - Wheel
        :target: https://pypi.python.org/pypi/gpx-converter

.. image:: https://pepy.tech/badge/gpx-converter
        :target: https://pepy.tech/project/gpx-converter


.. image:: https://img.shields.io/pypi/l/gpx-converter
        :alt: PyPI - License
        :target: https://pypi.python.org/pypi/gpx-converter


.. image:: https://img.shields.io/twitter/url?url=https%3A%2F%2Ftwitter.com%2FNidhalBaccouri
        :alt: Twitter URL
        :target: https://twitter.com/NidhalBaccouri



GPX manipulation for humans
----------------------------

Python package for manipulating gpx files and easily convert gpx to other different formats.

* Free software: MIT license
* Documentation: https://gpx-converter.readthedocs.io.

When & Why
----------
- You need to convert GPX to other formats
- You need to convert other formats like csv to GPX
- You want to interpolate the GPX coordinates
- High level of abstraction
- Stable API
- easy to use and to extend

Motivation
----------

I decided to create this project because I had gpx data that I needed to manipulate. I searched for a python
package for this but I did not find what I was looking for, therefore I created the gpx-converter package
to make gpx files manipulation very easy. Furthermore, the package contains methods for applying interpolation
on the gpx data. This feature was very helpful for me since I also needed to interpolate the gpx data and
convert it to csv.
Feel free to contribute or to give me feedback anytime :)

Features
--------

- Convert gpx files to other formats such as csv, numpy arrays, dataframes, excel and json
- Convert csv files to gpx
- Apply interpolation on the gpx data

Installation
------------

.. code-block:: console

    $ pip install -U gpx-converter


Quick Usage
-----------

.. code-block:: python

    from gpx_converter import Converter

**Just read the gpx to dictionary**

.. code-block:: python

    dic = Converter(input_file='your_input.gpx').gpx_to_dictionary(latitude_key='latitude', longitude_key='longitude')
    # now you have a dictionary and can access the longitudes and latitudes values from the keys
    latitudes = dic['latitude']
    longitudes = dic['longitude']

**Convert GPX to other formats**

- Convert from gpx to csv:

.. code-block:: python

    Converter(input_file='your_input.gpx').gpx_to_csv(output_file='your_output.csv')

- Convert from gpx to excel sheets:

.. code-block:: python

    Converter(input_file='your_input.gpx').gpx_to_excel(output_file='your_output.xlsx')

- Convert from gpx to json:

.. code-block:: python

    Converter(input_file='your_input.gpx').gpx_to_json(output_file='your_output.json)

- Convert gpx file to dataframe:

.. code-block:: python

    df = Converter(input_file='your_input.gpx').gpx_to_dataframe()

- Convert gpx file to numpy array:

.. code-block:: python

    np_array = Converter(input_file='your_input.gpx').gpx_to_numpy_array()


**Now convert other formats to GPX**

- csv to gpx

.. code-block:: python

    Converter(input_file='your_input.csv').csv_to_gpx(lats_colname='column_name_of_latitudes',
                                                     longs_colname='column_name_of_longitudes',
                                                     output_file='your_output.gpx')

- excel to gpx

.. code-block:: python

    Converter(input_file='your_input.xlsx').excel_to_gpx(lats_colname='column_name_of_latitudes',
                                                     longs_colname='column_name_of_longitudes',
                                                     output_file='your_output.gpx')

- dataframe to gpx (notice that the method is static)

.. code-block:: python

    Converter.dataframe_to_gpx(input_df=your_df,
                               lats_colname='column_name_of_latitudes',
                               longs_colname='column_name_of_longitudes',
                               output_file='your_output.gpx')

- json to gpx

.. code-block:: python

    Converter(input_file='your_input.json').json_to_gpx(input_df=your_df,
                                                       lats_colname='column_name_of_latitudes',
                                                       longs_colname='column_name_of_longitudes',
                                                       output_file='your_output.gpx')


- Automate the conversion of multiple csv file to gpx:

.. code-block:: python

    Converter.convert_multi_csv_to_gpx(dirpath='your_directory/')

- Apply spline interpolation on gpx file (you need to install scipy for this to work):

.. code-block:: python

    interpolated_coordinates = Converter.spline_interpolation(cv=your_array_of_control_vertices)

Usage from terminal
--------------------

Alternatively you can use the gpx_converter directly from terminal.
You just need to pass the function, input file and output file as arguments.

- function: the conversion method you want to use. For example "gpx_to_csv"
- input file: path to your input file
- output file: path to your output file

.. code-block:: console

    $ gpx_converter --function "gpx_to_csv" --input_file "home/your_input.gpx" --output_file "home/your_output.csv"

or maybe you prefer the short version

.. code-block:: console

    $ gpx_converter -func "gpx_to_csv" -in "home/your_input.gpx" -out "home/your_output.csv"

Links
-----
Check this article to know more about gpx files and how to use the gpx-converter package.
https://medium.com/p/57da00bd36fc/edit

Contributions
--------------
Contributions are always welcome. Make sure you check the guidlines first https://gpx-converter.readthedocs.io/en/latest/contributing.html
