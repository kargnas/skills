---
name: ai-ready
description: Transform the current project into an AI-ready codebase by migrating to AGENTS.md, setting up debugging/testing infrastructure, and creating comprehensive documentation
---

# Make this project AI-ready

Goal: Enhance outdated AI Rule file and the codebase in this project to up-to-date AI Rule file and AI-ready easy setting with up-to-date codebase understanding.

When this project is mono-repo and has multiple projects (with packages.json, composer.json, ...):
- Ensure having AGENTS.md in every project's root, separated from the root AGENTS.md
- Ensure having .env.example in every project's root, separated from the root .env.example
- Ensure having .env.ai-ready in every project's root, separated from the root .env.ai-ready

1. Update .gitignore
    - AGENTS.md and AI Agent rules shouldn't be in .gitignore
        - Check if AGENTS.md, CLAUDE.md, .cursorrules or any other AGENT related files are in `.gitignore`
        - If they are, remove those lines from `.gitignore`
        - Stash the AGENTS files if it's existing
        - Commit the `.gitignore` change
        - Then restash the AGENTS files
        - Explain (easily) to the users why the AGENTS.md shouldn't be in `.gitignore`.
    - Add missing ignore files
        - `.env`
        - `.env.*`
        - `!.env.ai-ready`
        - `!.env.example`
        - `.sisyphus/`
        - `.sisyphus/boulder.json`
        - `!.sisyphus/.gitignore`
        - `!.sisyphus/plans/`
        - `!.sisyphus/evidence/`
        - (and more you think it's needed...)

2. Migrate from CLAUDE.md to AGENTS.md
    1. If this project has CLAUDE.md but no AGENTS.md
        - Rename CLAUDE.md to AGENTS.md
        - Create CLAUDE.md and put '@AGENTS.md' only
    2. If this project has CLAUDE.md and AGENTS.md together
        - Combine both files into AGENTS.md, remove duplicates and merge content
        - Create CLAUDE.md and put '@AGENTS.md' only
    3. git commit

3. Enhance debugging and testing
    1. Ensure install all dependencies (be careful, use the node dependency manager this project already uses)
    2. Install debugging tools and commit the dependency manager file
        - Install static code analysis tools if not already installed
            - For Laravel
                - `larastan/larastan`
                - `laravel/boost --dev`
            - For PHP (but without Laravel)
                - `phpstan/phpstan` for PHP without Laravel
            - Pick some similar popular solutions for other languages and frameworks.
    3. Run static code analysis and debug any issues with minimum modification 
        - Only debug serious issues, add ignore for minor issues:
            - Unused variables, unused imports, unused functions, unused classes
            - Import order, ...
        - If you have anything you fixed, then show the summary of your modification
        - Take permission to "commit & continue" from the user
        - If the user accepts, then commit the changes and continue to the next step
    4. Run tests and debug any issues with minimum modification
        - If you have anything you fixed, then show the summary of your modification
        - Take permission to "commit & continue" from the user
        - If the user accepts, then commit the changes and continue to the next step

4. Ensure .env file is up-to-date
    1. If .env file is not present, create it from .env.example. If the existing example file name is weird, change it to .env.example.
        - If you changed the .env.example file name, you need to look at all the codebase, find all the references to the previous example file and change them to the new name.
    2. Find any missing environment variables and add them to .env.example file, and add explanation and the purpose of the variables
    3. If any environment variable isn't necessary, don't make unncessary .env files. Remove them.
    4. Commit if they are.

5. Create files for AI Agentic Coding
    1. Create .env.ai-ready
        - Default ready-to-use `.env` setup for AI Agent. (Built-in database, built-in fallback cache and etc)
        - Comments all the other keys, auth codes, Slack webhooks, tokens and other sensitive information (I will set it in the `secrets` in the environment) For mandatory tokens to run this project, you should ask to the user to add to the secrets or environment variables manually in the AI Agent system.
    2. Create README.ai-ready.md
        - Guide how to set the setup script and the environment secrets and variables for human coders who don't know about AI well. You should explain what's the purpose of this file exactly in the start of the document.
        - Minimize using many heavy services (like MySQL, Redis and etc). Try to use lightweight, file based, no install required services if possible.
            - Use these lightweight databases. Those are dev purpose file based databases:
                - For MySQL: SQLite
                - For PostgreSQL: PGLite with `pgvector` plugin
            - When you try to use lightweight DBMS instead of Production DBMS, if the migration files are not compatible, then you NEED to fix the migration files.
                - You need to run the migrations to check this.
                - Eventually uou should make the codebase compatible with sqlite.
            - Never guide that use `Brew` or `apt-get` to install services like MySQL, Redis, PgSQL and etc. That system-wide database solution souldn't be installed to the user's system. Instead, guide to use Docker if you need to guide it cause it can't be fall back to other lightweight solutions.
        - Add a short comment about this file in README.md for new developers (e.g. See README.ai-ready.md file if you want to set up the environment for AI Agentic Coding).
        - Make it very visualistic using Drawing, Table and ASCII Image and easy understandable.
        - For example:
            ```
            # install uv
            ...

            # copy .env.ai-ready .env if .env doesn't exist
            cp -n .env.ai-ready .env
            ...

            # install dependencies
            ...
            ```
    2. Add guide for Codex Cloud:
        - Start-up setup script for CODEX Cloud (Network access enabled) - Idealy only 10 lines, and should be less than 100 lines.
            - Codex Cloud uses Ubuntu 24.04 based docker image. (https://github.com/openai/codex-universal)
            - Codex Cloud can't use Docker. So use file based lightweight services for cache, database, and other services.
            - Don't make anything for production like caches (e.g. php artisan cache:route)
            - Don't use git command, they don't have git feature
            - Add seeders for the database if the seeders are available
            - e.g.
                ```bash
                pip install -r requirements.txt
                npm install
                ./run/setup.sh
                ```
        - Maintain script (Network access enabled) - Idealy only 5 lines, should be less than 30 lines.
            - This is for after checking out a branch.
            - e.g.
                ```bash
                pip install -r requirements.txt
                npm install
                ./run/maintenance_setup.sh
                ```
    3. Final test with a new agent if the guide is working as expected. If It isn't, fix it.

6. CI/CD Setup
    - Add GitHub Actions for linting (for every commits and manual running), testing (for every commits and manual running), and deploying (if you can figure out how to deploy, and for manual running)
        - Install Github Actions lint first (`npm install --save-dev @action‑validator/cli`)
        - Write all the necessary GitHub Actions.
        - Run `actionlint` after writing the actions. If it has errors, fix it.
    - Enhance or Create .vscode/settings.local.json for running local test using `vscode-ready` command
    - References:
        - Auto Bump Patch for NPM Packages: `@references/auto-bump-patch.yml`

7. Enhance AGENTS.md
    - Enhance the AGENTS.md file with following instructions:
        1. Change all the CLAUDE specific mentioning in the existing AGENTS.md to 'AI Agent'
        2. `tree` the codebase, and read all the important files in this codebase.
        3. Learn coding patterns and best practices
            - Learn from the codebase.
            - Learn from the recent 300 commits
                - Read file diff if you need to understand deeply
                - Read file diff for the critical changes
            - Learn from the recent 30 PRs
            - Learn from the all of the comments which were written by human coders.
        4. Attach or merge new AI rules based on the codebase understanding.
        5. Attach or merge new comprehensive documentation of the codebase.
            - Specify framework and libraries used in the codebase
            - How to start development in the local development environment
                - How to run tests or debug the codebase
                - Specify if you need to install any external dependencies on your machine (For example, Docker is mandatory)
                - Specify whether it's mandatory or optional. Mention if there are easy-to-install fallbacks. (Only after you tried and confirmed it's working perfectly)
            - Codebase structure and important classese and functions' responsibilities
                - Explain only important nested directories which can't be guessed the purpose by the directory name, not all the nested files and directory.
                - Add a line for strongly suggesting to run `tree` command to look up everything to understand for the readers.
            - What's the restriction and something to avoid
            - What's the mandatory when doing something
        6. Additional docs I specially want
            - Default language of the product should be English. (e.g. Laravel APP_LOCALE, APP_FALLBACK_LOCALE, APP_FAKER_LOCALE should be English)
            - Explicitly state that you should update/edit existing AGENTS.md when you have done every task
            - Focus on making coding rules/style guide, not documentation of the codebase.
            - All of the rules should be English, and format like this writing. (Markdown, minimize new lines, use bullet points and headers..)
            - Specify the code should be concise and clear like this:

                ```markdown
                ### Code Quality: Always look back your git status and make sure build success before commit
                - Before you commit to the git, or after you finish a task, you must follow the guidelines below:
                - You need to watch the `git status`, and make sure if there is no more unnecessary code, and see if strictly followed my prompts. Change your persona as critical code-reviewer, and blame code if there is some code that doesn't need. Then tell to the user which code is unnecessary and removable at the summary.
                - ALWAYS write human-readable code which is easy to understand and maintain even after a year when you look back. You can use any method to achieve this, such as using descriptive variable names, commenting your code, and writing modular code.
                - You can easily delete code, functions or files if you are sure that it is not needed anymore. We have git, so you never need to worry about losing code.
                - Make sure run and build success
                - For javascript or typescript edits, you must ALWAYS run `pnpm build` to make sure there is no error when build. If you find an error, you must fix it and run build again.
                - For tests, you must run `pnpm test` to make sure there is no error when test. If you find an error, you must fix it and run test again.
                - For smoke tests, you must run the smoke test you edited/added and make sure it's successfully passed. (Fix it if you find an error) But if you don't have any environment variables to run, just STOP working.
                ```

        7. Find what kind of speaking language the codebase uses, and specify it in AGENTS.md
            - If you can't find, then ask the user to specify it first
        8. Commit

8. Enhance or rewrite README.md
    - Decide between enhancing and rewriting:
        - If the README.md is only the default file of the framework or super out-dated like more than 1 year, then entirely rewrite it.
        - Else, enhance README.md with the recent information. Concise and clear, no duplicate information.
        - The writing style of README.md should be the same as ux/ui writing style.
    - Good README.md should include these. Include two perspectives:
        - **Product Perspective**: What is this for?
            - Explaining features that this product has
                - If this is an IT product, focus on the end-user features.
                - If this is an API server, what kind of APIs it has, and explain size of each API.
                - If this is a reporting tool, focus on what kind of analysis it does, and which tool it uses.
                - You should decide what you should focus on. Don't write any confused/useless feature explanations.
        - **Technical Perspective**: How to get started from the scratch?
            - Tech
                - Tech stack
                - How to setup and start developing (including .env), and checking with my own eyes from scratch.
                - How to test, lint, and etc.
                - How is the structure of the codebase. If it follows standard of the framework, just only mention it, don't be detailed. If the previous coder made a lot of custom code, then explain the rules and the principles. (You can see previous git history to check this)
                - Deployment
            - Docs
                - Mention only necessary documents for human coders.
            - How to contribute
                - Don't mention 'forking', just the user can clone the repo and start developing from a new branch.
                - Encourage making PR than commiting directly to the main branch.
                - Write the previous git commit rules and pattern (by you looking it) if it's good.
                - Don't mention other ways to contribute that I didn't mention now.
            - Links
                - Useful links (documents) for the developers about this project.
            - License
                - If the repository owner is a company organization on GitHub, add that company's internal-only notice (e.g. "This project is <Company> internal only. Developers should delete local copies when leaving <Company>.")
        - Don't do this:
            - Don't mention every APIs, classes, and functions in the README.md. Just mention rules of them to understand it.

9. Look back your commits, and make sure everything isn't bad affecting or too much the codebase. If it is, fix and rewrite it.

10. Make sure there is no issue with building this codebase finally

11. Show detailed and visualistic response to the user using Emoji, Markdown Table, and lists
