def authenticate(self):
    creds = None
    write_path = '/tmp/token.json' if os.path.exists('/etc/secrets') else TOKEN_FILE

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"'{CREDENTIALS_FILE}' not found. "
                    "Download it from Google Cloud Console → APIs & Services → Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0, prompt='consent')

        # Persist to a writable path — /etc/secrets is read-only on Render
        with open(write_path, 'w') as token:
            token.write(creds.to_json())

    self.creds = creds
    self.service = build('gmail', 'v1', credentials=creds)

    profile = self.service.users().getProfile(userId='me').execute()
    self.user_email = profile.get('emailAddress', '')

    return True