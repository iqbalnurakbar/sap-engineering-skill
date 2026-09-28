"""Fork features ported onto the upstream architecture (offline).

Covers what this fork adds on top of shrek-abaper/sap-engineering-skill:

* the sap-client URL parameter on every request;
* the per-profile backend platform (s4 / ecc) and the ECC transport paths;
* create-program / set-program-ldb;
* the Content-Type retry for bodyless lock/unlock POSTs;
* configure keeping saved settings for flags that were not given.

No HTTP, SAP system, real config file or OS keystore is involved. ECC
payloads here are synthetic (shaped after the documented asx:abap layout).
"""
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from test_sap_adt_cli_config import (  # noqa: E402
    SCRIPTS_PATH,
    MemoryKeystore,
    load_cli_module,
    load_config_module,
)

sys.path.insert(0, str(SCRIPTS_PATH))

BASE = "https://sap.example.invalid:44300"

_SAP_ENV_CLEARED = {
    key: ""
    for key in (
        "SAP_URL", "SAP_USERNAME", "SAP_PASSWORD", "SAP_CLIENT", "SAP_LANGUAGE",
        "SAP_VERIFY_SSL", "SAP_ALLOW_WRITE", "SAP_ALLOW_TRANSPORT",
        "SAP_ENVIRONMENT", "SAP_PROFILE", "SAP_PLATFORM",
    )
}

ECC_FIND_PAYLOAD = b"""<?xml version="1.0" encoding="utf-8"?>
<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">
  <asx:values>
    <DATA>
      <CTS_REQ_HEADER>
        <TRKORR>DEVK900101</TRKORR><TRFUNCTION>K</TRFUNCTION><TRSTATUS>D</TRSTATUS>
        <TARSYSTEM>QAS</TARSYSTEM><AS4USER>DEVELOPER</AS4USER><AS4DATE>20260901</AS4DATE>
        <AS4TIME>101500</AS4TIME><AS4TEXT>Fix rounding</AS4TEXT><CLIENT>300</CLIENT>
      </CTS_REQ_HEADER>
      <CTS_REQ_HEADER>
        <TRKORR>DEVK900077</TRKORR><TRFUNCTION>K</TRFUNCTION><TRSTATUS>R</TRSTATUS>
        <TARSYSTEM>QAS</TARSYSTEM><AS4USER>DEVELOPER</AS4USER><AS4TEXT>Old change</AS4TEXT>
      </CTS_REQ_HEADER>
      <CTS_REQ_HEADER><TRKORR></TRKORR></CTS_REQ_HEADER>
    </DATA>
  </asx:values>
</asx:abap>"""

LOCK_RESULT = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">'
    "<asx:values><DATA><LOCK_HANDLE>HANDLE123</LOCK_HANDLE></DATA></asx:values>"
    "</asx:abap>"
)


def _envelope(result):
    t = result.output
    return json.loads(t[t.find("{"):])


class FakeResponse:
    def __init__(self, text="", status=200, headers=None):
        self.text = text if isinstance(text, str) else text.decode("utf-8")
        self.content = self.text.encode("utf-8")
        self.status_code = status
        self.headers = headers or {}


class FakeConfig:
    def __init__(self, platform=""):
        self.platform = platform

    def base_url(self):
        return BASE


def _cli_config(*, platform="", allow_write=False, allow_transport=False):
    return types.SimpleNamespace(
        profile_name="dev",
        username="DEVELOPER",
        environment="dev",
        environment_source="inferred",
        allow_write=allow_write,
        allow_transport=allow_transport,
        from_environment=False,
        env_write_requested=False,
        env_transport_requested=False,
        write_source="profile",
        transport_source="profile",
        is_production=False,
        platform=platform,
    )


# ------------------------------- client.py -------------------------------

class _ClientResponse:
    def __init__(self, status=200, text="", headers=None):
        self.status_code = status
        self.text = text
        self.headers = headers or {}
        self.cookies = {}

    def raise_for_status(self):
        pass


