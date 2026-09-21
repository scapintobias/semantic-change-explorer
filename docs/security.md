<!-- @format -->

# Security boundary

No files leave your computer. Selected files are transferred only to the local loopback service, processed locally in a temporary workspace, and removed after processing. There is no account, telemetry or remote application backend. Reports use bundled assets and a loopback static server. These facts do not make Blender a sandbox.

## Input execution

The host uses an argument array with `subprocess.run`, never shell interpolation. The command starts Blender with `--background --factory-startup --disable-autoexec` **before** the source path. The installed Blender 4.4 `--help` was inspected to verify flag spelling and semantics. `--python-exit-code 3` makes an extractor exception observable. The explicit Python script is trusted repository code, not a text block read from the file. The extractor also refuses to run if the auto-execution preference is enabled. A registered text-block sentinel is included in generated fixtures and the integration test verifies that its marker is not created.

Blender's [security manual](https://docs.blender.org/UATEST/manual/en/dev/advanced/scripting/security.html) identifies registered text blocks and Python drivers as auto-execution paths; manually running scripts and Freestyle rendering are separate paths. This extractor does neither. Blender's [driver documentation](https://docs.blender.org/manual/vi/2.83/animation/drivers/drivers_panel.html) explains that simple restricted expressions can evaluate even when Python script execution is disabled. Therefore `--disable-autoexec` is not a promise that every expression is inert. Evaluated output may differ from a trusted session needing unrestricted drivers.

Blender still parses a complex native file, evaluates native modifiers and can read linked resources. Native-code vulnerabilities, memory exhaustion, dangerous caches and OS-level resource access are outside this control. There is a 300-second subprocess timeout; no memory cap, container, seccomp profile or network-denial sandbox is supplied. Use OS isolation for genuinely untrusted assets. Do not claim perfect sandboxing.

## File and resource handling

Source paths are resolved and passed literally. The extractor contains no save call. Hashes before/after detect changed input bytes; concurrent edits can cause a failure but are not prevented by a file lock. Both sources run in separate processes. Temporary output uses a unique directory; a report is published only after extraction and generation succeed. Existing report/snapshot output paths are refused. The output directory must not be either source path. Preview mesh copies and extra IDs exist only in memory.

Linked libraries and external files may be read by Blender. Provenance names linked libraries but does not fingerprint their contents. A file SHA identifies the `.blend` bytes only. Preview export replaces source materials with untextured solid colors to avoid texture dependencies in the report. This does not prevent Blender itself reading resources while loading/evaluating.

## Browser and server

The server binds `127.0.0.1`, denies directory listings and resolved symlink escapes, and emits a same-origin Content Security Policy and nosniff. It is a local development server, not an authenticated production service. Other local processes can read reports. JSON is fetched as data; React escapes source-derived names/values and no raw HTML injection is used. GLTFLoader's URL modifier rejects remote resource origins; the CSP additionally blocks external connections. Generated GLBs embed their resources. The browser test observes requests and rejects off-origin traffic.

Reports contain geometry, names, custom properties and other source-derived data. Local-only computation does not make a report non-confidential. Share deliberately. Third-party report content is not equivalent to a trusted generated report; do not host arbitrary executable HTML under this server and assume it is sanitized.

The development execution environment required running Blender outside its filesystem sandbox because Metal initialization crashed inside it. That local testing workaround is recorded; it does not add isolation to the shipped product.
