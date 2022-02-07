from typing import Any, Dict


class MockRequest:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self.payload = payload

    def get_json(self) -> Dict[str, Any]:
        return self.payload
