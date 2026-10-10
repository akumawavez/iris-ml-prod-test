# Azure DevOps Skill

Full Azure DevOps integration for AI coding assistants -- 99 tools across 13 domains via REST API v7.1.

## Supported AI Clients

<p align="center">
  <a href="#claude-code"><img src="https://img.shields.io/badge/Claude_Code-D97757?style=for-the-badge&logo=anthropic&logoColor=white" alt="Claude Code" /></a>
  <a href="#gemini-cli--cursor--codex--goose"><img src="https://img.shields.io/badge/Gemini_CLI-8E75B2?style=for-the-badge&logo=google&logoColor=white" alt="Gemini CLI" /></a>
  <a href="#gemini-cli--cursor--codex--goose"><img src="https://img.shields.io/badge/Antigravity-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google Antigravity" /></a>
  <a href="#gemini-cli--cursor--codex--goose"><img src="https://img.shields.io/badge/Cursor-000000?style=for-the-badge&logo=cursor&logoColor=white" alt="Cursor" /></a>
  <a href="#gemini-cli--cursor--codex--goose"><img src="https://img.shields.io/badge/OpenAI_Codex-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI Codex" /></a>
  <a href="#gemini-cli--cursor--codex--goose"><img src="https://img.shields.io/badge/Goose-FF6B35?style=for-the-badge&logo=go&logoColor=white" alt="Goose" /></a>
</p>

## Features

- **13 domains**: Work Items, Repos & PRs, Pipelines, Wiki, Search, Test Plans, Security Alerts, Variable Groups, Environments & Approvals, Branch Policies, Attachments, Iterations & Capacity, Core
- **99 tools** via Azure DevOps REST API v7.1
- **OAuth** (device code flow) or **PAT** authentication
- **Secure credential storage** via system keyring (macOS Keychain, Windows Credential Locker, Linux Secret Service)

## Quick Install

### Claude Code

```bash
/plugin marketplace add sanjay3290/azure-devops-skill
```

### Gemini CLI / Cursor / Codex / Goose

```bash
npx skills add sanjay3290/azure-devops-skill
```

## Setup

### Prerequisites

```bash
pip install keyring
```

### Option 1: OAuth (Recommended)

Login with OAuth device code flow:

```bash
python scripts/auth.py login --org MyOrganization
```

Follow the URL and enter the device code to authorize. Tokens auto-refresh.

### Option 2: Personal Access Token (PAT)

```bash
python scripts/auth.py login --org MyOrganization --pat YOUR_PAT
```

Create a PAT at `https://dev.azure.com/{org}/_usersSettings/tokens` with these scopes:

| Scope | Access |
|-------|--------|
| Work Items | Read & Write |
| Code | Read & Write |
| Build | Read & Execute |
| Wiki | Read & Write |
| Test Management | Read & Write |
| Advanced Security | Read |
| Project and Team | Read |
| Identity | Read |

### Common Commands

```bash
# Check authentication status
python scripts/auth.py status

# Logout
python scripts/auth.py logout
```

## Usage Examples

```bash
# List all projects in your organization
python scripts/core.py list-projects

# Create a work item
python scripts/work_items.py create --project MyProject --type Bug --title "Fix login timeout"

# List open pull requests
python scripts/repos.py list-prs --project MyProject --repo my-repo

# Run a pipeline
python scripts/pipelines.py run --project MyProject --pipeline-id 5 --branch develop

# Search code across repos
python scripts/search.py code --project MyProject --query "connectionString"

# Get wiki page content
python scripts/wiki.py get-page-content --project MyProject --wiki-id MyProject.wiki --path /Home

# List pending deployment approvals
python scripts/environments.py list-approvals --project MyProject

# View security alerts
python scripts/security.py list-alerts --project MyProject --repo my-repo --severity high

# Manage variable groups
python scripts/variable_groups.py list --project MyProject

# List branch policies
python scripts/policies.py list --project MyProject --branch main
```

## All Commands

### Core (`scripts/core.py`)

| Command | Description |
|---------|-------------|
| `list-projects` | List all projects in the organization |
| `list-teams` | List teams in a project |
| `get-identity` | Search for a user identity |

### Work Items (`scripts/work_items.py`)

| Command | Description |
|---------|-------------|
| `get` | Get a work item by ID |
| `create` | Create a new work item |
| `update` | Update work item fields |
| `batch-get` | Get multiple work items at once |
| `add-children` | Add child work items to a parent |
| `link` | Link two work items together |
| `unlink` | Remove a link between work items |
| `add-comment` | Add a comment to a work item |
| `list-comments` | List comments on a work item |
| `get-revisions` | Get work item revision history |
| `list-types` | List available work item types |
| `my-items` | List work items assigned to you |
| `iteration-items` | List work items in an iteration |
| `list-backlogs` | List backlogs for a team |
| `list-queries` | List saved queries |
| `get-query` | Get a saved query by path |
| `run-query` | Run a saved query by ID |
| `run-wiql` | Run a WIQL query |
| `delete` | Delete a work item |
| `recycle-bin` | List deleted work items |

### Repos & PRs (`scripts/repos.py`)

