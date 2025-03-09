import streamlit as st
import requests

token = "Bearer eyJraWQiOiJ1Z3Y3WHFlNW5cLzlHT3Rkdm56Qk0yY2E0WFBkcmNyVFZuempjSXdGZXZiMD0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI4ZGI0NDExMS1kM2JkLTQ5ZDAtODBiMC1kNzM4NjdhMjZlZjYiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfaEhHbkpGUXRJIiwicGhvbmVfbnVtYmVyX3ZlcmlmaWVkIjpmYWxzZSwiY29nbml0bzp1c2VybmFtZSI6IjhkYjQ0MTExLWQzYmQtNDlkMC04MGIwLWQ3Mzg2N2EyNmVmNiIsImdpdmVuX25hbWUiOiJFbGRlciIsImN1c3RvbTpwYXJ0bmVyIjoidHJ1ZSIsIm9yaWdpbl9qdGkiOiIwMTYyMjI5NS0yOTVmLTRhM2ItOGFjZS1jMDJlNGU3ZjM5MjMiLCJhdWQiOiI3ZGRhbW11cWNsZGlva2NlcWtvcmRyOWp0ciIsImV2ZW50X2lkIjoiN2IyMmZiZmMtOTE2Mi00MGFjLTgzZDEtNDQxNjViNDU3ZDlmIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3NDEyODA3OTcsInBob25lX251bWJlciI6IisxMzE0NjUzODE2MCIsImV4cCI6MTc0MTYyMDU3MiwiY3VzdG9tOmlzX2RldmVsb3BlciI6InRydWUiLCJjdXN0b206cm9sZSI6ImFkbWluIiwiaWF0IjoxNzQxNTM0MTcyLCJmYW1pbHlfbmFtZSI6IkFtYXlhIiwianRpIjoiZmZjOGJlOWUtY2RiZi00ODhiLTkxYWEtNzg1OTlkOTZiN2U0IiwiZW1haWwiOiJlbGFwb2FtYXlhQGdtYWlsLmNvbSJ9.cu7rbpaoXgkolkG6ICRDRKnUG8va3DlxSdMJh-E7RtiJgl1ENs19TIzjN6Di9voS-9HVzrMITymh2MiRqNRqqgZCRm7RQ6qcGOv5jr6UwAMbAJIZKibxVA6IqFqdUAnS_u5qk27PLe3Ke1rfUOSFlFuFsujtwyMDE0HwHWH1f4p4nBVfx_VoGhtYyx1zGMvgra4Wj0nBN8O9BLFiwOtNvwwNhhrKxxDJ0LkeJtSb_zo8H5B5hTNC0WwhyFIf9sa-6wCPQip9q01Z0ZcegjQrYhhxyzaKrk0noOz2qTH72itpyTvF-uu6rpB7OLmyjRbH-xTkZaii47epTU2sMNaeYQ"

# # Get query parameters
# query_params = st.query_params

# st.title("Hello World")

# # Check if there are any query parameters
# if query_params:
#     st.write("URL Parameters:")
#     for param, value in query_params.items():
#         st.write(f"{param}: {value}")

# # Example of how to use a specific parameter
# if 'token' in query_params:
#     token = query_params['token']
#     st.write(f"Received token: {token}")
    
#     # Make a request to the endpoint using the token
#     endpoint = "https://fjz7bfmml2.execute-api.us-east-1.amazonaws.com/dev/company_history"
#     try:
#         body = {
#             "origin": {
#                 "country": "USA",
#                 "mode": "country"
#             },
#             "destination": {
#                 "country": "USA",
#                 "mode": "country"
#             },
#             "truck_types": [
#                 "DRY"
#             ],
#             "pickup_start": 1721347200,
#             "pickup_end": 1721347200
#         }
        
#         response = requests.post(
#             endpoint, 
#             headers={"authorizationToken": f"Bearer {token}"},
#             json=body
#         )
        
#         if response.status_code == 200:
#             company_history = response.json()
#             st.write("Company History:")
#             st.json(company_history)
#         else:
#             st.error(f"Error fetching company history: {response.status_code}")
#             st.write(response.text)
#     except Exception as e:
#         st.error(f"Error making request: {str(e)}")

