# -*- coding: utf-8 -*-
"""空军番号译名规则（AirGroups.csv / AOGs.csv 的 Name 列）。

纯确定性转换：不联网、不引用任何第三方汉化资源。函数返回 None 表示「不认识，
保持英文」。体例与仓库既有 1,431 条译文一致：

  苏军  1 IAP            -> 第1歼击航空团
        1 GBAP           -> 近卫第1轰炸航空团
        1006 IAP PVO     -> 防空第1006歼击航空团
        10 OAS GVF       -> 民航第10独立航空中队
  德军  II./JG 1         -> 第1战斗机联队第2大队
        Stab/FAGr 1      -> 第1远程侦察大队指挥部
  英美  No.81 RAF FB Sqn -> 皇家空军第81战斗轰炸机中队
        93rd USAAF LB Grp-> 美国陆军航空队第93重型轰炸机大队

术语依据：Living manual 16.4.9（苏军番号缩写表）、16.4.8（德军缩写表）。
"""
import re

ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
         'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13,
         'XIV': 14, 'XV': 15}

TYPE = {
    'FB': '战斗轰炸机', 'LB': '重型轰炸机', 'Pa': '巡逻', 'TR': '运输',
    'Rec': '侦察', 'Recon': '侦察', 'NF': '夜间战斗机', 'TacB': '战术轰炸机',
    'TB': '鱼雷轰炸机', 'F': '战斗机', 'Ftr': '战斗机', 'B': '轰炸机',
    'Bomb': '轰炸机', 'DB': '俯冲轰炸机', 'Dive Bomb': '俯冲轰炸机',
    'Atk': '攻击机', 'PR': '照相侦察', 'Patrol': '巡逻', 'Transport': '运输',
    'Fighter': '战斗机', 'Bomber': '轰炸机',
    'Trans': '运输', 'Torpedo': '鱼雷', 'AS': '反潜', 'APC': '装甲运输',
    'Assault': '强击', 'Night Ftr': '夜间战斗机', 'Night Bomb': '夜间轰炸机',
    'Fast Bomb': '快速轰炸机', 'LR Recon': '远程侦察', 'Naval Recon': '海上侦察',
    'Ind. Ftr': '独立战斗机', 'Parachute Trans': '伞兵运输',
    'HS': '高速', 'HS Patrol': '高速巡逻',
}

FORCE = {
    'RAF': '皇家空军', 'RCAF': '加拿大皇家空军', 'RAAF': '澳大利亚皇家空军',
    'RNZAF': '新西兰皇家空军', 'SAAF': '南非空军', 'RIAF': '印度皇家空军',
    'NEIAF': '荷属东印度空军',
    'USAAF': '美国陆军航空队', 'USN': '美国海军', 'NAS': '海军航空兵',
    'FFr': '自由法国空军', 'Ital.': '意大利空军', 'Ita': '意大利空军',
    'Rum.': '罗马尼亚空军', 'Rum': '罗马尼亚空军',
    'Hun.': '匈牙利空军', 'Hun': '匈牙利空军',
    'Slov.': '斯洛伐克空军', 'Bul.': '保加利亚空军', 'Bul': '保加利亚空军',
    'Bra': '巴西空军', 'WAI': '盟军意大利空军', 'Croat.': '克罗地亚空军',
    'ANR': '意大利社会共和国空军',
}

RAF_TAG = {'PO': '波兰', 'FF': '自由法国', 'CZ': '捷克斯洛伐克', 'NO': '挪威',
           'BE': '比利时', 'NE': '荷兰', 'DU': '荷兰', 'YU': '南斯拉夫',
           'GR': '希腊', 'NL': '荷兰'}


def _clean(n):
    n = n.strip().replace('\u00a0', ' ')
    n = re.sub(r'\s+', ' ', n)
    n = n.replace('""', '"')
    return n


def _num(s):
    m = re.match(r'^(\d+)(?:st|nd|rd|th|a|\.|º|°)?$', s.strip())
    return m.group(1) if m else None


# ------------------------------------------------------------ 分组表头
THEATER = {
    'Italian Air Groups': '意大利航空队', 'German Air Groups': '德国航空队',
    'Soviet Air Groups': '苏联航空队', 'Finnish Air Groups': '芬兰航空队',
    'Rumanian Air Groups': '罗马尼亚航空队', 'Hungarian Air Groups': '匈牙利航空队',
    'Slovak Air Groups': '斯洛伐克航空队', 'Slovakian Air Groups': '斯洛伐克航空队',
    'Bulgarian Air Groups': '保加利亚航空队', 'Allied Maritime Groups': '盟军海上航空队',
    'Axis Maritime Groups': '轴心国海上航空队', 'Axis Air Divisions': '轴心国航空师',
    'Soviet Air Divisions': '苏联航空师', 'Soviet Navy Extension': '苏联海军扩展',
    'LW East Front': '东线德国空军', 'STAVKA': '最高统帅部',
    'Additional Axis AOGs': '轴心国增补航空作战群',
}
BOX = {
    'Northern Front Theater Box': '北方方面军战区盒',
    'Italy Theater Box': '意大利战区盒', 'Axis Reserves Box': '轴心国预备队战区盒',
    'Balkans Theater Box': '巴尔干战区盒', 'Far East Theater Box': '远东战区盒',
    'Finland Theater Box': '芬兰战区盒', 'North Africa Theater Box': '北非战区盒',
    'Norway Theater Box': '挪威战区盒', 'Transcaucasus Theater Box': '外高加索战区盒',
    'Western Europe Theater Box': '西欧战区盒', 'EF Holding Box - LF 1': '东线集结区 - 第1航空队',
    'LW Kdo Southeast Box': '东南空军司令部集结区',
    'Luftflotte 5 Holding Box': '第5航空队集结区', 'Luftflotte Reich': '国土航空队',
}


