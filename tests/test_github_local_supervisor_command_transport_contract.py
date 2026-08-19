from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / ".github" / "workflows" / "dispatch-local-supervisor-command-oda.yml"
INSTALL = ROOT / ".github" / "workflows" / "install-openworkerctl-oda.yml"
CTL = ROOT / "go-runtime" / "cmd" / "openworkerctl" / "main.go"


def test_dispatch_is_fixed_oda_transport_only_contract():
    text = DISPATCH.read_text(encoding="utf-8")

    assert "runs-on: [self-hosted, Windows, X64, ODA]" in text
    assert "DESKTOP-ODAQN0D" in text
    assert "timeout-minutes: 2" in text

    for command in ("supervisor_status", "case_status", "case_continue", "queue_clear"):
        assert f"- {command}" in text

    assert "openworkerctl.exe" in text
    assert "case','continue','0005" in text
    assert "queue','clear','DESKTOP-ODAQN0D" in text
    assert "github_action_used_for_command_transport=$true" in text
    assert "github_action_used_for_business_execution=$false" in text
    assert "Test-Accepted" in text
    assert "case_continue did not return accepted=true" in text

    # Transport workflow must not become an artifact or long-running business executor.
    forbidden = (
        "actions/upload-artifact",
        "SaveVideo",
        "blender",
        "comfyui",
        "presentation/storyboard-text-only.pptx",
        "drive.google.com",
        "googleapis.com/upload",
        "Start-Sleep -Seconds 60",
    )
    for token in forbidden:
        assert token.lower() not in text.lower()


def test_dispatch_has_no_free_form_case_machine_url_or_shell_inputs():
    text = DISPATCH.read_text(encoding="utf-8")

    assert "inputs:\n      command:" in text
    assert "case_id:" not in text.split("permissions:", 1)[0]
    assert "machine:" not in text.split("permissions:", 1)[0]
    assert "url:" not in text.split("permissions:", 1)[0]
    assert "script:" not in text.split("permissions:", 1)[0]
    assert "shell_command:" not in text.split("permissions:", 1)[0]


def test_installer_verifies_real_local_supervisor_before_transport_use():
    text = INSTALL.read_text(encoding="utf-8")

    assert "runs-on: [self-hosted, Windows, X64, ODA]" in text
    assert "install-openworkerctl.ps1" in text
    assert "openworkerctl.exe" in text
    assert "supervisor status" in text
    assert "OPERATIONAL" in text
    assert "LOCAL_SUPERVISOR" in text
    assert "github_action_used_for_business_execution=$false" in text


def test_openworkerctl_remains_localhost_fail_closed():
    text = CTL.read_text(encoding="utf-8")

    assert 'const defaultServer="http://127.0.0.1:8848"' in text
    assert 'id!="0005"' in text
    assert '"0005","DESKTOP-ODAQN0D"' in text
    assert 'server must be http localhost:8848 without path' in text
    assert 'GitHub business execution forbidden' in text
