from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bookkeeping_core.contracts import NormalizedMessageEnvelope
from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.models import IncomingMessage
from bookkeeping_core.runtime import UnifiedBookkeepingRuntime
from tests.support.postgres_test_case import PostgresTestCase
from wechat_adapter.config import CoreApiConfig, WeChatConfig


class _FakeListenedChat:
    def __init__(self, who: str) -> None:
        self.who = who


class UnifiedRuntimeTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.export_dir = self.temp_path / "exports"
        self.db = BookkeepingDB(self.make_dsn("runtime"))
        self.runtime = UnifiedBookkeepingRuntime(
            db=self.db,
            master_users=["master-user"],
            export_dir=self.export_dir,
        )

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def test_normalized_message_envelope_from_dict_populates_required_contract_fields(self) -> None:
        envelope = NormalizedMessageEnvelope.from_dict(
            {
                "platform": "wechat",
                "message_id": "msg-1",
                "chat_id": "room-a",
                "is_group": True,
                "sender_id": "user-1",
                "text": "+100rmb",
                "received_at": "2026-03-21 10:00:00",
            }
        )

        self.assertEqual(envelope.platform, "wechat")
        self.assertEqual(envelope.message_id, "msg-1")
        self.assertEqual(envelope.chat_id, "room-a")
        self.assertEqual(envelope.chat_name, "room-a")
        self.assertTrue(envelope.is_group)
        self.assertEqual(envelope.sender_id, "user-1")
        self.assertEqual(envelope.sender_name, "user-1")
        self.assertEqual(envelope.sender_kind, "user")
        self.assertEqual(envelope.content_type, "text")
        self.assertEqual(envelope.text, "+100rmb")
        self.assertEqual(envelope.received_at, "2026-03-21 10:00:00")

    def test_normalized_message_envelope_from_dict_defaults_sender_kind_to_self_when_from_self_is_true(self) -> None:
        envelope = NormalizedMessageEnvelope.from_dict(
            {
                "platform": "wechat",
                "message_id": "msg-self-1",
                "chat_id": "room-a",
                "is_group": True,
                "sender_id": "master-user",
                "text": "hi",
                "from_self": True,
                "received_at": "2026-03-21 10:00:00",
            }
        )

        self.assertTrue(envelope.from_self)
        self.assertEqual(envelope.sender_kind, "self")

    def test_normalized_message_envelope_from_dict_preserves_explicit_non_self_sender_kind(self) -> None:
        envelope = NormalizedMessageEnvelope.from_dict(
            {
                "platform": "wechat",
                "message_id": "msg-system-1",
                "chat_id": "room-a",
                "is_group": True,
                "sender_id": "system",
                "sender_kind": "system",
                "text": "notice",
                "from_self": False,
                "received_at": "2026-03-21 10:00:00",
            }
        )

        self.assertFalse(envelope.from_self)
        self.assertEqual(envelope.sender_kind, "system")

    def test_normalized_message_envelope_from_dict_normalizes_conflicting_self_flags(self) -> None:
        envelope = NormalizedMessageEnvelope.from_dict(
            {
                "platform": "wechat",
                "message_id": "msg-self-2",
                "chat_id": "room-a",
                "is_group": True,
                "sender_id": "master-user",
                "sender_kind": "user",
                "text": "hello",
                "from_self": True,
                "received_at": "2026-03-21 10:00:00",
            }
        )

        self.assertTrue(envelope.from_self)
        self.assertEqual(envelope.sender_kind, "self")

    def test_normalized_message_envelope_from_dict_rejects_blank_required_fields(self) -> None:
        valid_payload = {
            "platform": "wechat",
            "message_id": "msg-1",
            "chat_id": "room-a",
            "is_group": True,
            "sender_id": "user-1",
            "text": "+100rmb",
            "received_at": "2026-03-21 10:00:00",
        }

        for field in ("platform", "message_id", "chat_id", "sender_id"):
            with self.subTest(field=field):
                payload = dict(valid_payload)
                payload[field] = " "
                with self.assertRaises(ValueError):
                    NormalizedMessageEnvelope.from_dict(payload)

    def test_legacy_incoming_message_constructor_accepts_content_and_raw(self) -> None:
        message = IncomingMessage(
            platform="wechat",
            message_id="legacy-1",
            chat_id="room-a",
            chat_name="room-a",
            sender_id="user-1",
            sender_name="User One",
            content="hello",
            is_group=True,
            from_self=False,
            raw={"id": "legacy-1"},
        )

        self.assertEqual(message.content, "hello")
        self.assertEqual(message.sender_kind, "user")
        self.assertEqual(message.content_type, "text")
        self.assertEqual(message.raw["id"], "legacy-1")

    def test_legacy_incoming_message_normalizes_conflicting_self_flags(self) -> None:
        message = IncomingMessage(
            platform="wechat",
            message_id="legacy-2",
            chat_id="room-a",
            chat_name="room-a",
            sender_id="master-user",
            sender_name="Master",
            content="hello",
            is_group=True,
            from_self=True,
            sender_kind="user",
            raw={"id": "legacy-2"},
        )

        self.assertTrue(message.from_self)
        self.assertEqual(message.sender_kind, "self")
        self.assertTrue(message.normalized.from_self)
        self.assertEqual(message.normalized.sender_kind, "self")

    def test_legacy_incoming_message_preserves_explicit_non_user_sender_kind(self) -> None:
        message = IncomingMessage(
            platform="wechat",
            message_id="legacy-3",
            chat_id="room-a",
            chat_name="room-a",
            sender_id="system",
            sender_name="System",
            content="notice",
            is_group=True,
            from_self=False,
            sender_kind="system",
            raw={"id": "legacy-3"},
        )

        self.assertFalse(message.from_self)
        self.assertEqual(message.sender_kind, "system")
        self.assertEqual(message.normalized.sender_kind, "system")
        self.assertFalse(message.normalized.from_self)

    def test_wechat_platform_api_normalize_message_returns_normalized_message_envelope(self) -> None:
        from wechat_adapter.client import WeChatPlatformAPI

        api = WeChatPlatformAPI.__new__(WeChatPlatformAPI)
        api.self_name = "WeChat Self"
        api.self_wxid = "wxid-self"
        api._sender_cache = {}

        item = SimpleNamespace(
            details={
                "id": "wx-msg-1",
                "chat_name": "客户群-A",
                "chat_type": "group",
                "type": "self",
                "content": "  hello  ",
            }
        )

        envelope = api._normalize_message(item)

        self.assertIsInstance(envelope, NormalizedMessageEnvelope)
        self.assertEqual(envelope.platform, "wechat")
        self.assertEqual(envelope.message_id, "wx-msg-1")
        self.assertEqual(envelope.chat_id, "客户群-A")
        self.assertEqual(envelope.chat_name, "客户群-A")
        self.assertTrue(envelope.is_group)
        self.assertEqual(envelope.sender_id, "wxid-self")
        self.assertEqual(envelope.sender_name, "WeChat Self")
        self.assertEqual(envelope.sender_kind, "self")
        self.assertEqual(envelope.content_type, "text")
        self.assertEqual(envelope.text, "hello")

    def test_wechat_platform_api_poll_messages_keeps_whoami_for_runtime(self) -> None:
        from wechat_adapter.client import WeChatPlatformAPI

        api = WeChatPlatformAPI.__new__(WeChatPlatformAPI)
        api.listen_chats = ["客户群-A"]
        api._listeners_ready = True
        api.self_name = ""
        api.self_wxid = ""
        api._sender_cache = {}
        api.wx = MagicMock()
        api.wx.GetListenMessage.return_value = [
            SimpleNamespace(
                details={
                    "id": "wx-control-1",
                    "chat_name": "客户群-A",
                    "chat_type": "group",
                    "type": "other",
                    "sender": "User One",
                    "content": "/whoami",
                }
            )
        ]
        api.db = MagicMock()
        api.db.resolve_identity.return_value = "canonical-user"
        api.db.is_admin.return_value = False
        api.db.is_whitelisted.return_value = False
        api.config = WeChatConfig(
            listen_chats=["客户群-A"],
            master_users=[],
            poll_interval_seconds=1.0,
            log_level="INFO",
            language="cn",
            export_dir="/tmp/exports",
            runtime_dir="/tmp/runtime",
        )
        api.logger = MagicMock()
        api.send_text = MagicMock()

        messages = api.poll_messages()

        self.assertEqual(len(messages), 1)
        self.assertIsInstance(messages[0], NormalizedMessageEnvelope)
        self.assertEqual(messages[0].text, "/whoami")
        api.send_text.assert_not_called()

    def test_wechat_platform_api_poll_messages_keeps_set_command_for_runtime(self) -> None:
        from wechat_adapter.client import WeChatPlatformAPI

        api = WeChatPlatformAPI.__new__(WeChatPlatformAPI)
        api.listen_chats = ["客户群-A"]
        api._listeners_ready = True
        api.self_name = ""
        api.self_wxid = ""
        api._sender_cache = {}
        api.wx = MagicMock()
        api.wx.GetListenMessage.return_value = [
            SimpleNamespace(
                details={
                    "id": "wx-set-1",
                    "chat_name": "客户群-A",
                    "chat_type": "group",
                    "type": "other",
                    "sender": "User One",
                    "content": "/set 2",
                }
            )
        ]
        api.db = MagicMock()
        api.db.resolve_identity.return_value = "canonical-user"
        api.db.is_admin.return_value = False
        api.db.is_whitelisted.return_value = False
        api.config = WeChatConfig(
            listen_chats=["客户群-A"],
            master_users=[],
            poll_interval_seconds=1.0,
            log_level="INFO",
            language="cn",
            export_dir="/tmp/exports",
            runtime_dir="/tmp/runtime",
        )
        api.logger = MagicMock()
        api.send_text = MagicMock()

        messages = api.poll_messages()

        self.assertEqual(len(messages), 1)
        self.assertIsInstance(messages[0], NormalizedMessageEnvelope)
        self.assertEqual(messages[0].text, "/set 2")
        api.send_text.assert_not_called()

    def test_wechat_platform_api_poll_messages_skips_bad_payload_without_raising(self) -> None:
        from wechat_adapter.client import WeChatPlatformAPI

        api = WeChatPlatformAPI.__new__(WeChatPlatformAPI)
        api.listen_chats = ["客户群-A"]
        api._listeners_ready = True
        api.self_name = ""
        api.self_wxid = ""
        api._sender_cache = {}
        api.wx = MagicMock()
        api.wx.GetListenMessage.return_value = [
            SimpleNamespace(details={"id": "bad-1", "chat_name": "客户群-A"}),
            SimpleNamespace(details={"id": "good-1", "chat_name": "客户群-A", "sender": "User One", "content": "hello"}),
        ]
        api.db = MagicMock()
        api.db.resolve_identity.return_value = "canonical-user"
        api.db.is_admin.return_value = False
        api.db.is_whitelisted.return_value = False
        api.config = WeChatConfig(
            listen_chats=["客户群-A"],
            master_users=[],
            poll_interval_seconds=1.0,
            log_level="INFO",
            language="cn",
            export_dir="/tmp/exports",
            runtime_dir="/tmp/runtime",
        )
        api.logger = MagicMock()
        api.send_text = MagicMock()

        messages = api.poll_messages()

        self.assertEqual(len(messages), 1)
        self.assertIsInstance(messages[0], NormalizedMessageEnvelope)
        self.assertEqual(messages[0].text, "hello")
        api.send_text.assert_not_called()

    def test_wechat_platform_api_poll_messages_keeps_dict_payload_when_listened_alias_differs_from_details_chat_name(self) -> None:
        from wechat_adapter.client import WeChatPlatformAPI

        api = WeChatPlatformAPI.__new__(WeChatPlatformAPI)
        api.listen_chats = ["客户群-A-备注"]
        api._listeners_ready = True
        api.self_name = ""
        api.self_wxid = ""
        api._sender_cache = {}
        api.wx = MagicMock()
        api.wx.GetListenMessage.return_value = {
            _FakeListenedChat("客户群-A-备注"): [
                SimpleNamespace(
                    details={
                        "id": "good-2",
                        "chat_name": "客户群-A原名",
                        "chat_type": "group",
                        "sender": "User One",
                        "content": "hello",
                    }
                )
            ]
        }
        api.db = MagicMock()
        api.db.resolve_identity.return_value = "canonical-user"
        api.db.is_admin.return_value = False
        api.db.is_whitelisted.return_value = False
        api.config = WeChatConfig(
            listen_chats=["客户群-A-备注"],
            master_users=[],
            poll_interval_seconds=1.0,
            log_level="INFO",
            language="cn",
            export_dir="/tmp/exports",
            runtime_dir="/tmp/runtime",
        )
        api.logger = MagicMock()
        api.send_text = MagicMock()

        messages = api.poll_messages()

        self.assertEqual(len(messages), 1)
        self.assertIsInstance(messages[0], NormalizedMessageEnvelope)
        self.assertEqual(messages[0].chat_name, "客户群-A原名")
        self.assertEqual(messages[0].text, "hello")
        api.send_text.assert_not_called()

    def test_wechat_main_requires_remote_core_api_configuration(self) -> None:
        from wechat_adapter import main as wechat_main

        config = WeChatConfig(
            listen_chats=["文件传输助手"],
            master_users=[],
            poll_interval_seconds=1.0,
            log_level="INFO",
            language="cn",
            export_dir="/tmp/exports",
            runtime_dir="/tmp/runtime",
        )

        with (
            patch.object(wechat_main, "load_config", return_value=config),
            patch.object(wechat_main, "WeChatPlatformAPI") as platform_api_cls,
        ):
            exit_code = wechat_main.main()

        self.assertEqual(exit_code, 1)
        platform_api_cls.assert_not_called()

    def test_wechat_core_api_client_posts_normalized_envelope_to_remote_runtime(self) -> None:
        from wechat_adapter.core_api import WeChatCoreApiClient

        envelope = NormalizedMessageEnvelope.from_dict(
            {
                "platform": "wechat",
                "message_id": "msg-remote-1",
                "chat_id": "room-a",
                "chat_name": "客户群-A",
                "is_group": True,
                "sender_id": "user-1",
                "sender_name": "User One",
                "sender_kind": "user",
                "content_type": "text",
                "text": "+100rmb",
                "received_at": "2026-03-21 10:00:00",
            }
        )

        response = MagicMock()
        response.read.return_value = b'{"actions":[{"action_type":"send_text","chat_id":"room-a","text":"hello back"}]}'
        context = MagicMock()
        context.__enter__.return_value = response
        context.__exit__.return_value = False
        opener = MagicMock(return_value=context)

        client = WeChatCoreApiClient(
            endpoint="https://python.example.com",
            token="core-token",
            request_timeout_seconds=5.0,
            opener=opener,
        )

        actions = client.send_envelope(envelope)

        self.assertEqual(
            actions,
            [
                {
                    "action_type": "send_text",
                    "chat_id": "room-a",
                    "text": "hello back",
                }
            ],
        )
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, "https://python.example.com/api/core/messages")
        self.assertEqual(request.get_header("Authorization"), "Bearer core-token")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data.decode("utf-8")), {
            "platform": "wechat",
            "message_id": "msg-remote-1",
            "chat_id": "room-a",
            "chat_name": "客户群-A",
            "is_group": True,
            "sender_id": "user-1",
            "sender_name": "User One",
            "sender_kind": "user",
            "content_type": "text",
            "text": "+100rmb",
            "from_self": False,
            "received_at": "2026-03-21 10:00:00",
        })

    def test_wechat_main_uses_remote_core_api_when_configured(self) -> None:
        from wechat_adapter import main as wechat_main

        fake_message = NormalizedMessageEnvelope.from_dict(
            {
                "platform": "wechat",
                "message_id": "msg-remote-main-1",
                "chat_id": "room-a",
                "chat_name": "客户群-A",
                "is_group": True,
                "sender_id": "user-1",
                "sender_name": "User One",
                "sender_kind": "user",
                "content_type": "text",
                "text": "hello",
                "received_at": "2026-03-21 10:00:00",
            }
        )
        fake_platform_api = MagicMock()
        fake_platform_api.listen_chats = ["文件传输助手"]
        fake_platform_api.self_name = ""
        fake_platform_api.self_wxid = ""
        fake_platform_api.poll_messages.return_value = [fake_message]
        fake_remote_client = MagicMock()
        fake_remote_client.send_envelope.return_value = [
            {
                "action_type": "send_text",
                "chat_id": "room-a",
                "text": "hello back",
            }
        ]
        fake_remote_client.fetch_outbound_actions.return_value = []
        config = WeChatConfig(
            listen_chats=["文件传输助手"],
            master_users=[],
            poll_interval_seconds=1.0,
            log_level="INFO",
            language="cn",
            export_dir="/tmp/exports",
            runtime_dir="/tmp/runtime",
            core_api=CoreApiConfig(
                endpoint="https://python.example.com",
                token="core-token",
                request_timeout_seconds=5.0,
            ),
        )

        with (
            patch.object(wechat_main, "load_config", return_value=config),
            patch.object(wechat_main, "save_config"),
            patch.object(wechat_main, "WeChatPlatformAPI", return_value=fake_platform_api),
            patch.object(wechat_main, "WeChatCoreApiClient", return_value=fake_remote_client),
            patch.object(wechat_main.time, "sleep", side_effect=KeyboardInterrupt),
        ):
            exit_code = wechat_main.main()

        self.assertEqual(exit_code, 0)
        fake_remote_client.send_envelope.assert_called_once_with(fake_message)
        fake_platform_api.send_text.assert_called_once_with("room-a", "hello back")
        fake_remote_client.acknowledge_outbound_actions.assert_not_called()

    def test_wechat_main_flushes_remote_outbound_actions_for_web_queued_messages(self) -> None:
        from wechat_adapter import main as wechat_main

        fake_platform_api = MagicMock()
        fake_platform_api.listen_chats = ["文件传输助手"]
        fake_platform_api.self_name = ""
        fake_platform_api.self_wxid = ""
        fake_platform_api.poll_messages.return_value = []
        fake_remote_client = MagicMock()
        fake_remote_client.fetch_outbound_actions.return_value = [
            {
                "id": 41,
                "action_type": "send_text",
                "chat_id": "room-b",
                "text": "web diy",
            }
        ]
        config = WeChatConfig(
            listen_chats=["文件传输助手"],
            master_users=[],
            poll_interval_seconds=1.0,
            log_level="INFO",
            language="cn",
            export_dir="/tmp/exports",
            runtime_dir="/tmp/runtime",
            core_api=CoreApiConfig(
                endpoint="https://python.example.com",
                token="core-token",
                request_timeout_seconds=5.0,
            ),
        )

        with (
            patch.object(wechat_main, "load_config", return_value=config),
            patch.object(wechat_main, "save_config"),
            patch.object(wechat_main, "WeChatPlatformAPI", return_value=fake_platform_api),
            patch.object(wechat_main, "WeChatCoreApiClient", return_value=fake_remote_client),
            patch.object(wechat_main.time, "sleep", side_effect=KeyboardInterrupt),
        ):
            exit_code = wechat_main.main()

        self.assertEqual(exit_code, 0)
        fake_remote_client.send_envelope.assert_not_called()
        fake_platform_api.send_text.assert_called_once_with("room-b", "web diy")
        fake_remote_client.acknowledge_outbound_actions.assert_called_once_with(
            [
                {
                    "id": 41,
                    "success": True,
                }
            ]
        )

    def test_core_action_collector_emits_send_text_and_send_file_actions(self) -> None:
        from bookkeeping_core.contracts import CoreActionCollector, core_action_to_dict

        collector = CoreActionCollector()

        self.assertTrue(collector.send_text("room-a", "hello"))
        self.assertTrue(collector.send_file("room-a", "/tmp/export.csv", "report"))
        self.assertEqual(
            collector.actions,
            [
                {
                    "action_type": "send_text",
                    "chat_id": "room-a",
                    "text": "hello",
                },
                {
                    "action_type": "send_file",
                    "chat_id": "room-a",
                    "file_path": "/tmp/export.csv",
                    "caption": "report",
                },
            ],
        )
        self.assertEqual(
            core_action_to_dict(collector.actions[0]),
            {
                "action_type": "send_text",
                "chat_id": "room-a",
                "text": "hello",
            },
        )
        self.assertEqual(
            core_action_to_dict(collector.actions[1]),
            {
                "action_type": "send_file",
                "chat_id": "room-a",
                "file_path": "/tmp/export.csv",
                "caption": "report",
            },
        )

    def test_core_action_to_dict_rejects_unsupported_action_type(self) -> None:
        from bookkeeping_core.contracts import core_action_to_dict

        with self.assertRaises(ValueError):
            core_action_to_dict(
                {
                    "action_type": "delete_all",
                    "chat_id": "room-a",
                }
            )

    def test_set_command_returns_send_text_action_and_persists_group(self) -> None:
        actions = self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-set-1",
                chat_id="room-a",
                chat_name="客户群-A",
                text="/set 2",
            )
        )

        self.assertEqual(
            actions,
            [
                {
                    "action_type": "send_text",
                    "chat_id": "room-a",
                    "text": "✅ This group assigned to Group 2\nOnly groups with numbers can use bookkeeping",
                }
            ],
        )

        group = self.db.get_group_by_key("wechat:room-a")
        self.assertIsNotNone(group)
        self.assertEqual(int(group["group_num"]), 2)

    def test_balance_command_returns_legacy_emoji_balance_text(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-bal",
            chat_id="room-bal",
            chat_name="余额群",
            group_num=1,
        )

        actions = self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-bal-1",
                chat_id="room-bal",
                chat_name="余额群",
                text="/bal",
            )
        )

        self.assertEqual(
            actions,
            [
                {
                    "action_type": "send_text",
                    "chat_id": "room-bal",
                    "text": "📊 Current Balance: 0.00\n📝 No transactions\n📋 Group: Group 1",
                }
            ],
        )

    def test_transaction_message_returns_confirmation_send_text_action(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-tx",
            chat_id="room-tx",
            chat_name="交易群",
            group_num=3,
        )

        actions = self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-tx-1",
                chat_id="room-tx",
                chat_name="交易群",
                text="+100rmb",
            )
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "send_text")
        self.assertEqual(actions[0]["chat_id"], "room-tx")
        self.assertEqual(actions[0]["text"], "✅ +100.00\n📊 Balance: +100.00")

        incoming = self.db.get_incoming_message(
            platform="wechat",
            chat_id="room-tx",
            message_id="msg-tx-1",
        )
        self.assertIsNotNone(incoming)
        assert incoming is not None
        self.assertEqual(str(incoming["group_key"]), "wechat:room-tx")
        self.assertEqual(str(incoming["sender_name"]), "Master")
        self.assertEqual(str(incoming["text"]), "+100rmb")
        self.assertEqual(json.loads(str(incoming["raw_json"]))["message_id"], "msg-tx-1")

        rows, total = self.db.query_parse_results(platform="wechat", chat_id="room-tx", limit=10, offset=0)
        self.assertEqual(total, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["message_id"], "msg-tx-1")
        self.assertEqual(rows[0]["classification"], "transaction_like")
        self.assertEqual(rows[0]["parse_status"], "parsed")

    def test_command_message_records_parse_result(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-parse-cmd",
            chat_id="room-parse-cmd",
            chat_name="解析命令群",
            group_num=3,
        )

        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-parse-cmd-1",
                chat_id="room-parse-cmd",
                chat_name="解析命令群",
                text="/bal",
            )
        )

        rows, total = self.db.query_parse_results(platform="wechat", chat_id="room-parse-cmd", limit=10, offset=0)
        self.assertEqual(total, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["message_id"], "msg-parse-cmd-1")
        self.assertEqual(rows[0]["classification"], "command")
        self.assertEqual(rows[0]["parse_status"], "parsed")

    def test_duplicate_message_is_deduplicated_across_runtime_restarts(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-dedupe",
            chat_id="room-dedupe",
            chat_name="去重群",
            group_num=3,
        )
        message = self._message(
            platform="wechat",
            message_id="msg-dedupe-1",
            chat_id="room-dedupe",
            chat_name="去重群",
            text="+100rmb",
        )

        first_actions = self.runtime.process_envelope(message)
        restarted_runtime = UnifiedBookkeepingRuntime(
            db=self.db,
            master_users=["master-user"],
            export_dir=self.export_dir,
        )
        second_actions = restarted_runtime.process_envelope(message)

        self.assertEqual(len(first_actions), 1)
        self.assertEqual(second_actions, [])
        self.assertEqual(self.db.get_total_transaction_count(), 1)
        self.assertEqual(self.db.count_incoming_messages(), 1)

    def test_command_message_is_still_captured_before_business_filters(self) -> None:
        actions = self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-capture-cmd-1",
                chat_id="room-capture-cmd",
                chat_name="命令群",
                text="/whoami",
            )
        )

        self.assertTrue(actions)
        incoming = self.db.get_incoming_message(
            platform="wechat",
            chat_id="room-capture-cmd",
            message_id="msg-capture-cmd-1",
        )
        self.assertIsNotNone(incoming)

    def test_history_without_transactions_returns_legacy_empty_text(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-history",
            chat_id="room-history",
            chat_name="历史群",
            group_num=1,
        )

        actions = self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-history-1",
                chat_id="room-history",
                chat_name="历史群",
                text="/history",
            )
        )

        self.assertEqual(
            actions,
            [
                {
                    "action_type": "send_text",
                    "chat_id": "room-history",
                    "text": "📝 No transactions",
                }
            ],
        )

    def test_settlement_command_closes_accounting_period_window(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-settle",
            chat_id="room-settle",
            chat_name="结算群",
            group_num=3,
        )
        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-settle-seed",
                chat_id="room-settle",
                chat_name="结算群",
                text="+100rmb",
            )
        )

        actions = self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-settle-1",
                chat_id="room-settle",
                chat_name="结算群",
                text="/js",
            )
        )

        self.assertEqual(len(self.db.list_accounting_periods()), 1)
        self.assertEqual(self.db.get_unsettled_transactions("wechat:room-settle"), [])
        self.assertEqual(actions[0]["action_type"], "send_text")
        self.assertEqual(actions[0]["chat_id"], "room-settle")
        self.assertIn("Accounting period closed", actions[0]["text"])
        self.assertIn("Transactions: 1", actions[0]["text"])

    def test_all_settlement_command_closes_current_window_for_all_groups(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-settle-a",
            chat_id="room-settle-a",
            chat_name="结算群-A",
            group_num=3,
        )
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-settle-b",
            chat_id="room-settle-b",
            chat_name="结算群-B",
            group_num=4,
        )
        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-settle-a-seed",
                chat_id="room-settle-a",
                chat_name="结算群-A",
                text="+100rmb",
            )
        )
        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-settle-b-seed",
                chat_id="room-settle-b",
                chat_name="结算群-B",
                text="+50rmb",
            )
        )

        actions = self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-all-settle-1",
                chat_id="room-settle-a",
                chat_name="结算群-A",
                text="/alljs",
            )
        )

        periods = self.db.list_accounting_periods()
        self.assertEqual(len(periods), 1)
        self.assertEqual(self.db.get_groups_with_unsettled_transactions(), [])
        snapshots = self.db.list_period_group_snapshots(int(periods[0]["id"]))
        self.assertEqual(len(snapshots), 2)
        self.assertEqual(len(actions), 3)
        summary_actions = [action for action in actions if "Accounting period closed" in str(action.get("text") or "")]
        self.assertEqual(len(summary_actions), 1)
        self.assertEqual(summary_actions[0]["chat_id"], "room-settle-a")
        self.assertIn("Groups: 2", summary_actions[0]["text"])
        receipt_actions = [action for action in actions if "Closing Balance" in str(action.get("text") or "")]
        self.assertEqual(len(receipt_actions), 2)
        self.assertEqual({action["chat_id"] for action in receipt_actions}, {"room-settle-a", "room-settle-b"})

    def test_command_handler_uses_action_collector_boundary(self) -> None:
        from bookkeeping_core.commands import CommandHandler
        from bookkeeping_core.contracts import CoreActionCollector

        handler = CommandHandler(self.db, ["master-user"], self.export_dir)
        collector = CoreActionCollector()

        handler.set_action_collector(collector)
        handler.handle_command(
            platform="wechat",
            group_key="wechat:room-a",
            chat_id="room-a",
            chat_name="客户群-A",
            sender_id="master-user",
            sender_name="Master",
            command_text="/set 2",
        )

        self.assertEqual(
            collector.actions,
            [
                {
                    "action_type": "send_text",
                    "chat_id": "room-a",
                    "text": "✅ This group assigned to Group 2\nOnly groups with numbers can use bookkeeping",
                }
            ],
        )

    def test_command_handler_does_not_expose_transport_boundary(self) -> None:
        from bookkeeping_core.commands import CommandHandler

        handler = CommandHandler(self.db, ["master-user"], self.export_dir)

        self.assertTrue(hasattr(handler, "set_action_collector"))
        self.assertFalse(hasattr(handler, "set_transport"))

    def test_same_transaction_text_from_wechat_and_whatsapp_produces_same_facts(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-wx",
            chat_id="room-wx",
            chat_name="微信客户群",
            group_num=5,
        )
        self.db.set_group(
            platform="whatsapp",
            group_key="whatsapp:12036349999@g.us",
            chat_id="12036349999@g.us",
            chat_name="WhatsApp客户群",
            group_num=5,
        )

        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-wx-1",
                chat_id="room-wx",
                chat_name="微信客户群",
                text="+100rmb",
            )
        )
        self.runtime.process_envelope(
            self._message(
                platform="whatsapp",
                message_id="msg-wa-1",
                chat_id="12036349999@g.us",
                chat_name="WhatsApp客户群",
                text="+100rmb",
            )
        )

        wx_row = self.db.get_history("wechat:room-wx", 1)[0]
        wa_row = self.db.get_history("whatsapp:12036349999@g.us", 1)[0]

        compared_fields = [
            "input_sign",
            "amount",
            "category",
            "rate",
            "rmb_value",
            "raw",
            "group_num",
            "sender_id",
            "sender_name",
        ]
        for field in compared_fields:
            self.assertEqual(wx_row[field], wa_row[field], field)

    def test_runtime_transaction_created_at_does_not_reuse_received_at(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-created-at",
            chat_id="room-created-at",
            chat_name="创建时间测试群",
            group_num=5,
        )

        self.runtime.process_envelope(
            NormalizedMessageEnvelope.from_dict(
                {
                    "platform": "wechat",
                    "message_id": "msg-created-at-1",
                    "chat_id": "room-created-at",
                    "chat_name": "创建时间测试群",
                    "is_group": True,
                    "sender_id": "master-user",
                    "sender_name": "Master",
                    "sender_kind": "user",
                    "content_type": "text",
                    "text": "+100rmb",
                    "received_at": "2099-01-01 00:00:00",
                }
            )
        )

        row = self.db.get_history("wechat:room-created-at", 1)[0]

        self.assertNotEqual(row["created_at"], "2099-01-01 00:00:00")

    def test_incoming_group_message_refreshes_group_and_quote_profile_chat_name(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-rename",
            chat_id="room-rename",
            chat_name="旧群名",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-rename",
            chat_name="旧群名",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {"version": "group-parser-v1", "defaults": {}, "sections": []},
                ensure_ascii=False,
            ),
        )

        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-rename-1",
                chat_id="room-rename",
                chat_name="新群名",
                text="普通聊天，不记账",
            )
        )

        group_row = self.db.get_group_by_key("wechat:room-rename")
        self.assertEqual(str(group_row["chat_name"]), "新群名")
        profile_row = self.db.get_quote_group_profile(platform="wechat", chat_id="room-rename")
        self.assertEqual(str(profile_row["chat_name"]), "新群名")

    def test_whoami_command_returns_observed_and_canonical_identity_before_group_activation(self) -> None:
        self.db.bind_identity(
            platform="wechat",
            chat_id="room-whoami",
            observed_id="wx-user-1",
            observed_name="微信用户一",
            canonical_id="canonical-user-1",
        )

        actions = self.runtime.process_envelope(
            NormalizedMessageEnvelope.from_dict(
                {
                    "platform": "wechat",
                    "message_id": "msg-whoami-1",
                    "chat_id": "room-whoami",
                    "chat_name": "身份群",
                    "is_group": True,
                    "sender_id": "wx-user-1",
                    "sender_name": "微信用户一",
                    "sender_kind": "user",
                    "content_type": "text",
                    "text": "/whoami",
                    "received_at": "2026-03-21 10:00:00",
                }
            )
        )

        self.assertEqual(
            actions,
            [
                {
                    "action_type": "send_text",
                    "chat_id": "room-whoami",
                    "text": "name=微信用户一\nobserved_id=wx-user-1\nid=canonical-user-1\nis_master=false",
                }
            ],
        )

    def test_bind_command_binds_whatsapp_identity_before_group_activation(self) -> None:
        self.db.add_to_whitelist("+85212345678", "system", "bootstrap")

        actions = self.runtime.process_envelope(
            NormalizedMessageEnvelope.from_dict(
                {
                    "platform": "whatsapp",
                    "message_id": "msg-bind-1",
                    "chat_id": "12036349999@g.us",
                    "chat_name": "WhatsApp客户群",
                    "is_group": True,
                    "sender_id": "85299999999@s.whatsapp.net",
                    "sender_name": "85299999999@s.whatsapp.net",
                    "sender_kind": "user",
                    "content_type": "text",
                    "text": "/bind +85212345678",
                    "received_at": "2026-03-21 10:00:00",
                }
            )
        )

        self.assertEqual(
            actions,
            [
                {
                    "action_type": "send_text",
                    "chat_id": "12036349999@g.us",
                    "text": "绑定成功\nname=85299999999@s.whatsapp.net\nobserved_id=85299999999@s.whatsapp.net\ncanonical_id=+85212345678",
                }
            ],
        )
        self.assertEqual(
            self.db.resolve_identity(
                platform="whatsapp",
                chat_id="12036349999@g.us",
                observed_id="85299999999@s.whatsapp.net",
                observed_name="85299999999@s.whatsapp.net",
            ),
            "+85212345678",
        )

    def test_export_command_returns_send_file_action(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-export",
            chat_id="room-export",
            chat_name="导出群",
            group_num=7,
        )
        self.db.add_transaction(
            platform="wechat",
            group_key="wechat:room-export",
            group_num=7,
            chat_id="room-export",
            chat_name="导出群",
            sender_id="master-user",
            sender_name="Master",
            message_id="msg-export-seed",
            input_sign=1,
            amount=200,
            category="rmb",
            rate=None,
            rmb_value=200,
            raw="+200rmb",
        )

        actions = self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-export-1",
                chat_id="room-export",
                chat_name="导出群",
                text="/export",
            )
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "send_file")
        self.assertEqual(actions[0]["chat_id"], "room-export")
        self.assertTrue(str(actions[0]["file_path"]).endswith(".csv"))

    @staticmethod
    def _message(
        *,
        platform: str,
        message_id: str,
        chat_id: str,
        chat_name: str,
        text: str,
    ) -> NormalizedMessageEnvelope:
        return NormalizedMessageEnvelope.from_dict(
            {
                "platform": platform,
                "message_id": message_id,
                "chat_id": chat_id,
                "chat_name": chat_name,
                "is_group": True,
                "sender_id": "master-user",
                "sender_name": "Master",
                "sender_kind": "user",
                "content_type": "text",
                "text": text,
                "received_at": "2026-03-21 10:00:00",
            }
        )


if __name__ == "__main__":
    unittest.main()