def _theater(name):
    m = re.match(r'^(\*+)\s*(.+?)\s*(\*+)$', name)
    if not m:
        return None
    pre, inner, post = m.group(1), m.group(2), m.group(3)
    if inner in BOX:
        return '%s %s %s' % (pre, BOX[inner], post)
    if inner in THEATER:
        return '%s %s %s' % (pre, THEATER[inner], post)
    m2 = re.match(r'^(\d+)(?:st|nd|rd|th)?\s*(?:Air Army|IAK PVO Air Comd)$', inner)
    if m2:
        if 'IAK' in inner:
            return '%s 第%s防空歼击航空军 %s' % (pre, m2.group(1), post)
        return '%s 第%s航空集团军 %s' % (pre, m2.group(1), post)
    if inner == '':
        return None
    return None


# ------------------------------------------------------------ 德军
GER = {
    'JG': '战斗机联队', 'NJG': '夜间战斗机联队', 'ZG': '驱逐机联队',
    'StG': '俯冲轰炸机联队', 'SG': '对地攻击机联队', 'Sch.G': '对地攻击机联队',
    'Schl.G': '对地攻击机联队', 'KG': '轰炸机联队', 'KG(J)': '轰炸机联队',
    'KG (J)': '轰炸机联队', 'SKG': '快速轰炸机联队', 'LLG': '教导联队',
    'LehrG': '教导联队', 'LG': '教导联队', 'TG': '运输机联队', 'JV': '战斗机特遣队',
    'NAGr': '侦察大队', 'FAGr': '远程侦察大队', 'AufklarGr': '侦察大队',
    'Aufklar Gr': '侦察大队', 'NSGr': '夜间对地攻击机大队', 'NJG': '夜间战斗机联队',
    'NJGr': '夜间战斗机大队', 'SAGr': '海上侦察大队', 'KuFlGr': '海岸航空大队',
    'Ku.Fl.Gr': '海岸航空大队', 'BoFlGr': '舰载机大队', 'KGr': '轰炸机大队',
    'KGr zbV': '特种任务轰炸机大队', 'KG zbV': '特种任务轰炸机联队',
    'KGzbV': '特种任务轰炸机联队', 'TGr': '运输机大队', 'JGr': '战斗机大队',
    'ErgGr': '补充大队', 'Erg-ZGr': '补充驱逐机大队',
}
GER_ROLE = {'F': '远程侦察', 'H': '陆军侦察', 'Pz': '反坦克', 'PzJ': '反坦克',
            'Jabo': '战斗轰炸', 'Sturm': '突击', 'See': '海上', 'T': '鱼雷',
            'Stuka': '俯冲轰炸', 'Sch': '对地攻击', 'Jagd': '战斗机',
            'Hoeh.': '高空', 'Eis': '铁路', 'Span': '西班牙',
            'Croat': '克罗地亚', 'Slov': '斯洛伐克', 'Lett': '拉脱维亚',
            'Est': '爱沙尼亚', 'Croat.': '克罗地亚', 'Z': '驱逐机'}


def _ger_unit(s):
    """'JG 1' -> ('第1战斗机联队', None)；不认识的返回 (None, None)。"""
    s = s.strip()
    for key in sorted(GER, key=len, reverse=True):
        m = re.match(r'^%s\s*(\d+)(?:\s*\(([^)]*)\))?(\*?)$' % re.escape(key), s)
        if m:
            num, tag, star = m.group(1), m.group(2), m.group(3)
            label = GER[key]
            out = '第%s%s' % (num, label)
            if tag:
                if tag in GER_ROLE:
                    r = GER_ROLE[tag]
                    if label == '轰炸机联队' and r == '鱼雷':
                        out = out.replace(label, '鱼雷轰炸机联队')
                    elif label.endswith('联队') or label.endswith('大队'):
                        out = out.replace(label, r + label)
                else:
                    out += '（%s）' % tag
            return out + star, key
    return None, None


def _german(n):
    n = _clean(n)
    # 特殊前缀单位
    m = re.match(r'^(Sonderkommando|Einsatzkommando)\s+(.+)$', n)
    if m:
        return '特遣队%s' % m.group(2)
    m = re.match(r'^Gruppe\s+(.+)$', n)
    if m:
        return '%s大队' % m.group(1)
    # Stab / Stab I. / Stab(Sturm)
    m = re.match(r'^Stab(?:\(([\w.]+)\))?\s*(?:([IVX]+)\.\s*)?/\s*(.+)$', n)
    if m:
        role, grp, rest = m.group(1), m.group(2), m.group(3)
        base, key = _ger_unit(rest)
        if base:
            if grp:
                return '%s第%s大队指挥部' % (base, ROMAN.get(grp, grp))
            if role:
                return base + GER_ROLE.get(role, role) + '指挥部'
            return base + '指挥部'
    # II./JG 1 ；10.(Pz)/SG 1 ；1./Ku.Fl.Gr 196
    m = re.match(r'^([IVX]+|\d+)\.(?:\(([\w.]+)\))?\s*/\s*(.+?)(?:\s*\(([^)]*)\))?$', n)
    if m:
        num, role, rest, extra = m.groups()
        base, key = _ger_unit(rest)
        if base:
            if num.isdigit():
                tail = '第%s中队' % num
                if role:
                    tail += '（%s）' % GER_ROLE.get(role, role)
            else:
                tail = '第%s大队' % ROMAN.get(num, num)
                if role:
                    tail = '第%s%s大队' % (ROMAN.get(num, num), GER_ROLE.get(role, role))
            if extra:
                tail += '（%s）' % extra
            return base + tail
    # 10.(Sch)/LG 2 之类（role 在斜杠前）
    m = re.match(r'^([IVX]+|\d+)\.\(([\w.]+)\)\s*/\s*(.+)$', n)
    if m:
        num, role, rest = m.group(1), m.group(2), m.group(3)
        base, _ = _ger_unit(rest)
        if base:
            r = GER_ROLE.get(role, role)
            if num.isdigit():
                return base + '第%s%s中队' % (num, r)
            return base + '第%s%s大队' % (ROMAN.get(num, num), r)
    # PzJ/StG 1、Erg-Stfl/JG 77、Jabostaffel/JG 3、PzJ Staffel/JG 51
    m = re.match(r'^(PzJ|PzJ Staffel|Erg-Stfl(?:\s*\([^)]*\))?|Jabostaffel|Aufklar-Stfl|Sturmstaffel)\s*/\s*(.+)$', n)
    if m:
        base, _ = _ger_unit(m.group(2))
        if base:
            head = m.group(1)
            if head.startswith('PzJ'):
                return base + '反坦克中队'
            if head.startswith('Erg'):
                return base + '补充中队'
            if head.startswith('Jabo'):
                return base + '战斗轰炸中队'
            if head.startswith('Aufklar'):
                return base + '侦察中队'
            return base + '突击中队'
    m = re.match(r'^Aufklar-Stfl\s+([IVX]+)\s+(?:Flgkorps|Fliegerkorps)$', n)
    if m:
        return '第%s航空军侦察中队' % ROMAN.get(m.group(1), m.group(1))
    m = re.match(r'^(Transportstaffel|Sturmstaffel|Aufklar-Stfl|Aufklaerstaffel|Kuesten ?Staffel|Sonderkommando|Jabostaffel)\s+(.+)$', n)
    if m:
        head, rest = m.group(1), m.group(2)
        if _num(rest):
            if head.startswith('Transport'):
                return '第%s运输中队' % _num(rest)
            if head.startswith('Sturm'):
                return '第%s突击中队' % _num(rest)
            return '第%s侦察中队' % _num(rest)
        if head.startswith('Kuesten'):
            return '%s海岸中队' % _place_cn(rest)
        if head.startswith('Jabo'):
            return '%s战斗轰炸中队' % _place_cn(rest)
        if head.startswith('Sonder'):
            return '特遣队%s' % rest
        return '%s侦察中队' % _place_cn(rest)
    m = re.match(r'^KGr zbV\s+(\S+)$', n)
    if m:
        if _num(m.group(1)):
            return '第%s特种任务轰炸机大队' % _num(m.group(1))
        return '特种任务轰炸机大队%s' % _place_cn(m.group(1))
    m = re.match(r'^TS\.\s*/\s*([IVX]+)$', n)
    if m:
        return '第%s运输中队' % ROMAN.get(m.group(1), m.group(1))
    base, _ = _ger_unit(n)
    return base


