import asyncio
import json
import os
import signal
import sys
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import WebSocket, WebSocketDisconnect

from .exercises import Exercise


class ExerciseRunner:
    def __init__(
        self,
        exercise: Exercise,
        websocket: WebSocket,
        timeout_seconds: float,
        max_output_bytes: int,
    ) -> None:
        self.exercise = exercise
        self.websocket = websocket
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self.process: asyncio.subprocess.Process | None = None
        self.output_bytes = 0
        self.stop_reason: str | None = None

    async def run(self) -> None:
        with TemporaryDirectory(prefix="fakebook-run-") as temporary_dir:
            result_path = Path(temporary_dir) / "result.json"
            self.process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-u",
                "-m",
                "backend.exercise_runner",
                str(self.exercise.entrypoint),
                str(result_path),
                self.exercise.result_variable,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=temporary_dir,
                start_new_session=True,
                env=self._child_environment(),
            )

            await self.websocket.send_json({"type": "status", "status": "running"})

            output_task = asyncio.create_task(self._stream_output())
            input_task = asyncio.create_task(self._receive_input())
            process_task = asyncio.create_task(self._wait_for_process())

            done, _ = await asyncio.wait(
                {input_task, process_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            disconnected = False
            if input_task in done:
                try:
                    reason = input_task.result()
                except WebSocketDisconnect:
                    disconnected = True
                    reason = "disconnected"
                self.stop_reason = reason
                await self._terminate()
                await process_task
            else:
                input_task.cancel()
                with suppress(asyncio.CancelledError, WebSocketDisconnect):
                    await input_task

            with suppress(WebSocketDisconnect, RuntimeError):
                await output_task

            if disconnected:
                return

            result = self._read_result(result_path)
            if self.stop_reason:
                result["success"] = False
                result["reason"] = self.stop_reason

            await self.websocket.send_json(
                {
                    "type": "completed",
                    **result,
                    "successPath": (
                        self.exercise.success_path if result.get("success") else None
                    ),
                }
            )

    async def _stream_output(self) -> None:
        assert self.process is not None
        assert self.process.stdout is not None

        while chunk := await self.process.stdout.read(1024):
            self.output_bytes += len(chunk)
            if self.output_bytes > self.max_output_bytes:
                self.stop_reason = "output_limit"
                await self._terminate()
                return
            await self.websocket.send_json(
                {"type": "output", "text": chunk.decode("utf-8", errors="replace")}
            )

    async def _receive_input(self) -> str:
        assert self.process is not None
        assert self.process.stdin is not None

        while True:
            message = await self.websocket.receive_json()
            message_type = message.get("type")

            if message_type == "stop":
                return "stopped"

            if message_type == "input" and self.process.returncode is None:
                value = str(message.get("value", ""))
                self.process.stdin.write((value + "\n").encode())
                await self.process.stdin.drain()

    async def _wait_for_process(self) -> int:
        assert self.process is not None
        try:
            return await asyncio.wait_for(
                self.process.wait(),
                timeout=self.timeout_seconds,
            )
        except TimeoutError:
            self.stop_reason = "timeout"
            await self._terminate()
            return await self.process.wait()

    async def _terminate(self) -> None:
        if self.process is None or self.process.returncode is not None:
            return

        with suppress(ProcessLookupError):
            os.killpg(self.process.pid, signal.SIGTERM)

        try:
            await asyncio.wait_for(self.process.wait(), timeout=2)
        except TimeoutError:
            with suppress(ProcessLookupError):
                os.killpg(self.process.pid, signal.SIGKILL)
            await self.process.wait()

    @staticmethod
    def _read_result(result_path: Path) -> dict[str, object]:
        if not result_path.is_file():
            return {"success": False, "error": "exercise_failed"}
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"success": False, "error": "invalid_result"}
        return result if isinstance(result, dict) else {"success": False}

    @staticmethod
    def _child_environment() -> dict[str, str]:
        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        return environment
