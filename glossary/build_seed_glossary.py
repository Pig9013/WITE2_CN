#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the curated WWII / WitE2 English-Chinese glossary seed.

The CSV is the editable source of truth after generation.  This script keeps
the initial seed reviewable and validates duplicates before writing.

Columns:
  en, zh, category, aliases, forbidden, notes, confidence, mode, source
mode:
  strict - technical term; translation is checked and must use zh
  hint   - common word; supplied to the model but not enforced
  name   - part of a proper name / designation; usually kept or pattern-built
"""
from __future__ import annotations

import csv
import os

OUT = os.path.join(os.path.dirname(__file__), "ww2_military_en_zh.csv")

# (en, zh, category, aliases, forbidden, notes, confidence, mode)
ROWS = [
    # ---------------- Organization / branches ----------------
    ("Infantry", "步兵", "branch", "infantry; foot infantry", "歩兵", "兵种；苏军 Rifle 也译步兵", "A", "strict"),
    ("Motorized Infantry", "摩托化步兵", "branch", "motorised infantry", "机动步兵", "", "A", "strict"),
    ("Mechanized Infantry", "机械化步兵", "branch", "mechanised infantry", "机械步兵", "", "A", "strict"),
    ("Armored", "装甲", "branch", "armoured; armor; armour", "装甲兵种", "形容词用“装甲”", "A", "strict"),
    ("Panzer", "装甲", "branch", "panzer; pz.", "坦克", "德军装甲兵种；番号中译“装甲”", "A", "strict"),
    ("Panzergrenadier", "装甲掷弹兵", "branch", "panzer grenadier; pz.gren.", "装甲步兵", "德军摩托化/机械化步兵", "A", "strict"),
    ("Grenadier", "掷弹兵", "branch", "grenadiers", "手榴弹兵", "", "A", "strict"),
    ("Volksgrenadier", "国民掷弹兵", "branch", "volks grenadier", "人民掷弹兵", "1944 年后德军新编师", "A", "strict"),
    ("Cavalry", "骑兵", "branch", "cav", "马队", "", "A", "strict"),
    ("Artillery", "炮兵", "branch", "art", "火炮部队", "兵种", "A", "strict"),
    ("Rocket Artillery", "火箭炮兵", "branch", "rocket artillery", "导弹炮兵", "", "A", "strict"),
    ("Anti-Tank", "反坦克", "branch", "antitank; anti tank; at", "反战车", "形容词", "A", "strict"),
    ("Anti-Aircraft", "防空", "branch", "antiaircraft; anti aircraft; flak", "反飞机", "形容词；Flak 作名词时译高射炮", "A", "strict"),
    ("Engineer", "工兵", "branch", "engineers; eng", "工程师", "军事编制", "A", "strict"),
    ("Pioneer", "战斗工兵", "branch", "pioneers", "先锋", "德军战斗工兵", "A", "strict"),
    ("Reconnaissance", "侦察", "branch", "recon; recce", "侦查", "", "A", "strict"),
    ("Security", "治安", "branch", "security", "安全", "Security Division 治安师", "A", "strict"),
    ("Garrison", "守备", "branch", "garrison", "驻军", "编制用语", "A", "strict"),
    ("Mountain", "山地", "branch", "mountain; gebirgs", "高山", "", "A", "strict"),
    ("Airborne", "空降", "branch", "airborne; fallschirm", "空中", "", "A", "strict"),
    ("Marine", "海军陆战", "branch", "marines; naval infantry", "海军", "Naval Infantry 海军步兵", "A", "strict"),
    ("Militia", "民兵", "branch", "militia", "国民军", "", "A", "strict"),
    ("Reserve", "预备", "branch", "reserve; reserves", "储备", "编制/状态", "A", "strict"),
    ("Guards", "近卫", "branch", "guard; gds; gds.", "警卫", "苏军荣誉称号", "A", "strict"),
    ("Shock", "突击", "branch", "shock", "震惊", "Shock Army 突击集团军", "A", "strict"),
    ("Tank", "坦克", "branch", "tank; tanks", "战车", "兵种/装备", "A", "strict"),
    ("Rifle", "步兵", "branch", "rifle", "步枪", "苏军 Rifle Division 步兵师", "A", "strict"),
    ("Ski", "滑雪", "branch", "ski", "雪橇", "", "A", "strict"),
    ("Naval Infantry", "海军步兵", "branch", "naval infantry; marine infantry", "海军陆战队", "苏军", "A", "strict"),
    ("Penal", "惩戒", "branch", "penal; shtraf", "刑罚", "Penal Battalion 惩戒营", "A", "strict"),
    ("Partisan", "游击队", "branch", "partisans; partisan", "游击队员", "", "A", "strict"),
    ("SS", "党卫军", "branch", "ss; waffen-ss; waffen ss", "纳粹党卫队", "武装党卫军", "A", "strict"),
    ("Waffen-SS", "武装党卫军", "branch", "waffen ss", "党卫队", "", "A", "strict"),
    ("Luftwaffe", "空军", "branch", "luftwaffe", "航空队", "德国空军", "A", "strict"),
    ("Heer", "陆军", "branch", "heer", "德国陆军", "德国陆军", "A", "strict"),
    ("Kriegsmarine", "海军", "branch", "kriegsmarine", "德国海军", "德国海军", "A", "strict"),
    ("Wehrmacht", "国防军", "branch", "wehrmacht", "德军", "德国武装力量整体", "A", "strict"),
    ("OKH", "陆军总司令部", "organization", "okh", "", "Oberkommando des Heeres", "A", "strict"),
    ("OKW", "国防军最高统帅部", "organization", "okw", "", "Oberkommando der Wehrmacht", "A", "strict"),
    ("Stavka", "最高统帅部大本营", "organization", "stavka; stawka", "总部", "苏军最高统帅部", "A", "strict"),
    ("Army Group", "集团军群", "organization", "army group; heeresgruppe", "军团", "", "A", "strict"),
    ("Army", "集团军", "organization", "army", "军", "编成单位；Corps 才是军", "A", "strict"),
    ("Corps", "军", "organization", "corps", "军团", "", "A", "strict"),
    ("Division", "师", "organization", "division; div; div.", "分队", "", "A", "strict"),
    ("Brigade", "旅", "organization", "brigade; brig", "", "", "A", "strict"),
    ("Regiment", "团", "organization", "regiment; regt", "", "", "A", "strict"),
    ("Battalion", "营", "organization", "battalion; bn", "", "", "A", "strict"),
    ("Company", "连", "organization", "company; coy", "", "", "A", "strict"),
    ("Battery", "炮兵连", "organization", "battery", "电池", "炮兵编制", "A", "strict"),
    ("Front", "方面军", "organization", "front", "前线", "苏军战役战略军团", "A", "strict"),
    ("Military District", "军区", "organization", "military district", "", "", "A", "strict"),
    ("Theater", "战区", "organization", "theatre; theater", "剧院", "", "A", "strict"),
    ("AOG", "航空作战群", "organization", "aog; air operational group", "航空军", "Air Operational Group", "A", "strict"),
    ("HQ", "司令部", "organization", "hq; headquarters", "", "", "A", "strict"),
    ("TOE", "编制表", "organization", "toe; table of organization and equipment", "", "", "A", "strict"),
    ("OB", "战斗序列", "organization", "ob; order of battle", "", "", "A", "strict"),

    # ---------------- Ranks ----------------
    ("Generalfeldmarschall", "元帅", "rank", "general field marshal", "", "", "A", "strict"),
    ("Generaloberst", "大将", "rank", "general colonel", "", "", "A", "strict"),
    ("General der Infanterie", "步兵上将", "rank", "", "", "", "A", "strict"),
    ("General der Panzertruppe", "装甲兵上将", "rank", "general der panzertruppen", "", "", "A", "strict"),
    ("General der Artillerie", "炮兵上将", "rank", "", "", "", "A", "strict"),
    ("Generalleutnant", "中将", "rank", "general leutnant", "", "", "A", "strict"),
    ("Generalmajor", "少将", "rank", "", "", "", "A", "strict"),
    ("Oberst", "上校", "rank", "colonel", "", "", "A", "strict"),
    ("Oberstleutnant", "中校", "rank", "oberstleutnant; lieutenant colonel", "", "", "A", "strict"),
    ("Major", "少校", "rank", "major", "", "", "A", "strict"),
    ("Hauptmann", "上尉", "rank", "hauptmann; captain", "", "", "A", "strict"),
    ("Oberleutnant", "中尉", "rank", "oberleutnant; first lieutenant", "", "", "A", "strict"),
    ("Leutnant", "少尉", "rank", "leutnant; lieutenant", "", "", "A", "strict"),
    ("Feldwebel", "中士", "rank", "feldwebel; sergeant", "", "", "A", "strict"),
    ("Unteroffizier", "下士", "rank", "unteroffizier; corporal", "", "", "A", "strict"),
    ("Gefreiter", "上等兵", "rank", "gefreiter; lance corporal", "", "", "A", "strict"),
    ("Soldat", "列兵", "rank", "soldat; private", "", "", "A", "strict"),
    ("Marshal", "元帅", "rank", "marshal", "", "", "A", "strict"),
    ("Polkovnik", "上校", "rank", "polkovnik; colonel", "", "苏军", "A", "strict"),
    ("Podpolkovnik", "中校", "rank", "podpolkovnik; lieutenant colonel", "", "苏军", "A", "strict"),
    ("Mayor", "少校", "rank", "mayor; major", "", "苏军", "A", "strict"),
    ("Kapitan", "上尉", "rank", "kapitan; captain", "", "苏军", "A", "strict"),
    ("Starshiy Leytenant", "中尉", "rank", "starshiy leytenant; senior lieutenant", "", "苏军", "A", "strict"),
    ("Leytenant", "少尉", "rank", "leytenant; lieutenant", "", "苏军", "A", "strict"),
    ("Serzhant", "军士", "rank", "serzhant; sergeant", "", "苏军", "A", "strict"),
    ("Krasnoarmeets", "红军战士", "rank", "krasnoarmeets; red army man", "", "苏军", "A", "strict"),

    # ---------------- Armor / weapons ----------------
    ("Panzerkampfwagen", "装甲战车", "armor", "panzerkampfwagen; pz.kpfw.; pzkpfw", "坦克车", "德军正式装备名", "A", "strict"),
    ("Panzer IV", "四号坦克", "armor", "pz. iv; panzer iv; pzkpfw iv", "4号坦克", "", "A", "strict"),
    ("Panzer III", "三号坦克", "armor", "pz. iii; panzer iii; pzkpfw iii", "3号坦克", "", "A", "strict"),
    ("Panzer II", "二号坦克", "armor", "pz. ii; panzer ii; pzkpfw ii", "2号坦克", "", "A", "strict"),
    ("Tiger", "虎式坦克", "armor", "tiger i; tiger tank", "老虎", "Tiger I", "A", "strict"),
    ("King Tiger", "虎王坦克", "armor", "tiger ii; königstiger; konigstiger", "虎式二型", "Tiger II", "A", "strict"),
    ("Panther", "豹式坦克", "armor", "panther tank; pz. v", "黑豹", "Panzer V", "A", "strict"),
    ("Sturmgeschütz", "突击炮", "armor", "sturmgeschutz; stug", "冲锋炮", "", "A", "strict"),
    ("StuG III", "三号突击炮", "armor", "stug iii", "3号突击炮", "", "A", "strict"),
    ("Jagdpanzer", "歼击坦克", "armor", "jagdpanzer; tank destroyer", "猎虎", "德军无炮塔坦克歼击车", "A", "strict"),
    ("Panzerjäger", "坦克歼击车", "armor", "panzerjager; panzerjaeger", "反坦克炮", "", "A", "strict"),
    ("Hetzer", "追猎者", "armor", "hetzer; jagdpanzer 38(t)", "", "", "A", "strict"),
    ("Marder", "貂鼠", "armor", "marder ii; marder iii", "黄鼠狼", "自行反坦克炮", "A", "strict"),
    ("Hummel", "野蜂", "armor", "hummel; geschutzwagen iii/iv", "", "自行榴弹炮", "A", "strict"),
    ("Wespe", "黄蜂", "armor", "wespe", "", "自行榴弹炮", "A", "strict"),
    ("8.8 cm Flak", "88毫米高射炮", "weapon", "8.8cm flak; 88mm flak; 8.8 cm flak 36", "88毫米炮", "", "A", "strict"),
    ("7.5 cm Pak 40", "75毫米Pak 40反坦克炮", "weapon", "7.5cm pak 40; pak 40", "", "", "A", "strict"),
    ("5 cm Pak 38", "50毫米Pak 38反坦克炮", "weapon", "5cm pak 38; pak 38", "", "", "A", "strict"),
    ("3.7 cm Pak 36", "37毫米Pak 36反坦克炮", "weapon", "3.7cm pak 36; pak 36", "", "", "A", "strict"),
    ("MG 34", "MG 34通用机枪", "weapon", "mg34; mg 34", "", "", "A", "strict"),
    ("MG 42", "MG 42通用机枪", "weapon", "mg42; mg 42", "", "", "A", "strict"),
    ("Karabiner 98k", "毛瑟98k步枪", "weapon", "kar98k; k98k; mauser 98k", "卡宾枪98k", "", "A", "strict"),
    ("StG 44", "StG 44突击步枪", "weapon", "stg44; sturmgewehr 44", "", "", "A", "strict"),
    ("MP 40", "MP 40冲锋枪", "weapon", "mp40; mp 40", "", "", "A", "strict"),
    ("Panzerfaust", "铁拳反坦克火箭筒", "weapon", "panzerfaust", "装甲拳", "", "A", "strict"),
    ("Panzerschreck", "坦克杀手火箭筒", "weapon", "panzerschreck; raketenpanzerbüchse 54", "反坦克火箭", "", "A", "strict"),
    ("Nebelwerfer", "喷烟者火箭炮", "weapon", "nebelwerfer", "烟雾发射器", "", "A", "strict"),
    ("Flammenwerfer", "火焰喷射器", "weapon", "flammenwerfer; flamethrower", "", "", "A", "strict"),
    ("T-34", "T-34坦克", "armor", "t34; t 34", "", "", "A", "strict"),
    ("KV-1", "KV-1重型坦克", "armor", "kv1; kv 1", "", "", "A", "strict"),
    ("KV-2", "KV-2重型坦克", "armor", "kv2; kv 2", "", "", "A", "strict"),
    ("IS-2", "IS-2重型坦克", "armor", "is2; is 2; joseph stalin 2", "", "", "A", "strict"),
    ("T-60", "T-60轻型坦克", "armor", "t60; t 60", "", "", "A", "strict"),
    ("T-70", "T-70轻型坦克", "armor", "t70; t 70", "", "", "A", "strict"),
    ("BT-7", "BT-7快速坦克", "armor", "bt7; bt 7", "", "", "A", "strict"),
    ("SU-76", "SU-76自行火炮", "armor", "su76; su 76", "", "", "A", "strict"),
    ("SU-85", "SU-85坦克歼击车", "armor", "su85; su 85", "", "", "A", "strict"),
    ("SU-100", "SU-100坦克歼击车", "armor", "su100; su 100", "", "", "A", "strict"),
    ("ISU-152", "ISU-152自行火炮", "armor", "isu152; isu 152", "", "", "A", "strict"),
    ("Katyusha", "喀秋莎火箭炮", "weapon", "katyusha; katyusha rocket launcher", "", "", "A", "strict"),
    ("ZiS-3", "ZiS-3 76毫米加农炮", "weapon", "zis3; zis 3; zis-3 gun", "", "", "A", "strict"),
    ("PPSh-41", "波波沙-41冲锋枪", "weapon", "ppsh41; ppsh 41; papasha", "", "", "A", "strict"),
    ("Mosin-Nagant", "莫辛-纳甘步枪", "weapon", "mosin nagant; mosin", "", "", "A", "strict"),
    ("SVT-40", "SVT-40半自动步枪", "weapon", "svt40; svt 40", "", "", "A", "strict"),
    ("DP-27", "DP-27轻机枪", "weapon", "dp27; dp 27; degtyaryov", "", "", "A", "strict"),
    ("Maxim", "马克沁重机枪", "weapon", "maxim; maxim gun", "", "", "A", "strict"),
    ("45 mm anti-tank gun", "45毫米反坦克炮", "weapon", "45mm anti-tank gun; 45 mm at gun", "", "苏军 45mm M1937", "A", "strict"),
    ("122 mm howitzer", "122毫米榴弹炮", "weapon", "122mm howitzer; 122 mm howitzer m1938", "", "", "A", "strict"),
    ("152 mm howitzer", "152毫米榴弹炮", "weapon", "152mm howitzer; 152 mm howitzer", "", "", "A", "strict"),
    ("203 mm howitzer", "203毫米榴弹炮", "weapon", "203mm howitzer; 203 mm howitzer m1931", "", "", "A", "strict"),

    # ---------------- Aircraft ----------------
    ("Bf 109", "Bf 109战斗机", "aircraft", "bf109; me 109; me109", "", "", "A", "strict"),
    ("Fw 190", "Fw 190战斗机", "aircraft", "fw190", "", "", "A", "strict"),
    ("Ju 87", "Ju 87俯冲轰炸机", "aircraft", "ju87; stuka", "斯图卡轰炸机", "", "A", "strict"),
    ("Ju 88", "Ju 88轰炸机", "aircraft", "ju88", "", "", "A", "strict"),
    ("He 111", "He 111轰炸机", "aircraft", "he111", "", "", "A", "strict"),
    ("Do 17", "Do 17轰炸机", "aircraft", "do17", "", "", "A", "strict"),
    ("Bf 110", "Bf 110重型战斗机", "aircraft", "bf110; me 110", "", "", "A", "strict"),
    ("Me 262", "Me 262喷气战斗机", "aircraft", "me262", "", "", "A", "strict"),
    ("Ju 52", "Ju 52运输机", "aircraft", "ju52; tante ju", "", "", "A", "strict"),
    ("He 177", "He 177重型轰炸机", "aircraft", "he177", "", "", "A", "strict"),
    ("Il-2", "伊尔-2强击机", "aircraft", "il2; il 2; sturmovik", "伊尔2攻击机", "", "A", "strict"),
    ("La-5", "拉-5战斗机", "aircraft", "la5; la 5", "", "", "A", "strict"),
    ("Yak-9", "雅克-9战斗机", "aircraft", "yak9; yak 9", "", "", "A", "strict"),
    ("Pe-2", "佩-2俯冲轰炸机", "aircraft", "pe2; pe 2", "", "", "A", "strict"),
    ("Tu-2", "图-2轰炸机", "aircraft", "tu2; tu 2", "", "", "A", "strict"),
    ("MiG-3", "米格-3战斗机", "aircraft", "mig3; mig 3", "", "", "A", "strict"),
    ("I-16", "伊-16战斗机", "aircraft", "i16; i 16", "", "", "A", "strict"),
    ("Po-2", "波-2夜间轰炸机", "aircraft", "po2; po 2; u-2", "", "", "A", "strict"),
    ("Li-2", "里-2运输机", "aircraft", "li2; li 2", "", "", "A", "strict"),
    ("Yak-1", "雅克-1战斗机", "aircraft", "yak1; yak 1", "", "", "A", "strict"),

    # ---------------- Operations / places ----------------
    ("Operation Barbarossa", "巴巴罗萨行动", "operation", "barbarossa; operation barbarossa", "红胡子行动", "", "A", "strict"),
    ("Operation Typhoon", "台风行动", "operation", "typhoon; operation typhoon", "台风战役", "", "A", "strict"),
    ("Operation Blau", "蓝色行动", "operation", "blau; operation blue; fall blau", "蓝色计划", "", "A", "strict"),
    ("Operation Citadel", "堡垒行动", "operation", "citadel; operation citadel; unternehmen zitadelle", "城堡行动", "库尔斯克会战", "A", "strict"),
    ("Operation Uranus", "天王星行动", "operation", "uranus; operation uranus", "", "斯大林格勒反攻", "A", "strict"),
    ("Operation Saturn", "土星行动", "operation", "saturn; operation saturn", "", "", "A", "strict"),
    ("Operation Mars", "火星行动", "operation", "mars; operation mars", "", "勒热夫-瑟乔夫卡", "A", "strict"),
    ("Operation Bagration", "巴格拉季昂行动", "operation", "bagration; operation bagration", "", "", "A", "strict"),
    ("Leningrad", "列宁格勒", "place", "", "", "", "A", "strict"),
    ("Moscow", "莫斯科", "place", "", "", "", "A", "strict"),
    ("Stalingrad", "斯大林格勒", "place", "", "", "", "A", "strict"),
    ("Kursk", "库尔斯克", "place", "", "", "", "A", "strict"),
    ("Kharkov", "哈尔科夫", "place", "kharkiv", "", "", "A", "strict"),
    ("Kiev", "基辅", "place", "kyiv", "", "", "A", "strict"),
    ("Minsk", "明斯克", "place", "", "", "", "A", "strict"),
    ("Smolensk", "斯摩棱斯克", "place", "", "", "", "A", "strict"),
    ("Rostov", "罗斯托夫", "place", "", "", "", "A", "strict"),
    ("Sevastopol", "塞瓦斯托波尔", "place", "", "", "", "A", "strict"),
    ("Odessa", "敖德萨", "place", "", "", "", "A", "strict"),
    ("Voronezh", "沃罗涅日", "place", "", "", "", "A", "strict"),
    ("Tula", "图拉", "place", "", "", "", "A", "strict"),
    ("Kalinin", "加里宁", "place", "tver", "", "", "A", "strict"),
    ("Crimea", "克里米亚", "place", "", "", "", "A", "strict"),
    ("Don", "顿河", "place", "river don", "", "", "A", "strict"),
    ("Volga", "伏尔加河", "place", "river volga", "", "", "A", "strict"),
    ("Dnieper", "第聂伯河", "place", "dniepr; dnepr", "", "", "A", "strict"),
    ("Dniester", "德涅斯特河", "place", "dnestr", "", "", "A", "strict"),
    ("Pripyat", "普里皮亚季", "place", "pripyat marshes; pripet marshes", "", "", "A", "strict"),
    ("Warsaw", "华沙", "place", "", "", "", "A", "strict"),
    ("Berlin", "柏林", "place", "", "", "", "A", "strict"),
    ("Budapest", "布达佩斯", "place", "", "", "", "A", "strict"),
    ("Bucharest", "布加勒斯特", "place", "", "", "", "A", "strict"),
    ("Ploesti", "普洛耶什蒂", "place", "ploiesti", "", "罗马尼亚油田", "A", "strict"),
    ("Caucasus", "高加索", "place", "", "", "", "A", "strict"),
    ("Baku", "巴库", "place", "", "", "", "A", "strict"),

    # ---------------- Game mechanics / UI ----------------
    ("Admin Points", "行政点", "game", "admin points; aps; ap", "管理点", "WitE2 AP/APs", "A", "strict"),
    ("Combat Preparation Points", "战斗准备点", "game", "combat preparation points; cpp", "", "", "A", "strict"),
    ("Combat Value", "战斗值", "game", "combat value; cv", "作战值", "", "A", "strict"),
    ("Movement Points", "移动力", "game", "movement points; mp", "行动点", "", "A", "strict"),
    ("Supply", "补给", "game", "supply; supplies", "供应", "", "A", "strict"),
    ("Fuel", "燃料", "game", "fuel", "燃油", "", "A", "strict"),
    ("Ammo", "弹药", "game", "ammo; ammunition", "军火", "", "A", "strict"),
    ("Fatigue", "疲劳", "game", "fatigue", "劳累", "", "A", "strict"),
    ("Morale", "士气", "game", "morale", "斗志", "", "A", "strict"),
    ("Experience", "经验", "game", "experience; exp", "阅历", "", "A", "strict"),
    ("Initiative", "主动性", "game", "initiative", "主动权", "将领属性", "A", "strict"),
    ("Admin", "行政", "game", "admin; administration", "管理", "将领属性", "A", "strict"),
    ("Interdiction", "遮断", "game", "interdiction", "拦截", "军事术语", "A", "strict"),
    ("Attrition", "消耗", "game", "attrition", "磨损", "", "A", "strict"),
    ("Isolation", "孤立", "game", "isolation; isolated", "隔离", "", "A", "strict"),
    ("Pocket", "包围圈", "game", "pocket; encirclement", "口袋", "", "A", "strict"),
    ("Refit", "整补", "game", "refit", "改装", "", "A", "strict"),
    ("Fortification", "工事", "game", "fortification; fortifications", "堡垒", "", "A", "strict"),
    ("Entrenchment", "构筑工事", "game", "entrenchment; entrench", "堑壕", "", "A", "strict"),
    ("Rail Repair", "铁路修复", "game", "rail repair; rail repair unit", "铁路修理", "", "A", "strict"),
    ("Railhead", "铁路终点", "game", "railhead", "铁路头", "", "A", "strict"),
    ("Depot", "补给站", "game", "depot; depots", "仓库", "", "A", "strict"),
    ("HQ Buildup", "司令部集结补给", "game", "hq buildup; buildup", "", "WitE2 机制", "A", "strict"),
    ("Air Superiority", "制空权", "game", "air superiority", "空中优势", "", "A", "strict"),
    ("Air Interdiction", "空中遮断", "game", "air interdiction", "空中拦截", "", "A", "strict"),
    ("Ground Support", "近距空中支援", "game", "ground support", "地面支援", "", "A", "strict"),
    ("Weather", "天气", "game", "weather", "气候", "", "A", "strict"),
    ("Mud", "泥泞", "game", "mud; rasputitsa", "泥浆", "", "A", "strict"),
    ("Snow", "雪", "game", "snow", "下雪", "", "A", "strict"),
    ("Blizzard", "暴风雪", "game", "blizzard", "雪暴", "", "A", "strict"),
    ("Frozen", "冻结", "game", "frozen", "冰冻", "地面状态", "A", "strict"),
    ("Clear", "晴朗", "game", "clear", "清除", "天气", "A", "strict"),
    ("Rain", "雨", "game", "rain", "下雨", "", "A", "strict"),
    ("Air Directive", "空中指令", "game", "air directive; air directives", "空军指令", "", "A", "strict"),
    ("Air Phase", "空中阶段", "game", "air phase", "空军阶段", "", "A", "strict"),
    ("Ground Phase", "地面阶段", "game", "ground phase", "陆军阶段", "", "A", "strict"),
    ("Logistics Phase", "后勤阶段", "game", "logistics phase", "补给阶段", "", "A", "strict"),
    ("Commander's Report", "指挥官报告", "game", "commander's report; commanders report; cr", "司令报告", "", "A", "strict"),
    ("Ground Element", "地面分队", "game", "ground element; ground elements", "地面单位", "WitE2 装备级分队", "A", "strict"),
    ("Device", "装备", "game", "device; devices", "设备", "", "A", "strict"),
    ("Air Group", "航空队", "game", "air group; air groups", "飞行大队", "", "A", "strict"),
    ("Airbase", "机场", "game", "airbase; air base", "空军基地", "", "A", "strict"),
    ("Assault", "突击", "game", "assault", "强攻", "", "A", "strict"),
    ("Attack", "攻击", "game", "attack", "进攻", "", "A", "hint"),
    ("Defend", "防御", "game", "defend; defense; defence", "防守", "", "A", "hint"),
    ("Bombard", "炮击", "game", "bombard; bombardment", "轰炸", "", "A", "strict"),
    ("Move", "移动", "game", "move", "行动", "", "A", "hint"),
    ("Rail Transport", "铁路运输", "game", "rail transport; rail movement", "火车运输", "", "A", "strict"),
    ("Air Transport", "空运", "game", "air transport", "空中运输", "", "A", "strict"),
    ("Naval Transport", "海运", "game", "naval transport; sea transport", "海上运输", "", "A", "strict"),
    ("Resupply", "补给", "game", "resupply", "再供应", "", "A", "hint"),
    ("Reinforce", "增援", "game", "reinforce; reinforcement", "加强", "", "A", "hint"),
    ("Withdraw", "撤离", "game", "withdraw; withdrawal", "撤退", "", "A", "hint"),
    ("Transfer", "转隶", "game", "transfer", "转移", "部队调归", "A", "strict"),
    ("Attach", "配属", "game", "attach", "附加", "", "A", "strict"),
    ("Detach", "解除配属", "game", "detach", "分离", "", "A", "strict"),
    ("Support", "支援", "game", "support", "支持", "", "A", "hint"),
    ("Ready", "就绪", "game", "ready", "准备", "", "A", "hint"),
    ("Unready", "未就绪", "game", "unready", "未准备", "", "A", "strict"),
    ("Surrounded", "被包围", "game", "surrounded", "包围", "", "A", "strict"),
    ("Routed", "溃退", "game", "routed; rout", "击溃", "", "A", "strict"),
    ("Retreat", "撤退", "game", "retreat", "退却", "", "A", "hint"),
    ("Shattered", "被击溃", "game", "shattered", "粉碎", "", "A", "strict"),
    ("Destroyed", "被消灭", "game", "destroyed", "摧毁", "", "A", "strict"),
    ("Captured", "被俘", "game", "captured", "捕获", "", "A", "strict"),
    ("Disabled", "失能", "game", "disabled", "残疾", "装备/人员状态", "A", "strict"),
    ("Damaged", "受损", "game", "damaged", "损坏", "", "A", "strict"),
]

# Compound formation terms.  Longer forms win in the matcher, so these prevent
# "Panzer Army" from being checked as two unrelated words.
EXTRA_ROWS = [
    ("Panzer Army", "装甲集团军", "organization", "panzer army; panzerarmee", "坦克集团军", "", "A", "strict"),
    ("Tank Army", "坦克集团军", "organization", "tank army", "", "", "A", "strict"),
    ("Shock Army", "突击集团军", "organization", "shock army", "", "", "A", "strict"),
    ("Guards Army", "近卫集团军", "organization", "guards army", "", "", "A", "strict"),
    ("Rifle Division", "步兵师", "organization", "rifle division", "步枪师", "苏军", "A", "strict"),
    ("Guards Rifle Division", "近卫步兵师", "organization", "guards rifle division", "", "苏军", "A", "strict"),
    ("Panzer Division", "装甲师", "organization", "panzer division", "坦克师", "德军", "A", "strict"),
    ("Panzergrenadier Division", "装甲掷弹兵师", "organization", "panzergrenadier division", "装甲步兵师", "德军", "A", "strict"),
    ("Infantry Division", "步兵师", "organization", "infantry division", "", "", "A", "strict"),
    ("Cavalry Division", "骑兵师", "organization", "cavalry division", "", "", "A", "strict"),
    ("Mountain Division", "山地师", "organization", "mountain division", "", "", "A", "strict"),
    ("Airborne Division", "空降师", "organization", "airborne division", "", "", "A", "strict"),
    ("Security Division", "治安师", "organization", "security division", "", "", "A", "strict"),
    ("Luftwaffe Field Division", "空军野战师", "organization", "luftwaffe field division", "", "", "A", "strict"),
    ("Volksgrenadier Division", "国民掷弹兵师", "organization", "volksgrenadier division", "", "", "A", "strict"),
    ("Panzer Corps", "装甲军", "organization", "panzer corps", "", "", "A", "strict"),
    ("Tank Corps", "坦克军", "organization", "tank corps", "", "", "A", "strict"),
    ("Rifle Corps", "步兵军", "organization", "rifle corps", "", "", "A", "strict"),
    ("Cavalry Corps", "骑兵军", "organization", "cavalry corps", "", "", "A", "strict"),
    ("Mechanized Corps", "机械化军", "organization", "mechanized corps", "", "", "A", "strict"),
    ("Motorized Corps", "摩托化军", "organization", "motorized corps", "", "", "A", "strict"),
    ("Air Army", "空军集团军", "organization", "air army", "", "", "A", "strict"),
    ("Air Corps", "航空军", "organization", "air corps", "", "", "A", "strict"),
    ("Red Army", "红军", "organization", "red army; workers' and peasants' red army", "", "", "A", "strict"),
    ("Soviet Army", "苏军", "organization", "soviet army", "", "", "A", "strict"),
    ("German Army", "德军", "organization", "german army", "", "", "A", "strict"),
    ("Red Banner", "红旗", "organization", "red banner", "", "苏军荣誉称号", "A", "strict"),
    ("Soviet", "苏联", "nation", "soviet; soviet union; ussr", "", "", "A", "strict"),
    ("German", "德国", "nation", "german; germany", "", "", "A", "strict"),
    ("Romanian", "罗马尼亚", "nation", "romanian; rumanian; romania; rumania", "", "", "A", "strict"),
    ("Hungarian", "匈牙利", "nation", "hungarian; hungary", "", "", "A", "strict"),
    ("Italian", "意大利", "nation", "italian; italy", "", "", "A", "strict"),
    ("Finnish", "芬兰", "nation", "finnish; finland", "", "", "A", "strict"),
    ("Axis", "轴心国", "nation", "axis", "", "", "A", "strict"),
]

# Generic words that are too context-dependent to enforce mechanically.
GENERIC_HINT = {
    "Destroyed", "Captured", "Damaged", "Disabled", "Shattered", "Routed",
    "Surrounded", "Front", "Bombard", "Retreat", "Withdraw", "Reinforce",
    "Resupply", "Support", "Ready", "Unready", "Clear", "Major",
}

DROP_ALIASES = {
    "Anti-Tank": {"at"},
    "Artillery": {"art"},
    "Engineer": {"eng"},
    "Guards": {"guard"},
}

# English rank synonyms are ambiguous between the German and Soviet systems.
DROP_RANK_ALIASES = {
    "colonel", "lieutenant colonel", "major", "captain", "first lieutenant",
    "lieutenant", "sergeant", "corporal", "lance corporal", "private",
}

HEADER = ["en", "zh", "category", "aliases", "forbidden", "notes", "confidence", "mode", "source"]


def main():
    seen = {}
    rows = []
    for en, zh, cat, aliases, forbidden, notes, conf, mode in ROWS + EXTRA_ROWS:
        key = en.strip().lower()
        if key in seen:
            raise SystemExit(f"duplicate en: {en!r} (also {seen[key]!r})")
        seen[key] = en
        alias_list = [a.strip() for a in aliases.split(";") if a.strip()]
        if cat == "rank":
            alias_list = [a for a in alias_list if a.lower() not in DROP_RANK_ALIASES]
        if en == "Marine":
            alias_list = [a for a in alias_list if a.lower() != "naval infantry"]
        if en == "SS":
            alias_list = [a for a in alias_list if a.lower() not in ("waffen-ss", "waffen ss")]
        if en in DROP_ALIASES:
            alias_list = [a for a in alias_list if a.lower() not in DROP_ALIASES[en]]
        if en in GENERIC_HINT:
            mode = "hint"
        rows.append([en, zh, cat, ";".join(alias_list), forbidden, notes, conf, mode, "curated-seed"])
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    print(f"wrote {len(rows)} entries to {OUT}")


if __name__ == "__main__":
    main()