# ------------------------------------------------------------ 苏军
SOV = {
    'IAP': '歼击航空团', 'BAP': '轰炸航空团', 'SBAP': '混编轰炸航空团',
    'TBAP': '重型轰炸航空团', 'LBAP': '轻型轰炸航空团', 'DBAP': '远程轰炸航空团',
    'BBAP': '近程轰炸航空团', 'ShAP': '强击航空团', 'NBAP': '夜间轰炸航空团',
    'GBAP': '近卫轰炸航空团', 'GNBAP': '近卫夜间轰炸航空团', 'GIAP': '近卫歼击航空团',
    'GShAP': '近卫强击航空团', 'GRAP': '近卫侦察航空团', 'RAP': '侦察航空团',
    'TAP': '运输航空团', 'MTAP': '鱼雷航空团', 'MRAP': '海上侦察航空团',
    'ORAE': '独立侦察航空中队', 'ODRAE': '独立远程侦察航空中队',
    'OIAE': '独立歼击航空中队', 'OAS': '独立航空中队', 'OAPP': '独立航空团',
    'SAP': '混编航空团', 'PBAP': '俯冲轰炸航空团', 'RezAP': '预备航空团',
    'GTAP': '近卫运输航空团', 'GTBAP': '近卫重型轰炸航空团', 'TRAP': '运输航空团',
    'MRAE': '海上侦察航空中队', 'OMRAE': '独立海上侦察航空中队',
    'GMRAP': '近卫海上侦察航空团', 'IAPP': '歼击航空团', 'IAE': '歼击航空中队',
    'PDA': '转场航空团',
    'IAD': '歼击航空师', 'ShAD': '强击航空师', 'BAD': '轰炸航空师',
    'GShAK': '近卫强击航空军', 'ShAK': '强击航空军', 'IAK': '歼击航空军',
    'IABR': '歼击航空旅', 'RAG': '侦察航空团', 'CAP': '航空中队',
}
SOV_SUF = {'PVO': '防空', 'SF': '北方舰队', 'KBF': '红旗波罗的海舰队',
           'ChF': '黑海舰队', 'GVF': '民航', 'PF': '太平洋舰队',
           'BF': '波罗的海舰队'}


def _suf(s):
    """舰队/防空后缀，容忍大小写混写（Chf/ChF、Kbf/KBF）。"""
    if not s:
        return None
    for k, v in SOV_SUF.items():
        if k.lower() == s.lower():
            return v
    return None


def _sov_num(pre, num, typ):
    """苏军「第N兵种」；近卫部队固定写成「近卫第N」（与既有词典体例一致）。"""
    label = SOV[typ]
    if label.startswith('近卫'):
        return '%s近卫第%s%s' % (pre, num, label[2:])
    return '%s第%s%s' % (pre, num, label)


def _sov_body(num, typ, pre='', tag=None, star=''):
    out = _sov_num(pre, num, typ)
    if typ in ('IAP', 'IAPP') and pre == '防空':
        out = _sov_num('防空', num, typ)
    if tag:
        out += '「%s」' % tag
    return out + star


