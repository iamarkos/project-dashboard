from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Now providing defaults makes the linter happy!
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "dashboard_db"

    SECRET_KEY: str = "supersecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_BUCKET_NAME: str = "projects-bucket"
    MAX_PROJECT_SIZE_MB: int = 10

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
