from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def receive_until(websocket, expected_type: str, output: list[str]) -> dict:
    while True:
        message = websocket.receive_json()
        if message["type"] == "output":
            output.append(message["text"])
        if message["type"] == expected_type:
            return message


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_exercise_list_does_not_expose_source_or_credentials() -> None:
    response = client.get("/api/exercises")
    assert response.status_code == 200

    body = response.text
    assert "fakebook" in body
    assert "RedSimpsons" not in body
    assert "exercise.py" not in body

    private_source = client.get("/backend/exercises/fakebook/exercise.py")
    assert private_source.status_code == 404


def test_original_exercise_success() -> None:
    output: list[str] = []
    with client.websocket_connect("/api/runs/fakebook") as websocket:
        receive_until(websocket, "status", output)
        while "Please enter your username: " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "input", "value": "george"})

        while "Please enter your password: " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "input", "value": "RedSimpsons"})
        completed = receive_until(websocket, "completed", output)

    assert completed["success"] is True
    assert completed["successPath"] == "/fakebook/"
    assert "Welcome George" in "".join(output)


def test_original_exercise_failure() -> None:
    output: list[str] = []
    with client.websocket_connect("/api/runs/fakebook") as websocket:
        receive_until(websocket, "status", output)
        while "Please enter your username: " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "input", "value": "wrong"})

        while "Please enter your password: " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "input", "value": "wrong"})
        completed = receive_until(websocket, "completed", output)

    assert completed["success"] is False
    assert completed["successPath"] is None
    assert "Incorrect password" in "".join(output)


def test_running_exercise_can_be_stopped() -> None:
    output: list[str] = []
    with client.websocket_connect("/api/runs/fakebook-three-attempts") as websocket:
        receive_until(websocket, "status", output)
        while "Username: " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "stop"})
        completed = receive_until(websocket, "completed", output)

    assert completed["success"] is False
    assert completed["reason"] == "stopped"
