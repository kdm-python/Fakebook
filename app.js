let pyodide = null;
let exerciseCode = "";

const consoleOutput = document.getElementById("consoleOutput");
const runButton = document.getElementById("runButton");

const inputArea = document.getElementById("inputArea");
const inputPrompt = document.getElementById("inputPrompt");
const userInput = document.getElementById("userInput");
const submitInput = document.getElementById("submitInput");

// --------------------------------------------------
// Console output
// --------------------------------------------------

function writeOutput(text) {
  console.log("OUTPUT CHUNK:", JSON.stringify(text));

  consoleOutput.textContent += text;
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

function clearConsole() {
  consoleOutput.textContent = "";
}

// --------------------------------------------------
// Get input from the student
// --------------------------------------------------

function getInput(promptText = "") {
  return new Promise((resolve) => {
    // Put the Python prompt beside the real HTML input.
    inputPrompt.textContent = promptText;

    // Show the input line.
    inputArea.classList.remove("hidden");

    // Normal text input by default.
    userInput.type = "text";

    // Make password input behave like a password field.
    // if (promptText.toLowerCase().includes("password")) {
    //   userInput.type = "password";
    // }

    userInput.value = "";
    userInput.focus();

    function submit() {
      const value = userInput.value;

      // Hide input controls.
      inputArea.classList.add("hidden");

      // Remove event handlers.
      submitInput.removeEventListener("click", submit);
      userInput.removeEventListener("keydown", keyHandler);

      // Put the student's answer into the console.
      writeOutput(promptText + value + "\n");

      // Return the answer to Python.
      resolve(value);
    }

    function keyHandler(event) {
      if (event.key === "Enter") {
        event.preventDefault();
        submit();
      }
    }

    submitInput.addEventListener("click", submit);
    userInput.addEventListener("keydown", keyHandler);
  });
}

// --------------------------------------------------
// Load the exercise
// --------------------------------------------------

async function loadExercise() {
  const response = await fetch("exercises/fakebook.py");

  if (!response.ok) {
    throw new Error("Could not load exercise.");
  }

  exerciseCode = await response.text();
}

// --------------------------------------------------
// Run Python
// --------------------------------------------------

async function runPython() {
  console.log("NEW APP.JS VERSION - LOGIN RETURN FIX");
  if (!pyodide) {
    return;
  }

  clearConsole();

  runButton.disabled = true;

  inputArea.classList.add("hidden");

  try {
    // ------------------------------------------------
    // Python print()
    // ------------------------------------------------

    pyodide.setStdout({
      batched: (text) => {
        writeOutput(text + "\n");
      },
    });

    // ------------------------------------------------
    // JavaScript input function
    // ------------------------------------------------

    pyodide.globals.set("__browser_input", async (promptText) => {
      return await getInput(promptText);
    });

    // ------------------------------------------------
    // Give Python the exercise source
    // ------------------------------------------------

    pyodide.globals.set("__exercise_source", exerciseCode);

    // ------------------------------------------------
    // Python wrapper
    // ------------------------------------------------

    const runner = `
import ast

class InputTransformer(ast.NodeTransformer):

    def visit_Call(self, node):
        node = self.generic_visit(node)

        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "input"
        ):
            prompt = (
                node.args[0]
                if node.args
                else ast.Constant(value="")
            )

            new_node = ast.Await(
                value=ast.Call(
                    func=ast.Name(
                        id="__browser_input",
                        ctx=ast.Load()
                    ),
                    args=[prompt],
                    keywords=[]
                )
            )

            return ast.copy_location(new_node, node)

        return node


async def __run_exercise():

    tree = ast.parse(__exercise_source)

    tree = InputTransformer().visit(tree)

    ast.fix_missing_locations(tree)

    module = ast.Module(
        body=[
            ast.AsyncFunctionDef(
                name="__student_code",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[]
                ),
                body=tree.body + [
                    ast.Return(
                        value=ast.Name(
                            id="login_success",
                            ctx=ast.Load()
                        )
                    )
                ],
                decorator_list=[]
            )
        ],
        type_ignores=[]
    )

    ast.fix_missing_locations(module)

    namespace = globals()

    exec(
        compile(
            module,
            "<exercise>",
            "exec"
        ),
        namespace,
        namespace
    )

    return await namespace["__student_code"]()


await __run_exercise()
`;
    const loginSuccess = await pyodide.runPythonAsync(runner);

    if (loginSuccess === true) {
      window.location.href = "fakebook/";
    }
    // await pyodide.runPythonAsync(runner);

    // const loginSuccess = pyodide.globals.get("login_success");

    // if (loginSuccess === true) {
    //   window.location.href = "fakebook/";
    // }
  } catch (error) {
    writeOutput("\\nPython error:\\n");
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
    writeOutput("Loading Python...");

    pyodide = await loadPyodide();

    await loadExercise();

    writeOutput("Python ready.");
    writeOutput("Press Run to start the exercise.");

    runButton.textContent = "Run";
    runButton.disabled = false;
  } catch (error) {
    writeOutput("Failed to initialise:");
    writeOutput(error.toString());
  }
}

// --------------------------------------------------
// Run button
// --------------------------------------------------

runButton.addEventListener("click", runPython);

// --------------------------------------------------
// Start
// --------------------------------------------------

initialise();