def _soviet(n):
    n = _clean(n)
    # 2/13 IAP-KBF（大队/团号）
    m = re.match(r'^(\d+)/(\d+)\s+([A-Z]+)(?:-([A-Za-z]+))?(?:\s+([A-Za-z]+))?$', n)
    if m and m.group(3) in SOV:
        pre = _suf(m.group(4)) or _suf(m.group(5)) or ''
        return _sov_num(pre, m.group(2), m.group(3)) + '第%s大队' % m.group(1)
    # 10 IAP "A" / "10 IAP ""A""" / 24 IAP PVO "A" / 28 "A" IAP PVO
    m = re.match(r'^(\d+)\s+"([A-Z]+)"\s+([A-Z]+)(?:\s+([A-Za-z]+))?$', n)
    if m and m.group(3) in SOV:
        return _sov_body(m.group(1), m.group(3), _suf(m.group(4)) or '', m.group(2))
    m = re.match(r'^(\d+)\s+([A-Z]+)(?:-([A-Za-z]+))?(?:\s+([A-Za-z]+))?(?:\s+"([A-Z]+)")?$', n)
    if m and m.group(2) in SOV:
        num, typ, suf, extra, tag = m.groups()
        pre = ''
        if _suf(suf):
            pre = _suf(suf)
        elif suf:
            return None
        if _suf(extra):
            pre = _suf(extra)
        elif extra:
            return None
        return _sov_body(num, typ, pre, tag)
    # 地名前缀：Kiev OAS GVF / North Caucasus TAP GVF / 1 Latvian NBAP
    m = re.match(r'^(.+?)\s+(OAS|TAP|CAP)\s+GVF$', n)
    if m:
        return '民航%s%s' % (_place_cn(m.group(1)), SOV[m.group(2)])
    m = re.match(r'^(\d+)\s+(Latvian|Estonian|Lithuanian)\s+([A-Z]+)$', n)
    if m and m.group(3) in SOV:
        return '%s第%s%s' % ({'Latvian': '拉脱维亚', 'Estonian': '爱沙尼亚',
                            'Lithuanian': '立陶宛'}[m.group(2)], m.group(1), SOV[m.group(3)])
    if n == 'Penal ORAE':
        return '惩戒独立侦察航空中队'
    if n == 'RC Normandie-Nieman':
        return '诺曼底-涅曼歼击航空团'
    return None


PLACE_CN = {'Kiev': '基辅', 'North Caucasus': '北高加索', 'Southwest': '西南',
            'Finnland': '芬兰', 'Krim': '克里米亚', 'Kroatien': '克罗地亚',
            'Frankfurt': '法兰克福', 'Wittstock': '维茨托克', 'Ostsee': '波罗的海',
            'Northwest': '西北', 'E.Prussia': '东普鲁士', 'Hungary': '匈牙利',
            'Rumania': '罗马尼亚', 'Kaukasus': '高加索', 'Finnish': '芬兰',
            'Hungarian': '匈牙利', 'Italian': '意大利', 'Rumanian': '罗马尼亚',
            'Slovakian': '斯洛伐克', 'Norwegian': '挪威', 'Bulgarian': '保加利亚',
            'North': '北部', 'Western': '西部', 'Karelian': '卡累利阿',
            'Moscow': '莫斯科', 'Leningrad': '列宁格勒', 'Crimea': '克里米亚',
            'Baltic': '波罗的海', 'Arkhangelsk': '阿尔汉格尔斯克', 'Baku': '巴库',
            'Bryansk': '布良斯克', 'Kalinin': '加里宁', 'Kharkov': '哈尔科夫',
            'Odessa': '敖德萨', 'Orel': '奥廖尔', 'Volkhov': '沃尔霍夫',
            'Transbaikal': '外贝加尔', 'Transcaucasus': '外高加索',
            'Central Asia': '中亚', 'Far East': '远东', 'Urals': '乌拉尔',
            'Volga': '伏尔加', 'Siberia': '西伯利亚', 'Reserve': '预备',
            'Long Range': '远程', 'Northern Fleet': '北方舰队',
            'Pacific Fleet': '太平洋舰队', 'Baltic Fleet': '波罗的海舰队',
            'Black Sea Fleet': '黑海舰队', 'Dobrogea': '多布罗加'}


def _place_cn(p):
    return PLACE_CN.get(p, p)


# ------------------------------------------------------------ 英美
def _raf(n):
    m = re.match(r'^No\.(\d+)\s*(?:\(([A-Z]+)\)\s*)?(RAF|RCAF|RAAF|RNZAF|SAAF|RIAF|NEIAF)\s+([A-Za-z]+)\s+(Sqn|Squadron)$', n)
    if not m or m.group(4) not in TYPE:
        return None
    num, tag, force, typ, kind = m.groups()
    s = FORCE[force]
    if tag:
        s += '（%s）' % RAF_TAG.get(tag, tag)
    return '%s第%s%s%s' % (s, num, TYPE[typ], '中队' if kind.startswith('Sqn') else '大队')


def _usaaf(n):
    m = re.match(r'^(\d+)(?:st|nd|rd|th)\s+(USAAF|USN)\s+([A-Za-z]+)\s+(Grp|Sqn|Group|Squadron)$', n)
    if m and m.group(3) in TYPE:
        num, force, typ, kind = m.groups()
        return '%s第%s%s%s' % (FORCE[force], num, TYPE[typ], '大队' if kind.startswith('Grp') else '中队')
    m = re.match(r'^(\d+)(?:st|nd|rd|th)\s+USAAF$', n)
    if m:
        return '美国陆军航空队第%s大队' % m.group(1)
    return None


def _nas(n):
    m = re.match(r'^(\d+)\s+NAS\s+([A-Za-z]+)\s+Sqn$', n)
    if m and m.group(2) in TYPE:
        return '海军航空兵第%s%s中队' % (m.group(1), TYPE[m.group(2)])
    m = re.match(r'^(VP)-(\d+)\s+USN\s+([A-Za-z]+)\s+Sqn$', n)
    if m and m.group(3) in TYPE:
        return '美国海军第%s%s中队' % (m.group(2), TYPE[m.group(3)])
    return None


