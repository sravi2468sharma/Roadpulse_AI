import csv
import random

corridors = [
    {
        'state': 'Karnataka', 'district': 'Bengaluru Urban', 'city': 'Bengaluru',
        'road_name': 'NH-44 Bengaluru-Hosur Corridor',
        'road_segment': 'Attibele Border to Bommasandra km 18-24',
        'lat': 12.8012, 'lon': 77.7025, 'category': 'National Highway',
        'top_causes': ['Overspeeding', 'Poor Lighting', 'Wrong-side Driving', 'Potholes / Road Surface Defect'],
        'top_users': ['Two-Wheeler', 'Pedestrian', 'Heavy Truck', 'Auto-Rickshaw'],
        'base_risk_level': 'Critical'
    },
    {
        'state': 'Maharashtra', 'district': 'Pune', 'city': 'Lonavala',
        'road_name': 'Mumbai-Pune Expressway (Bhor Ghat)',
        'road_segment': 'Khandala Downhill S-Curve km 42-48',
        'lat': 18.7615, 'lon': 73.3821, 'category': 'Expressway',
        'top_causes': ['Overspeeding', 'Adverse Weather / Fog', 'Brake Failure / Defect', 'Dangerous Junction Geometry'],
        'top_users': ['Car', 'Heavy Truck', 'Bus'],
        'base_risk_level': 'Critical'
    },
    {
        'state': 'Delhi', 'district': 'North Delhi', 'city': 'New Delhi',
        'road_name': 'Delhi Outer Ring Road (Mukarba Chowk)',
        'road_segment': 'Mukarba Chowk to Burari Flyover Stretch',
        'lat': 28.7322, 'lon': 77.1724, 'category': 'Ring Road',
        'top_causes': ['Pedestrian Crossing Hazard', 'Poor Lighting', 'Overspeeding', 'Wrong-side Driving'],
        'top_users': ['Pedestrian', 'Two-Wheeler', 'Heavy Truck', 'Auto-Rickshaw'],
        'base_risk_level': 'Critical'
    },
    {
        'state': 'Rajasthan', 'district': 'Kotputli-Behror', 'city': 'Kotputli',
        'road_name': 'NH-48 Jaipur-Delhi Corridor',
        'road_segment': 'Behror Dhaba Cluster km 128-135',
        'lat': 27.8714, 'lon': 76.2758, 'category': 'National Highway',
        'top_causes': ['Drunk Driving', 'Adverse Weather / Fog', 'Overspeeding', 'Driver Drowsiness'],
        'top_users': ['Heavy Truck', 'Car', 'Two-Wheeler'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Tamil Nadu', 'district': 'Kanchipuram', 'city': 'Sriperumbudur',
        'road_name': 'Chennai-Bengaluru Highway NH-48',
        'road_segment': 'Irungattukottai SIPCOT Industrial Hub',
        'lat': 12.9682, 'lon': 79.9451, 'category': 'National Highway',
        'top_causes': ['Pedestrian Crossing Hazard', 'Overspeeding', 'Poor Lighting', 'Potholes / Road Surface Defect'],
        'top_users': ['Two-Wheeler', 'Pedestrian', 'Bus', 'Heavy Truck'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Telangana', 'district': 'Rangareddy', 'city': 'Hyderabad',
        'road_name': 'Hyderabad ORR (Gachibowli-Airport)',
        'road_segment': 'Exit 17 Rajendranagar to Shamshabad km 30-36',
        'lat': 17.3015, 'lon': 78.4124, 'category': 'Expressway',
        'top_causes': ['Overspeeding', 'Drunk Driving', 'Tire Burst / Mechanical', 'Dangerous Junction Geometry'],
        'top_users': ['Car', 'Two-Wheeler', 'Heavy Truck'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Uttar Pradesh', 'district': 'Kanpur Nagar', 'city': 'Kanpur',
        'road_name': 'GT Road NH-19 Kanpur-Prayagraj',
        'road_segment': 'Chakeri Industrial Extension to Maharajpur',
        'lat': 26.4491, 'lon': 80.3312, 'category': 'National Highway',
        'top_causes': ['Potholes / Road Surface Defect', 'Wrong-side Driving', 'Poor Lighting', 'Overspeeding'],
        'top_users': ['Two-Wheeler', 'Pedestrian', 'Heavy Truck', 'Bicycle'],
        'base_risk_level': 'Critical'
    },
    {
        'state': 'West Bengal', 'district': 'North 24 Parganas', 'city': 'Kolkata',
        'road_name': 'VIP Road Kolkata Airport Corridor',
        'road_segment': 'Ultadanga Hudson Flyover to Kaikhali Crossing',
        'lat': 22.6105, 'lon': 88.4231, 'category': 'Urban Arterial',
        'top_causes': ['Pedestrian Crossing Hazard', 'Dangerous Junction Geometry', 'Overspeeding', 'Poor Lighting'],
        'top_users': ['Auto-Rickshaw', 'Pedestrian', 'Two-Wheeler', 'Bus'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Maharashtra', 'district': 'Pune', 'city': 'Pune',
        'road_name': 'Pune-Solapur Highway NH-65',
        'road_segment': 'Hadapsar Gadital to Manjari Phata',
        'lat': 18.4902, 'lon': 74.0152, 'category': 'National Highway',
        'top_causes': ['Dangerous Junction Geometry', 'Overspeeding', 'Wrong-side Driving', 'Poor Lighting'],
        'top_users': ['Two-Wheeler', 'Pedestrian', 'Heavy Truck', 'Car'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Gujarat', 'district': 'Vadodara', 'city': 'Vadodara',
        'road_name': 'Ahmedabad-Vadodara Expressway NE-1',
        'road_segment': 'Anand Toll Plaza Interchange km 54-60',
        'lat': 22.5642, 'lon': 72.9281, 'category': 'Expressway',
        'top_causes': ['Overspeeding', 'Driver Drowsiness', 'Tire Burst / Mechanical', 'Poor Lighting'],
        'top_users': ['Car', 'Heavy Truck', 'Bus'],
        'base_risk_level': 'Medium'
    },
    {
        'state': 'Kerala', 'district': 'Ernakulam', 'city': 'Kochi',
        'road_name': 'Kochi Bypass NH-66',
        'road_segment': 'Edapally Toll Junction to Palarivattom',
        'lat': 9.9723, 'lon': 76.3182, 'category': 'Urban Arterial',
        'top_causes': ['Adverse Weather / Fog', 'Potholes / Road Surface Defect', 'Dangerous Junction Geometry', 'Overspeeding'],
        'top_users': ['Two-Wheeler', 'Car', 'Auto-Rickshaw', 'Pedestrian'],
        'base_risk_level': 'Medium'
    },
    {
        'state': 'Maharashtra', 'district': 'Mumbai Suburban', 'city': 'Mumbai',
        'road_name': 'Western Express Highway (WEH)',
        'road_segment': 'Goregaon Aarey Flyover to Malad Subway',
        'lat': 19.1685, 'lon': 72.8584, 'category': 'Urban Arterial',
        'top_causes': ['Overspeeding', 'Dangerous Junction Geometry', 'Poor Lighting', 'Potholes / Road Surface Defect'],
        'top_users': ['Two-Wheeler', 'Car', 'Auto-Rickshaw'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Delhi', 'district': 'East Delhi', 'city': 'Delhi',
        'road_name': 'Delhi-Meerut Expressway (NE-3)',
        'road_segment': 'Ghazipur Border to UP Gate Overpass',
        'lat': 28.6254, 'lon': 77.3852, 'category': 'Expressway',
        'top_causes': ['Wrong-side Driving', 'Overspeeding', 'Adverse Weather / Fog', 'Pedestrian Crossing Hazard'],
        'top_users': ['Two-Wheeler', 'Car', 'Heavy Truck'],
        'base_risk_level': 'Medium'
    },
    {
        'state': 'Karnataka', 'district': 'Bengaluru Rural', 'city': 'Bengaluru',
        'road_name': 'Old Madras Road NH-75',
        'road_segment': 'KR Puram Hanging Bridge to Avalahalli',
        'lat': 13.0075, 'lon': 77.7512, 'category': 'National Highway',
        'top_causes': ['Pedestrian Crossing Hazard', 'Poor Lighting', 'Potholes / Road Surface Defect', 'Dangerous Junction Geometry'],
        'top_users': ['Two-Wheeler', 'Pedestrian', 'Heavy Truck', 'Bus'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Tamil Nadu', 'district': 'Coimbatore', 'city': 'Coimbatore',
        'road_name': 'Avinashi Road Corridor',
        'road_segment': 'Peelamedu PSG College to SITRA Junction',
        'lat': 11.0314, 'lon': 77.0321, 'category': 'Urban Arterial',
        'top_causes': ['Dangerous Junction Geometry', 'Overspeeding', 'Pedestrian Crossing Hazard', 'Poor Lighting'],
        'top_users': ['Two-Wheeler', 'Pedestrian', 'Car', 'Bus'],
        'base_risk_level': 'Medium'
    },
    {
        'state': 'Uttar Pradesh', 'district': 'Kannauj', 'city': 'Kannauj',
        'road_name': 'Lucknow-Agra Expressway',
        'road_segment': 'Kannauj Interchange km 170-176',
        'lat': 26.9851, 'lon': 79.9124, 'category': 'Expressway',
        'top_causes': ['Driver Drowsiness', 'Overspeeding', 'Adverse Weather / Fog', 'Tire Burst / Mechanical'],
        'top_users': ['Car', 'Heavy Truck', 'Bus'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Haryana', 'district': 'Gurugram', 'city': 'Gurugram',
        'road_name': 'Mehrauli-Gurgaon (MG) Road',
        'road_segment': 'IFFCO Chowk Metro to Sikanderpur Underpass',
        'lat': 28.4812, 'lon': 77.0815, 'category': 'Urban Arterial',
        'top_causes': ['Drunk Driving', 'Pedestrian Crossing Hazard', 'Overspeeding', 'Poor Lighting'],
        'top_users': ['Car', 'Pedestrian', 'Two-Wheeler', 'Auto-Rickshaw'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Karnataka', 'district': 'Bengaluru Urban', 'city': 'Bengaluru',
        'road_name': 'Hosur Road Elevated Tollway',
        'road_segment': 'Central Silk Board Ramp to Bommanahalli',
        'lat': 12.9172, 'lon': 77.6231, 'category': 'Expressway',
        'top_causes': ['Overspeeding', 'Dangerous Junction Geometry', 'Potholes / Road Surface Defect', 'Poor Lighting'],
        'top_users': ['Two-Wheeler', 'Car', 'Bus'],
        'base_risk_level': 'Medium'
    },
    {
        'state': 'Madhya Pradesh', 'district': 'Indore', 'city': 'Indore',
        'road_name': 'Indore Bypass AB Road',
        'road_segment': 'Dewas Naka Bypass to Nipania Square',
        'lat': 22.7531, 'lon': 75.9224, 'category': 'Ring Road',
        'top_causes': ['Heavy Freight Congestion', 'Wrong-side Driving', 'Poor Lighting', 'Overspeeding'],
        'top_users': ['Heavy Truck', 'Two-Wheeler', 'Tractor', 'Car'],
        'base_risk_level': 'Medium'
    },
    {
        'state': 'Bihar', 'district': 'Patna', 'city': 'Patna',
        'road_name': 'Patna Bypass NH-30',
        'road_segment': 'Anisabad Roundabout to Didarganj Toll',
        'lat': 25.5824, 'lon': 85.1832, 'category': 'National Highway',
        'top_causes': ['Potholes / Road Surface Defect', 'Pedestrian Crossing Hazard', 'Poor Lighting', 'Wrong-side Driving'],
        'top_users': ['Pedestrian', 'Two-Wheeler', 'Heavy Truck', 'Auto-Rickshaw'],
        'base_risk_level': 'High'
    },
    {
        'state': 'Punjab', 'district': 'Mohali', 'city': 'Zirakpur',
        'road_name': 'Chandigarh-Kalka Highway NH-5',
        'road_segment': 'Zirakpur Flyover to Pinjore Gateway',
        'lat': 30.6552, 'lon': 76.8241, 'category': 'National Highway',
        'top_causes': ['Dangerous Junction Geometry', 'Overspeeding', 'Pedestrian Crossing Hazard', 'Poor Lighting'],
        'top_users': ['Two-Wheeler', 'Car', 'Heavy Truck', 'Pedestrian'],
        'base_risk_level': 'Low'
    },
    {
        'state': 'Andhra Pradesh', 'district': 'Visakhapatnam', 'city': 'Visakhapatnam',
        'road_name': 'Visakhapatnam Port Freight Corridor',
        'road_segment': 'Sheela Nagar Flyover to Scindia Junction',
        'lat': 17.6982, 'lon': 83.2184, 'category': 'State Highway',
        'top_causes': ['Poor Lighting', 'Heavy Freight Congestion', 'Potholes / Road Surface Defect', 'Overspeeding'],
        'top_users': ['Heavy Truck', 'Two-Wheeler', 'Auto-Rickshaw'],
        'base_risk_level': 'Medium'
    },
    {
        'state': 'Odisha', 'district': 'Khordha', 'city': 'Bhubaneswar',
        'road_name': 'Bhubaneswar-Cuttack Highway NH-16',
        'road_segment': 'Rasulgarh Square to Pahala Rasagola Mile',
        'lat': 20.3241, 'lon': 85.8672, 'category': 'National Highway',
        'top_causes': ['Pedestrian Crossing Hazard', 'Overspeeding', 'Adverse Weather / Fog', 'Poor Lighting'],
        'top_users': ['Two-Wheeler', 'Pedestrian', 'Bus', 'Car'],
        'base_risk_level': 'Medium'
    },
    {
        'state': 'Assam', 'district': 'Kamrup Metropolitan', 'city': 'Guwahati',
        'road_name': 'GS Road Khanapara Corridor',
        'road_segment': 'Khanapara Rotary to Six Mile Flyover',
        'lat': 26.1284, 'lon': 91.8021, 'category': 'Urban Arterial',
        'top_causes': ['Drunk Driving', 'Adverse Weather / Fog', 'Dangerous Junction Geometry', 'Poor Lighting'],
        'top_users': ['Two-Wheeler', 'Car', 'Pedestrian', 'Auto-Rickshaw'],
        'base_risk_level': 'Low'
    },
    {
        'state': 'Gujarat', 'district': 'Surat', 'city': 'Surat',
        'road_name': 'Surat-Dumas Airport Road',
        'road_segment': 'Sultanabad Junction to Dumas Beach Cross',
        'lat': 21.1421, 'lon': 72.7482, 'category': 'State Highway',
        'top_causes': ['Overspeeding', 'Dangerous Junction Geometry', 'Poor Lighting', 'Drunk Driving'],
        'top_users': ['Two-Wheeler', 'Car', 'Pedestrian'],
        'base_risk_level': 'Low'
    }
]

vru_set = {'Two-Wheeler', 'Pedestrian', 'Auto-Rickshaw', 'Bicycle'}
weather_list = ['Clear', 'Rain', 'Fog/Mist', 'Dust Storm']
road_conds = ['Dry / Smooth', 'Damaged / Potholes', 'Wet / Slippery', 'Under Construction']
light_conds = ['Daylight', 'Streetlights Operational', 'Unlit / Pitch Black', 'Poor / Intermittent']
traffic_levels = ['High', 'Medium', 'Low', 'Congested']

random.seed(42)
rows = []
record_id = 10001

for c in corridors:
    # Generate 35-50 incidents per corridor across 2021-2024
    count = 55 if c['base_risk_level'] == 'Critical' else (42 if c['base_risk_level'] == 'High' else (32 if c['base_risk_level'] == 'Medium' else 24))
    
    for _ in range(count):
        year = random.choice([2021, 2022, 2023, 2024])
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        
        # Temporal distributions: night-time peaks for high risk
        if random.random() < 0.65:
            # High risk hours: 19:00 - 02:00 or rush hours 08:00 - 10:00
            hour = random.choice([0, 1, 2, 7, 8, 9, 18, 19, 20, 21, 22, 23])
        else:
            hour = random.randint(3, 17)
            
        cause = random.choice(c['top_causes'])
        vtype = random.choice(c['top_users'])
        
        # Map user category
        user_cat = 'Vulnerable Road User (VRU)' if vtype in vru_set else ('Commercial Goods' if vtype == 'Heavy Truck' else 'Motorized Passenger')
        
        # Lighting depends on hour
        if 6 <= hour <= 17:
            light = 'Daylight'
        else:
            if cause == 'Poor Lighting' or random.random() < 0.45:
                light = random.choice(['Unlit / Pitch Black', 'Poor / Intermittent'])
            else:
                light = 'Streetlights Operational'
                
        # Road condition
        if cause == 'Potholes / Road Surface Defect':
            rcond = 'Damaged / Potholes'
        elif month in [6, 7, 8, 9] and random.random() < 0.5:
            rcond = 'Wet / Slippery'
        else:
            rcond = random.choice(road_conds)
            
        weather = 'Rain' if rcond == 'Wet / Slippery' else ('Fog/Mist' if (month in [11, 12, 1] and hour in [22, 23, 0, 1, 2, 3, 4, 5, 6]) else random.choice(['Clear', 'Clear', 'Clear', 'Rain']))
        traffic = random.choice(traffic_levels)
        
        accidents = 1
        
        # Severity calculation based on conditions
        is_high_risk = c['base_risk_level'] in ['Critical', 'High']
        is_vru = vtype in vru_set
        is_night = hour >= 21 or hour <= 4
        is_speed_or_drunk = cause in ['Overspeeding', 'Drunk Driving']
        
        fatal_prob = 0.08
        if is_high_risk: fatal_prob += 0.15
        if is_vru: fatal_prob += 0.12
        if is_night: fatal_prob += 0.10
        if is_speed_or_drunk: fatal_prob += 0.12
        if light == 'Unlit / Pitch Black': fatal_prob += 0.08
        
        if random.random() < fatal_prob:
            fatalities = random.choices([1, 2, 3], weights=[0.8, 0.16, 0.04])[0]
            injuries = random.choices([0, 1, 2, 3], weights=[0.2, 0.4, 0.3, 0.1])[0]
        else:
            fatalities = 0
            injuries = random.choices([0, 1, 2, 3, 4], weights=[0.2, 0.45, 0.25, 0.07, 0.03])[0]
            
        # Tiny jitter on coordinate for realism within road segment (+- 0.008 deg)
        lat_jitter = c['lat'] + random.uniform(-0.008, 0.008)
        lon_jitter = c['lon'] + random.uniform(-0.008, 0.008)
        
        rows.append({
            'id': f'ACC-{record_id}',
            'state': c['state'],
            'district': c['district'],
            'city': c['city'],
            'road_name': c['road_name'],
            'road_segment': c['road_segment'],
            'latitude': round(lat_jitter, 5),
            'longitude': round(lon_jitter, 5),
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'road_category': c['category'],
            'cause': cause,
            'vehicle_type': vtype,
            'road_user_type': user_cat,
            'weather': weather,
            'road_condition': rcond,
            'lighting_condition': light,
            'traffic_level': traffic,
            'accidents': accidents,
            'fatalities': fatalities,
            'injuries': injuries
        })
        record_id += 1

fieldnames = [
    'id', 'state', 'district', 'city', 'road_name', 'road_segment',
    'latitude', 'longitude', 'year', 'month', 'day', 'hour',
    'road_category', 'cause', 'vehicle_type', 'road_user_type',
    'weather', 'road_condition', 'lighting_condition', 'traffic_level',
    'accidents', 'fatalities', 'injuries'
]

output_path = 'data/demo_accidents.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f'Generated {len(rows)} accident records across {len(corridors)} Indian corridors in {output_path}')
