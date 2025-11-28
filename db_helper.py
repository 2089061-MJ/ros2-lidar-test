import pymysql

DB_CONFIG = dict(
    host = "localhost",
    user = "root",
    password = "test0123",
    database = "lidar_test",
    charset = "utf8"
)

class DB:
    def __init__(self, **config):
        self.config = config
        
    def connect(self):
        try:
            conn = pymysql.connect(**self.config)
            print("DB 연결 성공")
            return conn
        except pymysql.MySQLError as e:
            print(f" DB 연결 실패: {e}")
            return None
    
    
        
        
        