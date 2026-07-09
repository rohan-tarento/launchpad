# Publication checklist (v0.5.11)

Before pushing public changes to `launchpad`:

- [ ] No `.env` or real tokens in git
- [ ] No client PRDs, planning archives, or live work manifests
- [ ] No private org names in examples (`example-org` only)
- [ ] Harness examples reference public `drivestream-lab/*-rules` (not tenant-specific placeholders)
- [ ] No private repo lists — only `example-api`, `example-platform`, etc.
- [ ] `examples/tenant-meta/config/` uses 5-YAML model (`programme.yaml`, `governance-example-org.yaml`, `harness-example-org.yaml`, `scaffold-example-org.yaml`, `service-catalog-example-org.yaml`)
- [ ] `examples/tenant-meta/` contains structure only + `INIT-EXAMPLE-001.yaml`
- [ ] README states tenant vs kit separation and v0.5.11
- [ ] `launchpad --version` and `launchpad --help` work after `pip install .`
- [ ] `launchpad doctor` exits 0 with a valid `programme.yaml` and `GITHUB_TOKEN`
- [ ] `pytest tests/test_schema.py` passes (36 tests, no network required)
- [ ] Example config validates: `load_programme / load_governance / load_harness / load_scaffold / load_catalog` against `examples/tenant-meta/config/`
- [ ] `scripts/smoke-local.sh` exits 0 (dry-run only, no PAT required)
- [ ] CI (`ci.yml`) passes on `main` and `develop`
- [ ] No GitLab-specific commands in public CLI (`launchpad --help` output)
- [ ] `.launchpad-version` in `examples/tenant-meta/` matches `pyproject.toml` version
