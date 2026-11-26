from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app, base_url="http://miltoncross.localhost:8000")
test_school_client = TestClient(app, base_url="http://school-test.localhost:8000")


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
    assert response.json()["school"] == {"id": "miltoncross", "title": "Miltoncross"}
    assert "RedSimpsons" not in body
    assert "exercise.py" not in body

    private_source = client.get("/backend/exercises/miltoncross/fakebook/exercise.py")
    assert private_source.status_code == 404


def test_school_hosts_have_separate_exercises_and_pages() -> None:
    miltoncross = client.get("/api/exercises").json()
    other = test_school_client.get("/api/exercises").json()
    assert {exercise["id"] for exercise in miltoncross["exercises"]} == {"fakebook"}
    assert other == {
        "school": {"id": "school-test", "title": "School Test"},
        "exercises": [{
            "id": "hello-world",
            "title": "Hello World",
            "description": "A short greeting exercise for testing another school.",
        }],
    }
    assert client.get("/").status_code == 200
    assert client.get("/fakebook").status_code == 200
    assert client.get("/fakebook-alternative").status_code == 404
    assert test_school_client.get("/hello-world").status_code == 200
    assert client.get("/hello-world").status_code == 404
    assert test_school_client.get("/fakebook").status_code == 404
    assert client.get("/rewards/fakebook/").status_code == 200


def test_unknown_and_malformed_school_hosts_are_rejected() -> None:
    for host in ("unknown.localhost:8000", "miltoncross.example.com", "x.miltoncross.localhost"):
        response = client.get("/", headers={"host": host})
        assert response.status_code == 404
        assert "School not found" in response.text
        assert "text/html" in response.headers["content-type"]
        assert client.get("/api/exercises", headers={"host": host}).status_code == 404
        assert client.get("/index.html", headers={"host": host}).status_code == 404
        assert client.get("/style.css", headers={"host": host}).status_code == 200


def test_bare_parent_domain_explains_that_school_is_missing() -> None:
    for host in ("localhost:8000", "bytelets.org"):
        response = client.get("/", headers={"host": host})
        assert response.status_code == 404
        assert "No school specified" in response.text
        assert "miltoncross.localhost:8000" in response.text


def test_websocket_is_scoped_to_school() -> None:
    from starlette.websockets import WebSocketDisconnect
    import pytest

    with pytest.raises(WebSocketDisconnect):
        with test_school_client.websocket_connect("/api/runs/fakebook", headers={"host": "school-test.localhost:8000"}):
            pass

    output: list[str] = []
    with test_school_client.websocket_connect("/api/runs/hello-world", headers={"host": "school-test.localhost:8000"}) as websocket:
        receive_until(websocket, "status", output)
        while "What is your name? " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "input", "value": "Sam"})
        completed = receive_until(websocket, "completed", output)
    assert completed["success"] is True
    assert "Hello, Sam!" in "".join(output)


def test_original_exercise_success() -> None:
    output: list[str] = []
    with client.websocket_connect("/api/runs/fakebook", headers={"host": "miltoncross.localhost:8000"}) as websocket:
        receive_until(websocket, "status", output)
        while "Please enter your username: " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "input", "value": "george"})

        while "Please enter your password: " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "input", "value": "RedSimpsons"})
        completed = receive_until(websocket, "completed", output)

    assert completed["success"] is True
    assert completed["successPath"] == "/rewards/fakebook/"
    assert "Welcome George" in "".join(output)


def test_original_exercise_allows_unlimited_password_retries() -> None:
    output: list[str] = []
    with client.websocket_connect("/api/runs/fakebook", headers={"host": "miltoncross.localhost:8000"}) as websocket:
        receive_until(websocket, "status", output)
        while "Please enter your username: " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "input", "value": "george"})

        while "Please enter your password: " not in "".join(output):
            receive_until(websocket, "output", output)
        for _ in range(25):
            websocket.send_json({"type": "input", "value": "wrong"})
            previous_output_length = len("".join(output))
            while (
                "Please enter your password: "
                not in "".join(output)[previous_output_length:]
            ):
                receive_until(websocket, "output", output)
        websocket.send_json({"type": "input", "value": "RedSimpsons"})
        completed = receive_until(websocket, "completed", output)

    assert completed["success"] is True
    assert completed["successPath"] == "/rewards/fakebook/"
    assert "Incorrect password" in "".join(output)


def test_running_exercise_can_be_stopped() -> None:
    output: list[str] = []
    with client.websocket_connect("/api/runs/fakebook", headers={"host": "miltoncross.localhost:8000"}) as websocket:
        receive_until(websocket, "status", output)
        while "Please enter your username: " not in "".join(output):
            receive_until(websocket, "output", output)
        websocket.send_json({"type": "stop"})
        completed = receive_until(websocket, "completed", output)

    assert completed["success"] is False
    assert completed["reason"] == "stopped"