| Command | Description |
|---------|-------------|
| `list` | List repositories in a project |
| `get` | Get repository details |
| `list-branches` | List branches |
| `create-branch` | Create a new branch |
| `search-commits` | Search commit history |
| `list-prs` | List pull requests |
| `create-pr` | Create a pull request |
| `get-pr` | Get pull request details |
| `update-pr` | Update a pull request |
| `list-reviewers` | List PR reviewers |
| `add-reviewer` | Add a reviewer to a PR |
| `list-threads` | List PR comment threads |
| `create-thread` | Create a PR comment thread |
| `add-thread-comment` | Reply to a PR comment thread |
| `complete-pr` | Complete (merge) a pull request |
| `abandon-pr` | Abandon a pull request |
| `get-diff` | Get diff between branches |
| `list-files` | Browse repository files |

### Iterations & Capacity (`scripts/work.py`)

| Command | Description |
|---------|-------------|
| `list-iterations` | List iterations (sprints) |
| `create-iteration` | Create a new iteration |
| `get-iteration` | Get iteration details |
| `team-iterations` | List team iterations by timeframe |
| `assign-iteration` | Assign an iteration to a team |
| `get-capacities` | Get team capacities for an iteration |
| `set-capacity` | Set a team member's capacity |

### Pipelines & Builds (`scripts/pipelines.py`)

| Command | Description |
|---------|-------------|
| `create` | Create a pipeline definition |
| `list-builds` | List builds with filters |
| `get-build` | Get build details |
| `build-logs` | Get build logs |
| `build-changes` | List changes in a build |
| `list-definitions` | List pipeline definitions |
| `run` | Run a pipeline |
| `get-run` | Get pipeline run details |
| `list-runs` | List pipeline runs |
| `update-stage` | Retry or skip a pipeline stage |
| `get-artifacts` | Get build artifacts |
| `queue-build` | Queue a new build |
| `cancel-build` | Cancel a running build |
| `build-status` | Get latest build status |

### Search (`scripts/search.py`)

| Command | Description |
|---------|-------------|
| `code` | Search code across repositories |
| `wiki` | Search wiki pages |
| `work-items` | Search work items |

### Wiki (`scripts/wiki.py`)

| Command | Description |
|---------|-------------|
| `list` | List wikis in a project |
| `get` | Get wiki details |
| `list-pages` | List wiki pages |
| `get-page` | Get wiki page metadata |
| `get-page-content` | Get wiki page content |
| `create-or-update-page` | Create or update a wiki page |

### Test Plans (`scripts/test_plans.py`)

| Command | Description |
|---------|-------------|
| `list-plans` | List test plans |
| `get-plan` | Get test plan details |
| `create-plan` | Create a new test plan |
| `list-suites` | List test suites in a plan |
| `get-suite` | Get test suite details |
| `list-test-cases` | List test cases in a suite |
| `add-test-cases` | Add test cases to a suite |
| `list-results` | List test run results |
| `get-result` | Get a specific test result |

### Security Alerts (`scripts/security.py`)

| Command | Description |
|---------|-------------|
| `list-alerts` | List security alerts (filter by state, severity, type) |
| `get-alert` | Get alert details |

### Variable Groups (`scripts/variable_groups.py`)

| Command | Description |
|---------|-------------|
| `list` | List variable groups |
| `get` | Get a variable group |
| `create` | Create a variable group |
| `update` | Update a variable group |
| `add-variable` | Add or update a single variable (supports secrets) |
| `remove-variable` | Remove a variable from a group |
| `delete` | Delete a variable group |

### Environments & Approvals (`scripts/environments.py`)

| Command | Description |
|---------|-------------|
| `list` | List environments |
| `create` | Create an environment |
| `get` | Get environment details |
| `list-checks` | List checks/approvals on an environment |
| `list-approvals` | List pending approvals |
| `approve` | Approve a deployment |
| `reject` | Reject a deployment |
| `delete` | Delete an environment |

### Branch Policies (`scripts/policies.py`)

| Command | Description |
|---------|-------------|
| `list` | List policies (filter by branch/repo) |
| `get` | Get a policy by ID |
| `list-types` | List available policy types |
| `create-min-reviewers` | Create minimum reviewers policy |
| `create-build-policy` | Create build validation policy |
| `update` | Update a policy (enable/disable/blocking) |
| `list-evaluations` | List policy evaluations for a PR |
| `delete` | Delete a policy |

### Attachments (`scripts/attachments.py`)

| Command | Description |
|---------|-------------|
| `upload` | Upload a file |
| `attach` | Attach an uploaded file to a work item |
| `upload-and-attach` | Upload and attach in one step |
| `list` | List attachments on a work item |
| `download` | Download an attachment |
| `remove` | Remove an attachment from a work item |

## Common Work Item Fields

| Field | Reference Name |
|-------|---------------|
| Title | `System.Title` |
| State | `System.State` |
| Assigned To | `System.AssignedTo` |
| Description | `System.Description` |
| Area Path | `System.AreaPath` |
| Iteration Path | `System.IterationPath` |
| Priority | `Microsoft.VSTS.Common.Priority` |
| Story Points | `Microsoft.VSTS.Scheduling.StoryPoints` |
| Tags | `System.Tags` |

## Token Management

Credentials are stored securely using the system keyring:

| Platform | Backend |
|----------|---------|
| macOS | Keychain |
| Windows | Windows Credential Locker |
| Linux | Secret Service API |

Service name: `azure-devops-skill`

## Part of AI Skills Collection

This skill is also available in the [ai-skills](https://github.com/sanjay3290/ai-skills) collection with 20+ other skills for databases, Google Workspace, research, media generation, and more.

## License

Apache-2.0
