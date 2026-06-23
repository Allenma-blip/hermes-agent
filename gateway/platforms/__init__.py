"""
Platform adapters for messaging integrations.

Each adapter handles:
- Receiving messages from a platform
- Sending messages/responses back
- Platform-specific authentication
- Message formatting and media handling

============================================================================
Module reference — what each file/subpackage covers
============================================================================

Primary platform adapters  (each exposes an *Adapter class inheriting
BasePlatformAdapter):
    telegram          — Telegram Bot API via python-telegram-bot (long-polling)
    telegram_network  — Telegram-specific network helpers (proxy, connection mgmt)
    discord           — Discord Bot (via discord.py)
    slack             — Slack app (Socket Mode)
    whatsapp          — WhatsApp Baileys bridge (unofficial WebSocket)
    whatsapp_cloud    — WhatsApp Cloud API (official Meta Business Platform)
    whatsapp_common   — Transport-agnostic WhatsApp logic shared by both bridges
    signal            — Signal Messenger (via signal-cli REST)
    signal_rate_limit — Signal attachment rate-limit scheduler
    matrix            — Matrix protocol (via nio)
    dingtalk          — DingTalk (钉钉) Stream Mode WebSocket
    feishu            — Feishu/Lark (飞书) WebSocket event subscription
    wecom             — WeCom/企业微信 (Enterprise WeChat) callback mode
    weixin            — Weixin (微信) official account adapter
    email             — Email (IMAP/SMTP)
    sms               — SMS (Twilio)
    webhook           — Generic webhook ingress adapter
    bluebubbles       — BlueBubbles iMessage bridge (Apple ecosystem)
    api_server        — OpenAI-compatible API server (expose Hermes as an API)
    msgraph_webhook   — Microsoft Graph change-notification webhook

Feishu/Lark ecosystem (separate modules, not full platform adapters):
    feishu_codex          — Business adapter layer (feishu ↔ Codex routing)
    feishu_comment        — Feishu document comment handling
    feishu_comment_rules  — Feishu doc comment access-control rules
    feishu_meeting_invite — Feishu meeting-invitation event handling

WeCom support modules:
    wecom_callback   — Callback-mode adapter for self-built apps
    wecom_crypto     — BizMsgCrypt-compatible AES-CBC encryption

Yuanbao (元宝):
    yuanbao         — Yuanbao platform WebSocket adapter
    yuanbao_media   — Media file processing (images, voice, video)
    yuanbao_proto   — WebSocket protocol codec (pure Python)
    yuanbao_sticker — TIMFaceElem sticker support

QQ Bot (subpackage):
    qqbot/          — QQ Bot platform adapter + chunked upload, keyboards,
                      onboard flow, constants, crypto, utils
    qqbot/adapter           — QQAdapter class
    qqbot/chunked_upload    — Chunked file upload for QQ CDN
    qqbot/keyboards         — Inline keyboard renderer
    qqbot/onboard           — Bot onboarding flows
    qqbot/crypto            — QQ-specific crypto
    qqbot/constants         — QQ API constants
    qqbot/utils             — Shared QQ helpers

Codex-specific adapters (inner-loop routing for the Codex product workflow):
    codex_router   — Determines whether a Feishu message routes to Codex CLI
    codex_landing  — Posts review results back to Feishu
    codex_review   — Sub-module for executing Codex reviews
    codex_health   — Health-check / readiness probe for the Codex gateway

Infrastructure:
    base                     — BasePlatformAdapter, MessageEvent, SendResult
    helpers                  — Shared utility classes for all adapters
    _http_client_limits      — Shared HTTP client factory with connection limits
    ADDING_A_PLATFORM.md     — Onboarding guide for writing a new adapter
============================================================================
"""

# Lazy re-exports — QQAdapter and YuanbaoAdapter are heavy (48 ms / 8 MB RSS
# on import). They are exposed from the package root via PEP 562 __getattr__
# so existing call sites still work without paying the cost on every CLI
# invocation.
from .base import BasePlatformAdapter, MessageEvent, SendResult

__all__ = [
    "BasePlatformAdapter",
    "MessageEvent",
    "SendResult",
    "QQAdapter",
    "YuanbaoAdapter",
]


def __getattr__(name):
    if name == "QQAdapter":
        from .qqbot import QQAdapter  # noqa: F401
        return QQAdapter
    if name == "YuanbaoAdapter":
        from .yuanbao import YuanbaoAdapter  # noqa: F401
        return YuanbaoAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__)
