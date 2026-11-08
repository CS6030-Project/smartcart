# SmartCart: GitHub Organization, SSH, Git and First CI Run (macOS)

This guide assumes a new, empty GitHub organization repository. The files are already prepared in `SmartCart_Starter.zip`; the organization and repository must still be created in your own GitHub account.

## Step 1 - Check your Mac tools

1. Open **Terminal** (Command + Space, type `Terminal`).
2. Run:

```bash
git --version
python3 --version
java -version
```

- If Git is missing, run `xcode-select --install`, follow the Apple pop-up, then run `git --version` again.
- Python 3 is needed for the JSON example tests. If it is missing, install Python 3 from [python.org](https://www.python.org/downloads/macos/) or your existing package manager.
- Java 21 is needed to run the small matching program **locally**. If Java is missing, you can still push the files. GitHub Actions will install Java 21 on its runner. You can install a JDK later.

## Step 2 - Configure your Git name and email

Replace these with the name and email associated with your GitHub profile:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
git config --global --get user.name
git config --global --get user.email
```

This sets the author information for Git commits. You can use GitHub's noreply email if you prefer to keep your personal email private.

## Step 3 - Check SSH access

```bash
ls -al ~/.ssh
ssh -T git@github.com
```

If the last command already replies `Hi YOUR_USERNAME! You've successfully authenticated...`, SSH is working. Skip to Step 4.

If not, check for an existing SSH key you already use. **Do not overwrite a working private key.** If you don't have one, generate a key:

```bash
ssh-keygen -t ed25519 -C "your-github-email@example.com"
```

At the filename prompt, press Enter to accept `~/.ssh/id_ed25519` **only if it does not exist**. Choose a passphrase. (When prompted to type a passphrase, the Terminal will not show characters.)

Next:

```bash
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
pbcopy < ~/.ssh/id_ed25519.pub
```

If `ssh-add` says `illegal option -- apple-use-keychain`, use `ssh-add ~/.ssh/id_ed25519` instead.

1. In Chrome go to [GitHub SSH settings](https://github.com/settings/keys).
2. Click **New SSH key**.
3. Title: `Mac - SmartCart`.
4. Key type: `Authentication Key`.
5. Paste the copied **public** key (it starts with `ssh-ed25519`).
6. Save. Never paste or share the **private** key file (without `.pub`).

Now check:

```bash
ssh -T git@github.com
```

The expected result is a friendly `Hi YOUR_USERNAME!` authentication message (GitHub does not provide shell access). If SSH asks to trust GitHub's server for the first time, verify the host fingerprint against GitHub's published fingerprints before typing `yes`.

## Step 4 - Create the free organization

1. Sign in to [github.com](https://github.com).
2. Profile picture (top right) -> **Settings** -> **Organizations** -> **New organization**.
3. Choose **GitHub Free**.
4. Organization name: `CS6030-Project`, if it is available and under your control. Otherwise choose a unique project name.
5. Complete the contact-email/verification steps.

An organization is a shared container for repositories and teams. **It is not the repository itself.**

## Step 5 - Create one private repository inside the organization

1. Open [New repository](https://github.com/new).
2. Set **Owner** to `CS6030-Project` (or the exact organization name you created).
3. Repository name: `smartcart`.
4. Description: `Explainable cross-retailer product matching | WMU CS6030 Fall 2026`.
5. Select **Private**.
6. Do **not** check `Add a README`, `.gitignore`, or license. The starter files contain them.
7. Click **Create repository**.

The expected address is `https://github.com/CS6030-Project/smartcart` (only if you used those exact names).

## Step 6 - Download and unpack the starter ZIP

Save `SmartCart_Starter.zip` from this chat to **Downloads**. In Terminal:

```bash
mkdir -p ~/Documents/WMU-CS6030
cd ~/Documents/WMU-CS6030
unzip ~/Downloads/SmartCart_Starter.zip
mv SmartCart_Starter smartcart
cd smartcart
pwd
ls -la
```

You should see `README.md`, `.github/`, `backend/`, `contracts/`, `docs/`, and `scripts/`. `ls -la` includes hidden folders like `.github`.

If you already have a folder named `smartcart`, do not overwrite it; choose a new folder and copy files carefully.

## Step 7 - Run the starter tests locally

```bash
python3 -m unittest discover -s tests -v
```

Expected: `Ran 2 tests` and `OK`.

If `javac` (Java compiler) is installed, also run:

```bash
bash scripts/check.sh
```

Expected: five Java matching checks plus the two JSON tests pass. If Java is not installed locally, the CI workflow will test it in GitHub after your first push.

These are **starter** tests: they do not mean a Chrome extension, Spring Boot API, or cloud deployment is running.

## Step 8 - Make the first Git commit and upload it

From the `smartcart` folder:

```bash
git init -b main
git status --short
git add .
git commit -m "chore: initialize SmartCart team project"
git remote add origin git@github.com:CS6030-Project/smartcart.git
git push -u origin main
```

If you used a different organization or repository name, change that in `git remote add origin`.

**What the commands mean:**
- `git init -b main`: begin local version tracking using the `main` branch.
- `git add .`: stage files for the commit.
- `git commit`: record the starting version.
- `git remote add origin`: connect your local folder to GitHub.
- `git push`: upload your commits.

If you accidentally created the GitHub repository with a README, follow a safer merge/clone path rather than using `git push --force`.

## Step 9 - Confirm the first CI workflow

1. Open your new repository on github.com.
2. Click **Actions**.
3. Open **Starter CI**.
4. The `push` should trigger a workflow automatically. If it does not appear, inspect organization/repository Actions settings and whether the workflow is under `.github/workflows/starter-ci.yml` on `main`.
5. When the check finishes, you want a **green check**.
6. Click the job and read the logs. You should see Java matching and Python JSON tests.
7. You can also run it through **Actions -> Starter CI -> Run workflow** because this file has `workflow_dispatch`.

A green check is real evidence of the starting **continuous integration** setup. This workflow does **not** deploy to GCP or Azure. That comes later, after cloud infrastructure and credentials are configured.

## Step 10 - Invite Aayush and Diego

1. Organization page -> **People** -> **Invite member**.
2. Invite each teammate by GitHub username or their verified GitHub email.
3. Ask them to accept the invitation.
4. In the private repo, open **Settings -> Collaborators and teams**, then grant each person **Write** access if organization membership has not already granted the needed access. (UI wording may vary.)
5. Keep the organization Owner role limited to people who need to manage organization settings.

## Step 11 - Create the first tasks

Under repository **Issues**, create:
- Agree on comparison API fields (Aayush, review with Diego/Rishikesh).
- Extract a supported product page (Diego).
- Select and validate initial product fixture data (Rishikesh).
- Convert Java matcher baseline into Spring Boot API (Aayush).
- Set up frontend shell and API request display (Diego).
- Start PostgreSQL and plan GCP/Azure IaC (Rishikesh).

Later: use Projects board, pull requests, and GitHub Actions for each component.

## Step 12 - Record actual progress in the midterm report

Once your GitHub repo exists and the green workflow has run, you can update the report status to:

> The team created its shared GitHub repository at [actual URL], committed a starter monorepo and initial Java matching example, and configured a GitHub Actions workflow. The starter Java and JSON tests passed in GitHub Actions. The next phase is the full Spring Boot API, Chrome extension, database integration, and cloud deployment.

**Only say these things after you have verified them in your repository.** Keep the current PDF wording until then.

## Quick troubleshooting

- `git: command not found`: run `xcode-select --install`.
- `Permission denied (publickey)`: your SSH key is not added to GitHub, has not been loaded, or GitHub is using a different key. Retry Steps 3 and 8; never share your private key.
- `Repository not found`: check organization/repo spelling, repo creation, and your access.
- `fatal: remote origin already exists`: run `git remote -v` and use `git remote set-url origin git@github.com:...` if it is the wrong URL.
- `failed to push some refs`: do **not** use force push. Check whether the remote is truly empty and whether someone has added commits; pull/reconcile safely.
- Red GitHub Actions check: click the failed step, read the error, and fix it in a new commit. A workflow file existing does not by itself prove CI passes.
