def connect_database():
    username = "demo-user"
    password = "demo-password"
    return f"postgresql://{username}:{password}@localhost/example"
