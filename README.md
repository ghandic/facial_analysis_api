# Facial Analysis - Quality checking

Querying the API
-----
The API currently has one URL available to it, namely <ip>/api/v1/face which requires the use of the POST method.
The image needs to be supplied during the request inside a form.

## How to run
```bash
docker-compose up -d
open web/index.html
```

## Example of calling the API from python
```python
import requests
import json

image_path = "path/to/image.jpg"
api_url = "http://localhost:8686/api/v1/face"

# Send image to receive facial analysis
response = requests.post('', files={'image': open(image_path, 'rb')})

# Pretty print the response
print(json.loads(response.text, indent=2, sort_keys=True))
```
