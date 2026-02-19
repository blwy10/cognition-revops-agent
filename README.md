# Demo revops tool
- Generate and load data
- Run analysis (with optional scheduled runs)
- Change the threshold settings for Low, Medium, High severity of issues detected
- See previous runs and issues detected
- See the issues in a selected run

# Setup instructions
- Install Python 3.11 or higher
- Install dependencies: `pip3 install -r requirements.txt`
- Run the app: `python3 main.py`

# How to use
- In the "Data Generator" tab, click "Generate data" to generate sample data
  - You can also load existing data by clicking "Load Existing Data..."
- In the "Settings" tab, adjust the threshold settings for Low, Medium, and High severity issues
- In the "Run" tab, click "Run" to execute the rules and see the results
- In the "Previous Runs" tab, view all previous runs
- In the "Inbox" tab, see the issues in a selected run. You can also export a run's issues to a CSV file
- All settings are saved live i.e. the data you've loaded, threshold settings for rules, run history - if you restart the app it should pick up where you left off

# Architecture overview and key logic
- The app is built using Python + PySide6 for the GUI
- There are 3 components:
  - Data generation and loading (under `generator`)
  - Rule definition (under `rules`)
  - UI (under `app`)
- The generator has a single public function to generate data based on the provided schema
- Analysis / rules:
  - The rules are defined as instances of the `Rule` class. They draw settings from `RuleSettings`
  - Rules are a metric, a condition, and some prettifier functions to make display prettier (descriptions, explanations, etc.)
  - There are 4 kinds of rules:
    - Rules run on each opportunity e.g., stale opportunities
    - Rules run on each account e.g., accounts with no opportunities
    - Rules run on each rep e.g., reps with too many accounts
    - Rules run on all opportunities at once e.g., opportunity portfolio-wide early stage concentration
    - Rules run on all accounts at once e.g., duplicate accounts
  - Rules are executed in `run_tab.py`. The data is then passed into `AppState` which holds an in-memory version of all the runs and issues
  - Settings for rules are collected using widgets defined in `settings_tab.py`
  - New rules can be created by following the format of the rules in the `rules/default_rules` directory, and adding it to the right list in `run_tab.py`. If you want settings input for a rule, you can collect it by adding a new settings group in `settings_tab.py` - see the `_build_*` functions and where they're called in the main class constructor `__init__`
- `state.py` contains the main application state class as a singleton object

# Tradeoffs
- I used a local stack for faster development (traditional GUI app built in Python). This is easier to run and deploy locally, but not scalable for shared use, and is probably not aligned with the broader market of available engineering knowledge
- I used simplified territory assumptions - 1 territory per rep, 1 territory per account, 1 rep per account - to simplify my object model
- No concurrency by design, as there are not many data points and simplifies the code
- No metrics later, as there aren't many shared metrics right now and it simplifies the layers
- I use a number of singleton objects like `AppState` and `RuleSettings` to simplify data sharing - but this is brittle long term especially when moving to multiple parallel users

# What would I improve with more time
- Improve industry classification - currently it is flat and the generic BLS top-level classification
  - Why important: Better alignment with Cognition ICP
- Create a dedicated metrics later - currently all metrics are calculated within Rule objects
  - Why important: More scalable once I have duplicate metrics, and better separation of concerns and testability
- Concurrent rule execution - currently they run sequentially as there aren't many rules or data points to analyse
  - Why important: When the number of rules increase or the number of opportunities / accounts / reps, it will improve waiting time
- Improve the UI - currently it is functional but a bit ugly on the Mac
  - Why important: Makes it easier to onboard new colleagues and encourage people to use it
- Smarter saving behaviour - currently the app saves on every change, which is inefficient and prevents parallel use
  - Why important: When there are multiple users, it will prevent data loss and improve performance
- Migrate to a web-based stack for scalability - currently it is a local desktop GUI app
  - Why important: Enables multiple users, and easier to onboard new people

# Debugging approach and use of Windsurf
- The main way the app will break is if there is an issue with executing rules. In the terminal, it will print what exact file is there a break. All the rule files are in the `rules/default_rules` directory.
- Typical reason for a break is the data types not adhering to expectation e.g., amount is a text string rather than a number
- The largest bug I encountered was a state bug in the UI code
  - I needed to save the open / resolved etc. state of each issue in the table in the Inbox tab
  - However, that was also triggering a rebuild of the entire table (and resetting what the user is selecting) as the original UI update code (make the rows not bold, add a tick for resolved) was written by Windsurf / Cascade to rely on rebuilding the entire table
  - I resolved it by asking Windsurf to move the UI update to separate functions to decouple it from the data model rebuild and call it explicitly when needed
- My general approach to using Windsurf vs writing my own code / refactoring is:
  - Windsurf is used for:
    - Writing code docs
    - Writing boilerplate code e.g., PySide6 UI code, Python property boilerplate, settings management
    - Writing code that is not "critical" to performance e.g., data generation (the prompt was generated after a long conversation in ChatGPT, and then I did some minor adjustments by talking to Cascade)
    - Suggestions for UI fixes
    - Wiring in a new component that needed to be done in several places e.g., when I started incorporating the rule engine, I asked Windsurf to help me integrate it into the generated run function in several places
  - I wrote my own:
    - Critical code - the most important thing to design is the Rule system, so most of that was written by myself initially. Simpler rules like `NoOpps` can be done by Windsurf
    - Fine-tuning UI code was done by hand e.g., rearranging vertical sequencing of widgets