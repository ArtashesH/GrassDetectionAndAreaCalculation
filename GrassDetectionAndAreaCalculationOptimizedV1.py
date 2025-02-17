import time

from shapely.geometry import Point
from pyproj import Transformer
from shapely.ops import transform
import simplekml
from argparse import ArgumentParser
import argparse
import os
from datetime import datetime

import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from ultralytics import YOLO
from shapely.geometry import Polygon
import requests
import numpy as np
import math
import csv
import cv2
import sys
from concurrent.futures import ThreadPoolExecutor




import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey1.json")
firebase_admin.initialize_app(cred)

# Get Firestore Client
db = firestore.client()



#Update percent of processing in firebase 

def update_firestore_document_percent(current_percent):
    # Reference the document to update (e.g., "users/{document_id}")
    doc_ref = db.collection("users").document("Mcai8aARVSHXVICky4mn")

    # Fields to update
    updated_data = {
        "percent": current_percent#,  # Update age
        #"status": "active"  # Add a new field or update existing one
    }

    # Update the document
    doc_ref.update(updated_data)

    print("Document updated successfully.")



#Update error type in firebase 

def update_firestore_document_error(current_error):
    # Reference the document to update (e.g., "users/{document_id}")
    doc_ref = db.collection("users").document("Mcai8aARVSHXVICky4mn")

    # Fields to update
    updated_data = {
        "error": current_error#,  # Update age
        #"status": "active"  # Add a new field or update existing one
    }

    # Update the document
    doc_ref.update(updated_data)

    print("Document updated successfully.")





def get_lat_long_google(address, api_key):
    # Base URL for the Google Maps Geocoding API
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    # Parameters for the request
    params = {
        "address": address,
        "key": api_key
    }

    # Send the request
    response = requests.get(url, params=params)

    # Parse the response
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            # Extract latitude and longitude
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            print("Geocoding error:", data['status'])
            update_firestore_document_error("Geocoding error")
    else:
        print("Request error:", response.status_code)
        update_firestore_document_error("Request error")

    
    return None, None





