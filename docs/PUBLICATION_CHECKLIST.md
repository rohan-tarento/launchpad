# Publication checklist

Before pushing public changes to `launchpad`:

- [ ] No `.env` or real tokens in git
- [ ] No client PRDs, planning archives, or live work manifests
- [ ] No private org names in examples (`example-org` only)
- [ ] No MDC / `.cursor/rules` content — harness examples use placeholder `your-org/*-rules`
- [ ] No private repo lists (example-api, example-platform, example-org, etc.)
- [ ] `examples/tenant-meta/` contains structure only + `INIT-EXAMPLE-001.yaml`
- [ ] README states tenant vs kit separation
- [ ] `launchpad doctor` and `launchpad --help` work after `pip install -e .`
