---
name: vscode-ready
description: Scaffolds one-click VS Code/Cursor debug, run, tasks, and settings configs from the codebase stack. Triggers on make project VSCode-ready, /vscode-ready.
---

# Make this project VSCode-Ready

Act as a Principal Software Architect and Tooling Expert. Goal: create a seamless, "one-click" developer experience (DX) that leverages the full power of the IDE (VS Code, Cursor).

# Objective
Analyze the existing codebase and scaffold the infrastructure needed for a disciplined, high-automation environment. **MUST use available tools (agents, file readers, search)** to deeply understand the current stack before generating configurations.

# Execution Steps

## Step 0: Deep Codebase Analysis (CRITICAL)
**Before generating any files, scan the codebase thoroughly.**
- **Use Agents/Tools**: If `explore`, `grep`, or file-reading tools are available, use them to map the project structure.
- **Identify**:
  - The full Tech Stack (Languages, Frameworks, Database).
  - Existing build scripts (`package.json`, `Makefile`, `Cargo.toml`, etc.).
  - Entry points for debugging (where does `main` start?).
  - Current directory structure and module relationships.
  - Recent history of this repository using git (recent 20 commits).

## Step 1: The "Context" (`AGENTS.md` / `README.md`)
Create or update documentation to serve as the "manual" for both developers and AI.
- **Project Structure**: Based on the Step 0 scan, map out the file system.
- **Tech Stack**: Explicit versions and libraries found.
- **Dev Workflow**: How to build, run, and test based on existing scripts.

## Step 2: The "Controls" (VS Code Configuration)
Create a `.vscode` folder to standardize the workflow:
- **`launch.json`**: Create something the user can run as a daemon (for example `Run Dev Server`).
  - Create debug configurations for *every* part of the stack found in Step 0. Include a compound config to run everything at once.
  - The name MUST NOT have an emoji prefix. Exception: the 2 most important runs MAY use an emoji prefix.
  - Use separators to group the runs.
- **`tasks.json`**: Abstract complex CLI commands found in scripts into simple IDE tasks (e.g., `Install`, `Database Sync`).
  - Format: the name MUST have an emoji prefix. Append '...' when something must be chosen before running.
  - NO daemons allowed.
  - Don't make too-small tasks. Make tasks the user runs occasionally or initially. Maximum 5 tasks.
- **`settings.json`**: Enforce formatting (Prettier/Black/Rustfmt) and linting rules at the workspace level.
  - Add this recommended-plugin json (makes VS Code Tasks visible on the bottom status bar):
    ```json
    {
      "recommendations": [
        "actboy168.tasks"
      ]
    }
    ```

Don't confuse `launch` and `tasks` purposes. Ensure no duplicated features, be creative, and improve the user's AI-assisted development efficiency. Take care of feature order.

## Step 3: Ensure dependencies
- If dependencies are needed, add them to `package.json` / `Cargo.toml`, or add a script into `tasks.json` and tell the user to run it.

## Output Requirement
1. **Analysis Summary**: Briefly state what Step 0 found.
2. **Configuration Files**: Output the full content for `.vscode/launch.json`, `.vscode/tasks.json`, and `AGENTS.md`.
3. **Scripts**: Any shell/node scripts needed to glue the automation.

## Test
- Ensure everything works.

# Instruction
1. Start by scanning the current directory to understand the project state.
2. Remove unnecessary/outdated tasks and launches in `tasks.json` and `launch.json`.
3. Add fresh new tasks and launches following the steps.
4. Re-order and group the launches.
5. Re-order the tasks.
6. Commit the changes to the repository.
