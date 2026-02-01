
class BaseScm:
    def request(self, method: str, endpoint: str, accept: str) -> requests.Response:
        pass