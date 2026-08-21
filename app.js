let pyodide = null;

const codeEditor = document.getElementById("codeEditor");
const consoleOutput = document.getElementById("console");

const runButton = document.getElementById("runButton");

const inputArea = document.getElementById("inputArea");
const userInput = document.getElementById("userInput");
const submitInput = document.getElementById("submitInput");

// --------------------------------------------------
// Console output
// --------------------------------------------------

function writeOutput(text) {
  consoleOutput.textContent += text;
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

function clearConsole() {
  consoleOutput.textContent = "";
}

// --------------------------------------------------
// Load the exercise
// --------------------------------------------------

async function loadExercise() {
  const response = await fetch("exercises/fakebook.py");

  if (!response.ok) {
    throw new Error("Could not load exercise.");
  }

  const code = await response.text();

  codeEditor.value = code;
}

// --------------------------------------------------
// Get input from the student
// --------------------------------------------------

function getInput() {
  return new Promise((resolve) => {
    inputArea.classList.remove("hidden");

    userInput.value = "";
    userInput.focus();

    function submit() {
      const value = userInput.value;

      inputArea.classList.add("hidden");

      submitInput.removeEventListener("click", submit);
      userInput.removeEventListener("keydown", keyHandler);

      writeOutput(value + "\n");

      resolve(value);
    }

    function keyHandler(event) {
      if (event.key === "Enter") {
        submit();
      }
    }

    submitInput.addEventListener("click", submit);
    userInput.addEventListener("keydown", keyHandler);
  });
}

// --------------------------------------------------
// Run Python
// --------------------------------------------------

async function runPython() {
  if (!pyodide) {
    return;
  }

  clearConsole();

  runButton.disabled = true;

  try {
    const code = codeEditor.value;

    /*
     * Tell Pyodide how to handle print().
     */
    pyodide.setStdout({
      batched: (text) => {
        writeOutput(text);
      },
    });

    /*
     * Tell Pyodide how to handle input().
     */
    pyodide.setStdin({
      stdin: async () => {
        return prompt("Python input:");
        // return await getInput();
      },
    });

    /*
     * Execute the student's Python.
     */
    await pyodide.runPythonAsync(code);
  } catch (error) {
    writeOutput("\nPython error:\n");
    writeOutput(error.toString());
  } finally {
    runButton.disabled = false;
  }
}

// --------------------------------------------------
// Initialise
// --------------------------------------------------

async function initialise() {
  try {
    writeOutput("Loading Python...\n");

    pyodide = await loadPyodide();

    await loadExercise();

    writeOutput("Python ready.\n");
    writeOutput("Press Run to start the exercise.\n\n");

    runButton.textContent = "Run";
    runButton.disabled = false;
  } catch (error) {
    writeOutput("\nFailed to initialise:\n");
    writeOutput(error.toString());
  }
}

// --------------------------------------------------
// Button
// --------------------------------------------------

runButton.addEventListener("click", runPython);

// Start everything
initialise();