#Calculate Distance between two points with given lat long
def calculateDistanceBetweenTwoPoints(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance in meters between two latitude-longitude points.

    Returns:
        Distance in meters.
    """
    # Radius of Earth in meters
    R = 6371000

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    #This calculation is returning distance in meters
    return distance

# Function to load YOLO model. Model is for detecting and classification of grass areas. We have two classes - artificial , natural
def load_yolo_model(model_path):
    # Load YOLO model from the specified path
    model = YOLO(model_path)  # Adjust based on the YOLO library in use
    return model


#Write data about locations in csv. This function we are using to add generated lat/long points inside of circle with given radius
def data_in_csv(user_id, latitude, longitude):
    display_data = {
        'user_id': user_id,
        'latitude': latitude,
        'longitude': longitude

    }
    csv_file_name = 'circle_results.csv'
    csv_file_path = os.path.join(os.getcwd(), csv_file_name)

    with open(csv_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        if os.stat(csv_file_path).st_size == 0:
            writer.writerow(display_data.keys())
        writer.writerow(display_data.values())

    print(f"Data added to CSV successfully.")

#Write data about areas, address, distances   in result csv file. This function is used for final output csv file generation
def data_in_csvArea(address, minDistLat, minDistLong, minDist,  listOfAreas, minumumArea):
    if len(address) == 0:
        display_data = {
            'Contact Type (Lead, Customer, Other)' : '',
            'Contact First Name': '',
            'Contact Last Name': '',
            'Contact Email': '',
            'Country Code' : '',
            'Contact Phone': '',
            'Contact Status': 'New',
            'Contact Business Name': '',
            'Contact Title' : '',            
            'Contact Address': '',
            'Address2' : '',
            'City': '',
            'State': '',
            'Zip':  '',
            'Contact Latitude' : '',
            'Contact Longitude' : '',
            'Notes' :  '',
            'Date Contact was Created' : '',
            'User Email (RepCard user)' : ''
          ########  'Country':   adressComp[len(adressComp) - 1],
          #####  'Lat/Long': finalLatLong,
          ######  'Distance from input address (in miles)': minDist,
          #####  'Artificial grass (in sq ft)': listOfAreas,
           #### 'WholeArea': sumOfAreas

        }
        #Write datainto output csv file 
        csv_file_name = 'addressData.csv'
        csv_file_path = os.path.join(os.getcwd(), csv_file_name)

        with open(csv_file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            if os.stat(csv_file_path).st_size == 0:
                writer.writerow(display_data.keys())
            writer.writerow(display_data.values())
        return            
        
    sumOfAreas = 0
    finalLatLong = str(minDistLong) + ' ' + str(minDistLat)
    #Devide address to components , zip , state, city country , etc
    adressComp = address.split(',') 
    finalAddrComp = ''
    if len(adressComp) == 4:
        finalAddrComp = adressComp[len(adressComp) - 4]
    if len(adressComp) > 4:
        finalAddrComp = adressComp[len(adressComp) - 5] + ', '  + adressComp[len(adressComp) - 4]
    #if len(adressComp) >= 4:
    #    contactAddress = adressComp[0:len(adressComp) - 4]
    #    for v in range(len(contactAddress)):
    #        finalAddrComp = finalAddrComp + contactAddress[v]
    #        if v < len(contactAddress):
    #            finalAddrComp = finalAddrComp + ', '
    stateAndZipCode = adressComp[len(adressComp) - 2].split(' ')
   # print("INSIDE OF CSV!!!!!!!!!!!!!!!!!!!1 ")
    for i in range(len(listOfAreas)):
        sumOfAreas += listOfAreas[i]
    if sumOfAreas < float(minumumArea):
        return
    if len(adressComp) >= 4:
        display_data = {
            'Contact Type (Lead, Customer, Other)' : 'Lead',
            'Contact First Name': '',
            'Contact Last Name': '',
            'Contact Email': '',
            'Country Code' : '',
            'Contact Phone': '',
            'Contact Status': 'New',
            'Contact Business Name': '',
            'Contact Title' : '',            
            'Contact Address': finalAddrComp,#adressComp[len(adressComp) - 4],
            'Address2' : '',
            'City': adressComp[len(adressComp) - 3],
            'State': stateAndZipCode[1],
            'Zip':  stateAndZipCode[2],
            'Contact Latitude' : minDistLong,
            'Contact Longitude' : minDistLat,
            'Notes' :  sumOfAreas,
            'Date Contact was Created' : '',
            'User Email (RepCard user)' : ''
          ########  'Country':   adressComp[len(adressComp) - 1],
          #####  'Lat/Long': finalLatLong,
          ######  'Distance from input address (in miles)': minDist,
          #####  'Artificial grass (in sq ft)': listOfAreas,
           #### 'WholeArea': sumOfAreas

        }
        #Write datainto output csv file 
        csv_file_name = 'addressData.csv'
        csv_file_path = os.path.join(os.getcwd(), csv_file_name)

        with open(csv_file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            if os.stat(csv_file_path).st_size == 0:
                writer.writerow(display_data.keys())
            writer.writerow(display_data.values())

        print(f"Data added to CSV successfully.")

#With using google api, get satellite image for given location , with given size, zoom parameters
def get_satellite_image_with_resolution(lat, lon,api_key, zoom=20, size=(640, 640), scale=1):
    # Base URL for static map image
    base_url = "https://maps.googleapis.com/maps/api/staticmap?"
    params = {
        'center': f'{lat},{lon}',
        'zoom': zoom,
        'size': f'{size[0]}x{size[1]}',
        'scale': scale,
        'maptype': 'satellite',
        'key': api_key
    }

    # Fetch satellite image and measure latency
    start_time = time.time()
    response = requests.get(base_url, params=params)
    end_time = time.time()
    latency = end_time - start_time
    print(f"API request latency: {latency:.2f} seconds")

    if response.status_code == 200:
        img_arr = np.asarray(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

        # Calculate meters per pixel
        earth_circumference = 40075016.686  # in meters
        tile_size = 256  # Google's tile size in pixels
        meters_per_pixel = (earth_circumference * math.cos(math.radians(lat))) / (2 ** zoom * tile_size)
        # metersPerPx = 156543.03392 * math.cos(lat * np.pi/180) / 2 ** zoom
        # Return the image and the meters per pixel resolution
        return image, meters_per_pixel
    else:
        print("Error fetching satellite image")
        update_firestore_document_error("Error fetching satellite image")
        return None, None

#Order polygon points for area calculation
def order_polygon_points(coords):
    # Calculate the centroid
    cx = sum(x for x, y in coords) / len(coords)
    cy = sum(y for x, y in coords) / len(coords)

    # Sort points by angle from the centroid
    sorted_coords = sorted(coords, key=lambda point: math.atan2(point[1] - cy, point[0] - cx))

    # Return the ordered points as a Polygon
    polygon = Polygon(sorted_coords)
    return polygon

#Calcualte address from given lat long with geolocation api
def latlng_to_address(lat, lng, api_key):
    """Convert latitude and longitude to an address using Google Geocoding API."""
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{lat},{lng}", "key": api_key}
    response = requests.get(geocode_url, params=params).json()

    if response["status"] == "OK":
        # Return the formatted address from the response
        return response["results"][0]["formatted_address"]
    else:
        
        update_firestore_document_error("Geocoding API error: convertion from address to lat/lng")
        return -1
       # raise  Exception(f"Geocoding API error: {response['status']} - {response.get('error_message')}")



#Calculate lat long from given point and given meter transform
def calculate_new_coordinates(initial_lat, initial_lng, distance_x, distance_y):
    """
    Calculate new latitude and longitude after moving a specified distance in X and Y.

    Args:
        initial_lat (float): Initial latitude in decimal degrees.
        initial_lng (float): Initial longitude in decimal degrees.
        distance_x (float): Distance to move in the X direction (meters, longitude).
        distance_y (float): Distance to move in the Y direction (meters, latitude).

    Returns:
        tuple: New latitude and longitude in decimal degrees.
    """
    # Earth's radius in meters
    earth_radius = 6371000

    # Convert initial latitude to radians
    initial_lat_rad = math.radians(initial_lat)

    # Calculate the new latitude
    new_lat = initial_lat + (distance_y / earth_radius) * (180 / math.pi)

    # Calculate the new longitude
    new_lng = initial_lng + (distance_x / (earth_radius * math.cos(initial_lat_rad))) * (180 / math.pi)

    return new_lat, new_lng


# Function to perform building detection and area calculation
def detect_grass_and_calculate_area(image, model,meters_per_pixel=0.1):
    # Detect buildings using YOLO model
    results = model(image, conf=0.1)

    clist = results[0].boxes.cls

    areas = []
    centerOfPolygons  = []
    if len(results) == 0 or results[0].boxes is None:
        return image, areas
    # Assuming the result has polygons in format [x, y] for each vertex


    if results[0].masks is None:
        return image, areas, centerOfPolygons
    maske_buildings = results[0].masks.xy  # Polygons for detected buildings
    print("Current image detect ")
    indexOfMask = 0
    for maske_building in maske_buildings:
        # Format points for use with OpenCV and Shapely
        polygon_points = maske_building.astype(int).reshape((-1, 1, 2))
        #Filter from detected regions just artificial grass class
        ##if model.names[int(clist[indexOfMask])] != 'artifical':
        ###    continue
        if model.names[int(clist[indexOfMask])] != 'artifical': # or model.names[int(clist[indexOfMask])] == 'natural_grass':
            continue
        #else:
        cv2.polylines(image, [polygon_points], isClosed=True, color=(0, 255, 0), thickness=2)

        
        # Reformat polygon for Shapely and calculate area
        maske_building = [tuple(point) for point in maske_building.astype(int)]
        if len(maske_building) == 0:
            continue
        polygon = order_polygon_points(maske_building)
        centerOfPolygon = polygon.centroid
        area = (polygon.area * ((meters_per_pixel ) ** 2) ) * 10.7639 # Convert to square footage
        areas.append(area)
        centerOfPolygons.append(centerOfPolygon)

        # Draw on image found region and measured areas
        cv2.putText(image, f' {area:.2f}', (int(maske_building[0][0]), int(maske_building[0][1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        indexOfMask += 1
        cv2.circle(image,(int(centerOfPolygon.x), int(centerOfPolygon.y)),5,(255,0,0),-1)
   # cv2.imshow("Satellite", image)
   # cv2.waitKey(0)

    return image, areas, centerOfPolygons



#For given address  and radius, generate list of points, which are inside of the circle with given radius and given center point from address.
def generate_circle_points(center_lat, center_lng, radius, step=10):
    """
    Generate latitude and longitude points at regular intervals within a circle.

    Args:
        center_lat (float): Latitude of the circle center.
        center_lng (float): Longitude of the circle center.
        radius (float): Radius of the circle in meters.
        step (float): Distance between points in meters (default is 10 meters).

    Returns:
        list: List of latitude and longitude points within the circle.
    """
    points = []
    earth_radius = 6371000  # Earth's radius in meters

    for r in range(0, int(radius) + 1, step):
        # For each radius step, calculate points in a circular pattern
        for angle in range(0, 360, int(360 * step / (2 * math.pi * r)) if r > 0 else 1):
            theta = math.radians(angle)  # Convert angle to radians
            delta_lat = r * math.cos(theta) / earth_radius
            delta_lng = r * math.sin(theta) / (earth_radius * math.cos(math.radians(center_lat)))

            point_lat = center_lat + math.degrees(delta_lat)
            point_lng = center_lng + math.degrees(delta_lng)

            points.append((point_lat, point_lng))

    return points



#Grass region detection based on pure Computer vision 


#from skimage.feature import local_binary_pattern

def segment_green_areas(currImg):
    # Load the image
    image = currImg.copy()
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    
    # Define the range of green color in HSV
    lower_green = np.array([36, 20, 25])
    upper_green = np.array([86, 200, 255])
    
    
    
   # lower_green = np.array([35, 100, 50])  # Lower bound for green (trees)
   # upper_green = np.array([85, 255, 255])  # Upper bound for green (trees)
    
    # Create a mask for green colors
    mask = cv2.inRange(hsv_image, lower_green, upper_green)
    
    # Bitwise-AND mask and original image
    segmented_image = cv2.bitwise_and(image_rgb, image_rgb, mask=mask)
    cv2.imshow("Segmented", segmented_image)
    cv2.imshow("InitImg", image)
    cv2.waitKey(0)
    # Display the results
   # plt.figure(figsize=(12, 6))
   # plt.subplot(1, 3, 1)
   # plt.title('Original Image')
   # plt.imshow(image_rgb)
   # plt.axis('off')
    
   # plt.subplot(1, 3, 2)
   # plt.title('Mask')
   # plt.imshow(mask, cmap='gray')
   # plt.axis('off')
    
   # plt.subplot(1, 3, 3)
   # plt.title('Segmented Image')
   # plt.imshow(segmented_image)
   # plt.axis('off')
    
   # plt.tight_layout()
   # plt.show()





#Main function for processing all units.
def mainProcessingFunction(inputAddress, inputRadius, minimumSquare, API_KEY):

    # Track timing for different components
    total_model_time = 0
    total_other_time = 0

    # Yolo based model for grass region detection
    model = YOLO('graddDetModelL.pt', 0.5)

    #Remove previously generated csv files.
    os.remove('addressData.csv') if os.path.exists('addressData.csv') else None
    os.remove('circle_results.csv') if os.path.exists('circle_results.csv') else None
    addressesWithAreas = {}
    addressesWithLatLong = {}
    
    address =  inputAddress #  '10449 E Topaz Cir, Mesa, AZ 85212, USA'  # '10642 E Trillium Ave, Mesa, AZ 85212'
    ###########geolocator = Nominatim(user_agent="Your_Name")
    ############location = geolocator.geocode(address)
    
    
    center_lat, center_lng = get_lat_long_google(address, API_KEY)
    if not(center_lat and center_lng):
        print("Failed to retrieve geocoding information.")
        update_firestore_document_error("Failed to retrieve geocoding information.")
        return
    # Define circle parameters
    ##########center_lat = location.latitude
    ###############center_lng = location.longitude
     


    radius =  (float(inputRadius) * 1609.34)
    radius = int(radius)


    step = 60  # Distance between points in meters

    # Generate circle points from given point with given radius 
    points = generate_circle_points(center_lat, center_lng, radius, step)
    print(points)
    pointsUnique = [item for index, item in enumerate(points) if item not in points[:index]]
    # Print the points
    print(f"Generated {len(pointsUnique)} points within the circle:")

    indexOfPoint = 0
    #Get minumum number from 10 and foind circle points, for multithread based satellite image download via google api
    numberOfThreads =  min(len(pointsUnique), 10)
    #Go through all circle points
    for pointIndex in range(0,len(pointsUnique),numberOfThreads):
        argumentCurrent = []
        #Multithread based satellite image download via google api
        point0 = pointsUnique[pointIndex]
        argumentCurrent.append((point0[0], point0[1],API_KEY, 20, (640, 640), 1))
      
        for v in range(1, numberOfThreads, 1):
            if pointIndex + v < len(pointsUnique):
                point1 = pointsUnique[pointIndex+v]
                argumentCurrent.append((point1[0], point1[1],API_KEY, 20, (640, 640), 1))
       
        
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(get_satellite_image_with_resolution, a, b, c, d, e, f) for a, b, c, d, e, f in argumentCurrent]
            #Downloading satellite images via multithread
            currResFromThread = [future.result() for future in futures]
            for i, (currImg, meterInPixel) in enumerate(currResFromThread):
               
                #All lat/long points , generated inside of circle, add into the csv file.
                #data_in_csv(indexOfPoint, point[0], point[1])
                if currImg is None:
                    continue
               
              ##############  segment_green_areas(currImg) 
                                
                start_time = time.time()

                indexOfPoint += 1
                print("Current processing point ", indexOfPoint , "From point ", len(pointsUnique))
                current_percent =int( indexOfPoint * 100 / len(pointsUnique))
                print("current percent  ", current_percent) 
                update_firestore_document_percent(current_percent)
                # Get satellite image timing
                sat_start_time = time.time()
                #currImg , meterInPixel  = get_satellite_image_with_resolution(point[0], point[1],API_KEY, zoom=20, size=(640, 640), scale=1)
                sat_end_time = time.time()
                total_other_time += (sat_end_time - sat_start_time)
                print(f"Satellite image fetch time: {sat_end_time - sat_start_time:.2f} seconds")
    
                # Grass detection timing
                detect_start_time = time.time()
                resImg, areas, polygonCenterPoints = detect_grass_and_calculate_area(currImg, model,meterInPixel)
                detect_end_time = time.time()
                total_model_time += (detect_end_time - detect_start_time)
                print(f"Grass detection time: {detect_end_time - detect_start_time:.2f} seconds")

                tmpAddressMap = {}
                tmpAddressMapLatLong = {}
      
        
                # Process each detected area timing
                areas_start_time = time.time()
              #  from concurrent.futures import ThreadPoolExecutor
                from functools import partial

                def process_area(j, point, polygonCenterPoints, areas, meterInPixel, API_KEY):
                    tmpArea = areas[j]
                    tmpCenterPoint = polygonCenterPoints[j]
            
                    #For each detected area on image get center and with google geoapi get address
                    tmpDeltaX = (tmpCenterPoint.x - 320)* meterInPixel
                    tmpDeltaY = (320 - tmpCenterPoint.y) * meterInPixel
            
                    coord_start_time = time.time()
                    newLat, newLog = calculate_new_coordinates(point[0], point[1], tmpDeltaX, tmpDeltaY)
                    coord_end_time = time.time()
                    print(f"Coordinate calculation time: {coord_end_time - coord_start_time:.2f} seconds")
            
                    start_time_geocode = time.time()
                    finalAddress = latlng_to_address(newLat, newLog, API_KEY)
                    end_time_geocode = time.time()
                    print(f"Geocoding API request time: {end_time_geocode - start_time_geocode:.2f} seconds")
            
                    return (finalAddress, newLat, newLog, tmpArea)

                # Create partial function with fixed arguments
                process_area_partial = partial(process_area, 
                                             point=pointsUnique[pointIndex+i],
                                             polygonCenterPoints=polygonCenterPoints,
                                             areas=areas,
                                             meterInPixel=meterInPixel,
                                             API_KEY=API_KEY)

                # Process areas in parallel using ThreadPoolExecutor
                if len(polygonCenterPoints) > 0:
                    with ThreadPoolExecutor(max_workers=min(len(polygonCenterPoints), 10)) as executor:
                        results = list(executor.map(process_area_partial, range(len(polygonCenterPoints))))
                else:
                    results = []

                # Process results
                for finalAddress, newLat, newLog, tmpArea in results:
                    if finalAddress != -1:
                        addressesWithLatLong[finalAddress] = [newLat, newLog]
                        if finalAddress in tmpAddressMap:
                            print('Found same address ', finalAddress, tmpArea)
                            tmpAddressMap[finalAddress].append(tmpArea)
                        else:
                            tmpAddressMap[finalAddress] = [tmpArea]

                areas_end_time = time.time()
                total_other_time += (areas_end_time - areas_start_time)
                print(f"Areas processing time: {areas_end_time - areas_start_time:.2f} seconds")

                # Map merging timing
                map_start_time = time.time()
                #If current adress is not in map, add it , if exists, add bigger area for current adress
                if len(addressesWithAreas) == 0:
                    addressesWithAreas = tmpAddressMap
                else:
                    for tmpEl in tmpAddressMap:
                        if tmpEl in addressesWithAreas and len(tmpAddressMap[tmpEl]) > len(addressesWithAreas[tmpEl]):
                            addressesWithAreas[tmpEl] = tmpAddressMap[tmpEl]
                        if not(tmpEl in addressesWithAreas):
                            addressesWithAreas[tmpEl] = tmpAddressMap[tmpEl]
                map_end_time = time.time()
                total_other_time += (map_end_time - map_start_time)
                print(f"Map merging time: {map_end_time - map_start_time:.2f} seconds")

                end_time = time.time()
                execution_time = end_time - start_time
                print(f"**** Processing time for point {indexOfPoint}: {execution_time:.2f} seconds ****")
     #   pointIndex = pointIndex +4
        
    #Sort all found adresses from given input adress by the distance increase
    while len(addressesWithAreas) > 0:
        minDist = sys.float_info.max
        minDistLat = ''
        minDistLong = ''
        removeAddress = ''
        for tmpElWr in addressesWithAreas:


            currLat = addressesWithLatLong[tmpElWr][0]
            currLong = addressesWithLatLong[tmpElWr][1]
            #tmp_lat =      location.latitude
            #tmp_lng = location.longitude
            distBet = calculateDistanceBetweenTwoPoints(currLat, currLong, center_lat, center_lng)
            if distBet < minDist:
                minDist = distBet
                minDistLat = currLat
                minDistLong = currLong
                removeAddress = tmpElWr
        if removeAddress != '':

            listOfAreas = addressesWithAreas[removeAddress]
            #print("LIST OF AREAS ")
            #print(listOfAreas)
            #Add all data into final output csv
            data_in_csvArea(removeAddress,minDistLong, minDistLat, minDist*0.0006213712, listOfAreas, minimumSquare)
            del addressesWithAreas[removeAddress]
    
    
    if not(os.path.exists('addressData.csv')):
        data_in_csvArea('','', '', '', [], '')    
    
    
    print("\nTiming Analysis:")
    print(f"Total time spent on AI model interactions: {total_model_time:.2f} seconds")
    print(f"Total time spent on other operations: {total_other_time:.2f} seconds")
    print(f"Difference (Other - Model): {total_other_time - total_model_time:.2f} seconds")


if __name__ == "__main__":
   
    #Use API 
    API_KEY =  "AIzaSyDc1IhzrtalHNSrwKG5s_TMV-P5KvIPr84"
   # API_KEY = "AIzaSyCERUAbDAq1561tMBdONbgpokSWhhuzBHI"
  
    parser = argparse.ArgumentParser(description="Process images and find areas")

    # Define input and output arguments
    parser.add_argument('-a', '--address', required=True, help="Input address")
    parser.add_argument('-r', '--radius', required=True,help="Provide radius in miles")
    parser.add_argument('-m', '--minimum', required=True, help="Minumum square footage for each address")
    args = parser.parse_args()
    
    # Measure execution time
    start_time = time.time()
    
    mainProcessingFunction(args.address, args.radius, args.minimum, API_KEY)
    
    # Calculate and print execution time
    execution_time = time.time() - start_time
    print(f"\nTotal execution time: {execution_time:.2f} seconds")



