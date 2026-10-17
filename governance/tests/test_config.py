import importlib.util
import pathlib

_s = importlib.util.spec_from_file_location("config", pathlib.Path(__file__).resolve().parent.parent / "config.py")
cfg = importlib.util.module_from_spec(_s)
_s.loader.exec_module(cfg)
ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_brand_file_values_and_environment_overrides(tmp_path):
    f = tmp_path / "brand.env"
    f.write_text("# comment\nBRAND_NAME=Acme\nSITE_DOMAIN=acme.example  # trailing note\n")
    v = cfg.load(f, environ={"SITE_DOMAIN": "other.example"})
    assert v["BRAND_NAME"] == ("Acme", "brand.env") and v["SITE_DOMAIN"] == ("other.example", "environment")
    assert v["CONTACT_EMAIL"] == ("", "default")                         # optional: absent is fine


def test_no_brand_file_means_neutral_defaults(tmp_path):
    v = cfg.values(path=tmp_path / "missing.env", environ={})
    assert v["PRODUCT_NAME"] == "SecuRAX" and v["SITE_DOMAIN"] == "" and v["BRAND_NAME"] == ""


def test_integrations_are_switched_like_requirements_txt(tmp_path):
    f = tmp_path / "integrations.txt"
    f.write_text("# header\ntailscale   # phones\n# ntfy\ncron\n")
    assert cfg.integrations(f) == {"tailscale", "cron"}
    assert cfg.enabled("tailscale", f) and not cfg.enabled("ntfy", f)
    assert cfg.enabled("ntfy", tmp_path / "none.txt")                    # no file at all = everything on, as before


def test_render_fills_placeholders_and_leaves_unknown_ones():
    out = cfg.render("mail {{ CONTACT_EMAIL }} at {{SITE_DOMAIN}} {{NOPE}}", {"CONTACT_EMAIL": "a@b.co", "SITE_DOMAIN": "b.co"})
    assert out == "mail a@b.co at b.co {{NOPE}}"


def test_check_finds_hardwired_values_vendors_and_bad_config():
    vals = {"BRAND_NAME": "Acme", "SITE_DOMAIN": "acme.example", "CONTACT_EMAIL": "not-an-email", "REPO_SLUG": "x/y"}
    files = {"app/x.py": "URL = 'https://acme.example/'", "docs/x.md": "acme.example is fine in docs",
             "tools/dns.sh": "# uses namecheap api", "brand.env": "SITE_DOMAIN=acme.example"}
    probs = cfg.problems(vals, list(files), read=files.__getitem__, on={"tailscale", "carrier-pigeon"})
    assert any("app/x.py" in p and "SITE_DOMAIN" in p for p in probs)
    assert any("tools/dns.sh" in p and "namecheap" in p for p in probs)
    assert any("CONTACT_EMAIL" in p and "not an e-mail" in p for p in probs) and any("carrier-pigeon" in p for p in probs)
    assert not any("docs/x.md" in p or "hardwired" in p and p.startswith("brand.env") for p in probs)   # docs + the file itself may name them


def test_the_real_repository_is_clean_and_the_site_renders_completely():
    vals = cfg.values()
    assert cfg.problems(vals, cfg.tracked_files(), on=cfg.integrations() or set()) == []
    for page in ["website/index.html", "website/personal/index.html", "website/assess/index.html", "website/assess/assess.js"]:
        out = cfg.render((ROOT / page).read_text("utf-8"), vals)
        assert "{{CONTACT_EMAIL}}" not in out and "{{SITE_DOMAIN}}" not in out and "{{BRAND_NAME}}" not in out, page
