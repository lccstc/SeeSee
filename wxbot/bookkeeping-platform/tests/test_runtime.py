from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bookkeeping_core.contracts import NormalizedMessageEnvelope
from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.models import IncomingMessage
from bookkeeping_core.quote_publisher import QuoteFactPublishResult
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

    def test_fixed_code_text_does_not_trigger_invalid_transaction_reply(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-code",
            chat_id="room-code",
            chat_name="卡密群",
            group_num=3,
        )

        for message_id, text in (
            ("msg-code-1", "2V7CQ-FKT6F-KWWK7-V9GRM-N9X9Z"),
            ("msg-code-2", "2V7CQ-FKT6F-KWWK7-V9GRM-N9X9Z 100 done 5.03"),
            ("msg-code-3", "KJRVC-XPO7O-GZOPR 20 done"),
        ):
            actions = self.runtime.process_envelope(
                self._message(
                    platform="wechat",
                    message_id=message_id,
                    chat_id="room-code",
                    chat_name="卡密群",
                    text=text,
                )
            )
            self.assertEqual(actions, [])
        self.assertEqual(
            self.db.get_unsettled_transactions("wechat:room-code"),
            [],
        )
        rows, total = self.db.query_parse_results(
            platform="wechat",
            chat_id="room-code",
            limit=10,
            offset=0,
        )
        self.assertEqual(total, 3)
        self.assertTrue(
            all(row["classification"] == "normal_chat" for row in rows)
        )
        self.assertTrue(
            all(row["parse_status"] == "unparsable" for row in rows)
        )

    def test_ls_and_hd_categories_are_accepted(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-ls-hd",
            chat_id="room-ls-hd",
            chat_name="卡种群",
            group_num=3,
        )

        for index, text in enumerate(("+500ls3", "+80hd2.5"), start=1):
            actions = self.runtime.process_envelope(
                self._message(
                    platform="wechat",
                    message_id=f"msg-ls-hd-{index}",
                    chat_id="room-ls-hd",
                    chat_name="卡种群",
                    text=text,
                )
            )
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0]["action_type"], "send_text")
            self.assertEqual(actions[0]["chat_id"], "room-ls-hd")

        rows = self.db.get_unsettled_transactions("wechat:room-ls-hd")
        categories = [str(row["category"]) for row in rows]
        self.assertEqual(categories, ["ls", "hd"])
        self.assertEqual(round(float(rows[0]["rmb_value"]), 2), -1500.00)
        self.assertEqual(round(float(rows[1]["rmb_value"]), 2), -200.00)

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

    def test_runtime_quote_capture_persists_candidate_bundle_without_mutating_quote_price_rows(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-quotes-runtime",
            chat_id="room-quotes-runtime",
            chat_name="报价群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-quotes-runtime",
            chat_name="报价群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {
                    "version": "group-parser-v1",
                    "defaults": {},
                    "sections": [
                        {
                            "id": "apple-us-100",
                            "enabled": True,
                            "priority": 1,
                            "defaults": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                            },
                            "lines": [
                                {
                                    "kind": "quote",
                                    "pattern": "{country}={price}",
                                    "outputs": {
                                        "card_type": "Apple",
                                        "country_or_currency": "USD",
                                        "amount_range": "100",
                                        "form_factor": "横白卡",
                                    },
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        )

        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-quote-runtime-1",
                chat_id="room-quotes-runtime",
                chat_name="报价群",
                text="US=5.10\nUK=6.20",
            )
        )

        document = self._get_quote_document(
            platform="wechat",
            chat_id="room-quotes-runtime",
            message_id="msg-quote-runtime-1",
        )

        self.assertIsNotNone(document)
        assert document is not None
        self.assertEqual(str(document["run_kind"]), "runtime")
        self.assertIn("run_kind", document.keys())
        self.assertIn("replay_of_quote_document_id", document.keys())
        self.assertEqual(document["replay_of_quote_document_id"], None)
        self.assertTrue(str(document["message_fingerprint"]))
        self.assertGreater(float(document["confidence"]), 0.0)
        self.assertEqual(str(document["snapshot_hypothesis"]), "unresolved")
        self.assertEqual(str(document["snapshot_hypothesis_reason"]), "phase1-default")
        self.assertEqual(str(document["parser_kind"]), "group-parser")
        self.assertEqual(str(document["parser_template"]), "group-parser")
        self.assertEqual(str(document["parser_version"]), "group-parser-v1")

        candidate_rows = self.db.list_quote_candidate_rows(
            quote_document_id=int(document["id"])
        )
        self.assertEqual(len(candidate_rows), 1)
        self.assertEqual(str(candidate_rows[0]["source_line"]), "US=5.10")
        self.assertTrue(bool(candidate_rows[0]["row_publishable"]))
        self.assertEqual(
            str(candidate_rows[0]["publishability_basis"]),
            "parser_prevalidation",
        )
        field_sources = self._decode_json(candidate_rows[0]["field_sources_json"])
        self.assertEqual(
            field_sources["line_evidence"]["source_line"],
            "US=5.10",
        )
        self.assertEqual(field_sources["line_evidence"]["source_line_index"], 0)
        self.assertEqual(field_sources["price"]["raw_fragment"], "5.10")

        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=int(document["id"])
        )
        self.assertIsNotNone(validation_run)
        assert validation_run is not None
        self.assertEqual(str(validation_run["run_kind"]), "runtime")
        self.assertEqual(str(validation_run["message_decision"]), "publishable_rows_available")
        self.assertEqual(int(validation_run["candidate_row_count"]), 1)
        self.assertEqual(int(validation_run["publishable_row_count"]), 1)
        self.assertEqual(int(validation_run["rejected_row_count"]), 0)
        validation_rows = self.db.list_quote_validation_row_results(
            validation_run_id=int(validation_run["id"])
        )
        self.assertEqual(len(validation_rows), 1)
        self.assertEqual(str(validation_rows[0]["schema_status"]), "passed")
        self.assertEqual(str(validation_rows[0]["final_decision"]), "publishable")

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE message_id = ?",
            ("msg-quote-runtime-1",),
        )
        self.assertEqual(quote_price_row_count, 0)

        parse_exceptions = self.db.conn.execute(
            """
            SELECT reason, source_line
            FROM quote_parse_exceptions
            WHERE quote_document_id = ?
            ORDER BY id ASC
            """,
            (int(document["id"]),),
        ).fetchall()
        self.assertEqual(len(parse_exceptions), 1)
        self.assertEqual(str(parse_exceptions[0]["reason"]), "strict_match_failed")
        self.assertIn("UK=6.20", str(parse_exceptions[0]["source_line"]))

    def test_runtime_quote_capture_persists_mixed_validation_outcomes_and_publishable_helper(
        self,
    ) -> None:
        from bookkeeping_core.quote_candidates import (
            QuoteCandidateMessage,
            QuoteCandidateRow,
        )

        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-runtime-mixed",
            chat_id="room-runtime-mixed",
            chat_name="报价群-混合校验",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-runtime-mixed",
            chat_name="报价群-混合校验",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {"version": "group-parser-v1", "defaults": {}, "sections": []},
                ensure_ascii=False,
            ),
        )

        candidate = QuoteCandidateMessage(
            platform="wechat",
            source_group_key="wechat:room-runtime-mixed",
            chat_id="room-runtime-mixed",
            chat_name="报价群-混合校验",
            message_id="msg-runtime-mixed-1",
            source_name="报价员",
            sender_id="seller-runtime",
            sender_display="报价员",
            raw_message="patched mixed runtime candidate",
            message_time="2026-04-14 14:00:00",
            parser_kind="group-parser",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.99,
            parse_status="parsed",
            message_fingerprint="runtime-mixed-fingerprint",
            snapshot_hypothesis="unresolved",
            snapshot_hypothesis_reason="phase1-default",
            rows=[
                QuoteCandidateRow(
                    row_ordinal=1,
                    source_line="US=5.10",
                    source_line_index=0,
                    line_confidence=0.98,
                    normalized_sku_key="Apple|USD|100|横白卡",
                    normalization_status="normalized",
                    row_publishable=False,
                    publishability_basis="parser_prevalidation",
                    restriction_parse_status="parsed",
                    card_type="Apple",
                    country_or_currency="USD",
                    amount_range="100",
                    multiplier=None,
                    form_factor="横白卡",
                    price=5.10,
                    quote_status="active",
                    restriction_text="",
                ),
                QuoteCandidateRow(
                    row_ordinal=2,
                    source_line="UK=6.20",
                    source_line_index=1,
                    line_confidence=0.62,
                    normalized_sku_key="Apple|GBP|100|横白卡",
                    normalization_status="normalized",
                    row_publishable=True,
                    publishability_basis="parser_prevalidation",
                    restriction_parse_status="parsed",
                    card_type="Apple",
                    country_or_currency="GBP",
                    amount_range="100",
                    multiplier=None,
                    form_factor="横白卡",
                    price=6.20,
                    quote_status="active",
                    restriction_text="",
                ),
                QuoteCandidateRow(
                    row_ordinal=3,
                    source_line="Razer 100=7.10",
                    source_line_index=2,
                    line_confidence=0.97,
                    normalized_sku_key="Razer|USD|100|不限",
                    normalization_status="normalized",
                    row_publishable=True,
                    publishability_basis="parser_prevalidation",
                    restriction_parse_status="parsed",
                    card_type="Razer",
                    country_or_currency="USD",
                    amount_range="100",
                    multiplier=None,
                    form_factor="不限",
                    price=7.10,
                    quote_status="inactive",
                    restriction_text="",
                ),
            ],
        )

        with patch(
            "bookkeeping_core.quotes.should_attempt_template_quote_capture",
            return_value=True,
        ), patch(
            "bookkeeping_core.quotes._parse_quote_message_to_candidate_details",
            return_value=(candidate, [], []),
        ):
            self.runtime.process_envelope(
                self._message(
                    platform="wechat",
                    message_id="msg-runtime-mixed-1",
                    chat_id="room-runtime-mixed",
                    chat_name="报价群-混合校验",
                    text="patched mixed runtime candidate",
                )
            )

        document = self._get_quote_document(
            platform="wechat",
            chat_id="room-runtime-mixed",
            message_id="msg-runtime-mixed-1",
        )
        self.assertIsNotNone(document)
        assert document is not None

        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=int(document["id"])
        )
        self.assertIsNotNone(validation_run)
        assert validation_run is not None
        self.assertEqual(str(validation_run["message_decision"]), "mixed_outcome")
        self.assertEqual(int(validation_run["candidate_row_count"]), 3)
        self.assertEqual(int(validation_run["publishable_row_count"]), 1)
        self.assertEqual(int(validation_run["rejected_row_count"]), 1)
        self.assertEqual(int(validation_run["held_row_count"]), 1)

        validation_rows = self.db.list_quote_validation_row_results(
            validation_run_id=int(validation_run["id"])
        )
        self.assertEqual(
            [str(row["final_decision"]) for row in validation_rows],
            ["publishable", "held", "rejected"],
        )

        candidate_rows = self.db.list_quote_candidate_rows(
            quote_document_id=int(document["id"])
        )
        self.assertEqual([bool(row["row_publishable"]) for row in candidate_rows], [False, True, True])

        publishable_rows = self.db.list_publishable_quote_candidate_rows(
            quote_document_id=int(document["id"])
        )
        self.assertEqual(len(publishable_rows), 1)
        self.assertEqual(str(publishable_rows[0]["source_line"]), "US=5.10")
        self.assertFalse(bool(publishable_rows[0]["row_publishable"]))
        self.assertEqual(str(publishable_rows[0]["final_decision"]), "publishable")
        self.assertEqual(str(publishable_rows[0]["business_status"]), "passed")

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE message_id = ?",
            ("msg-runtime-mixed-1",),
        )
        self.assertEqual(quote_price_row_count, 0)

        exceptions = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE quote_document_id = ?
            ORDER BY id ASC
            """,
            (int(document["id"]),),
        ).fetchall()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(str(exceptions[0]["reason"]), "validator_mixed_outcome")
        self.assertIn("UK=6.20", str(exceptions[0]["source_line"]))
        self.assertIn("Razer 100=7.10", str(exceptions[0]["source_line"]))

        repair_case = self.db.conn.execute(
            """
            SELECT *
            FROM quote_repair_cases
            WHERE origin_exception_id = ?
            LIMIT 1
            """,
            (int(exceptions[0]["id"]),),
        ).fetchone()
        self.assertIsNotNone(repair_case)
        assert repair_case is not None
        self.assertEqual(
            int(repair_case["origin_validation_run_id"]),
            int(validation_run["id"]),
        )

    def test_runtime_quote_capture_calls_guarded_publisher_with_validator_owned_rows(
        self,
    ) -> None:
        from bookkeeping_core.quote_candidates import (
            QuoteCandidateMessage,
            QuoteCandidateRow,
        )

        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-runtime-publisher",
            chat_id="room-runtime-publisher",
            chat_name="报价群-publisher",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-runtime-publisher",
            chat_name="报价群-publisher",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {"version": "group-parser-v1", "defaults": {}, "sections": []},
                ensure_ascii=False,
            ),
        )

        candidate = QuoteCandidateMessage(
            platform="wechat",
            source_group_key="wechat:room-runtime-publisher",
            chat_id="room-runtime-publisher",
            chat_name="报价群-publisher",
            message_id="msg-runtime-publisher-1",
            source_name="报价员",
            sender_id="seller-runtime",
            sender_display="报价员",
            raw_message="patched mixed runtime candidate",
            message_time="2026-04-15 10:00:00",
            parser_kind="group-parser",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.99,
            parse_status="parsed",
            message_fingerprint="runtime-publisher-fingerprint",
            snapshot_hypothesis="unresolved",
            snapshot_hypothesis_reason="phase1-default",
            rows=[
                QuoteCandidateRow(
                    row_ordinal=1,
                    source_line="US=5.10",
                    source_line_index=0,
                    line_confidence=0.98,
                    normalized_sku_key="Apple|USD|100|横白卡",
                    normalization_status="normalized",
                    row_publishable=False,
                    publishability_basis="parser_prevalidation",
                    restriction_parse_status="parsed",
                    card_type="Apple",
                    country_or_currency="USD",
                    amount_range="100",
                    multiplier=None,
                    form_factor="横白卡",
                    price=5.10,
                    quote_status="active",
                    restriction_text="",
                ),
                QuoteCandidateRow(
                    row_ordinal=2,
                    source_line="UK=6.20",
                    source_line_index=1,
                    line_confidence=0.62,
                    normalized_sku_key="Apple|GBP|100|横白卡",
                    normalization_status="normalized",
                    row_publishable=True,
                    publishability_basis="parser_prevalidation",
                    restriction_parse_status="parsed",
                    card_type="Apple",
                    country_or_currency="GBP",
                    amount_range="100",
                    multiplier=None,
                    form_factor="横白卡",
                    price=6.20,
                    quote_status="active",
                    restriction_text="",
                ),
            ],
        )

        with patch(
            "bookkeeping_core.quotes.should_attempt_template_quote_capture",
            return_value=True,
        ), patch(
            "bookkeeping_core.quotes._parse_quote_message_to_candidate_details",
            return_value=(candidate, [], []),
        ), patch(
            "bookkeeping_core.quote_publisher.QuoteFactPublisher.publish_quote_document",
            autospec=True,
            side_effect=lambda _publisher, **kwargs: QuoteFactPublishResult.no_op(
                quote_document_id=int(kwargs["quote_document_id"]),
                validation_run_id=int(kwargs["validation_run_id"]),
                source_group_key=str(kwargs["source_group_key"]),
                publish_mode=str(kwargs["publish_mode"]),
                reason="runtime_validation_only",
                attempted_row_count=len(kwargs["publishable_rows"]),
            ),
        ) as publish_mock:
            self.runtime.process_envelope(
                self._message(
                    platform="wechat",
                    message_id="msg-runtime-publisher-1",
                    chat_id="room-runtime-publisher",
                    chat_name="报价群-publisher",
                    text="patched mixed runtime candidate",
                )
            )

        document = self._get_quote_document(
            platform="wechat",
            chat_id="room-runtime-publisher",
            message_id="msg-runtime-publisher-1",
        )
        self.assertIsNotNone(document)
        assert document is not None
        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=int(document["id"])
        )
        self.assertIsNotNone(validation_run)
        assert validation_run is not None

        publish_mock.assert_called_once()
        call_kwargs = publish_mock.call_args.kwargs
        self.assertEqual(call_kwargs["publish_mode"], "validation_only")
        self.assertEqual(call_kwargs["quote_document_id"], int(document["id"]))
        self.assertEqual(call_kwargs["validation_run_id"], int(validation_run["id"]))
        self.assertEqual(len(call_kwargs["publishable_rows"]), 1)
        self.assertEqual(str(call_kwargs["publishable_rows"][0]["source_line"]), "US=5.10")
        self.assertFalse(bool(call_kwargs["publishable_rows"][0]["row_publishable"]))
        self.assertEqual(
            str(call_kwargs["publishable_rows"][0]["final_decision"]),
            "publishable",
        )

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE message_id = ?",
            ("msg-runtime-publisher-1",),
        )
        self.assertEqual(quote_price_row_count, 0)

    def test_runtime_quote_capture_returns_explicit_noop_publish_result(self) -> None:
        from bookkeeping_core.quote_candidates import (
            QuoteCandidateMessage,
            QuoteCandidateRow,
        )

        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-runtime-noop",
            chat_id="room-runtime-noop",
            chat_name="报价群-noop",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-runtime-noop",
            chat_name="报价群-noop",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {"version": "group-parser-v1", "defaults": {}, "sections": []},
                ensure_ascii=False,
            ),
        )

        candidate = QuoteCandidateMessage(
            platform="wechat",
            source_group_key="wechat:room-runtime-noop",
            chat_id="room-runtime-noop",
            chat_name="报价群-noop",
            message_id="msg-runtime-noop-1",
            source_name="报价员",
            sender_id="seller-runtime-noop",
            sender_display="报价员",
            raw_message="patched runtime no-op candidate",
            message_time="2026-04-15 12:00:00",
            parser_kind="group-parser",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.99,
            parse_status="parsed",
            message_fingerprint="runtime-noop-fingerprint",
            snapshot_hypothesis="unresolved",
            snapshot_hypothesis_reason="phase1-default",
            rows=[
                QuoteCandidateRow(
                    row_ordinal=1,
                    source_line="US=5.10",
                    source_line_index=0,
                    line_confidence=0.98,
                    normalized_sku_key="Apple|USD|100|横白卡",
                    normalization_status="normalized",
                    row_publishable=False,
                    publishability_basis="parser_prevalidation",
                    restriction_parse_status="parsed",
                    card_type="Apple",
                    country_or_currency="USD",
                    amount_range="100",
                    multiplier=None,
                    form_factor="横白卡",
                    price=5.10,
                    quote_status="active",
                    restriction_text="",
                )
            ],
        )

        with patch(
            "bookkeeping_core.quotes.should_attempt_template_quote_capture",
            return_value=True,
        ), patch(
            "bookkeeping_core.quotes._parse_quote_message_to_candidate_details",
            return_value=(candidate, [], []),
        ):
            result = self.runtime.quote_capture.capture_from_message(
                self._message(
                    platform="wechat",
                    message_id="msg-runtime-noop-1",
                    chat_id="room-runtime-noop",
                    chat_name="报价群-noop",
                    text="patched runtime no-op candidate",
                )
            )

        self.assertTrue(result["captured"])
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["exceptions"], 0)
        self.assertEqual(result["publish_result"]["status"], "no_op")
        self.assertEqual(
            result["publish_result"]["publish_mode"],
            "validation_only",
        )
        self.assertEqual(result["publish_result"]["reason"], "runtime_validation_only")
        self.assertEqual(result["publish_result"]["attempted_row_count"], 1)
        self.assertEqual(result["publish_result"]["applied_row_count"], 0)

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE message_id = ?",
            ("msg-runtime-noop-1",),
        )
        self.assertEqual(quote_price_row_count, 0)

    def test_runtime_quote_capture_records_missing_template_candidate_header(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-missing-template",
            chat_id="room-missing-template",
            chat_name="缺模板报价群",
            group_num=5,
        )

        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-missing-template-1",
                chat_id="room-missing-template",
                chat_name="缺模板报价群",
                text="【Apple】\nUS=5.10\nUK=6.20",
            )
        )

        document = self._get_quote_document(
            platform="wechat",
            chat_id="room-missing-template",
            message_id="msg-missing-template-1",
        )

        self.assertIsNotNone(document)
        assert document is not None
        self.assertEqual(str(document["run_kind"]), "runtime")
        self.assertEqual(document["replay_of_quote_document_id"], None)
        self.assertTrue(str(document["message_fingerprint"]))
        self.assertEqual(float(document["confidence"]), 0.0)
        self.assertEqual(str(document["snapshot_hypothesis"]), "unresolved")
        self.assertEqual(str(document["snapshot_hypothesis_reason"]), "phase1-default")
        self.assertEqual(str(document["parser_kind"]), "group-parser")
        self.assertEqual(str(document["parse_status"]), "empty")
        rejection_reasons = self._decode_json(document["rejection_reasons_json"])
        self.assertEqual(len(rejection_reasons), 1)
        self.assertEqual(rejection_reasons[0]["reason"], "missing_group_template")

        candidate_rows = self.db.list_quote_candidate_rows(
            quote_document_id=int(document["id"])
        )
        self.assertEqual(candidate_rows, [])

        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=int(document["id"])
        )
        self.assertIsNotNone(validation_run)
        assert validation_run is not None
        self.assertEqual(str(validation_run["message_decision"]), "no_publish")
        self.assertEqual(int(validation_run["candidate_row_count"]), 0)
        self.assertEqual(int(validation_run["publishable_row_count"]), 0)
        self.assertEqual(
            self.db.list_quote_validation_row_results(
                validation_run_id=int(validation_run["id"])
            ),
            [],
        )
        validation_summary = self._decode_json(validation_run["summary_json"])
        self.assertEqual(
            validation_summary["message_reasons"][0]["code"],
            "message_no_candidate_rows",
        )

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE message_id = ?",
            ("msg-missing-template-1",),
        )
        self.assertEqual(quote_price_row_count, 0)

        parse_exceptions = self.db.conn.execute(
            """
            SELECT reason, source_line
            FROM quote_parse_exceptions
            WHERE quote_document_id = ?
            ORDER BY id ASC
            """,
            (int(document["id"]),),
        ).fetchall()
        self.assertEqual(len(parse_exceptions), 1)
        self.assertEqual(str(parse_exceptions[0]["reason"]), "missing_group_template")
        self.assertEqual(str(parse_exceptions[0]["source_line"]), "【Apple】")

    def test_runtime_sanitizes_polluted_supermarket_profile_countries(self) -> None:
        self.db.set_group(
            platform="whatsapp",
            group_key="whatsapp:room-supermarket-sanitize",
            chat_id="room-supermarket-sanitize",
            chat_name="污染超市卡群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="whatsapp",
            chat_id="room-supermarket-sanitize",
            chat_name="污染超市卡群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="不限",
            parser_template="supermarket-card",
            template_config=json.dumps(
                {
                    "version": "group-parser-v1",
                    "defaults": {},
                    "sections": [
                        {
                            "id": "section-1",
                            "enabled": True,
                            "priority": 10,
                            "label": "Apple",
                            "defaults": {
                                "card_type": "Apple",
                                "country_or_currency": "横白卡图",
                                "form_factor": "不限",
                            },
                            "lines": [
                                {
                                    "kind": "quote",
                                    "pattern": "横白卡图:{amount}={price}(单张清晰)",
                                    "outputs": {
                                        "card_type": "Apple",
                                        "country_or_currency": "横白卡图",
                                        "form_factor": "不限",
                                        "amount_range": "100-150",
                                    },
                                }
                            ],
                        },
                        {
                            "id": "section-2",
                            "enabled": True,
                            "priority": 20,
                            "label": "Apple",
                            "defaults": {
                                "card_type": "Apple",
                                "country_or_currency": "整卡卡密",
                                "form_factor": "不限",
                            },
                            "lines": [
                                {
                                    "kind": "quote",
                                    "pattern": "整卡卡密:{amount}={price}(50倍数)",
                                    "outputs": {
                                        "card_type": "Apple",
                                        "country_or_currency": "整卡卡密",
                                        "form_factor": "不限",
                                        "amount_range": "100-500",
                                    },
                                }
                            ],
                        },
                    ],
                },
                ensure_ascii=False,
            ),
        )

        self.runtime.process_envelope(
            self._message(
                platform="whatsapp",
                message_id="msg-runtime-supermarket-sanitize-1",
                chat_id="room-supermarket-sanitize",
                chat_name="污染超市卡群",
                text=(
                    "iTunes US 快刷\n"
                    "横白卡图：100/150=5.38（单张清晰）\n"
                    "整卡卡密：100-500=5.2（50倍数）\n"
                ),
            )
        )

        document = self._get_quote_document(
            platform="whatsapp",
            chat_id="room-supermarket-sanitize",
            message_id="msg-runtime-supermarket-sanitize-1",
        )
        self.assertIsNotNone(document)
        assert document is not None

        candidate_rows = self.db.list_quote_candidate_rows(
            quote_document_id=int(document["id"])
        )
        self.assertEqual(len(candidate_rows), 2)
        self.assertEqual(
            [str(row["country_or_currency"]) for row in candidate_rows],
            ["USD", "USD"],
        )
        self.assertEqual(
            [str(row["form_factor"]) for row in candidate_rows],
            ["横白卡", "代码"],
        )

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

    def _get_quote_document(
        self,
        *,
        platform: str,
        chat_id: str,
        message_id: str,
    ):
        return self.db.conn.execute(
            """
            SELECT *
            FROM quote_documents
            WHERE platform = ? AND chat_id = ? AND message_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (platform, chat_id, message_id),
        ).fetchone()

    @staticmethod
    def _decode_json(value):
        if isinstance(value, (dict, list)):
            return value
        return json.loads(str(value))

    def _count_rows(
        self,
        table_name: str,
        where_clause: str = "",
        params: tuple[object, ...] = (),
    ) -> int:
        row = self.db.conn.execute(
            f"SELECT COUNT(*) AS cnt FROM {table_name} {where_clause}",
            params,
        ).fetchone()
        return int(row["cnt"] or 0)

    def _upsert_bootstrap_profile(
        self,
        *,
        fixture_name: str,
        platform: str,
        chat_id: str,
        chat_name: str,
    ) -> dict:
        from scripts.bootstrap_quote_group_profiles import build_bootstrap_profile_payload

        payload = build_bootstrap_profile_payload(
            fixture_name=fixture_name,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
        )
        self.db.upsert_quote_group_profile(
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            default_card_type=str(payload["default_card_type"]),
            default_country_or_currency=str(payload["default_country_or_currency"]),
            default_form_factor=str(payload["default_form_factor"]),
            default_multiplier=str(payload["default_multiplier"]),
            parser_template=str(payload["parser_template"]),
            stale_after_minutes=int(payload["stale_after_minutes"]),
            note=str(payload["note"]),
            template_config=json.dumps(payload["template_config"], ensure_ascii=False),
        )
        return payload