# ------------------------------------------------------------ 意大利
def _italian(n):
    m = re.match(r'^(\d+)a\s+(Ital\.|Ita|ANR)\s+([A-Za-z.]+(?:\s[A-Za-z.]+)?)\s+(Grp|Sqn)$', n)
    if m:
        typ = TYPE.get(m.group(3))
        if typ:
            return '%s第%s%s%s' % (FORCE.get(m.group(2), '意大利空军'), m.group(1), typ,
                                 '大队' if m.group(4) == 'Grp' else '中队')
    m = re.match(r'^(\d+)a/(\d+)a\s+Ita\s+([A-Za-z]+)\s+Sqn$', n)
    if m and m.group(3) in TYPE:
        return '意大利空军第%s大队第%s%s中队' % (m.group(2), m.group(1), TYPE[m.group(3)])
    m = re.match(r'^([IVX]+) ?a\s+Gruppo\s+(\w+)$', n)
    if m:
        return '意大利空军第%s%s大队' % (ROMAN.get(m.group(1), m.group(1)),
                                     {'Caccia': '战斗机', 'Bombardamento': '轰炸机'}.get(m.group(2), m.group(2)))
    m = re.match(r"^'([^']+)'\s+Ita\s+([A-Za-z]+)\s+(Grp|Sqn)$", n)
    if m and m.group(2) in TYPE:
        return '意大利空军「%s」%s%s' % (m.group(1), TYPE[m.group(2)], '大队' if m.group(3) == 'Grp' else '中队')
    m = re.match(r'^Sezione\s+Ita\s+([A-Za-z]+)\s+Sqn$', n)
    if m and m.group(1) in TYPE:
        return '意大利空军%s小队' % TYPE[m.group(1)]
    if n == 'ANR Ital. Air Force':
        return '意大利社会共和国空军'
    if n == 'Italian Co-Belligerent Air Force':
        return '意大利协同交战国空军'
    return None


# ------------------------------------------------------------ 罗马尼亚
def _romanian(n):
    m = re.match(r'^(\d+)(?:st|nd|rd|th)?\s+Rum\.?\s+([A-Za-z. ]+?)\s+(Sqn|Group|Grp|Flotilla)$', n)
    if m:
        typ = TYPE.get(m.group(2))
        if typ:
            return '罗马尼亚空军第%s%s%s' % (m.group(1), typ,
                                        {'Sqn': '中队', 'Group': '大队', 'Grp': '大队', 'Flotilla': '支队'}[m.group(3)])
    m = re.match(r'^(\d+)(?:st|nd|rd|th)/(\d+)(?:st|nd|rd|th)\s+Rum\.?\s+([A-Za-z. ]+?)\s+Sqn$', n)
    if m and m.group(3) in TYPE:
        return '罗马尼亚空军第%s大队第%s%s中队' % (m.group(2), m.group(1), TYPE[m.group(3)])
    # 41st/8th Rum Ftr Sqn（无 th 后缀形式）
    m = re.match(r'^(\d+)/(\d+)\s+Rum\.?\s+([A-Za-z. ]+?)\s+Sqn$', n)
    if m and m.group(3) in TYPE:
        return '罗马尼亚空军第%s大队第%s%s中队' % (m.group(2), m.group(1), TYPE[m.group(3)])
    if n == 'Rum. Combat Air Cmd':
        return '罗马尼亚空军作战司令部'
    m = re.match(r'^Rum\.\s+Air\s+Cmd\s+(North|South)$', n)
    if m:
        return '罗马尼亚空军%s司令部' % ('北部' if m.group(1) == 'North' else '南部')
    return None


# ------------------------------------------------------------ 匈牙利
def _hungarian(n):
    m = re.match(r'^([IVX]+)\.\s*/\s*(\d+)(?:st|nd|rd|th)?\.?\s+Hun\.?\s+([A-Za-z. ]+?)\s+(Group|Sqn)$', n)
    if m and m.group(3) in TYPE:
        return '匈牙利空军第%s%s大队第%s中队' % (m.group(2), TYPE[m.group(3)],
                                          ROMAN.get(m.group(1), m.group(1)))
    m = re.match(r'^(\d+)/(\d+)\.?\s+Hun\.?\s+([A-Za-z. ]+?)\s+(FB|Rec|TacB|LB)\s+Sqn$', n)
    if m and m.group(3) in TYPE:
        return '匈牙利空军第%s大队第%s%s中队' % (m.group(2), m.group(1), TYPE[m.group(3)])
    m = re.match(r'^([IVX]+)\.?\s*/\s*(\d+)(?:st|nd|rd|th)\s+([A-Za-z. ]+?)\s+(Group|Sqn)$', n)
    if m and m.group(3).startswith('Hun') and m.group(4) in ('Group', 'Sqn'):
        pass
    m = re.match(r'^([IVX]+)\s+Hun\.?\s+([A-Za-z]+)\s+Sqn$', n)
    if m and m.group(2) in TYPE:
        return '匈牙利空军%s中队' % TYPE[m.group(2)]
    m = re.match(r'^(\d+)(?:st|nd|rd|th)?\.?\s+Hun\.?\s+([A-Za-z. ]+?)\s+(Group|Sqn|Regiment)$', n)
    if m and m.group(2) in TYPE:
        return '匈牙利空军第%s%s%s' % (m.group(1), TYPE[m.group(2)],
                                    {'Group': '大队', 'Sqn': '中队', 'Regiment': '团'}[m.group(3)])
    m = re.match(r'^(\d+)(?:st|nd|rd|th)?\s+([A-Za-z. ]+?)\s+(Group|Sqn)$', n)
    if m and m.group(2).startswith('Hun') and m.group(2)[3:].strip('. ') in TYPE:
        return '匈牙利空军第%s%s%s' % (m.group(1), TYPE[m.group(2)[3:].strip('. ')],
                                    '大队' if m.group(3) == 'Group' else '中队')
    return None


# ------------------------------------------------------------ 芬兰/斯洛伐克/保加利亚/法国/巴西
def _finnish(n):
    m = re.match(r'^(\d+)/LeLv\s+(\d+)$', n)
    if m:
        return '芬兰空军第%s航空中队第%s飞行队' % (m.group(2), m.group(1))
    m = re.match(r'^LeLv\s+(\d+)$', n)
    if m:
        return '芬兰空军第%s飞行中队' % m.group(1)
    return None


def _slovak(n):
    m = re.match(r'^(\d+)(?:st|nd|rd|th)?\.?\s+Slov\.?\s+([A-Za-z]+)\s+(Sqn|Group)$', n)
    if m and m.group(2) in TYPE:
        return '斯洛伐克空军第%s%s%s' % (m.group(1), TYPE[m.group(2)],
                                    '大队' if m.group(3) == 'Group' else '中队')
    if n == 'Slovakian Air Command':
        return '斯洛伐克空军司令部'
    if n == 'Slovakian Air Regiment':
        return '斯洛伐克航空团'
    if n == 'Slovak Expeditionary Air Bde':
        return '斯洛伐克远征航空旅'
    return None


