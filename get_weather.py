import requests
from datetime import datetime

API_KEY = "f03b36735cfd0c63f8e994c5fee09c2c"  # Replace with your API key
city = "London"

url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    extracted_data = {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "conditions": data["weather"][0]["description"],
        "date": datetime.utcfromtimestamp(data["dt"]).strftime("%Y-%m-%d %H:%M:%S")
    }

    print(extracted_data)

else:
    print("Error:", response.status_code, response.text)