class RuntimeRepairCaseTests(PostgresTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.export_dir = self.temp_path / "exports"
        self.db = BookkeepingDB(self.make_dsn("runtime-repair-cases"))
        self.runtime = UnifiedBookkeepingRuntime(
            db=self.db,
            master_users=["master-user"],
            export_dir=self.export_dir,
        )

    def tearDown(self) -> None:
        self.db.close()
        super().tearDown()

    def test_parse_failures_open_repair_cases_for_strict_match_and_missing_template(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-repair-parse",
            chat_id="room-repair-parse",
            chat_name="修复解析群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-repair-parse",
            chat_name="修复解析群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {
                    "version": "group-parser-v1",
                    "defaults": {},
                    "sections": [
                        {
                            "id": "apple-us-100",
                            "enabled": True,
                            "priority": 1,
                            "defaults": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                            },
                            "lines": [
                                {
                                    "kind": "quote",
                                    "pattern": "{country}={price}",
                                    "outputs": {
                                        "card_type": "Apple",
                                        "country_or_currency": "USD",
                                        "amount_range": "100",
                                        "form_factor": "横白卡",
                                    },
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        )

        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-repair-strict-1",
                chat_id="room-repair-parse",
                chat_name="修复解析群",
                text="US=5.10\nUK=6.20",
            )
        )

        strict_document = self._get_quote_document(
            platform="wechat",
            chat_id="room-repair-parse",
            message_id="msg-repair-strict-1",
        )
        self.assertIsNotNone(strict_document)
        assert strict_document is not None
        strict_validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=int(strict_document["id"])
        )
        strict_exception = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE quote_document_id = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (int(strict_document["id"]),),
        ).fetchone()
        self.assertIsNotNone(strict_exception)
        assert strict_exception is not None
        strict_repair_case = self.db.conn.execute(
            """
            SELECT *
            FROM quote_repair_cases
            WHERE origin_exception_id = ?
            LIMIT 1
            """,
            (int(strict_exception["id"]),),
        ).fetchone()
        self.assertIsNotNone(strict_repair_case)
        assert strict_validation_run is not None
        assert strict_repair_case is not None
        self.assertEqual(str(strict_exception["reason"]), "strict_match_failed")
        self.assertEqual(
            int(strict_repair_case["origin_quote_document_id"]),
            int(strict_document["id"]),
        )
        self.assertEqual(
            int(strict_repair_case["origin_validation_run_id"]),
            int(strict_validation_run["id"]),
        )
        self.assertIn(
            str(strict_repair_case["lifecycle_state"]),
            {"ready_for_attempt", "attempt_failed", "closed_resolved", "escalated"},
        )
        self.assertIsNotNone(strict_repair_case["baseline_attempt_id"])
        strict_summary = self.db.get_quote_repair_case_summary(
            repair_case_id=int(strict_repair_case["id"])
        )
        self.assertIsNotNone(strict_summary)
        assert strict_summary is not None
        self.assertGreaterEqual(int(strict_summary["attempt_count"]), 1)
        self.assertEqual(strict_summary["baseline_attempt_id"], int(strict_repair_case["baseline_attempt_id"]))
        self.assertIn(
            str(strict_summary["last_attempt_outcome"] or ""),
            {"pending", "blocked", "completed"},
        )
        strict_attempts = self.db.list_quote_repair_case_attempts(
            repair_case_id=int(strict_repair_case["id"])
        )
        strict_remediation = [
            item for item in strict_attempts if str(item.get("attempt_kind") or "") == "remediation"
        ]
        self.assertGreaterEqual(len(strict_remediation), 1)
        strict_attempt_summary = strict_remediation[0]["attempt_summary_json"]
        if isinstance(strict_attempt_summary, str):
            strict_attempt_summary = json.loads(strict_attempt_summary)
        self.assertEqual(strict_attempt_summary["proposal_scope"], "group_profile")

        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-repair-missing-template",
            chat_id="room-repair-missing-template",
            chat_name="修复缺模板群",
            group_num=5,
        )
        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id="msg-repair-missing-template-1",
                chat_id="room-repair-missing-template",
                chat_name="修复缺模板群",
                text="【Apple】\nUS=5.10\nUK=6.20",
            )
        )

        missing_document = self._get_quote_document(
            platform="wechat",
            chat_id="room-repair-missing-template",
            message_id="msg-repair-missing-template-1",
        )
        self.assertIsNotNone(missing_document)
        assert missing_document is not None
        missing_validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=int(missing_document["id"])
        )
        missing_exception = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE quote_document_id = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (int(missing_document["id"]),),
        ).fetchone()
        self.assertIsNotNone(missing_exception)
        assert missing_exception is not None
        missing_repair_case = self.db.conn.execute(
            """
            SELECT *
            FROM quote_repair_cases
            WHERE origin_exception_id = ?
            LIMIT 1
            """,
            (int(missing_exception["id"]),),
        ).fetchone()
        self.assertIsNotNone(missing_repair_case)
        assert missing_validation_run is not None
        assert missing_repair_case is not None
        self.assertEqual(str(missing_exception["reason"]), "missing_group_template")
        self.assertEqual(
            int(missing_repair_case["origin_quote_document_id"]),
            int(missing_document["id"]),
        )
        self.assertEqual(
            int(missing_repair_case["origin_validation_run_id"]),
            int(missing_validation_run["id"]),
        )
        self.assertIn(
            str(missing_repair_case["lifecycle_state"]),
            {"ready_for_attempt", "attempt_failed", "closed_resolved", "escalated"},
        )
        self.assertIsNotNone(missing_repair_case["baseline_attempt_id"])
        missing_summary = self.db.get_quote_repair_case_summary(
            repair_case_id=int(missing_repair_case["id"])
        )
        self.assertIsNotNone(missing_summary)
        assert missing_summary is not None
        self.assertGreaterEqual(int(missing_summary["attempt_count"]), 1)
        self.assertIn(
            str(missing_summary["last_attempt_outcome"] or ""),
            {"pending", "blocked", "completed"},
        )
        missing_attempts = self.db.list_quote_repair_case_attempts(
            repair_case_id=int(missing_repair_case["id"])
        )
        missing_remediation = [
            item for item in missing_attempts if str(item.get("attempt_kind") or "") == "remediation"
        ]
        self.assertGreaterEqual(len(missing_remediation), 1)
        missing_attempt_summary = missing_remediation[0]["attempt_summary_json"]
        if isinstance(missing_attempt_summary, str):
            missing_attempt_summary = json.loads(missing_attempt_summary)
        self.assertEqual(missing_attempt_summary["proposal_scope"], "bootstrap")

        self.assertEqual(
            self._count_rows("quote_price_rows", "WHERE source_group_key IN (?, ?)", ("wechat:room-repair-parse", "wechat:room-repair-missing-template")),
            0,
        )

    def test_validator_no_publish_outcomes_open_exception_and_repair_case(self) -> None:
        from bookkeeping_core.quote_candidates import (
            QuoteCandidateMessage,
            QuoteCandidateRow,
        )

        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-repair-validator",
            chat_id="room-repair-validator",
            chat_name="修复校验群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-repair-validator",
            chat_name="修复校验群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {"version": "group-parser-v1", "defaults": {}, "sections": []},
                ensure_ascii=False,
            ),
        )

        candidate = QuoteCandidateMessage(
            platform="wechat",
            source_group_key="wechat:room-repair-validator",
            chat_id="room-repair-validator",
            chat_name="修复校验群",
            message_id="msg-repair-validator-1",
            source_name="报价员",
            sender_id="seller-runtime",
            sender_display="报价员",
            raw_message="validator no publish candidate",
            message_time="2026-04-14 14:30:00",
            parser_kind="group-parser",
            parser_template="group-parser",
            parser_version="group-parser-v1",
            confidence=0.92,
            parse_status="parsed",
            message_fingerprint="repair-validator-fingerprint",
            snapshot_hypothesis="unresolved",
            snapshot_hypothesis_reason="phase1-default",
            rows=[
                QuoteCandidateRow(
                    row_ordinal=1,
                    source_line="US=5.10",
                    source_line_index=0,
                    line_confidence=0.61,
                    normalized_sku_key="Apple|USD|100|横白卡",
                    normalization_status="normalized",
                    row_publishable=True,
                    publishability_basis="parser_prevalidation",
                    restriction_parse_status="ambiguous",
                    card_type="Apple",
                    country_or_currency="USD",
                    amount_range="100",
                    multiplier=None,
                    form_factor="横白卡",
                    price=5.10,
                    quote_status="active",
                    restriction_text="ask first",
                ),
                QuoteCandidateRow(
                    row_ordinal=2,
                    source_line="US inactive=6.10",
                    source_line_index=1,
                    line_confidence=0.95,
                    normalized_sku_key="Apple|USD|200|横白卡",
                    normalization_status="normalized",
                    row_publishable=True,
                    publishability_basis="parser_prevalidation",
                    restriction_parse_status="parsed",
                    card_type="Apple",
                    country_or_currency="USD",
                    amount_range="200",
                    multiplier=None,
                    form_factor="横白卡",
                    price=6.10,
                    quote_status="inactive",
                    restriction_text="",
                ),
            ],
        )

        with patch(
            "bookkeeping_core.quotes.should_attempt_template_quote_capture",
            return_value=True,
        ), patch(
            "bookkeeping_core.quotes._parse_quote_message_to_candidate_details",
            return_value=(candidate, [], []),
        ):
            self.runtime.process_envelope(
                self._message(
                    platform="wechat",
                    message_id="msg-repair-validator-1",
                    chat_id="room-repair-validator",
                    chat_name="修复校验群",
                    text="validator no publish candidate",
                )
            )

        document = self._get_quote_document(
            platform="wechat",
            chat_id="room-repair-validator",
            message_id="msg-repair-validator-1",
        )
        self.assertIsNotNone(document)
        assert document is not None

        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=int(document["id"])
        )
        self.assertIsNotNone(validation_run)
        assert validation_run is not None
        self.assertEqual(str(validation_run["message_decision"]), "no_publish")

        exceptions = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE quote_document_id = ?
            ORDER BY id ASC
            """,
            (int(document["id"]),),
        ).fetchall()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(str(exceptions[0]["reason"]), "validator_no_publish")

        repair_case = self.db.conn.execute(
            """
            SELECT *
            FROM quote_repair_cases
            WHERE origin_exception_id = ?
            LIMIT 1
            """,
            (int(exceptions[0]["id"]),),
        ).fetchone()
        self.assertIsNotNone(repair_case)
        assert repair_case is not None
        self.assertEqual(
            int(repair_case["origin_validation_run_id"]),
            int(validation_run["id"]),
        )
        self.assertTrue(str(repair_case["current_failure_reason"] or "").strip())
        self.assertIn(
            str(repair_case["lifecycle_state"]),
            {"ready_for_attempt", "attempt_failed", "closed_resolved", "escalated"},
        )
        self.assertIsNotNone(repair_case["baseline_attempt_id"])
        summary = self.db.get_quote_repair_case_summary(
            repair_case_id=int(repair_case["id"])
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertGreaterEqual(int(summary["attempt_count"]), 1)
        self.assertIn(
            str(summary["last_attempt_outcome"] or ""),
            {"pending", "blocked", "completed"},
        )

        self.assertEqual(
            self._count_rows(
                "quote_price_rows",
                "WHERE message_id = ?",
                ("msg-repair-validator-1",),
            ),
            0,
        )

    def test_begin_quote_repair_remediation_attempt_is_fact_neutral(self) -> None:

        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-repair-remediation",
            chat_id="room-repair-remediation",
            chat_name="修复尝试群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-repair-remediation",
            chat_name="修复尝试群",
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
                message_id="msg-repair-remediation-1",
                chat_id="room-repair-remediation",
                chat_name="修复尝试群",
                text="[Apple]\nUS=5.10\nUK=6.20",
            )
        )
        exception_row = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ("room-repair-remediation",),
        ).fetchone()
        self.assertIsNotNone(exception_row)
        assert exception_row is not None
        repair_case = self.db.get_quote_repair_case_by_origin_exception(
            origin_exception_id=int(exception_row["id"])
        )
        self.assertIsNotNone(repair_case)
        assert repair_case is not None
        attempts = self.db.list_quote_repair_case_attempts(repair_case_id=int(repair_case["id"]))
        remediation_attempts = [
            item for item in attempts if str(item.get("attempt_kind") or "") == "remediation"
        ]
        self.assertEqual(len(remediation_attempts), 1)
        attempt = remediation_attempts[0]
        self.assertEqual(int(attempt["attempt_number"]), 1)
        self.assertIn(str(attempt["outcome_state"]), {"pending", "completed", "blocked"})
        stored_case = self.db.get_quote_repair_case(repair_case_id=int(repair_case["id"]))
        self.assertIsNotNone(stored_case)
        assert stored_case is not None
        summary = stored_case["case_summary_json"]
        if isinstance(summary, str):
            summary = json.loads(summary)
        self.assertGreaterEqual(int(summary["attempt_count"]), 1)
        self.assertEqual(summary["remediation_attempt_limit"], 3)
        self.assertGreaterEqual(int(summary["remediation_attempts_remaining"]), 0)
        self.assertEqual(
            self._count_rows(
                "quote_price_rows",
                "WHERE source_group_key = ?",
                ("wechat:room-repair-remediation",),
            ),
            0,
        )

    def test_begin_quote_repair_remediation_attempt_blocks_parallel_pending_retries(self) -> None:
        from bookkeeping_core.remediation import begin_quote_repair_remediation_attempt

        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-repair-remediation-pending",
            chat_id="room-repair-remediation-pending",
            chat_name="修复挂起群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-repair-remediation-pending",
            chat_name="修复挂起群",
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
                message_id="msg-repair-remediation-pending-1",
                chat_id="room-repair-remediation-pending",
                chat_name="修复挂起群",
                text="[Apple]\nUS=5.10\nUK=6.20",
            )
        )
        exception_row = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ("room-repair-remediation-pending",),
        ).fetchone()
        self.assertIsNotNone(exception_row)
        assert exception_row is not None
        repair_case = self.db.get_quote_repair_case_by_origin_exception(
            origin_exception_id=int(exception_row["id"])
        )
        self.assertIsNotNone(repair_case)
        assert repair_case is not None
        with self.assertRaisesRegex(ValueError, "pending|closed"):
            begin_quote_repair_remediation_attempt(
                db=self.db,
                repair_case_id=int(repair_case["id"]),
                trigger="subagent_retry",
                proposal_scope="group_profile",
                proposal_kind="template_patch",
            )

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

    def _get_quote_document(
        self,
        *,
        platform: str,
        chat_id: str,
        message_id: str,
    ):
        return self.db.conn.execute(
            """
            SELECT *
            FROM quote_documents
            WHERE platform = ? AND chat_id = ? AND message_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (platform, chat_id, message_id),
        ).fetchone()

    def _count_rows(
        self,
        table_name: str,
        where_clause: str = "",
        params: tuple[object, ...] = (),
    ) -> int:
        row = self.db.conn.execute(
            f"SELECT COUNT(*) AS cnt FROM {table_name} {where_clause}",
            params,
        ).fetchone()
        return int(row["cnt"] or 0)

    def _upsert_bootstrap_profile(
        self,
        *,
        fixture_name: str,
        platform: str,
        chat_id: str,
        chat_name: str,
    ) -> dict:
        from scripts.bootstrap_quote_group_profiles import build_bootstrap_profile_payload

        payload = build_bootstrap_profile_payload(
            fixture_name=fixture_name,
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
        )
        self.db.upsert_quote_group_profile(
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            default_card_type=str(payload["default_card_type"]),
            default_country_or_currency=str(payload["default_country_or_currency"]),
            default_form_factor=str(payload["default_form_factor"]),
            default_multiplier=str(payload["default_multiplier"]),
            parser_template=str(payload["parser_template"]),
            stale_after_minutes=int(payload["stale_after_minutes"]),
            note=str(payload["note"]),
            template_config=json.dumps(payload["template_config"], ensure_ascii=False),
        )
        return payload

    def test_runtime_bootstrap_profiles_persist_candidate_rows_without_mutating_active_facts(
        self,
    ) -> None:
        from tests.support.quote_exception_corpus import load_gold_fixture

        fixtures = [
            ("sk_steam_price_update", "room-bootstrap-sk", "SK Steam 报价群"),
            ("yingzi_steam_razer", "room-bootstrap-shadow", "影子 Steam/Razer 报价群"),
            ("yangyang_supermarket_updates", "room-bootstrap-yangyang", "洋羊晚班报价群"),
        ]

        for fixture_name, chat_id, chat_name in fixtures:
            with self.subTest(fixture_name=fixture_name):
                self.db.set_group(
                    platform="wechat",
                    group_key=f"wechat:{chat_id}",
                    chat_id=chat_id,
                    chat_name=chat_name,
                    group_num=5,
                )
                payload = self._upsert_bootstrap_profile(
                    fixture_name=fixture_name,
                    platform="wechat",
                    chat_id=chat_id,
                    chat_name=chat_name,
                )
                fixture = load_gold_fixture(str(payload["canonical_fixture_name"]))
                message_id = f"msg-{fixture_name}"

                self.runtime.process_envelope(
                    self._message(
                        platform="wechat",
                        message_id=message_id,
                        chat_id=chat_id,
                        chat_name=chat_name,
                        text=str(fixture["raw_text"]),
                    )
                )

                document = self._get_quote_document(
                    platform="wechat",
                    chat_id=chat_id,
                    message_id=message_id,
                )
                self.assertIsNotNone(document)
                assert document is not None
                self.assertEqual(str(document["parser_version"]), "group-parser-v1")

                candidate_rows = self.db.list_quote_candidate_rows(
                    quote_document_id=int(document["id"])
                )
                self.assertGreater(len(candidate_rows), 0)

                validation_run = self.db.get_latest_quote_validation_run(
                    quote_document_id=int(document["id"])
                )
                self.assertIsNotNone(validation_run)
                assert validation_run is not None
                self.assertGreater(int(validation_run["candidate_row_count"]), 0)
                self.assertGreater(int(validation_run["publishable_row_count"]), 0)

                quote_price_row_count = self._count_rows(
                    "quote_price_rows",
                    "WHERE quote_document_id = ?",
                    (int(document["id"]),),
                )
                self.assertEqual(quote_price_row_count, 0)

    def test_runtime_unapproved_fixture_without_bootstrap_stays_in_exception_path(self) -> None:
        from tests.support.quote_exception_corpus import load_gold_fixture

        fixture = load_gold_fixture("wannuo_xbox_shorthand_174")
        chat_id = "room-bootstrap-unapproved"
        message_id = "msg-bootstrap-unapproved"
        self.db.set_group(
            platform="wechat",
            group_key=f"wechat:{chat_id}",
            chat_id=chat_id,
            chat_name="未引导报价群",
            group_num=5,
        )

        self.runtime.process_envelope(
            self._message(
                platform="wechat",
                message_id=message_id,
                chat_id=chat_id,
                chat_name="未引导报价群",
                text=str(fixture["raw_text"]),
            )
        )

        document = self._get_quote_document(
            platform="wechat",
            chat_id=chat_id,
            message_id=message_id,
        )
        self.assertIsNotNone(document)
        assert document is not None
        self.assertEqual(str(document["parse_status"]), "empty")

        candidate_rows = self.db.list_quote_candidate_rows(
            quote_document_id=int(document["id"])
        )
        self.assertEqual(candidate_rows, [])

        validation_run = self.db.get_latest_quote_validation_run(
            quote_document_id=int(document["id"])
        )
        self.assertIsNotNone(validation_run)
        assert validation_run is not None
        self.assertEqual(int(validation_run["publishable_row_count"]), 0)

        parse_exceptions = self.db.conn.execute(
            """
            SELECT reason
            FROM quote_parse_exceptions
            WHERE quote_document_id = ?
            ORDER BY id ASC
            """,
            (int(document["id"]),),
        ).fetchall()
        self.assertEqual(len(parse_exceptions), 1)
        self.assertEqual(str(parse_exceptions[0]["reason"]), "missing_group_template")

        quote_price_row_count = self._count_rows(
            "quote_price_rows",
            "WHERE quote_document_id = ?",
            (int(document["id"]),),
        )
        self.assertEqual(quote_price_row_count, 0)

    def test_runtime_auto_remediation_absorbs_saveable_group_profile_case(self) -> None:
        self.db.set_group(
            platform="whatsapp",
            group_key="whatsapp:room-auto-remediate-ok",
            chat_id="room-auto-remediate-ok",
            chat_name="自动修复成功群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="whatsapp",
            chat_id="room-auto-remediate-ok",
            chat_name="自动修复成功群",
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
                platform="whatsapp",
                message_id="msg-auto-remediate-ok-1",
                chat_id="room-auto-remediate-ok",
                chat_name="自动修复成功群",
                text=(
                    "报价更新\n"
                    "【Steam蒸汽】\n"
                    "USD-10-200【4.94】\n"
                    "UK【6.66】  EUR【5.8】\n"
                    "CAD【3.57】 AUD【3.49】\n"
                    "【苹果-快加/快刷】\n"
                    "US-300-500   白卡   【5.36】\n"
                    "US-200-450   白卡   【5.36】\n"
                    "US-100/150   白卡   【5.36】\n"
                    "【US-XBOX--Rate】\n"
                    "US：10-250=5.06\n"
                    "UK【6.15】     新加坡【3.55】\n"
                    "EUR【5.3】     CAD【3.35】\n"
                ),
            )
        )

        exception_row = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ("room-auto-remediate-ok",),
        ).fetchone()
        self.assertIsNotNone(exception_row)
        assert exception_row is not None
        self.assertEqual(str(exception_row["resolution_status"]), "resolved")

        repair_case = self.db.get_quote_repair_case_by_origin_exception(
            origin_exception_id=int(exception_row["id"])
        )
        self.assertIsNotNone(repair_case)
        assert repair_case is not None
        self.assertEqual(str(repair_case["lifecycle_state"]), "closed_resolved")

        summary = self.db.get_quote_repair_case_summary(
            repair_case_id=int(repair_case["id"])
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary["attempt_count"], 1)
        self.assertEqual(summary["last_attempt_outcome"], "completed")
        self.assertEqual(summary["remediation_attempts_remaining"], 2)

        attempts = self.db.list_quote_repair_case_attempts(
            repair_case_id=int(repair_case["id"])
        )
        self.assertEqual(len(attempts), 2)
        remediation_attempt = attempts[-1]
        remediation_summary = remediation_attempt["attempt_summary_json"]
        if isinstance(remediation_summary, str):
            remediation_summary = json.loads(remediation_summary)
        self.assertEqual(remediation_summary["proposal_scope"], "group_profile")
        self.assertEqual(remediation_summary["protocol_stage"], "finalized")
        self.assertEqual(remediation_summary["absorption_decision"], "absorbed")

        profile = self.db.get_quote_group_profile(
            platform="whatsapp",
            chat_id="room-auto-remediate-ok",
        )
        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertIn('"group-parser-v1"', str(profile["template_config"]))
        self.assertEqual(
            self._count_rows(
                "quote_price_rows",
                "WHERE source_group_key = ?",
                ("whatsapp:room-auto-remediate-ok",),
            ),
            0,
        )

    def test_runtime_auto_remediation_updates_existing_unique_sections_at_capacity(self) -> None:
        self.db.set_group(
            platform="whatsapp",
            group_key="whatsapp:room-auto-remediate-capacity",
            chat_id="room-auto-remediate-capacity",
            chat_name="自动修复骨架上限群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="whatsapp",
            chat_id="room-auto-remediate-capacity",
            chat_name="自动修复骨架上限群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {
                    "version": "group-parser-v1",
                    "defaults": {},
                    "sections": [
                        {
                            "id": "section-1",
                            "enabled": True,
                            "priority": 10,
                            "label": "Steam",
                            "defaults": {
                                "card_type": "Steam",
                                "country_or_currency": "USD",
                                "form_factor": "不限",
                            },
                            "lines": [
                                {
                                    "kind": "quote",
                                    "pattern": "USD {amount}={price}",
                                    "outputs": {
                                        "card_type": "Steam",
                                        "country_or_currency": "USD",
                                        "form_factor": "不限",
                                        "amount_range": "10-200",
                                    },
                                }
                            ],
                        },
                        {
                            "id": "section-2",
                            "enabled": True,
                            "priority": 20,
                            "label": "Apple",
                            "defaults": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                            },
                            "lines": [
                                {
                                    "kind": "quote",
                                    "pattern": "US-{amount} 白卡 【{price}】",
                                    "outputs": {
                                        "card_type": "Apple",
                                        "country_or_currency": "USD",
                                        "form_factor": "横白卡",
                                        "amount_range": "100-150",
                                    },
                                }
                            ],
                        },
                        {
                            "id": "section-3",
                            "enabled": True,
                            "priority": 30,
                            "label": "Xbox",
                            "defaults": {
                                "card_type": "Xbox",
                                "country_or_currency": "USD",
                                "form_factor": "不限",
                            },
                            "lines": [
                                {
                                    "kind": "quote",
                                    "pattern": "US：{amount}={price}",
                                    "outputs": {
                                        "card_type": "Xbox",
                                        "country_or_currency": "USD",
                                        "form_factor": "不限",
                                        "amount_range": "10-250",
                                    },
                                }
                            ],
                        },
                    ],
                },
                ensure_ascii=False,
            ),
        )

        self.runtime.process_envelope(
            self._message(
                platform="whatsapp",
                message_id="msg-auto-remediate-capacity-1",
                chat_id="room-auto-remediate-capacity",
                chat_name="自动修复骨架上限群",
                text=(
                    "报价更新\n"
                    "【Steam蒸汽】\n"
                    "USD-10-200【4.94】\n"
                    "UK【6.66】\n"
                    "【苹果-快加/快刷】\n"
                    "US-300-500   白卡   【5.36】\n"
                    "US-100/150   白卡   【5.36】\n"
                    "【US-XBOX--Rate】\n"
                    "US：10-250=5.06\n"
                    "UK【6.15】\n"
                ),
            )
        )

        exception_row = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ("room-auto-remediate-capacity",),
        ).fetchone()
        self.assertIsNotNone(exception_row)
        assert exception_row is not None
        self.assertEqual(str(exception_row["resolution_status"]), "resolved")

        repair_case = self.db.get_quote_repair_case_by_origin_exception(
            origin_exception_id=int(exception_row["id"])
        )
        self.assertIsNotNone(repair_case)
        assert repair_case is not None
        self.assertEqual(str(repair_case["lifecycle_state"]), "closed_resolved")

        summary = self.db.get_quote_repair_case_summary(
            repair_case_id=int(repair_case["id"])
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary["attempt_count"], 1)
        self.assertEqual(summary["last_attempt_outcome"], "completed")

        profile = self.db.get_quote_group_profile(
            platform="whatsapp",
            chat_id="room-auto-remediate-capacity",
        )
        self.assertIsNotNone(profile)
        assert profile is not None
        template = json.loads(str(profile["template_config"]))
        self.assertEqual(len(list(template.get("sections") or [])), 3)
        xbox_section = next(
            section
            for section in list(template.get("sections") or [])
            if str((section.get("defaults") or {}).get("card_type") or "") == "Xbox"
        )
        self.assertTrue(
            any(
                str(((line.get("outputs") or {}).get("country_or_currency")) or "") == "GBP"
                for line in list(xbox_section.get("lines") or [])
            )
        )
        self.assertEqual(
            self._count_rows(
                "quote_price_rows",
                "WHERE source_group_key = ?",
                ("whatsapp:room-auto-remediate-capacity",),
            ),
            0,
        )

    def test_runtime_auto_remediation_blocks_new_skeleton_append_for_existing_profile(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-auto-remediate-guard",
            chat_id="room-auto-remediate-guard",
            chat_name="自动修补护栏群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-auto-remediate-guard",
            chat_name="自动修补护栏群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {
                    "version": "group-parser-v1",
                    "defaults": {},
                    "sections": [
                        {
                            "id": "section-1",
                            "enabled": True,
                            "priority": 10,
                            "label": "Apple",
                            "defaults": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                            },
                            "lines": [
                                {
                                    "kind": "quote",
                                    "pattern": "{amount}={price}",
                                    "outputs": {
                                        "card_type": "Apple",
                                        "country_or_currency": "USD",
                                        "form_factor": "横白卡",
                                        "amount_range": "100-150",
                                    },
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        )

        forced_preview = {
            "can_save": True,
            "strict_replay_ok": True,
            "errors": [],
            "strict_replay_errors": [],
            "preview_rows": [
                {
                    "card_type": "Xbox",
                    "country_or_currency": "USD",
                    "amount": "10-250",
                    "form_factor": "不限",
                    "price": "5.06",
                    "source_line": "US：10-250=5.06",
                }
            ],
            "derived_sections": [
                {
                    "label": "Xbox",
                    "priority": 10,
                    "defaults": {
                        "card_type": "Xbox",
                        "country_or_currency": "USD",
                        "form_factor": "不限",
                    },
                    "lines": [
                        {
                            "kind": "quote",
                            "pattern": "US：{amount}={price}",
                            "outputs": {
                                "card_type": "Xbox",
                                "country_or_currency": "USD",
                                "form_factor": "不限",
                                "amount_range": "10-250",
                            },
                        }
                    ],
                }
            ],
            "draft_structure": {"defaults": {}},
        }
        with patch(
            "bookkeeping_web.app._build_quote_result_preview_payload",
            return_value=forced_preview,
        ):
            self.runtime.process_envelope(
                self._message(
                    platform="wechat",
                    message_id="msg-auto-remediate-guard-1",
                    chat_id="room-auto-remediate-guard",
                    chat_name="自动修补护栏群",
                    text="[Xbox]\nUS：10-250=5.06",
                )
            )

        exception_row = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ("room-auto-remediate-guard",),
        ).fetchone()
        self.assertIsNotNone(exception_row)
        assert exception_row is not None
        self.assertEqual(str(exception_row["resolution_status"]), "open")

        repair_case = self.db.get_quote_repair_case_by_origin_exception(
            origin_exception_id=int(exception_row["id"])
        )
        self.assertIsNotNone(repair_case)
        assert repair_case is not None
        self.assertEqual(str(repair_case["lifecycle_state"]), "escalated")
        self.assertEqual(
            str(repair_case["current_failure_reason"]),
            "自动修补只允许更新现有群骨架，不允许新增骨架。",
        )

        summary = self.db.get_quote_repair_case_summary(
            repair_case_id=int(repair_case["id"])
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary["attempt_count"], 3)
        self.assertEqual(summary["last_attempt_outcome"], "blocked")
        self.assertTrue(
            all(
                str(item.get("failure_note") or "") == "自动修补只允许更新现有群骨架，不允许新增骨架。"
                for item in list(summary.get("failure_log_json") or [])
            )
        )

    def test_runtime_auto_remediation_promotes_multi_section_expansion_to_supermarket_mode(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-auto-remediate-supermarket",
            chat_id="room-auto-remediate-supermarket",
            chat_name="自动修补混合群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-auto-remediate-supermarket",
            chat_name="自动修补混合群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {
                    "version": "group-parser-v1",
                    "defaults": {},
                    "sections": [
                        {
                            "id": "section-1",
                            "enabled": True,
                            "priority": 10,
                            "label": "Apple",
                            "defaults": {
                                "card_type": "Apple",
                                "country_or_currency": "USD",
                                "form_factor": "横白卡",
                            },
                            "lines": [
                                {
                                    "kind": "quote",
                                    "pattern": "{amount}={price}",
                                    "outputs": {
                                        "card_type": "Apple",
                                        "country_or_currency": "USD",
                                        "form_factor": "横白卡",
                                        "amount_range": "100-150",
                                    },
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        )

        forced_preview = {
            "can_save": True,
            "strict_replay_ok": True,
            "errors": [],
            "strict_replay_errors": [],
            "preview_rows": [
                {
                    "card_type": "Xbox",
                    "country_or_currency": "USD",
                    "amount": "10-250",
                    "form_factor": "不限",
                    "price": "5.06",
                    "source_line": "US：10-250=5.06",
                },
                {
                    "card_type": "Razer",
                    "country_or_currency": "USD",
                    "amount": "100",
                    "form_factor": "不限",
                    "price": "7.10",
                    "source_line": "Razer 100=7.10",
                },
            ],
            "derived_sections": [
                {
                    "label": "Xbox",
                    "priority": 10,
                    "defaults": {
                        "card_type": "Xbox",
                        "country_or_currency": "USD",
                        "form_factor": "不限",
                    },
                    "lines": [
                        {
                            "kind": "quote",
                            "pattern": "US：{amount}={price}",
                            "outputs": {
                                "card_type": "Xbox",
                                "country_or_currency": "USD",
                                "form_factor": "不限",
                                "amount_range": "10-250",
                            },
                        }
                    ],
                },
                {
                    "label": "Razer",
                    "priority": 20,
                    "defaults": {
                        "card_type": "Razer",
                        "country_or_currency": "USD",
                        "form_factor": "不限",
                    },
                    "lines": [
                        {
                            "kind": "quote",
                            "pattern": "Razer {amount}={price}",
                            "outputs": {
                                "card_type": "Razer",
                                "country_or_currency": "USD",
                                "form_factor": "不限",
                                "amount_range": "100",
                            },
                        }
                    ],
                },
            ],
            "draft_structure": {"defaults": {}},
        }
        forced_replay = {
            "replayed": True,
            "rows": 2,
            "exceptions": 0,
            "detected_exceptions": 0,
            "quote_document_id": None,
            "validation_run_id": None,
            "remaining_lines": [],
            "mutated_active_facts": False,
            "message_decision": "publishable_rows_available",
            "publishable_row_count": 2,
            "held_row_count": 0,
            "rejected_row_count": 0,
            "comparison": {"classification": "better"},
        }
        with patch(
            "bookkeeping_web.app._build_quote_result_preview_payload",
            return_value=forced_preview,
        ), patch(
            "bookkeeping_web.app._replay_latest_quote_document_with_current_template",
            return_value=forced_replay,
        ):
            self.runtime.process_envelope(
                self._message(
                    platform="wechat",
                    message_id="msg-auto-remediate-supermarket-1",
                    chat_id="room-auto-remediate-supermarket",
                    chat_name="自动修补混合群",
                    text="[Xbox]\nUS：10-250=5.06\n[Razer]\nRazer 100=7.10",
                )
            )

        profile = self.db.get_quote_group_profile(
            platform="wechat",
            chat_id="room-auto-remediate-supermarket",
        )
        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertEqual(str(profile["parser_template"]), "supermarket-card")
        config = json.loads(str(profile["template_config"]))
        self.assertEqual(str(config["version"]), "group-parser-v1")
        self.assertEqual(len(list(config.get("sections") or [])), 3)

        exception_row = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ("room-auto-remediate-supermarket",),
        ).fetchone()
        self.assertIsNotNone(exception_row)
        assert exception_row is not None
        self.assertEqual(str(exception_row["resolution_status"]), "resolved")

        repair_case = self.db.get_quote_repair_case_by_origin_exception(
            origin_exception_id=int(exception_row["id"])
        )
        self.assertIsNotNone(repair_case)
        assert repair_case is not None
        self.assertEqual(str(repair_case["lifecycle_state"]), "closed_resolved")

    def test_runtime_auto_remediation_retries_three_times_then_escalates(self) -> None:
        self.db.set_group(
            platform="wechat",
            group_key="wechat:room-auto-remediate-escalate",
            chat_id="room-auto-remediate-escalate",
            chat_name="自动修复升级群",
            group_num=5,
        )
        self.db.upsert_quote_group_profile(
            platform="wechat",
            chat_id="room-auto-remediate-escalate",
            chat_name="自动修复升级群",
            default_card_type="Apple",
            default_country_or_currency="USD",
            default_form_factor="横白卡",
            parser_template="group-parser",
            template_config=json.dumps(
                {"version": "group-parser-v1", "defaults": {}, "sections": []},
                ensure_ascii=False,
            ),
        )

        forced_preview = {
            "can_save": False,
            "strict_replay_ok": False,
            "errors": ["forced auto remediation failure"],
            "strict_replay_errors": ["forced auto remediation failure"],
            "preview_rows": [],
            "derived_sections": [],
            "draft_structure": {},
        }
        with patch(
            "bookkeeping_web.app._build_quote_result_preview_payload",
            return_value=forced_preview,
        ):
            self.runtime.process_envelope(
                self._message(
                    platform="wechat",
                    message_id="msg-auto-remediate-escalate-1",
                    chat_id="room-auto-remediate-escalate",
                    chat_name="自动修复升级群",
                    text="[Apple]\nUS=5.10\nUK=6.20",
                )
            )

        exception_row = self.db.conn.execute(
            """
            SELECT *
            FROM quote_parse_exceptions
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ("room-auto-remediate-escalate",),
        ).fetchone()
        self.assertIsNotNone(exception_row)
        assert exception_row is not None
        self.assertEqual(str(exception_row["resolution_status"]), "open")

        repair_case = self.db.get_quote_repair_case_by_origin_exception(
            origin_exception_id=int(exception_row["id"])
        )
        self.assertIsNotNone(repair_case)
        assert repair_case is not None
        self.assertEqual(str(repair_case["lifecycle_state"]), "escalated")

        summary = self.db.get_quote_repair_case_summary(
            repair_case_id=int(repair_case["id"])
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary["attempt_count"], 3)
        self.assertEqual(summary["escalation_state"], "ready")
        self.assertEqual(len(list(summary.get("failure_log_json") or [])), 3)

        attempts = self.db.list_quote_repair_case_attempts(
            repair_case_id=int(repair_case["id"])
        )
        remediation_attempts = [
            item for item in attempts if str(item.get("attempt_kind") or "") == "remediation"
        ]
        self.assertEqual(len(remediation_attempts), 3)
        scopes = []
        for item in remediation_attempts:
            summary_payload = item["attempt_summary_json"]
            if isinstance(summary_payload, str):
                summary_payload = json.loads(summary_payload)
            scopes.append(str(summary_payload.get("proposal_scope") or ""))
        self.assertEqual(scopes, ["group_profile", "group_section", "bootstrap"])
        self.assertEqual(
            self._count_rows(
                "quote_price_rows",
                "WHERE source_group_key = ?",
                ("wechat:room-auto-remediate-escalate",),
            ),
            0,
        )


if __name__ == "__main__":
    unittest.main()
