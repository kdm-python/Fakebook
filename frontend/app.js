const exerciseSelect = document.getElementById("exerciseSelect");
const schoolName = document.getElementById("schoolName");
const exerciseHeading = document.getElementById("exerciseHeading");
const exerciseDescription = document.getElementById("exerciseDescription");
const runButton = document.getElementById("runButton");
const stopButton = document.getElementById("stopButton");
const clearButton = document.getElementById("clearButton");
const connectionStatus = document.getElementById("connectionStatus");
const consoleWindow = document.getElementById("consoleWindow");
const consoleOutput = document.getElementById("consoleOutput");
const inputForm = document.getElementById("inputForm");
const userInput = document.getElementById("userInput");
const passwordHistory = document.getElementById("passwordHistory");
const passwordAttempts = document.getElementById("passwordAttempts");
const passwordAttemptCount = document.getElementById("passwordAttemptCount");

let exercises = [];
let socket = null;
let runFinished = true;
let currentPrompt = "";
let attemptedPasswords = [];
let pendingPassword = null;
let passwordAttemptsTotal = 0;
let isPasswordInput = false;

function resetPasswordHistory() {
  attemptedPasswords = [];
  pendingPassword = null;
  passwordAttemptsTotal = 0;
  passwordAttemptCount.textContent = "0";
  passwordAttempts.replaceChildren();
  passwordHistory.classList.add("hidden");
}

function recordPasswordAttempt(value) {
  attemptedPasswords.unshift(value);
  attemptedPasswords = attemptedPasswords.slice(0, 20);
  passwordAttemptsTotal += 1;
  passwordAttemptCount.textContent = String(passwordAttemptsTotal);
  passwordAttempts.replaceChildren(
    ...attemptedPasswords.map((password) => {
      const item = document.createElement("li");
      const attempt = document.createElement("code");
      attempt.textContent = password;
      item.append(attempt);
      return item;
    }),
  );
  passwordHistory.classList.remove("hidden");
}

function setPasswordMode(isPassword) {
  isPasswordInput = isPassword;
  userInput.type = "text";
  userInput.autocomplete = "off";
}

function setStatus(text, state) {
  connectionStatus.textContent = text;
  connectionStatus.dataset.state = state;
}

function setRunning(isRunning) {
  runFinished = !isRunning;
  runButton.disabled = isRunning || exercises.length === 0;
  stopButton.disabled = !isRunning;
  exerciseSelect.disabled = isRunning || exercises.length === 0;
  inputForm.classList.toggle("hidden", !isRunning);

  if (isRunning) {
    userInput.value = "";
    currentPrompt = "";
    setPasswordMode(false);
    userInput.focus();
    setStatus("Running", "running");
  } else {
    setPasswordMode(false);
  }
}

function writeOutput(text) {
  consoleOutput.textContent += text;
  consoleWindow.scrollTop = consoleWindow.scrollHeight;
}

function clearConsole() {
  consoleOutput.textContent = "";
}

function selectedExercise() {
  return exercises.find((exercise) => exercise.id === exerciseSelect.value);
}

function updateExerciseDescription() {
  const exercise = selectedExercise();
  exerciseDescription.textContent = exercise?.description ?? "";
}

