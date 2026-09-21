# Security

Only the current v0.1 development line receives fixes. This tool starts Blender to parse files; disabling embedded auto-execution is defense in depth, not an OS sandbox. Read [the security model](docs/security.md) before processing untrusted assets.

The repository is currently private. Authorized collaborators can report concerns through its [private issue tracker](https://github.com/scapintobias/semantic-change-explorer/issues). Do not attach secrets, private geometry or malicious files; describe a sanitized reproduction first. Before changing repository visibility to public, configure GitHub private vulnerability reporting and replace this reporting route.

A useful report includes the tested tool/Blender/OS versions, affected command, expected boundary, sanitized reproduction and impact. We cannot promise a response SLA before maintainers and channels exist.
