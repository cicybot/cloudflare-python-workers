from google_auth_oauthlib.flow import InstalledAppFlow


# YouTube Data API scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/youtubepartner",
          "https://www.googleapis.com/auth/youtube"]

flow = InstalledAppFlow.from_client_secrets_file(
    "/Users/data/doc/google/client_secret.json",
    SCOPES
)

creds = flow.run_local_server(port=0)
print(f"export GOOGLE_ACCESS_TOKEN=\"{creds.token}\"")
# print("ACCESS TOKEN:\n", creds.token)
# print("\nREFRESH TOKEN:\n", creds.refresh_token)
# print("\nTOKEN EXPIRY:\n", creds.expiry)