def _bulgarian(n):
    m = re.match(r'^(\d+)/(\d+)\.?\s+Bul\.?\s+([A-Za-z]+)\s+Sqn$', n)
    if m and m.group(3) in TYPE:
        return '保加利亚空军第%s大队第%s%s中队' % (m.group(2), m.group(1), TYPE[m.group(3)])
    return None


def _french(n):
    m = re.match(r'^(GB|GC)\s+([IVX]+)/(\d+)\s+FFr\s+([A-Za-z]+)\s+Sqn$', n)
    if m and m.group(4) in TYPE:
        kind = '轰炸机' if m.group(1) == 'GB' else '战斗机'
        return '自由法国空军第%s/%s%s大队' % (ROMAN.get(m.group(2), m.group(2)), m.group(3), kind)
    return None


def _brazil(n):
    m = re.match(r'^(\d+)(?:st|nd|rd|th)\s+Bra\s+([A-Za-z]+)\s+Sqn$', n)
    if m and m.group(2) in TYPE:
        return '巴西空军第%s%s中队' % (m.group(1), TYPE[m.group(2)])
    return None


def _wai(n):
    m = re.match(r'^(\d+)(?:st|nd|rd|th)\s+WAI\s+([A-Za-z]+)\s+(Sqn|Grp)$', n)
    if m and m.group(2) in TYPE:
        return '盟军意大利空军第%s%s%s' % (m.group(1), TYPE[m.group(2)],
                                      '大队' if m.group(3) == 'Grp' else '中队')
    m = re.match(r'^(\w+)\s+WAI\s+([A-Za-z]+)\s+Sqn$', n)
    if m and m.group(2) in TYPE:
        return '盟军意大利空军「%s」%s中队' % (m.group(1), TYPE[m.group(2)])
    return None


def _misc(n):
    if n.startswith('Sonderkommando '):
        return '特遣队%s' % n[len('Sonderkommando '):]
    if n == 'Savoiastaffel':
        return '萨伏依中队'
    if n == 'Sahariana Ital. Recon Grp':
        return '意大利空军撒哈拉侦察大队'
    return None


# ------------------------------------------------------------ 兜底补丁（第二批）
HUN_TYPE = {'FB': '战斗轰炸机', 'DB': '俯冲轰炸机', 'Bomb': '轰炸机', 'LB': '重型轰炸机',
            'LR Recon': '远程侦察', 'Recon': '侦察', 'Rec': '侦察',
            'Night Bomb': '夜间轰炸机', 'Ftr': '战斗机', 'Ftr Grouo': '战斗机',
            'TacB': '战术轰炸机', 'TR': '运输', 'Assault Bomb': '强击轰炸机',
            'HS Patrol': '高速巡逻', 'Rec Sqn': '侦察', 'Ftr Grouo': '战斗机'}
GER_PLACE = {'Drontheim': '特隆赫姆', 'Kirkenes': '希尔克内斯',
             'Stavanger': '斯塔万格', 'Sued': '南部', 'Krim': '克里米亚',
             'Ostsee': '波罗的海'}
HUN_UNIT = {'Group': '大队', 'Grp': '大队', 'Sqn': '中队', 'Regiment': '团',
            'Grouo': '大队'}


