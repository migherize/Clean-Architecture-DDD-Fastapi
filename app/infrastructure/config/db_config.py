from pydantic_settings import BaseSettings

class DBSettings(BaseSettings):
    DB: str
    USERDB: str
    PASSWORDDB: str
    NAME_SERVICEDB: str
    PORT: int
    NAMEDB: str

    @property
    def DATABASE_URL(self) -> str:
        return f"{self.DB}://{self.USERDB}:{self.PASSWORDDB}@{self.NAME_SERVICEDB}:{self.PORT}/{self.NAMEDB}"

    class Config:
        env_file = ".env"