class SapClientParameterTests(unittest.TestCase):
    """The client number travels as header AND ?sap-client= on every call."""

    def setUp(self):
        _, config_mod = load_cli_module()
        self.client = sys.modules["lib.client"]
        self.cfg = config_mod.SapConfig(
            url=BASE, username="TESTER", password="pw-not-real", client="300")
        self.calls = []
        self.responses = []

        def fake_request(config, method, url, **kwargs):
            self.calls.append({"method": method, "url": url, **kwargs})
            return self.responses.pop(0) if self.responses else _ClientResponse()

        for p in (patch.object(self.client, "get_config", return_value=self.cfg),
                  patch.object(self.client, "_request", side_effect=fake_request)):
            p.start()
            self.addCleanup(p.stop)

    def test_get_sends_sap_client_and_keeps_existing_params(self):
        self.client.make_adt_request(f"{BASE}/sap/bc/adt/x", params={"a": "1"})
        call = self.calls[0]
        self.assertEqual(call["params"], {"a": "1", "sap-client": "300"})
        self.assertEqual(call["headers"]["X-SAP-Client"], "300")

    def test_get_without_params_still_sends_sap_client(self):
        self.client.make_adt_request(f"{BASE}/sap/bc/adt/x")
        self.assertEqual(self.calls[0]["params"], {"sap-client": "300"})

    def test_post_csrf_fetch_and_csrf_retry_all_send_sap_client(self):
        self.responses = [
            _ClientResponse(headers={"x-csrf-token": "tok1"}),         # fetch
            _ClientResponse(status=403, text="CSRF token validation failed"),
            _ClientResponse(headers={"x-csrf-token": "tok2"}),         # re-fetch
            _ClientResponse(),                                         # retry
        ]
        self.client.make_adt_request(f"{BASE}/sap/bc/adt/x", method="POST",
                                     params={"b": "2"})
        self.assertEqual([c["method"] for c in self.calls],
                         ["GET", "POST", "GET", "POST"])
        for call in self.calls:
            self.assertEqual(call["params"].get("sap-client"), "300", call)
        self.assertEqual(self.calls[3]["params"]["b"], "2")
        self.assertEqual(self.calls[3]["headers"]["x-csrf-token"], "tok2")


# ------------------------------- config.py -------------------------------

class PlatformConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(self.tmp.name)
        self.module = load_config_module()
        self.keystore = MemoryKeystore()
        self.module.credentials.set_registry_override([self.keystore])
        self.config_file = tmp_path / "home" / ".sap-adt-cli" / "config.json"
        self.config_file.parent.mkdir(parents=True)
        self.module._SKILL_DOTENV = tmp_path / "skill" / ".env"
        self.module.CONFIG_DIR = self.config_file.parent
        self.module.CONFIG_FILE = self.config_file
        self.module._OLD_CONFIG_DIR = tmp_path / "home" / ".sap-abap-cli"
        self.module._OLD_CONFIG_FILE = self.module._OLD_CONFIG_DIR / "config.json"
        env = patch.dict(os.environ, _SAP_ENV_CLEARED)
        env.start()
        self.addCleanup(env.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def _raw(self):
        return json.loads(self.config_file.read_text(encoding="utf-8"))

    def _save_dev(self, **overrides):
        kwargs = dict(name="dev", url="https://dev.example.invalid", username="DEV",
                      password="pw", client="100")
        kwargs.update(overrides)
        return self.module.save_profile(**kwargs)

    def test_normalize_platform_accepts_common_spellings(self):
        n = self.module.normalize_platform
        for value in ("s4", "S/4HANA", "S4 HANA", "hana"):
            self.assertEqual(n(value), "s4", value)
        for value in ("ecc", "ECC 6.0", "ERP", "R/3", "NetWeaver", "nw"):
            self.assertEqual(n(value), "ecc", value)
        for value in ("", None, "bw", "???"):
            self.assertEqual(n(value), "", value)

    def test_v1_config_platform_survives_migration(self):
        self.config_file.write_text(json.dumps({
            "url": "https://ecc.example.invalid", "username": "DEV",
            "password": "pw", "client": "300", "platform": "ECC",
        }), encoding="utf-8")
        cfg = self.module.load_config()
        self.assertEqual(cfg.platform, "ecc")
        self.assertEqual(self._raw()["profiles"]["default"]["platform"], "ecc")

    def test_save_profile_keeps_platform_and_ssl_when_not_given(self):
        self._save_dev(platform="ecc", verify_ssl=False)
        cfg = self._save_dev(client="200", verify_ssl=None)
        section = self._raw()["profiles"]["dev"]
        self.assertEqual(section["platform"], "ecc")
        self.assertFalse(section["verify_ssl"])
        self.assertEqual(section["client"], "200")
        self.assertEqual(cfg.platform, "ecc")

    def test_explicit_platform_replaces_saved_one(self):
        self._save_dev(platform="ecc")
        self._save_dev(platform="s4")
        self.assertEqual(self._raw()["profiles"]["dev"]["platform"], "s4")
        self.assertEqual(self.module.list_profiles()[0]["platform"], "s4")

    def test_flags_not_given_keep_saved_values(self):
        self._save_dev(verify_ssl=False, allow_write=True, allow_transport=True)
        self.module.save_config_from_flags(
            url=None, username=None, password=None, client=None,
            verify_ssl=None, allow_write=None, allow_transport=None,
            profile="dev", profile_scope=True, platform="ecc",
        )
        section = self._raw()["profiles"]["dev"]
        self.assertEqual(section["platform"], "ecc")
        self.assertFalse(section["verify_ssl"])
        self.assertTrue(section["allow_write"])
        self.assertTrue(section["allow_transport"])

    def test_unknown_platform_is_rejected_before_saving(self):
        with self.assertRaises(ValueError):
            self.module.save_config_from_flags(
                url="https://dev.example.invalid", username="DEV", password="pw",
                client="100", profile="dev", profile_scope=True, platform="bw",
            )
        self.assertFalse(self.config_file.exists())

    def test_env_path_reads_sap_platform(self):
        with patch.dict(os.environ, {
            "SAP_URL": BASE, "SAP_USERNAME": "DEV", "SAP_PASSWORD": "pw",
            "SAP_CLIENT": "100", "SAP_PLATFORM": "ECC",
        }):
            cfg = self.module.load_config()
        self.assertTrue(cfg.from_environment)
        self.assertEqual(cfg.platform, "ecc")


# ------------------------------ records parser ------------------------------

class EccRecordsParserTests(unittest.TestCase):
    def test_request_headers_normalize_to_records_shape(self):
        from lib.parsers import records

        data = records.parse_request_headers(ECC_FIND_PAYLOAD)
        self.assertEqual([t["trkorr"] for t in data["transports"]],
                         ["DEVK900101", "DEVK900077"])
        first = data["transports"][0]
        self.assertEqual(first, {
            "trkorr": "DEVK900101",
            "description": "Fix rounding",
            "status": "D",
            "status_text": "modifiable",
            "owner": "DEVELOPER",
            "target": "QAS",
            "tasks": [],
        })


# -------------------------------- handlers.py --------------------------------

class _HandlerTestBase(unittest.TestCase):
    platform = "ecc"

    def setUp(self):
        load_cli_module()
        self.handlers = sys.modules["lib.handlers"]
        self.errors = sys.modules["lib.errors"]
        self.calls = []
        self.replies = []

        def fake(url, method="GET", **kw):
            self.calls.append({"url": url, "method": method, **kw})
            reply = self.replies.pop(0) if self.replies else FakeResponse()
            if isinstance(reply, Exception):
                raise reply
            return reply

        for p in (patch.object(self.handlers, "get_config",
                               return_value=FakeConfig(self.platform)),
                  patch.object(self.handlers, "make_adt_request", side_effect=fake)):
            p.start()
            self.addCleanup(p.stop)


class EccTransportHandlerTests(_HandlerTestBase):
    platform = "ecc"

    def test_list_uses_find_action_and_filters_status(self):
        self.replies = [FakeResponse(ECC_FIND_PAYLOAD)]
        result = self.handlers.list_transports("DEVELOPER", status="D")
        self.assertFalse(result.is_error, result.text)
        self.assertEqual(result.kind, "records")
        call = self.calls[0]
        self.assertEqual(call["url"], f"{BASE}/sap/bc/adt/cts/transports")
        self.assertEqual(call["params"],
                         {"_action": "FIND", "user": "DEVELOPER", "trfunction": "K"})
        self.assertEqual([t["trkorr"] for t in result.data["transports"]],
                         ["DEVK900101"])

    def test_create_sends_only_devclass_and_request_text(self):
        self.replies = [FakeResponse("/com.sap.cts/object_record/DEVK900123")]
        result = self.handlers.create_transport("ZMM", 'Fix <a> & "b"', "")
        self.assertFalse(result.is_error, result.text)
        self.assertEqual(result.text, "Created transport: DEVK900123")
        call = self.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertTrue(call["url"].endswith("/sap/bc/adt/cts/transports"))
        self.assertIn("com.sap.adt.CreateCorrectionRequest",
                      call["extra_headers"]["Content-Type"])
        self.assertNotIn("Accept", call["extra_headers"])
        body = call["data"].decode()
        self.assertIn("<DEVCLASS>ZMM</DEVCLASS>", body)
        self.assertIn("<REQUEST_TEXT>Fix &lt;a&gt; &amp; &quot;b&quot;</REQUEST_TEXT>", body)
        self.assertNotIn("<REF>", body)
        self.assertNotIn("<OPERATION>", body)

    def test_create_ignores_ref_on_ecc(self):
        self.replies = [FakeResponse("/com.sap.cts/object_record/DEVK900124")]
        result = self.handlers.create_transport(
            "ZMM", "desc", "/sap/bc/adt/programs/programs/zx/source/main")
        self.assertFalse(result.is_error, result.text)
        self.assertNotIn("<REF>", self.calls[0]["data"].decode())

    def test_create_without_package_is_bad_request(self):
        result = self.handlers.create_transport("", "desc", "")
        self.assertTrue(result.is_error)
        self.assertEqual(result.error_code, self.errors.BAD_REQUEST)
        self.assertEqual(self.calls, [])

    def test_release_is_refused_without_any_request(self):
        result = self.handlers.release_transport("DEVK900101")
        self.assertTrue(result.is_error)
        self.assertEqual(result.error_code, self.errors.BAD_REQUEST)
        self.assertIn("SE01/SE09", result.text)
        self.assertEqual(self.calls, [])


class S4TransportHandlerTests(_HandlerTestBase):
    platform = "s4"

    def test_list_keeps_transport_organizer_tree(self):
        self.replies = [FakeResponse(b"<tm:root xmlns:tm='http://www.sap.com/cts/adt/tm'/>")]
        result = self.handlers.list_transports("DEVELOPER")
        self.assertFalse(result.is_error, result.text)
        self.assertTrue(self.calls[0]["url"].endswith("/sap/bc/adt/cts/transportrequests"))

    def test_create_still_requires_ref(self):
        result = self.handlers.create_transport("ZMM", "desc", "")
        self.assertTrue(result.is_error)
        self.assertEqual(result.error_code, self.errors.BAD_REQUEST)
        self.assertEqual(self.calls, [])


class BodylessPostFallbackTests(_HandlerTestBase):
    platform = ""

    def _content_type_missing(self):
        return self.handlers.AdtHttpError(
            "HTTP 400 for POST https://h/x: <exc:exception><type id=\"ExceptionContentTypeMissing\"/>"
            "<message>contentTypeMissing</message></exc:exception>",
            status=400,
        )

    def test_lock_retries_once_with_content_type(self):
        self.replies = [self._content_type_missing(), FakeResponse(LOCK_RESULT)]
        result = self.handlers.lock_object("/sap/bc/adt/programs/programs/ZX")
        self.assertFalse(result.is_error, result.text)
        self.assertEqual(result.text, "HANDLE123")
        self.assertEqual(len(self.calls), 2)
        self.assertNotIn("Content-Type", self.calls[0]["extra_headers"])
        self.assertEqual(self.calls[1]["extra_headers"]["Content-Type"],
                         "application/vnd.sap.as+xml; charset=UTF-8")
        self.assertEqual(self.calls[1]["params"],
                         {"_action": "LOCK", "accessMode": "MODIFY"})

    def test_lock_does_not_retry_other_errors(self):
        self.replies = [self.handlers.AdtHttpError(
            "HTTP 403 for POST https://h/x: currently editing", status=403)]
        result = self.handlers.lock_object("/sap/bc/adt/programs/programs/ZX")
        self.assertTrue(result.is_error)
        self.assertEqual(len(self.calls), 1)

    def test_unlock_retries_once_with_content_type(self):
        self.replies = [self._content_type_missing(), FakeResponse()]
        result = self.handlers.unlock_object("/sap/bc/adt/programs/programs/ZX", "H")
        self.assertEqual(result.text, "OK")
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.calls[1]["params"],
                         {"_action": "UNLOCK", "lockHandle": "H"})


