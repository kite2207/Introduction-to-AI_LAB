import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const projectRoot = path.resolve(frontendRoot, "..");
const viteEntry = path.join(frontendRoot, "node_modules", "vite", "bin", "vite.js");

const backend = spawn(
  process.platform === "win32" ? "python" : "python3",
  ["-m", "uvicorn", "backend.api:app", "--host", "127.0.0.1", "--port", "8000"],
  { cwd: projectRoot, stdio: "inherit" },
);

let backendExited = false;
backend.once("exit", (code) => {
  backendExited = true;
  if (code && code !== 0) {
    console.error(`Backend exited with code ${code}.`);
  }
});

async function waitForBackend() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (backendExited) {
      throw new Error("Backend failed to start. Check the Python error above.");
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/");
      if (response.ok) return;
    } catch {
      // The server is still starting.
    }

    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  throw new Error("Backend did not become ready at http://127.0.0.1:8000.");
}

let frontend;

function stop() {
  if (frontend && !frontend.killed) frontend.kill();
  if (!backend.killed) backend.kill();
}

process.on("SIGINT", stop);
process.on("SIGTERM", stop);
process.on("exit", stop);

try {
  await waitForBackend();
  console.log("Backend ready at http://127.0.0.1:8000");

  frontend = spawn(process.execPath, [viteEntry, ...process.argv.slice(2)], {
    cwd: frontendRoot,
    stdio: "inherit",
  });

  frontend.once("exit", (code) => {
    stop();
    process.exit(code ?? 0);
  });
} catch (error) {
  console.error(error.message);
  stop();
  process.exit(1);
}