async function loadExercises() {
  try {
    const response = await fetch("/api/exercises", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const data = await response.json();
    exercises = data.exercises ?? [];
    schoolName.textContent = data.school.title;
    document.title = `${data.school.title} · Python Exercise Runner`;

    exerciseSelect.replaceChildren(
      ...exercises.map((exercise) => {
        const option = document.createElement("option");
        option.value = exercise.id;
        option.textContent = exercise.title;
        return option;
      }),
    );

    if (exercises.length === 0) {
      exerciseSelect.innerHTML = "<option>No exercises available</option>";
      exerciseDescription.textContent = "No exercises are configured on the server.";
      setStatus("No exercises", "error");
      return;
    }

    const exerciseId = decodeURIComponent(window.location.pathname.slice(1).replace(/\/$/, ""));
    if (exerciseId) {
      const exercise = exercises.find((item) => item.id === exerciseId);
      if (!exercise) {
        throw new Error("This exercise is not available for this school.");
      }
      exerciseSelect.value = exerciseId;
      exerciseHeading.textContent = exercise.title;
    }

    exerciseSelect.disabled = false;
    runButton.disabled = false;
    updateExerciseDescription();
    setStatus("Ready", "ready");
  } catch (error) {
    exerciseDescription.textContent = "The exercise server could not be reached.";
    clearConsole();
    writeOutput(`Connection error: ${error.message}`);
    setStatus("Offline", "error");
  }
}

function startRun() {
  const exercise = selectedExercise();
  if (!exercise || (socket && socket.readyState < WebSocket.CLOSING)) {
    return;
  }

  clearConsole();
  resetPasswordHistory();
  setRunning(true);

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${window.location.host}/api/runs/${encodeURIComponent(exercise.id)}`;
  socket = new WebSocket(url);

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);

    if (message.type === "output") {
      writeOutput(message.text);
      currentPrompt += message.text;
      const currentLine = currentPrompt.slice(currentPrompt.lastIndexOf("\n") + 1);
      const isPasswordPrompt = /\bpassword\b/i.test(currentLine);
      if (isPasswordPrompt && pendingPassword !== null) {
        recordPasswordAttempt(pendingPassword);
        pendingPassword = null;
      }
      setPasswordMode(isPasswordPrompt);
      return;
    }

    if (message.type === "completed") {
      finishRun(message);
    }
  });

  socket.addEventListener("error", () => {
    if (!runFinished) {
      writeOutput("\nConnection to the exercise server was lost.\n");
      setStatus("Connection error", "error");
    }
  });

  socket.addEventListener("close", (event) => {
    if (!runFinished) {
      setRunning(false);
      if (event.code !== 1000) {
        writeOutput("\nThe exercise ended unexpectedly.\n");
        setStatus("Stopped", "error");
      }
    }
    socket = null;
  });
}

function finishRun(message) {
  if (!message.success && pendingPassword !== null) {
    recordPasswordAttempt(pendingPassword);
  }
  pendingPassword = null;
  setRunning(false);

  if (message.reason === "stopped") {
    writeOutput("\nExercise stopped.\n");
    setStatus("Stopped", "ready");
  } else if (message.reason === "output_limit") {
    writeOutput("\nExercise stopped after producing too much output.\n");
    setStatus("Output limit", "error");
  } else if (message.error) {
    setStatus("Program error", "error");
  } else if (message.success) {
    setStatus("Completed", "success");
  } else {
    setStatus("Finished", "ready");
  }

  if (message.success && message.successPath) {
    window.setTimeout(() => {
      window.location.assign(message.successPath);
    }, 350);
  }
}

function stopRun() {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "stop" }));
    stopButton.disabled = true;
    setStatus("Stopping", "loading");
  }
}

inputForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (socket?.readyState !== WebSocket.OPEN) {
    return;
  }

  const value = userInput.value;
  const isPassword = isPasswordInput;
  socket.send(JSON.stringify({ type: "input", value }));
  if (isPassword) {
    pendingPassword = value;
  }
  writeOutput(`${value}\n`);
  userInput.value = "";
  currentPrompt = "";
  setPasswordMode(false);
  userInput.focus();
});

exerciseSelect.addEventListener("change", () => {
  updateExerciseDescription();
  const exercise = selectedExercise();
  if (exercise) {
    window.history.pushState({}, "", `/${encodeURIComponent(exercise.id)}`);
    exerciseHeading.textContent = exercise.title;
  }
});
window.addEventListener("popstate", () => {
  const exerciseId = window.location.pathname.slice(1).replace(/\/$/, "");
  const exercise = exercises.find((item) => item.id === exerciseId);
  if (exercise) exerciseSelect.value = exercise.id;
  exerciseHeading.textContent = exercise?.title ?? "Choose a Python exercise";
  updateExerciseDescription();
});
runButton.addEventListener("click", startRun);
stopButton.addEventListener("click", stopRun);
clearButton.addEventListener("click", clearConsole);

loadExercises();