class ProgramHandlerTests(_HandlerTestBase):
    platform = "ecc"

    def test_create_program_posts_v2_document_with_transport(self):
        self.replies = [FakeResponse(status=201)]
        result = self.handlers.create_program(
            "zmm_report", 'Stock "report"', "zmm", transport="DEVK900042")
        self.assertFalse(result.is_error, result.text)
        self.assertIn("Created PROGRAM ZMM_REPORT in package ZMM", result.text)
        call = self.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], f"{BASE}/sap/bc/adt/programs/programs")
        self.assertEqual(call["params"], {"corrNr": "DEVK900042"})
        self.assertIn("programs.programs.v2+xml", call["extra_headers"]["Content-Type"])
        body = call["data"].decode()
        self.assertIn('adtcore:name="ZMM_REPORT"', body)
        self.assertIn('adtcore:description="Stock &quot;report&quot;"', body)
        self.assertIn('<adtcore:packageRef adtcore:name="ZMM"/>', body)
        self.assertIn('program:programType="executableProgram"', body)

    def test_create_local_program_sends_no_transport(self):
        self.handlers.create_program("ZTMP", "t", "$tmp")
        self.assertIsNone(self.calls[0]["params"])

    def test_set_ldb_blanks_block_under_lock(self):
        doc = ('<program:abapProgram xmlns:program="p" xmlns:adtcore="a">'
               '<program:logicalDatabase><program:ref adtcore:name="D$S"/>'
               "</program:logicalDatabase></program:abapProgram>")
        self.replies = [FakeResponse(doc), FakeResponse(LOCK_RESULT),
                        FakeResponse(), FakeResponse()]
        result = self.handlers.set_program_logical_database(
            "zmm_report", logical_database="", transport="DEVK900042")
        self.assertFalse(result.is_error, result.text)
        uri = f"{BASE}/sap/bc/adt/programs/programs/ZMM_REPORT"
        self.assertEqual([(c["method"], c["url"]) for c in self.calls],
                         [("GET", uri), ("POST", uri), ("PUT", uri), ("POST", uri)])
        put = self.calls[2]
        self.assertEqual(put["params"], {"lockHandle": "HANDLE123", "corrNr": "DEVK900042"})
        self.assertIn('<program:ref adtcore:name=""/>', put["data"].decode())
        self.assertEqual(self.calls[3]["params"]["_action"], "UNLOCK")

    def test_set_ldb_nothing_to_blank_takes_no_lock(self):
        self.replies = [FakeResponse('<program:abapProgram xmlns:program="p"/>')]
        result = self.handlers.set_program_logical_database("ZX", logical_database="")
        self.assertFalse(result.is_error)
        self.assertIn("nothing to do", result.text)
        self.assertEqual(len(self.calls), 1)


