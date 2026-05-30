from app.models.career import Career
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig
from app.genre import load_genre_config

GENRE_CAREER_PROMPTS = {
    "xianxia": {
        "name": "修仙境界",
        "stages": [
            {"name": "炼气期", "features": "引气入体，淬炼肉身", "power_range": "常人3-5倍", "social_status": "修士入门"},
            {"name": "筑基期", "features": "筑就道基，寿元延长", "power_range": "常人10倍", "social_status": "宗门弟子"},
            {"name": "金丹期", "features": "凝结金丹，御剑飞行", "power_range": "常人50倍", "social_status": "宗门长老"},
            {"name": "元婴期", "features": "元婴出窍，神游太虚", "power_range": "常人200倍", "social_status": "一宗之主"},
            {"name": "化神期", "features": "化神合道，天人感应", "power_range": "常人1000倍", "social_status": "一方霸主"},
        ]
    },
    "western-fantasy": {
        "name": "魔法等级",
        "stages": [
            {"name": "学徒", "features": "感知魔力，基础咒语", "power_range": "点燃蜡烛/移动小物", "social_status": "魔法学院新生"},
            {"name": "正式法师", "features": "掌握元素魔法，独立施法", "power_range": "战斗级魔法", "social_status": "冒险者/佣兵团"},
            {"name": "高阶法师", "features": "复合魔法，魔法阵构筑", "power_range": "改变地形", "social_status": "宫廷法师/学院教授"},
            {"name": "大法师", "features": "禁咒级魔法，魔力领域", "power_range": "影响城市", "social_status": "魔法学院院长/王国顾问"},
            {"name": "传奇法师", "features": "触及世界法则，创造生命", "power_range": "改变国家命运", "social_status": "历史留名"},
        ]
    },
    "urban": {
        "name": "社会阶层",
        "stages": [
            {"name": "底层", "features": "月薪3-5k，合租，月光族", "power_range": "无", "social_status": "普通打工者"},
            {"name": "白领", "features": "月薪8-15k，独立租房，有积蓄", "power_range": "无", "social_status": "公司职员"},
            {"name": "中层", "features": "年薪30-50w，有房有车", "power_range": "小范围人脉影响力", "social_status": "部门主管/小企业主"},
            {"name": "精英", "features": "年薪100w+，多套房产，投资", "power_range": "行业内影响力", "social_status": "企业高管/知名人士"},
            {"name": "顶层", "features": "资产过亿，跨行业布局", "power_range": "跨行业资源调动", "social_status": "资本掌控者"},
        ]
    },
    "scifi-apocalypse": {
        "name": "进化等级",
        "stages": [
            {"name": "普通幸存者", "features": "基本生存技能", "power_range": "勉强个体生存", "social_status": "避难所底层居民"},
            {"name": "觉醒者", "features": "基因初步优化，感官强化", "power_range": "常人3倍", "social_status": "探索队成员"},
            {"name": "进化者", "features": "专项能力强化，战斗/感知/修复", "power_range": "常人10倍", "social_status": "避难所核心成员"},
            {"name": "支配者", "features": "区域掌控，精神力外放", "power_range": "影响一个区域", "social_status": "避难所领袖"},
            {"name": "超越者", "features": "人类极限突破，适应任何环境", "power_range": "改变生态环境", "social_status": "新人类先驱"},
        ]
    },
}


async def generate_career_system(novel_id: str, genre_id: str, provider: BaseLLMProvider) -> Career:
    """根据类型自动生成职业体系——内置模板快速、确定性"""
    if genre_id in GENRE_CAREER_PROMPTS:
        template = GENRE_CAREER_PROMPTS[genre_id]
        return Career(
            novel_id=novel_id,
            name=template["name"],
            stages=template["stages"],
            max_stage=len(template["stages"]),
        )

    # 未知类型用 LLM 生成
    genre_config = load_genre_config(genre_id)
    messages = [
        LLMMessage(role="system", content="你是游戏/小说职业体系设计师。设计5-8级等级体系。输出严格JSON：{\"name\":\"...\",\"stages\":[{\"name\":\"...\",\"features\":\"...\",\"power_range\":\"...\",\"social_status\":\"...\"}]}"),
        LLMMessage(role="user", content=f"为{genre_config['name']}类型小说设计职业等级体系。"),
    ]
    resp = await provider.generate(messages, LLMConfig(model="deepseek-chat", temperature=0.7, max_tokens=2000))
    import json
    data = json.loads(resp.content)
    return Career(novel_id=novel_id, name=data["name"], stages=data["stages"], max_stage=len(data["stages"]))