def _hun_type(t):
    t = re.sub(r'\bHun\.?\b', ' ', t)
    t = re.sub(r'\bRum\.?\b', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip(' .')
    return HUN_TYPE.get(t)


def _extra(n):
    """第二批兜底：德军零散单位、苏军带引号番号、匈牙利/罗马尼亚/意大利边角。"""
    # --- 苏军带引号番号（CSV 里被写成 ""10 IAP ""A""""）
    if '"' in n:
        q = ' '.join(n.replace('"', ' ').split())
        toks = q.split()
        tag = None
        if len(toks) > 1 and len(toks[-1]) == 1:
            tag, toks = toks[-1], toks[:-1]
        elif len(toks) > 2 and len(toks[1]) == 1:
            tag, toks = toks[1], [toks[0]] + toks[2:]
        if len(toks) >= 2 and toks[0].isdigit() and toks[1] in SOV:
            suf = _suf(toks[2]) if len(toks) > 2 else None
            if len(toks) <= 2 or suf:
                return _sov_body(toks[0], toks[1], suf or '', tag)
        return None
    # --- 苏军：空降团、独立运输中队、预备团
    m = re.match(r'^(\d+)\s+Airborne\s+OAPP$', n)
    if m:
        return '空降第%s独立航空团' % m.group(1)
    m = re.match(r'^(\d+)\s+(OTAE|RezAP)(?:-([A-Za-z]+))?$', n)
    if m:
        pre = _suf(m.group(3)) or ''
        return '%s第%s%s' % (pre, m.group(1), SOV.get(m.group(2), '预备航空团'))
    # --- 德军：NSGr./TGr./NJGr. 带点
    n2 = re.sub(r'\b(NSGr|TGr|NJGr|NJG|KGr|JGr|JG|KG|LG|SG|ZG|StG|TG|JV|NAGr|SAGr|AufklarGr|FAGr)\.', r'\1', n)
    if n2 != n:
        base, _ = _ger_unit(n2)
        if base:
            return base
    # --- 德军：1.(F) Nacht AufklarGr / 1.(F)/ObdL
    m = re.match(r'^(\d+)\.?\(F\)\s*/?\s*(Nacht AufklarGr|Nacht Aufklarungsgruppe)$', n)
    if m:
        return '夜间远程侦察大队第%s中队' % m.group(1)
    m = re.match(r'^(\d+)\.?\(F\)\s*/\s*ObdL$', n)
    if m:
        return '空军总司令部长程侦察第%s中队' % m.group(1)
    if n == 'Erg-AufklarGr/ObdH':
        return '陆军总司令部补充侦察大队'
    if n == 'Erg-AufklarGr/ObdL':
        return '空军总司令部补充侦察大队'
    if n == 'Erg-ZGr':
        return '补充驱逐机大队'
    m = re.match(r'^ErgGr\s*/\s*(.+)$', n)
    if m:
        base, _ = _ger_unit(m.group(1))
        if base:
            return base + '补充大队'
    m = re.match(r'^JGr\s+(\S+)$', n)
    if m:
        return '%s战斗机大队' % GER_PLACE.get(m.group(1), m.group(1))
    if n == 'Kroat./JGr 1':
        return '克罗地亚第1战斗机大队'
    m = re.match(r'^Kuestenstaffel\s+(\S+)$', n)
    if m:
        return '%s海岸中队' % GER_PLACE.get(m.group(1), m.group(1))
    if n == 'NJ Norway':
        return '挪威夜间战斗机大队'
    m = re.match(r'^NJ-(?:Sta|Stfl)\.?\s*(\S+)$', n)
    if m:
        return '%s夜间战斗机中队' % _place_cn(m.group(1))
    if n == 'Aufklarungs Ostsee':
        return '波罗的海侦察大队'
    m = re.match(r'^(\d+)\.\s*/\s*Jabogruppe Afrika$', n)
    if m:
        return '非洲战斗轰炸机大队第%s中队' % m.group(1)
    m = re.match(r'^([IVX]+)\.\s*\(([A-Za-z]+)\)\s*/\s*(.+)$', n)
    if m:
        base, _ = _ger_unit(m.group(3))
        if base:
            return base + '第%s%s大队' % (ROMAN.get(m.group(1), m.group(1)),
                                       GER_ROLE.get(m.group(2), m.group(2)))
    m = re.match(r'^([IVX]+)\.\s*(JG|KG|LG|SG|ZG|StG|NJG|NSGr|TGr)\s*(\d+)$', n)
    if m:
        label = GER.get(m.group(2))
        if label:
            return '第%s%s第%s大队' % (m.group(3), label, ROMAN.get(m.group(1), m.group(1)))
    m = re.match(r'^([IVX]+|\d+)\.?\s*/\s*(.+)$', n)
    if m:
        rest = re.sub(r'\b(NSGr|TGr|NJGr|NJG|KGr|JGr|JG|KG|LG|SG|ZG|StG|TG|JV|NAGr|SAGr|AufklarGr|FAGr)\.', r'\1', m.group(2))
        base, _ = _ger_unit(rest)
        if base:
            a = m.group(1)
            tail = ('第%s中队' % a) if a.isdigit() else ('第%s大队' % ROMAN.get(a, a))
            return base + tail
    m = re.match(r'^Stab\s*/\s*(.+)$', n)
    if m:
        rest = re.sub(r'\b(NSGr|TGr|NJGr|NJG|KGr|JGr|JG|KG|LG|SG|ZG|StG|TG|JV|NAGr|SAGr|AufklarGr|FAGr)\.', r'\1', m.group(1))
        base, _ = _ger_unit(rest)
        if base:
            return base + '指挥部'
    # --- 意大利
    m = re.match(r'^(\d+)a\s+Ital\.\s+Patrol\s+FF\.NN\s+Grp$', n)
    if m:
        return '意大利空军第%s巡逻大队（FF.NN）' % m.group(1)
    m = re.match(r'^(\d+)a\s+Ital\.\s+RM\s+Patrol\s+Grp$', n)
    if m:
        return '意大利空军第%s海上巡逻大队' % m.group(1)
    m = re.match(r'^(\d+)a\s+Ital\.\s+Recon\s+APC\s+Grp$', n)
    if m:
        return '意大利空军第%s侦察装甲车大队' % m.group(1)
    m = re.match(r'^([IVX]+)\s*(?:°|a|\.a)\s+Gruppo\s+(\w+)$', n)
    if m:
        return '意大利空军第%s%s大队' % (ROMAN.get(m.group(1), m.group(1)),
                                     {'Caccia': '战斗机', 'Bombardamento': '轰炸机'}.get(m.group(2), m.group(2)))
    # --- 罗马尼亚
    m = re.match(r'^(\d+)(?:st|nd|rd|th)\s+HS\s+Rum\.\s+Patrol\s+Sqn$', n)
    if m:
        return '罗马尼亚空军第%s高速巡逻中队' % m.group(1)
    if n == 'Rum. Combat Air Cmd':
        return '罗马尼亚空军作战司令部'
    m = re.match(r'^Rum\.\s+Air\s+Cmd\s+(North|South)$', n)
    if m:
        return '罗马尼亚空军%s司令部' % ('北部' if m.group(1) == 'North' else '南部')
    if n == 'Dobrogea Rum. Air Command':
        return '多布罗加罗马尼亚空军司令部'
    # --- 匈牙利：大队/中队两级（1./101st / 1/101. / 1./III / 1./1st）
    m = re.match(r'^([IVX]+|\d+)\.?\s*/\s*(\d+)(?:st|nd|rd|th)?\.?\s+(.+?)\s+(Group|Grp|Sqn|Regiment)$', n)
    if m:
        a, b, mid, unit = m.groups()
        typ = _hun_type(mid)
        if typ:
            if a.isdigit():
                return '匈牙利空军第%s%s大队第%s中队' % (b, typ, a)
            return '匈牙利空军第%s%s大队第%s中队' % (ROMAN.get(a, a), typ, b)
    m = re.match(r'^(\d+)\.?\s*/\s*([IVX]+)\s+(.+?)\s+(Group|Grp|Sqn|Regiment)$', n)
    if m:
        typ = _hun_type(m.group(3))
        if typ:
            return '匈牙利空军第%s%s大队第%s中队' % (ROMAN.get(m.group(2), m.group(2)), typ, m.group(1))
    m = re.match(r'^(\d+)(?:st|nd|rd|th)\.?\s+(.+?)\s+(Group|Grp|Sqn|Regiment|Grouo)$', n)
    if m:
        typ = _hun_type(m.group(2))
        if typ:
            return '匈牙利空军第%s%s%s' % (m.group(1), typ, HUN_UNIT[m.group(3)])
    return None


def translate_airgroup(name):
    n = _clean(name)
    for fn in (_theater, _german, _soviet, _raf, _usaaf, _nas, _italian,
               _romanian, _hungarian, _finnish, _slovak, _bulgarian, _french,
               _brazil, _wai, _misc, _extra):
        try:
            r = fn(n)
        except Exception:
            r = None
        if r:
            return r
    return None


# ------------------------------------------------------------ 航空作战群（AOGs.csv）
def translate_aog(name):
    n = _clean(name)
    r = _theater(n)
    if r:
        return r
    r = _german(n)
    if r:
        return r
    m = re.match(r'^(\d+)(?:st|nd|rd|th)\s+Air Army\s+(Recon|Transport)\s+Group$', n)
    if m:
        return '第%s航空集团军%s大队' % (m.group(1), '侦察' if m.group(2) == 'Recon' else '运输')
    m = re.match(r'^(\w[\w ]*?)\s+(Air Command|Recon Group|Transport Group|Transport Groiup)$', n)
    if m:
        place = _place_cn(m.group(1))
        if m.group(1) in ('Hungarian', 'Italian', 'Rumanian', 'Finnish',
                          'Slovakian', 'Bulgarian'):
            place += '空军'
        kind = {'Air Command': '空军司令部', 'Recon Group': '侦察大队',
                'Transport Group': '运输大队', 'Transport Groiup': '运输大队'}[m.group(2)]
        return '%s%s' % (place, kind)
    m = re.match(r'^(\w[\w ]*?)\s+PVO\s+(IAD|Corps)$', n)
    if m:
        p = m.group(1)
        p = ('第' + re.sub(r'(st|nd|rd|th)$', '', p)) if p[0].isdigit() else _place_cn(p)
        return '%s防空%s' % (p, '歼击航空师' if m.group(2) == 'IAD' else '军')
    m = re.match(r'^(\d+)\s+PVO\s+(IAD|Corps)$', n)
    if m:
        return '防空第%s%s' % (m.group(1), '歼击航空师' if m.group(2) == 'IAD' else '军')
    m = re.match(r'^(\d+)(?:st|nd|rd|th)?\s+PVO\s+Corps$', n)
    if m:
        return '第%s防空军' % m.group(1)
    m = re.match(r'^(\d+)\s+(GShAK|ShAD|BAD|IABR|IAK|RAG)$', n)
    if m:
        return _sov_num('', m.group(1), m.group(2))
    m = re.match(r'^(\d+)\s+(ShAD|IABR|IAK|BAD)\s*-\s*(ChF|Chf|KBF|SF|PF)$', n)
    if m:
        return '%s第%s%s' % (_suf(m.group(3)), m.group(1), SOV[m.group(2)])
    m = re.match(r'^(\d+)\s+(IAK)\s+PVO\s+Corps$', n)
    if m:
        return '防空第%s歼击航空军' % m.group(1)
    m = re.match(r'^(\d+)\s+IAK\s+PVO\s+Air\s+Comd$', n)
    if m:
        return '防空第%s歼击航空军' % m.group(1)
    m = re.match(r'^Koluft\s+(\d+)(?:\s+(PGr))?$', n)
    if m:
        return '第%s空军联络司令部%s' % (m.group(1), '（集团军群）' if m.group(2) else '')
    m = re.match(r'^Fliegerfuehrer\s+(.+)$', n)
    if m:
        return '第%s航空兵指挥部' % m.group(1) if m.group(1).isdigit() else '%s航空兵指挥部' % m.group(1)
    m = re.match(r'^Jagdfliegerfuehrer\s+(.+)$', n)
    if m:
        return '%s战斗机指挥部' % _place_cn(m.group(1))
    m = re.match(r'^(Lw Kdo)\s+(.+)$', n)
    if m:
        return '%s空军司令部' % _place_cn(m.group(2))
    m = re.match(r'^Transport Gr\.\s+(Mitte|Nord|Sud)$', n)
    if m:
        return '%s运输大队' % {'Mitte': '中部', 'Nord': '北部', 'Sud': '南部'}[m.group(1)]
    m = re.match(r'^(\d+)(?:st|nd|rd|th)\s+(Hun|Rum)\.?\s+(.+)$', n)
    if m:
        force = '匈牙利空军' if m.group(2) == 'Hun' else '罗马尼亚空军'
        table = {'Fighter Regiment': '战斗机团', 'Bomber Regiment': '轰炸机团',
                 'Recon Group': '侦察大队', 'Army Recon Group': '陆军侦察大队',
                 'Bomb Flotilla': '轰炸机支队', 'Fighter Flotilla': '战斗机支队',
                 'Bomb Group': '轰炸机大队', 'Recon Regiment': '侦察团'}
        if m.group(3) in table:
            return '%s第%s%s' % (force, m.group(1), table[m.group(3)])
        return None
    if n == 'Finnish Air Command':
        return '芬兰空军司令部'
    if n == 'Italian Fighter Group':
        return '意大利空军战斗机大队'
    if n == 'Italian Bomber Group':
        return '意大利空军轰炸机大队'
    if n == 'Italian Recon Group':
        return '意大利空军侦察大队'
    if n == 'Hungarian Transport Group':
        return '匈牙利空军运输大队'
    if n == 'Rumanian Transport Group':
        return '罗马尼亚空军运输大队'
    if n == 'Long Range Hun. Recon Group':
        return '匈牙利空军远程侦察大队'
    if n == 'Reserve Hun. Recon Regiment':
        return '匈牙利空军预备侦察团'
    if n == '3 RAG' or n == '4 RAG' or n == '6 RAG':
        return '第%s侦察航空团' % n.split()[0]
    if n == 'CSIR Ital. Air Brigade':
        return '意大利远征军航空旅'
    if n == '2nd RHAF Brigade':
        return '匈牙利皇家空军第2旅'
    if n == 'KG zbV 1 Transport':
        return '第1特种任务轰炸机联队（运输）'
    if n == 'Baltic Fleet Air Command':
        return '波罗的海舰队空军司令部'
    if n == 'Northern Fleet Air Command':
        return '北方舰队空军司令部'
    if n == 'Pacific Fleet Air Command':
        return '太平洋舰队空军司令部'
    r = translate_airgroup(n)
    if r:
        return r
    return None
