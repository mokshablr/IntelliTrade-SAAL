import requests

# Replace with your actual API endpoint
url = "http://127.0.0.1:8000/api/generate"

# Example payload for POST request
payload = {
    "user_input": "Tell me about MACD"
}

# Make the POST request
response = requests.post(url, json=payload)

# Convert response to JSON
data = response.json()

# Print the 'message' field
print("API says:", data["message"])

