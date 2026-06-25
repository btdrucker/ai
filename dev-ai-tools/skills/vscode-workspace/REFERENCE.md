# Workspace Management -- Reference

Detailed reference content for the `vscode-workspace` skill.

## Registry generation

The registry file `workspace-registry.json` lives in the same directory as
the `.code-workspace` file. It catalogs ALL cloned repos, not just active ones.

For each cloned repo in the target directory (scan the filesystem, not the
workspace file), run in parallel:

```bash
git -C <path> remote get-url origin
git -C <path> remote show origin | grep 'HEAD branch' | awk '{print $NF}'
```

- Parse `owner/repo` from the remote URL for the `github` field
- Use the HEAD branch output for the `defaultBranch` field
- Determine `type`:
  - Repo name matches `search.lambda.*` -> `lambda`
  - Has `build.gradle` or `pom.xml` -> `service`
  - Has `template.yaml` or `template.yml` -> `lambda`
  - Is the dev-ai-tools repo -> `tooling`
  - Otherwise -> `unknown`
- Determine `role`:
  - `search.service.*`, `search.server.*`, `search.web.*`, `search.lambda.*`,
    `gcde.service.*` -> `"project"`
  - The dev-ai-tools repo -> `"tooling"`
  - Otherwise -> `"misc"`

Write `workspace-registry.json`:

```json
{
  "generated": "<ISO 8601 timestamp>",
  "repos": {
    "<short-name>": {
      "path": "/absolute/path/to/repo",
      "github": "owner/repo",
      "defaultBranch": "master",
      "type": "service",
      "role": "project"
    }
  }
}
```

Keys use the base name (e.g. `kingpin-v1`, not `kingpin-v1 (service)`).

Registry generation runs in bootstrap, update, and after focus/add/remove if
new repos were cloned. It scans the filesystem so it always reflects the full
set of cloned repos.

## Java/Gradle project setup

After any operation that activates repos (bootstrap with focus, focus, add),
run this setup for each newly activated repo that contains a `build.gradle`
or `pom.xml` file. This ensures the Java Language Server can resolve types
and dependencies.

### Step J0: SDKMAN setup (optional)

Check if SDKMAN is installed:

```bash
ls ~/.sdkman/bin/sdkman-init.sh 2>/dev/null
```

If detected, read and follow the `sdkman` skill to:

- Detect the required Java version from build files
- Install the JDK if missing
- Create `.sdkmanrc` in the project root
- Add `.sdkmanrc` to `.gitignore`
- Activate the correct version

Use the `jdkHomePath` returned by the sdkman skill for the remaining
steps. If SDKMAN is not installed, fall back to detecting JDKs manually
(see step J1).

### Step J1: Detect required JDK version

Determine which Java version the project needs:

1. Check `build.gradle` for `toolchain { languageVersion }` (e.g.
   `JavaLanguageVersion.of(21)`) -- this is the authoritative source
2. Check `build.gradle` for `sourceCompatibility` (e.g. `JavaVersion.VERSION_11`)
3. Check `pom.xml` for `<maven.compiler.source>` or `<java.version>`
4. Fall back to the major version from `java -version`

Resolve the JDK home path. List installed JDKs:

```bash
ls ~/.sdkman/candidates/java/
```

**macOS JDK paths:** Amazon Corretto JDKs on macOS have the actual JDK under
`Contents/Home/`. Verify the correct path:

```bash
# Java 11 (flat structure):  ~/.sdkman/candidates/java/11.x.y-amzn/bin/java
# Java 17+ (macOS bundle):   ~/.sdkman/candidates/java/21.x.y-amzn/Contents/Home/bin/java
```

Test with `<path>/bin/java -version` to confirm.

### Step J2: Run `./gradlew eclipse` (if plugin available)

Check if the project's `build.gradle` applies the `eclipse` plugin. If so:

```bash
cd <repo-path> && ./gradlew eclipse
```

This generates `.classpath`, `.project`, and `.settings/` files that the JDT
Language Server needs to understand source roots and resolve dependencies.

If the project does not have the `eclipse` plugin (e.g. only has `idea`),
skip this step -- the JDT Language Server can import Gradle projects directly
when `java.import.gradle.enabled` is true.

**SSL certificate errors when downloading Gradle wrapper:** Corporate proxies
may intercept SSL, causing `SSLHandshakeException` / `PKIX path building
failed` with freshly installed JDKs. Workaround:

1. Use an older JDK (e.g. Java 11) that already has certs to download the
   Gradle distribution: `JAVA_HOME=<java-11-path> ./gradlew eclipse`
2. Once the Gradle distribution is cached in `~/.gradle/wrapper/dists/`, run
   again with the required JDK -- it won't re-download.

This step requires network access to the artifact repository (e.g.
`artifactory.nike.com`). If it fails due to network issues, warn the user
they may need VPN and note they can re-run this later.

### Step J3: Configure workspace and project JDK settings

The Java Language Server runs as a single process on one JDK but can compile
projects targeting different Java versions using `java.configuration.runtimes`.

**Workspace-level settings** (in `.code-workspace` file):

- Set `java.jdt.ls.java.home` to the **highest** installed JDK -- the
  language server is backward compatible.
- List **all** installed JDKs in `java.configuration.runtimes` so the LS
  auto-selects the correct one per project based on source compatibility.
- Set the highest version as `"default": true`.
- Do NOT set `java.import.gradle.java.home` at the workspace level -- it
  prevents per-project overrides from working.
- Set `spring-boot.ls.java.home` to the same JDK as `java.jdt.ls.java.home`
  -- the Spring Boot Tools extension runs its own language server with its
  own JDK. Without this, it may use an embedded JRE that lacks corporate
  CA certificates.

```json
{
  "java.jdt.ls.java.home": "<highest-jdk-path>",
  "spring-boot.ls.java.home": "<highest-jdk-path>",
  "java.configuration.runtimes": [
    {
      "name": "JavaSE-11",
      "path": "<java-11-path>"
    },
    {
      "name": "JavaSE-21",
      "path": "<java-21-path>",
      "default": true
    }
  ]
}
```

**Per-project settings** (in `<repo-path>/.vscode/settings.json`):

Create per-project settings for each activated repo with the project's
required JDK:

```json
{
  "java.import.gradle.java.home": "<project-jdk-path>",
  "java.import.gradle.enabled": true
}
```

Do not duplicate `java.jdt.ls.java.home` or `java.configuration.runtimes`
in per-project settings -- those are workspace-wide since there is only one
language server process.

If the file already exists, merge the java settings without overwriting other
settings.

### Step J4: Ensure `.gitignore` coverage

Check the repo's `.gitignore` for these entries and append any that are
missing:

```
# Cursor / VS Code
.vscode/

# Eclipse (generated by ./gradlew eclipse)
.classpath
.project
```

Skip entries already covered (e.g. `.settings/` is often already present in
Java `.gitignore` templates). Do not duplicate existing entries.

### Step J5: Prompt language server reload

After setup, tell the user:

> Gradle project configured. Run **Java: Clean Language Server Workspace**
> (`Cmd+Shift+P` / `Ctrl+Shift+P`) and choose **Restart and delete** to pick up the changes.
