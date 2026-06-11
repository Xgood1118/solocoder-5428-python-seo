from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.TDK,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class TDKChecks(BaseCheck):
    category = Category.TDK

    @staticmethod
    def check_title_exists(page, context=None):
        results = []
        has_dup = context.get("title_duplicate", False) if context else False
        if not page.title:
            results.append(_r("title_missing", False, "页面缺少 title 标签"))
            results.append(_r("title_duplicate", True, "无 title 标签，不涉及重复问题"))
        else:
            results.append(_r("title_missing", True, "页面有 title 标签"))
            if has_dup:
                results.append(_r("title_duplicate", False, "有其他页面使用了相同的 title"))
            else:
                results.append(_r("title_duplicate", True, "Title 唯一，无重复"))
        return results

    @staticmethod
    def check_title_length(page, context=None):
        if not page.title:
            return _r("title_length", False, "无 title 标签，无法检查长度")
        length = len(page.title)
        if length < 30:
            return _r("title_length", False, f"Title 只有 {length} 字符，偏短",
                     {"length": length, "min": 30, "max": 60})
        elif length > 60:
            return _r("title_length", False, f"Title 有 {length} 字符，超长可能被截断",
                     {"length": length, "min": 30, "max": 60})
        return _r("title_length", True, f"Title 长度 {length} 字符，符合要求",
                 {"length": length, "min": 30, "max": 60})

    @staticmethod
    def check_description_exists(page, context=None):
        results = []
        has_dup = context.get("description_duplicate", False) if context else False
        if not page.description:
            results.append(_r("description_missing", False, "页面缺少 meta description"))
            results.append(_r("description_duplicate", True, "无 description，不涉及重复问题"))
        else:
            results.append(_r("description_missing", True, "页面有 meta description"))
            if has_dup:
                results.append(_r("description_duplicate", False, "有其他页面使用了相同的 description"))
            else:
                results.append(_r("description_duplicate", True, "Description 唯一，无重复"))
        return results

    @staticmethod
    def check_description_length(page, context=None):
        if not page.description:
            return _r("description_length", False, "无 description，无法检查长度")
        length = len(page.description)
        if length < 70:
            return _r("description_length", False, f"Description 只有 {length} 字符，偏短",
                     {"length": length, "min": 70, "max": 160})
        elif length > 160:
            return _r("description_length", False, f"Description 有 {length} 字符，超长可能被截断",
                     {"length": length, "min": 70, "max": 160})
        return _r("description_length", True, f"Description 长度 {length} 字符，符合要求",
                 {"length": length, "min": 70, "max": 160})

    @staticmethod
    def check_keywords_exists(page, context=None):
        results = []
        has_dup = context.get("keywords_duplicate", False) if context else False
        if not page.keywords:
            results.append(_r("keywords_missing", False, "页面缺少 meta keywords"))
            results.append(_r("keywords_duplicate", True, "无 keywords，不涉及重复问题"))
        else:
            results.append(_r("keywords_missing", True, "页面有 meta keywords"))
            if has_dup:
                results.append(_r("keywords_duplicate", False, "有其他页面使用了相同的 keywords"))
            else:
                results.append(_r("keywords_duplicate", True, "Keywords 唯一，无重复"))
        return results

    @staticmethod
    def check_title_brand(page, context=None):
        if not page.title:
            return _r("title_brand", True, "无 title 标签")
        has_separator = any(s in page.title for s in [" - ", " | ", " _ "])
        return _r(
            "title_brand", has_separator,
            "Title 包含品牌分隔符" if has_separator else "Title 未包含品牌/站点名分隔符",
        )

    @staticmethod
    def check_title_keyword_first(page, context=None):
        if not page.title or not page.keywords:
            return _r("title_keyword_first", True, "条件不足")
        first_kw = page.keywords.split(",")[0].strip().lower()
        title_lower = page.title.lower()
        idx = title_lower.find(first_kw)
        first_half = idx >= 0 and idx < len(page.title) / 2
        return _r(
            "title_keyword_first", first_half,
            "主关键词出现在 title 前半部分" if first_half else "主关键词未出现在 title 前半部分",
        )

    @staticmethod
    def check_title_has_keyword(page, context=None):
        if not page.title:
            return _r("title_has_keyword", False, "无 title 标签，无法检查关键词")
        if not page.keywords:
            return _r("title_has_keyword", True, "未设置 keywords，无法对比")
        keywords_list = [kw.strip().lower() for kw in page.keywords.split(",") if kw.strip()]
        title_lower = page.title.lower()
        has_keyword = any(kw in title_lower for kw in keywords_list)
        matched = [kw for kw in keywords_list if kw in title_lower]
        return _r(
            "title_has_keyword", has_keyword,
            f"Title 包含主关键词: {', '.join(matched)}" if has_keyword else "Title 未包含设置的主关键词",
            {"matched_keywords": matched, "total_keywords": len(keywords_list)},
        )

    @staticmethod
    def check_title_has_brand(page, context=None):
        if not page.title:
            return _r("title_has_brand", True, "无 title 标签")
        brand_positions = []
        for sep in [" - ", " | ", " _ "]:
            idx = page.title.rfind(sep)
            if idx != -1:
                brand_part = page.title[idx + len(sep):].strip()
                if brand_part:
                    brand_positions.append(idx)
        has_brand_end = len(brand_positions) > 0
        return _r(
            "title_has_brand", has_brand_end,
            "Title 末尾包含品牌词" if has_brand_end else "Title 末尾未发现品牌/站点名",
            {"brand_separator_found": has_brand_end},
        )

    @staticmethod
    def check_title_no_stopwords(page, context=None):
        if not page.title:
            return _r("title_no_stopwords", True, "无 title 标签")
        stopwords = ["首页", "欢迎", "主页", "官网", "官方网站", "首页-", "首页_", "欢迎您"]
        found_stopwords = [sw for sw in stopwords if sw in page.title]
        no_stopwords = len(found_stopwords) == 0
        return _r(
            "title_no_stopwords", no_stopwords,
            "Title 未发现冗余停用词" if no_stopwords else f"Title 包含冗余停用词: {', '.join(found_stopwords)}",
            {"found_stopwords": found_stopwords},
        )

    @staticmethod
    def check_title_no_special_chars(page, context=None):
        if not page.title:
            return _r("title_no_special_chars", True, "无 title 标签")
        control_chars = []
        for char in page.title:
            code = ord(char)
            if (code < 32 and code not in (9, 10, 13)) or code == 127 or (0x80 <= code <= 0x9F):
                control_chars.append(f"U+{code:04X}")
        no_special = len(control_chars) == 0
        return _r(
            "title_no_special_chars", no_special,
            "Title 无特殊控制字符" if no_special else f"Title 含有特殊控制字符: {', '.join(control_chars)}",
            {"special_chars": control_chars, "count": len(control_chars)},
        )

    @staticmethod
    def check_title_unique_sitewide(page, context=None):
        if not page.title:
            return _r("title_unique_sitewide", True, "无 title 标签，不涉及全站重复")
        is_dup = context.get("title_unique_sitewide", False) if context else False
        return _r(
            "title_unique_sitewide", not is_dup,
            "全站 Title 唯一" if not is_dup else "发现其他页面使用了相同的 Title",
            {"is_duplicate": is_dup},
        )

    @staticmethod
    def check_description_has_keyword(page, context=None):
        if not page.description:
            return _r("description_has_keyword", False, "无 description，无法检查关键词")
        if not page.keywords:
            return _r("description_has_keyword", True, "未设置 keywords，无法对比")
        keywords_list = [kw.strip().lower() for kw in page.keywords.split(",") if kw.strip()]
        desc_lower = page.description.lower()
        has_keyword = any(kw in desc_lower for kw in keywords_list)
        matched = [kw for kw in keywords_list if kw in desc_lower]
        return _r(
            "description_has_keyword", has_keyword,
            f"Description 包含主关键词: {', '.join(matched)}" if has_keyword else "Description 未包含设置的主关键词",
            {"matched_keywords": matched, "total_keywords": len(keywords_list)},
        )

    @staticmethod
    def check_description_has_cta(page, context=None):
        if not page.description:
            return _r("description_has_cta", True, "无 description")
        cta_words = [
            "立即查看", "免费试用", "点击了解", "立即购买", "马上咨询",
            "快来看看", "立即体验", "免费咨询", "立即注册", "点击进入",
            "了解更多", "详情点击", "立即下单", "免费获取", "欢迎咨询",
            "查看详情", "立即申请", "在线咨询", "立即领取", "抢先体验",
        ]
        desc_lower = page.description.lower()
        found_cta = [cta for cta in cta_words if cta in page.description]
        has_cta = len(found_cta) > 0
        return _r(
            "description_has_cta", has_cta,
            f"Description 包含 CTA 用语: {', '.join(found_cta)}" if has_cta else "Description 未发现号召性用语 CTA",
            {"found_cta": found_cta},
        )

    @staticmethod
    def check_description_no_duplicate(page, context=None):
        if not page.description:
            return _r("description_no_duplicate", True, "无 description，不涉及全站重复")
        is_dup = context.get("description_no_duplicate", False) if context else False
        return _r(
            "description_no_duplicate", not is_dup,
            "全站 Description 唯一" if not is_dup else "发现其他页面使用了相同的 Description",
            {"is_duplicate": is_dup},
        )

    @staticmethod
    def check_description_no_punctuation_abuse(page, context=None):
        if not page.description:
            return _r("description_no_punctuation_abuse", True, "无 description")
        abuse_chars = ["★", "☆", "【", "】", "〖", "〗", "■", "□", "●", "○", "◆", "◇", "▲", "△",
                       "※", "♦", "♠", "♣", "♥", "✿", "❀", "✓", "✔", "✗", "✘", "×", "★", "☆"]
        found_abuse = [c for c in abuse_chars if c in page.description]
        no_abuse = len(found_abuse) == 0
        return _r(
            "description_no_punctuation_abuse", no_abuse,
            "Description 未滥用标点符号" if no_abuse else f"Description 含装饰符号: {', '.join(found_abuse)}",
            {"found_abuse_chars": found_abuse, "count": len(found_abuse)},
        )

    @staticmethod
    def check_keywords_not_stuffed(page, context=None):
        if not page.keywords:
            return _r("keywords_not_stuffed", True, "无 keywords，不涉及堆砌")
        keywords_list = [kw.strip().lower() for kw in page.keywords.split(",") if kw.strip()]
        seen = set()
        duplicates = []
        for kw in keywords_list:
            if kw in seen:
                duplicates.append(kw)
            seen.add(kw)
        kw_count = len(keywords_list)
        is_stuffed = kw_count > 10 or len(duplicates) > 0
        details = {
            "total_count": kw_count,
            "duplicate_keywords": duplicates,
            "duplicate_count": len(duplicates),
        }
        return _r(
            "keywords_not_stuffed", not is_stuffed,
            "Keywords 未堆砌" if not is_stuffed else f"Keywords 存在堆砌问题: 数量{kw_count}个, 重复词{len(duplicates)}个",
            details,
        )

    @staticmethod
    def check_keywords_count_reasonable(page, context=None):
        if not page.keywords:
            return _r("keywords_count_reasonable", True, "无 keywords，跳过数量检查")
        keywords_list = [kw.strip() for kw in page.keywords.split(",") if kw.strip()]
        kw_count = len(keywords_list)
        reasonable = 3 <= kw_count <= 5
        return _r(
            "keywords_count_reasonable", reasonable,
            f"Keywords 数量 {kw_count} 个，符合建议" if reasonable else f"Keywords 数量 {kw_count} 个，建议 3-5 个",
            {"count": kw_count, "min": 3, "max": 5},
        )

    @staticmethod
    def check_keywords_comma_format(page, context=None):
        if not page.keywords:
            return _r("keywords_comma_format", True, "无 keywords，跳过格式检查")
        has_chinese_comma = "，" in page.keywords
        has_chinese_dun = "、" in page.keywords
        has_space = any(kw.strip() and " " in kw.strip() for kw in page.keywords.split(","))
        format_ok = not has_chinese_comma and not has_chinese_dun
        issues = []
        if has_chinese_comma:
            issues.append("使用了中文逗号")
        if has_chinese_dun:
            issues.append("使用了顿号")
        return _r(
            "keywords_comma_format", format_ok,
            "Keywords 格式正确" if format_ok else f"Keywords 格式问题: {'; '.join(issues)}",
            {"has_chinese_comma": has_chinese_comma, "has_chinese_dun": has_chinese_dun},
        )

    @staticmethod
    def check_h1_title_consistent(page, context=None):
        if not page.title:
            return _r("h1_title_consistent", True, "无 title 标签，跳过一致性检查")
        if not page.h1_tags:
            return _r("h1_title_consistent", True, "无 H1 标签，跳过一致性检查")
        h1_text = " ".join(page.h1_tags).lower()
        title_lower = page.title.lower()
        if page.keywords:
            keywords_list = [kw.strip().lower() for kw in page.keywords.split(",") if kw.strip()]
            title_kws = [kw for kw in keywords_list if kw in title_lower]
            h1_kws = [kw for kw in keywords_list if kw in h1_text]
            consistent = len(title_kws) > 0 and len(h1_kws) > 0 and len(set(title_kws) & set(h1_kws)) > 0
            shared_kws = list(set(title_kws) & set(h1_kws))
            return _r(
                "h1_title_consistent", consistent,
                f"H1 与 Title 主题一致，共享关键词: {', '.join(shared_kws)}" if consistent else "H1 与 Title 主题关键词未重叠",
                {"shared_keywords": shared_kws, "title_keywords": title_kws, "h1_keywords": h1_kws},
            )
        title_words = set(title_lower.split())
        h1_words = set(h1_text.split())
        overlap = title_words & h1_words
        consistent = len(overlap) > 0
        return _r(
            "h1_title_consistent", consistent,
            f"H1 与 Title 主题一致，共享词汇: {len(overlap)} 个" if consistent else "H1 与 Title 无共享词汇",
            {"overlap_word_count": len(overlap), "overlap_words": list(overlap)[:10]},
        )

    @staticmethod
    def check_h1_title_not_identical(page, context=None):
        if not page.title or not page.h1_tags:
            return _r("h1_title_not_identical", True, "缺少 title 或 H1，跳过检查")
        h1_first = page.h1_tags[0].strip()
        not_identical = h1_first.strip().lower() != page.title.strip().lower()
        return _r(
            "h1_title_not_identical", not_identical,
            "H1 与 Title 文案有区分" if not_identical else "H1 与 Title 完全相同，建议文案差异化",
            {"h1_text": h1_first, "title_text": page.title},
        )

    @staticmethod
    def check_og_title_complete(page, context=None):
        og_title = page.og_tags.get("og:title", "") if page.og_tags else ""
        has_og_title = bool(og_title.strip())
        return _r(
            "og_title_complete", has_og_title,
            "已设置 og:title" if has_og_title else "未设置 og:title 标签",
            {"og_title": og_title if has_og_title else ""},
        )

    @staticmethod
    def check_og_description_complete(page, context=None):
        og_desc = page.og_tags.get("og:description", "") if page.og_tags else ""
        has_og_desc = bool(og_desc.strip())
        return _r(
            "og_description_complete", has_og_desc,
            "已设置 og:description" if has_og_desc else "未设置 og:description 标签",
            {"og_description": og_desc if has_og_desc else ""},
        )

    @staticmethod
    def check_twitter_title_complete(page, context=None):
        tw_title = page.twitter_tags.get("twitter:title", "") if page.twitter_tags else ""
        has_tw_title = bool(tw_title.strip())
        return _r(
            "twitter_title_complete", has_tw_title,
            "已设置 twitter:title" if has_tw_title else "未设置 twitter:title 标签",
            {"twitter_title": tw_title if has_tw_title else ""},
        )

    @staticmethod
    def check_twitter_description_complete(page, context=None):
        tw_desc = page.twitter_tags.get("twitter:description", "") if page.twitter_tags else ""
        has_tw_desc = bool(tw_desc.strip())
        return _r(
            "twitter_description_complete", has_tw_desc,
            "已设置 twitter:description" if has_tw_desc else "未设置 twitter:description 标签",
            {"twitter_description": tw_desc if has_tw_desc else ""},
        )

    @staticmethod
    def check_canonical_title_match(page, context=None):
        if not page.canonical:
            return _r("canonical_title_match", True, "未设置 canonical，跳过匹配检查")
        if not page.title:
            return _r("canonical_title_match", True, "无 title，跳过匹配检查")
        canonical_titles = context.get("canonical_titles", {}) if context else {}
        canonical_title = canonical_titles.get(page.canonical, "")
        if not canonical_title:
            return _r(
                "canonical_title_match", True,
                "无法获取 canonical 目标页 title，跳过检查",
                {"canonical": page.canonical},
            )
        match = canonical_title.strip().lower() == page.title.strip().lower()
        return _r(
            "canonical_title_match", match,
            "Canonical 目标页 Title 与当前页一致" if match else "Canonical 目标页 Title 与当前页不一致",
            {"canonical": page.canonical, "canonical_title": canonical_title, "current_title": page.title},
        )

    @staticmethod
    def check_meta_robots_noindex(page, context=None):
        if not page.meta_robots:
            return _r("meta_robots_noindex", True, "未设置 meta robots，默认允许索引")
        robots_lower = page.meta_robots.lower()
        has_noindex = "noindex" in robots_lower
        return _r(
            "meta_robots_noindex", not has_noindex,
            "meta robots 未设置 noindex，允许索引" if not has_noindex else "meta robots 设置了 noindex，将阻止搜索引擎索引",
            {"meta_robots": page.meta_robots, "has_noindex": has_noindex},
        )

    @staticmethod
    def check_meta_robots_nosnippet(page, context=None):
        if not page.meta_robots:
            return _r("meta_robots_nosnippet", True, "未设置 meta robots，默认生成摘要")
        robots_lower = page.meta_robots.lower()
        has_nosnippet = "nosnippet" in robots_lower
        return _r(
            "meta_robots_nosnippet", not has_nosnippet,
            "meta robots 未设置 nosnippet，允许生成摘要" if not has_nosnippet else "meta robots 设置了 nosnippet，阻止搜索引擎生成摘要",
            {"meta_robots": page.meta_robots, "has_nosnippet": has_nosnippet},
        )

    @staticmethod
    def check_meta_robots_noarchive(page, context=None):
        if not page.meta_robots:
            return _r("meta_robots_noarchive", True, "未设置 meta robots，默认允许存档")
        robots_lower = page.meta_robots.lower()
        has_noarchive = "noarchive" in robots_lower
        return _r(
            "meta_robots_noarchive", not has_noarchive,
            "meta robots 未设置 noarchive，允许网页存档" if not has_noarchive else "meta robots 设置了 noarchive，阻止搜索引擎存档",
            {"meta_robots": page.meta_robots, "has_noarchive": has_noarchive},
        )
