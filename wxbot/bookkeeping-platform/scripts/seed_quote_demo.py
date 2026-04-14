from __future__ import annotations

import argparse
from datetime import datetime, timedelta

from bookkeeping_core.contracts import NormalizedMessageEnvelope
from bookkeeping_core.database import BookkeepingDB
from bookkeeping_core.quotes import QuoteCaptureService


DEFAULT_DSN = "postgresql://bookkeeping:password@127.0.0.1:5432/bookkeeping_test"


SAMPLES: list[tuple[str, str, str, int]] = [
    (
        "customer-1",
        "客人1 Apple报价群",
        """
US极速网单#使用时间30s-3min
US横白卡：50=5.3
US横白卡：100-150=5.4（50倍数）
#竖卡-0.1
#电子-0.15
#代码-0.3
""".strip(),
        60,
    ),
    (
        "customer-2",
        "客人2报价群",
        """
【 影子steam价格表】
美金USD :5.10
欧元EUR :6.09
=== 雷蛇/Razer ===
美 USD ：5.90
新加坡：4.30
""".strip(),
        44,
    ),
    (
        "customer-1",
        "客人1 Apple报价群",
        """
US极速网单#使用时间30s-3min
US横白卡：50=5.4
US横白卡：100-150=5.45（50倍数）
#竖卡-0.1
#电子-0.15
#代码-0.3
-----------------------------------
#尾刀勿清
#尾刀勿清
#尾刀勿清
40分钟赎回/被扫的话扣账单
尾刀被快加请标记后续不退邮箱扣账单
-----------------------------------
所有面额连卡都不要#！！！！！！！
拆开发也不要#！！！！！！！！
如若拆开发后续卡出现问题扣账单
""".strip(),
        35,
    ),
    (
        "customer-2",
        "客人2报价群",
        """
【 影子steam价格表】
**********************
美金USD :5.30
欧元EUR :6.09
英镑GBP :6.90
加元CAD :3.80
澳元AUD :3.70
新西兰NZD ：3.05
瑞士CHF ：6.55
波兰PLN  :1.39
*************************
报其他国家按到账美金*5.30
        【影子】
=== 雷蛇/Razer ===
   美  USD ：5.83
   新 加 坡 ：4.30
   加 拿 大 ：4.15
   澳大利亚：4.00
   新西兰   ：3.23
   马来西亚：1.46
推荐客户有红包（200-2000)
    上不封顶
""".strip(),
        19,
    ),
    (
        "customer-3",
        "客人3报价群",
        """
岚京超市卡   夜班广告更新
═════════════
【Xbox】#非5倍数问 #批量先问！
US：10~250/5倍数图密=5.0
UK卡图/纸质=6.2 （电子/代码6.15）
EUR卡图/纸质=5.3（电子/代码5.15）
CAD=3.4              AUD=3.6
NZD=2.8              CHF=5.1
丹麦=0.55             瑞典=0.455
巴西图=0.75          挪威=0.455
捷克=0.14             波兰=1.05
新加坡=3.55           墨西哥=0.27
韩国=0.0036          哥伦比亚=0.0006
#CAD测不出面值的需退
═════════════
【Razer Gold 雷蛇】
美国=5.74               新加坡=4.23
澳大利亚=3.9           加拿大=4.1
马来西亚=1.4           巴西=1.05
墨西哥=0.315           菲律宾=0.09
欧盟/英国 (RG开头20位）10+=问
雷蛇待定卡不加账！！
提供购买收据到账后加账！！
═════════════
【Steam 蒸汽】#急卡发代码
USD美元=5.1        EUR欧元=5.88
AUD澳元=3.48      CAD加元=3.62
CHF瑞士=6.36       GBP英镑=6.72
NZD新币=2.87
其他国家按到账美金*5.0
═════════════
【Google play 谷歌】
US=4.4                  德国=4.1
UK=3.8                  CHF=3.8
CAD=2.7                AUD=2.2
NZD=2.0                MX=0.12
韩谷=带今日收据问
#连卡/大额需要压1h
═════════════
【Roblox 罗布乐思】
US:10~200=3.5
#其他国家按到账美金*3.5#10以下3.3
结算取整数=小数点后面不加账
#需要RI/RB/RE开头或者纯数字
#批量问价批量问价
""".strip(),
        18,
    ),
    (
        "customer-single",
        "零碎问价群",
        "Mexico apple card 200 0.265",
        15,
    ),
    (
        "customer-short",
        "缺上下文短回复群",
        """
uk 10
6.25
""".strip(),
        14,
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed quote wall demo data.")
    parser.add_argument("--db", default=DEFAULT_DSN)
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    if args.clear:
        print(
            "--clear 已禁用：Phase 03 不再允许脚本直接删除 active quote facts。"
            "请改用测试 schema 重建或手动重置候选/异常数据。"
        )
        return 1

    db = BookkeepingDB(args.db)
    try:
        db.upsert_quote_group_profile(
            platform="demo",
            chat_id="customer-1",
            chat_name="客人1 Apple报价群",
            default_card_type="Apple",
            parser_template="apple_modifier_sheet",
            stale_after_minutes=30,
            note="横白卡基准价，#竖卡/#电子/#代码 按同卡种上下文派生",
        )

        service = QuoteCaptureService(db)
        now = datetime.now().replace(microsecond=0)
        for index, (chat_id, chat_name, text, minutes_ago) in enumerate(SAMPLES, start=1):
            received_at = (now - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S")
            envelope = NormalizedMessageEnvelope(
                platform="demo",
                message_id=f"quote-demo-{index}",
                chat_id=chat_id,
                chat_name=chat_name,
                is_group=True,
                sender_id=f"sender-{index}",
                sender_name=chat_name,
                content_type="text",
                text=text,
                received_at=received_at,
            )
            result = service.capture_from_message(envelope, raw_text=text)
            print(chat_name, result)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