# ------------------------------- CLI commands -------------------------------

class CliPlatformGateTests(unittest.TestCase):
    def setUp(self):
        self.cli, self.config_mod = load_cli_module()
        self.handlers = sys.modules["lib.handlers"]

    def _invoke(self, args, cfg):
        with patch.object(self.cli, "load_config", return_value=cfg), \
                patch.object(self.handlers, "make_adt_request") as no_http:
            r = CliRunner().invoke(self.cli.cli, args)
        return r, no_http

    def test_transport_commands_refuse_unset_platform(self):
        cfg = _cli_config(allow_transport=True)
        for args in (["list-transports"],
                     ["create-transport", "--package", "ZMM", "--description", "x",
                      "--ref", "/sap/bc/adt/programs/programs/zx", "--yes"],
                     ["release-transport", "DEVK900001", "--yes"]):
            r, no_http = self._invoke(args, cfg)
            self.assertEqual(r.exit_code, 2, (args, r.output))
            env = _envelope(r)
            self.assertEqual(env["error"]["code"], "CONFIG_MISSING")
            self.assertIn("configure --platform", env["error"]["message"])
            no_http.assert_not_called()

    def test_transport_gate_still_fires_before_platform_check(self):
        r, no_http = self._invoke(
            ["create-transport", "--package", "ZMM", "--description", "x", "--yes"],
            _cli_config())
        self.assertEqual(r.exit_code, 3, r.output)
        self.assertEqual(_envelope(r)["error"]["code"], "TRANSPORT_DISABLED")
        no_http.assert_not_called()

    def test_release_on_ecc_is_refused_before_confirmation(self):
        r, no_http = self._invoke(["release-transport", "DEVK900001"],
                                  _cli_config(platform="ecc", allow_transport=True))
        self.assertEqual(r.exit_code, 1, r.output)
        env = _envelope(r)
        self.assertEqual(env["error"]["code"], "BAD_REQUEST")
        self.assertIn("SE01/SE09", env["error"]["message"])
        no_http.assert_not_called()

    def test_create_transport_requires_ref_on_s4_only(self):
        r, no_http = self._invoke(
            ["create-transport", "--package", "ZMM", "--description", "x", "--yes"],
            _cli_config(platform="s4", allow_transport=True))
        self.assertEqual(r.exit_code, 1, r.output)
        self.assertEqual(_envelope(r)["error"]["code"], "BAD_REQUEST")
        no_http.assert_not_called()

        created = self.handlers.AdtResult(text="Created transport: DEVK900123")
        with patch.object(self.cli, "load_config",
                          return_value=_cli_config(platform="ecc", allow_transport=True)), \
                patch.object(self.handlers, "create_transport",
                             return_value=created) as create:
            r = CliRunner().invoke(self.cli.cli, [
                "create-transport", "--package", "ZMM", "--description", "x", "--yes"])
        self.assertEqual(r.exit_code, 0, r.output)
        self.assertIn("Created transport: DEVK900123", r.output)
        create.assert_called_once_with("ZMM", "x", "")

    def test_create_program_gates(self):
        r, no_http = self._invoke(
            ["create-program", "ZX", "--description", "d", "--package", "ZMM", "--yes"],
            _cli_config())
        self.assertEqual(r.exit_code, 3, r.output)
        self.assertEqual(_envelope(r)["error"]["code"], "WRITE_DISABLED")

        r, no_http = self._invoke(
            ["create-program", "ZX", "--description", "d", "--package", "ZMM", "--yes"],
            _cli_config(allow_write=True))
        self.assertEqual(r.exit_code, 1, r.output)
        self.assertEqual(_envelope(r)["error"]["code"], "BAD_REQUEST")
        self.assertIn("--transport", _envelope(r)["error"]["message"])
        no_http.assert_not_called()

    def test_status_shows_platform(self):
        cfg = self.config_mod.SapConfig(
            url=BASE, username="DEV", password="pw", client="300",
            profile_name="dev", platform="ecc")
        with patch.object(self.cli, "load_config_with_source",
                          return_value=(cfg, "test source")):
            r = CliRunner().invoke(self.cli.cli, ["status"])
        self.assertEqual(r.exit_code, 0, r.output)
        self.assertIn("Platform:        ECC", r.output)


class CliConfigureKeepsSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(self.tmp.name)
        self.cli, self.config = load_cli_module()
        self.config.credentials.set_registry_override([MemoryKeystore()])
        self.config_file = tmp_path / "home" / ".sap-adt-cli" / "config.json"
        self.config_file.parent.mkdir(parents=True)
        self.config._SKILL_DOTENV = tmp_path / "skill" / ".env"
        self.config.CONFIG_DIR = self.config_file.parent
        self.config.CONFIG_FILE = self.config_file
        self.config._OLD_CONFIG_DIR = tmp_path / "home" / ".sap-abap-cli"
        self.config._OLD_CONFIG_FILE = self.config._OLD_CONFIG_DIR / "config.json"
        env = patch.dict(os.environ, _SAP_ENV_CLEARED)
        env.start()
        self.addCleanup(env.stop)
        self.config.save_profile(
            name="dev", url="https://dev.example.invalid", username="DEV",
            password="pw", client="100", verify_ssl=False,
            allow_write=True, allow_transport=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _section(self):
        return json.loads(self.config_file.read_text(encoding="utf-8"))["profiles"]["dev"]

    def _configure(self, *args):
        # input=None: a wizard prompt would fail on EOF, proving the path
        # was non-interactive.
        return CliRunner().invoke(self.cli.cli, ["configure", *args], input=None)

    def test_platform_alone_is_non_interactive_and_keeps_everything(self):
        r = self._configure("--platform", "ecc")
        self.assertEqual(r.exit_code, 0, r.output)
        section = self._section()
        self.assertEqual(section["platform"], "ecc")
        self.assertFalse(section["verify_ssl"])
        self.assertTrue(section["allow_write"])
        self.assertTrue(section["allow_transport"])
        self.assertEqual(section["client"], "100")

    def test_single_flag_changes_only_that_flag(self):
        self._configure("--platform", "s4")
        r = self._configure("--no-allow-write")
        self.assertEqual(r.exit_code, 0, r.output)
        section = self._section()
        self.assertFalse(section["allow_write"])
        self.assertTrue(section["allow_transport"])
        self.assertFalse(section["verify_ssl"])
        self.assertEqual(section["platform"], "s4")

    def test_connection_flag_no_longer_resets_capabilities(self):
        r = self._configure("--client", "200")
        self.assertEqual(r.exit_code, 0, r.output)
        section = self._section()
        self.assertEqual(section["client"], "200")
        self.assertTrue(section["allow_write"])
        self.assertTrue(section["allow_transport"])
        self.assertFalse(section["verify_ssl"])

    def test_unknown_platform_is_bad_request(self):
        r = self._configure("--platform", "bw")
        self.assertEqual(r.exit_code, 1, r.output)
        self.assertEqual(_envelope(r)["error"]["code"], "BAD_REQUEST")
        self.assertNotIn("platform", self._section())

    def test_profile_list_shows_platform(self):
        self._configure("--platform", "ecc")
        r = CliRunner().invoke(self.cli.cli, ["profile", "list"])
        self.assertEqual(r.exit_code, 0, r.output)
        self.assertIn("PLAT", r.output)
        self.assertRegex(r.output, r"\* dev\s+dev\s+ecc\s+100")


if __name__ == "__main__":
    unittest.main()
