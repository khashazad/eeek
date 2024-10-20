import os 
import shutil
import random
from lib.image_collections import COLLECTIONS
import ee
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from enum import Enum
import sys

ee.Initialize(opt_url=ee.data.HIGH_VOLUME_API_BASE_URL)

class Stability(Enum):
    STABLE = "stable"
    UNSTABLE = "unstable"

MODE = Stability(sys.argv[1]) if len(sys.argv) > 1 else Stability.STABLE

NUMBER_OF_POINTS = 20
POLYGON_COORDINATES = [(-126.04, 49.59), (-126.04, 40.76), (-118.93, 40.76), (-118.93, 49.59)]

MINIMUM_NUMBER_OF_MEASUREMENTS = 15
if MODE == Stability.UNSTABLE:
    MEAN_SWIR_THRESHOLD = 0.15
else:
    MEAN_SWIR_THRESHOLD = 0.01

image_collection = COLLECTIONS["L8_L9_2022_2023"]

script_directory = os.path.dirname(os.path.abspath(__file__))

if MODE == Stability.UNSTABLE:
    measurement_directory = os.path.join(script_directory,"points", "new", "unstable")
else:
    measurement_directory = os.path.join(script_directory,"points", "new", "stable")

# if os.path.exists(measurement_directory):
#     shutil.rmtree(measurement_directory)
# os.makedirs(measurement_directory)


def generate_random_points(polygon, num_points, scale=10):
    min_lat = min(polygon, key=lambda x: x[1])[1]
    max_lat = max(polygon, key=lambda x: x[1])[1]
    min_lon = min(polygon, key=lambda x: x[0])[0]
    max_lon = max(polygon, key=lambda x: x[0])[0]

    points = []
    for _ in range(num_points):
        lat = random.uniform(min_lat, max_lat)
        lon = random.uniform(min_lon, max_lon)
        
        # lat += random.uniform(-scale * 0.00001, scale * 0.00001)
        # lon += random.uniform(-scale * 0.00001, scale * 0.00001)
        points.append((lon, lat))
    
    return points

valid_points_counter = 0

while valid_points_counter < NUMBER_OF_POINTS:
    geometries = ee.FeatureCollection(ee.List(generate_random_points(POLYGON_COORDINATES, 100, 10)).map(lambda coordinate: ee.Feature(ee.Geometry.Point(coordinate))))

    def process_image(image):
        img = image

        def sample_and_copy(feature):
            return feature.copyProperties(img, img.propertyNames().remove(ee.String("nominalDate")))

        sampled = img.sampleRegions(
            collection=geometries,
            scale=10,
            geometries=True
        ).map(sample_and_copy)

        return sampled

    measurements = ee.FeatureCollection(
        image_collection.map(process_image).flatten()
    )

    features = measurements.getInfo()["features"]

    measurements = pd.DataFrame([
        {
            "longitude": feature["geometry"]["coordinates"][0],
            "latitude": feature["geometry"]["coordinates"][1],
            "date": feature["properties"]["millis"],
            "swir": feature["properties"]["swir"]
        }
        for feature in features if "swir" in feature["properties"]
    ])

    grouped_measurements = measurements.groupby(['longitude', 'latitude'])

    for point, data in grouped_measurements:

        if valid_points_counter > NUMBER_OF_POINTS:
            break

        if (len(data) < MINIMUM_NUMBER_OF_MEASUREMENTS):
            continue

        data['year'] = pd.to_datetime(data['date'], unit='ms').dt.year
        mean_swir_2022 = data[data['year'] == 2022]['swir'].mean()
        mean_swir_2023 = data[data['year'] == 2023]['swir'].mean()

        if MODE == Stability.UNSTABLE:
            if abs(mean_swir_2022 - mean_swir_2023) < MEAN_SWIR_THRESHOLD:
                continue
        else:
            if abs(mean_swir_2022 - mean_swir_2023) > MEAN_SWIR_THRESHOLD:
                continue
        
        valid_points_counter += 1

        fig, axs = plt.subplots(1, 2, figsize=(24, 8))  
        data['date'] = pd.to_datetime(data['date'], unit='ms')

        axs[0].scatter(data['date'], data['swir'], label='SWIR', color='red')
        axs[0].xaxis.set_major_locator(mdates.AutoDateLocator())
        axs[0].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        axs[0].tick_params(axis='x', labelsize=8)
        axs[0].set_title(f"{data['longitude'].iloc[0]},{data['latitude'].iloc[0]}")
        axs[0].legend()

        axs[1].scatter(data['date'], data['swir'], label='SWIR', color='blue')
        axs[1].xaxis.set_major_locator(mdates.AutoDateLocator())
        axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        axs[1].tick_params(axis='x', labelsize=8)
        axs[1].set_ylim(0, 0.5) 
        axs[1].set_title(f"{data['longitude'].iloc[0]},{data['latitude'].iloc[0]}")
        axs[1].legend()


        fig.savefig(f"{measurement_directory}/{point}.png")
