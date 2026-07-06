# Publication checklist

Before pushing public changes to `launchpad`:

- [x] No `.env` or real tokens in git
- [x] No client PRDs, planning archives, or live work manifests
- [x] No private org names in examples (`example-org` only)
- [x] Harness examples reference public `drivestream-lab/*-rules` (not tenant-specific placeholders)
- [x] No private repo lists (example-api, example-platform, example-org, etc.)
- [x] `examples/tenant-meta/` contains structure only + `INIT-EXAMPLE-001.yaml`
- [x] README states tenant vs kit separation
- [x] `launchpad doctor` and `launchpad --help` work after `pip install -e .`
