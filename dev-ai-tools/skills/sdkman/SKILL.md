---
name: sdkman
description: >
  Manage JDK versions with SDKMAN. Detects the required Java version from
  build.gradle or pom.xml, installs missing JDKs, creates .sdkmanrc, adds
  .sdkmanrc to .gitignore, and activates the correct version. Use when
  setting up Java for a project, switching JDK versions, or when another
  skill needs SDKMAN operations.
---

# SDKMAN

Manages JDK versions per project using SDKMAN and `.sdkmanrc`.

## Prerequisites

```bash
source ~/.sdkman/bin/sdkman-init.sh && sdk version
```

If missing, tell the user to install from https://sdkman.io and stop.

## Step 1: Detect required Java version

Check the project root in this order:

1. **`build.gradle` toolchain** -- `JavaLanguageVersion.of(<N>)`
2. **`build.gradle` sourceCompatibility** --
   `sourceCompatibility = JavaVersion.VERSION_<N>` or `'<N>'`
3. **`pom.xml`** -- `<maven.compiler.source>` or `<java.version>`
4. **`.sdkmanrc`** -- if it already exists, read the version from it

If none found, ask the user.

## Step 2: Resolve installed candidate

```bash
ls ~/.sdkman/candidates/java/
```

Match the detected major version (e.g. `11` -> `11.*-amzn`). If multiple
builds of the same major version exist, use the highest patch.

**macOS JDK paths:** Amazon Corretto JDKs on macOS have the actual JDK
under `Contents/Home/` for Java 17+. Verify the correct home path:

```bash
# Java 11 (flat):   ~/.sdkman/candidates/java/11.x.y-amzn/bin/java
# Java 17+ (macOS): ~/.sdkman/candidates/java/21.x.y-amzn/Contents/Home/bin/java
```

Test with `<path>/bin/java -version` to confirm.

## Step 3: Install if missing

If the required major version is not installed:

```bash
source ~/.sdkman/bin/sdkman-init.sh
sdk install java <version>-amzn
```

Use `amzn` (Amazon Corretto) as the default distribution. If it fails,
try without a vendor suffix and let SDKMAN pick the default.

**SDKMAN may fail silently on macOS.** If the download completes but
the JDK directory is not created, manually extract:

```bash
mkdir -p ~/.sdkman/candidates/java/<version>-amzn
tar xzf ~/.sdkman/tmp/java-<version>-amzn.bin \
  -C ~/.sdkman/candidates/java/<version>-amzn --strip-components=1
```

## Step 4: Import Nike corporate CA certificates

After installing a JDK, check if it has Nike's CA certs:

```bash
<jdk-path>/bin/keytool -list -keystore <jdk-path>/lib/security/cacerts \
  -storepass changeit 2>/dev/null | grep -i nike
```

If no `nike` entries are found, import them. Nike uses GlobalProtect
(Palo Alto Networks) for SSL inspection. Two certs are needed:

| Certificate | Purpose |
|---|---|
| **Nike Root Authority NG** | Trusts Nike internal servers (artifactory.nike.com, etc.) |
| **Nike Forward Trust ECDSA CA** | Trusts GlobalProtect's SSL-inspected external traffic |

Extract from the macOS Keychain and a live connection:

```bash
security find-certificate -c "Nike Root Authority NG" -p > /tmp/nike-root.pem

echo | openssl s_client -showcerts -connect dl.google.com:443 2>/dev/null \
  | sed -n '/BEGIN CERTIFICATE/,/END CERTIFICATE/p' > /tmp/nike-forward-trust.pem
```

Import into the JDK truststore:

```bash
<jdk-path>/bin/keytool -importcert -alias nike-root-authority-ng \
  -file /tmp/nike-root.pem \
  -keystore <jdk-path>/lib/security/cacerts \
  -storepass changeit -noprompt

<jdk-path>/bin/keytool -importcert -alias nike-forward-trust-ecdsa \
  -file /tmp/nike-forward-trust.pem \
  -keystore <jdk-path>/lib/security/cacerts \
  -storepass changeit -noprompt
```

Run this for **every** installed JDK that is missing the certs, not just
the one the current project uses. The language server may run on a
different JDK than the project.

## Step 5: Create or update `.sdkmanrc`

If `.sdkmanrc` does not exist in the project root, create it:

```
# SDKMAN environment
java=<full-candidate-version>
```

`<full-candidate-version>` is the directory name under
`~/.sdkman/candidates/java/` (e.g. `11.0.31-amzn`).

If `.sdkmanrc` exists and the version differs, update it.

## Step 6: Update `.gitignore`

Check the project's `.gitignore` for `.sdkmanrc`. If missing, append:

```
# SDKMAN
.sdkmanrc
```

Do not duplicate existing entries.

## Step 7: Activate

```bash
source ~/.sdkman/bin/sdkman-init.sh && sdk env
```

Verify:

```bash
java -version
```

Confirm the major version matches the project requirement.

## Step 8: Report

Tell the user which version was activated and what files were
created/updated.

## Return values for calling skills

When invoked by another skill (e.g. `vscode-workspace`), return:

- `javaVersion` -- the major version (e.g. `11`, `21`)
- `candidateVersion` -- the full SDKMAN candidate (e.g. `11.0.31-amzn`)
- `jdkHomePath` -- the resolved JDK home path
- `sdkmanrcCreated` -- whether `.sdkmanrc` was created or updated
