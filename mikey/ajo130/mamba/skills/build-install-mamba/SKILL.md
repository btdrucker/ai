---
name: build-install-mamba
description: >-
  Build the Mamba Android app and install it on a connected device or emulator.
  Use when the user says "build mamba", "install mamba", "deploy mamba",
  "build and install", "run the app on device", or needs the app freshly
  installed before testing or verification.
---

# Build & Install Mamba Android

## Workflow

### 1. Discover the target device

Use the `mobile_list_available_devices` MCP tool (user-mobile-mcp server).
If multiple devices are returned, ask the user to pick one.

### 2. Build the APK

Run from the **mpe.app.mamba-android** project root:

```bash
./gradlew :app:assembleWorldDebug
```

The default build variant is `worldDebug` (flavor=world, buildType=debug).

If the user requests a different variant, map it:

| Variant | Command |
|---------|---------|
| worldDebug (default) | `./gradlew :app:assembleWorldDebug` |
| worldRelease | `./gradlew :app:assembleWorldRelease` |
| chinaDebug | `./gradlew :app:assembleChinaDebug` |
| chinaRelease | `./gradlew :app:assembleChinaRelease` |

Wait for the build to complete. If it fails, report the error and stop.

### 3. Locate the APK

After a successful build, the APK is at:

```
app/build/outputs/apk/world/debug/app-world-debug.apk
```

Adjust the path for other variants: `app/build/outputs/apk/{flavor}/{buildType}/app-{flavor}-{buildType}.apk`

### 4. Install on device

Use the `mobile_install_app` MCP tool:

- `device`: the device id from step 1
- `path`: absolute path to the APK from step 3

### 5. Report result

Confirm to the user:
- Build variant used
- Device name and id where the app was installed
- That the app is ready for use

## Important Notes

- Package name: `com.nike.app.mamba`
- NEVER use `adb install` directly — always use the `mobile_install_app` MCP tool.
- The build can take several minutes. Use `block_until_ms` of at least 300000 (5 min) when running Gradle.
- If the user hasn't specified a variant, default to `worldDebug`.
