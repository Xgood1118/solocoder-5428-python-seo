from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.CONTENT_QUALITY,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class ContentQualityChecks(BaseCheck):
    category = Category.CONTENT_QUALITY

    @staticmethod
    def check_word_count(page, context=None):
        if page.word_count < 300:
            return _r("low_word_count", False, f"页面正文只有 {page.word_count} 字",
                     {"word_count": page.word_count, "min_required": 300})
        return _r("low_word_count", True, f"页面正文 {page.word_count} 字，内容充足",
                 {"word_count": page.word_count})

    @staticmethod
    def check_h1_exists(page, context=None):
        results = []
        if not page.h1_tags:
            results.append(_r("h1_missing", False, "页面缺少 H1 标签"))
            results.append(_r("multiple_h1", True, "无 H1 标签，不涉及多个 H1 问题"))
        elif len(page.h1_tags) > 1:
            results.append(_r("h1_missing", True, "页面有 H1 标签"))
            results.append(_r("multiple_h1", False, f"页面有 {len(page.h1_tags)} 个 H1 标签",
                             {"h1_count": len(page.h1_tags)}))
        else:
            results.append(_r("h1_missing", True, "页面有 H1 标签"))
            results.append(_r("multiple_h1", True, "页面有唯一的 H1 标签"))
        return results

    @staticmethod
    def check_keyword_density(page, context=None):
        if page.word_count < 50 or not page.text_content:
            return _r("keyword_density", True, "内容较少，关键词密度不适用")
        keywords = page.keywords.split(",") if page.keywords else []
        keywords = [k.strip().lower() for k in keywords if k.strip()]
        if not keywords:
            return _r("keyword_density", True, "未设置关键词，无法计算密度")
        text_lower = page.text_content.lower()
        total = sum(text_lower.count(kw) for kw in keywords[:3])
        density = (total / page.word_count) * 100 if page.word_count > 0 else 0
        if density < 2:
            return _r("keyword_density", False, f"主要关键词密度约 {density:.1f}%，偏低",
                     {"density": round(density, 2), "min": 2, "max": 8})
        elif density > 8:
            return _r("keyword_density", False, f"主要关键词密度约 {density:.1f}%，可能有堆砌嫌疑",
                     {"density": round(density, 2), "min": 2, "max": 8})
        return _r("keyword_density", True, f"主要关键词密度约 {density:.1f}%，在合理范围",
                 {"density": round(density, 2), "min": 2, "max": 8})

    @staticmethod
    def check_image_alt(page, context=None):
        total = len(page.images)
        if total == 0:
            return _r("image_alt", True, "页面没有图片",
                     {"total": 0, "missing": 0, "missing_rate": 0})
        missing = sum(1 for img in page.images if not img["has_alt"])
        rate = (missing / total) * 100
        if rate > 30:
            return _r("image_alt", False, f"图片 Alt 缺失率 {rate:.0f}%（{missing}/{total}）",
                     {"total": total, "missing": missing, "missing_rate": round(rate, 1)})
        return _r("image_alt", True, f"图片 Alt 缺失率 {rate:.0f}%（{missing}/{total}）",
                 {"total": total, "missing": missing, "missing_rate": round(rate, 1)})

    @staticmethod
    def check_internal_links(page, context=None):
        n = len(page.internal_links)
        if n == 0:
            return _r("internal_links", False, "页面没有内部链接", {"count": 0})
        return _r("internal_links", True, f"页面有 {n} 个内部链接", {"count": n})

    @staticmethod
    def check_external_links(page, context=None):
        n = len(page.external_links)
        if n == 0:
            return _r("external_links", True, "页面没有外部链接", {"count": 0})
        return _r("external_links", True, f"页面有 {n} 个外部链接", {"count": n})

    @staticmethod
    def check_h2_structure(page, context=None):
        if not page.h2_tags:
            return _r("h2_structure", False, "页面缺少 H2 副标题", {"h2_count": 0})
        return _r("h2_structure", True, f"页面有 {len(page.h2_tags)} 个 H2 副标题",
                 {"h2_count": len(page.h2_tags)})

    @staticmethod
    def check_content_unique(page, context=None):
        dup = context.get("content_duplicate", False)
        return _r(
            "content_unique", not dup,
            "内容为原创" if not dup else "检测到与其他页面内容重复",
        )

    @staticmethod
    def check_paragraph_structure(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("paragraph_structure", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        p_count = len(soup.find_all("p"))
        has_list = bool(soup.find_all(["ul", "ol"]))
        ok = p_count >= 3
        return _r(
            "paragraph_structure", ok,
            f"页面有 {p_count} 个段落，结构{'合理' if ok else '偏少'}",
            {"paragraph_count": p_count, "has_list": has_list},
        )

    @staticmethod
    def check_bold_keywords(page, context=None):
        if not page.keywords or not page.html:
            return _r("bold_keywords", True, "条件不足")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page.html, "html.parser")
        bold_texts = [b.get_text().lower() for b in soup.find_all(["b", "strong"])]
        first_kw = page.keywords.split(",")[0].strip().lower()
        has_kw_bold = any(first_kw in t for t in bold_texts)
        return _r(
            "bold_keywords", has_kw_bold,
            "有关键词加粗强调" if has_kw_bold else "关键词未使用加粗强调",
        )

    @staticmethod
    def check_word_count_500_plus(page, context=None):
        if page.word_count >= 500:
            return _r("word_count_500_plus", True, f"页面正文 {page.word_count} 字，达到 500+ 标准",
                     {"word_count": page.word_count})
        return _r("word_count_500_plus", False, f"页面正文 {page.word_count} 字，未达到 500 字标准",
                 {"word_count": page.word_count, "min_required": 500})

    @staticmethod
    def check_word_count_1000_plus(page, context=None):
        if page.word_count >= 1000:
            return _r("word_count_1000_plus", True, f"页面正文 {page.word_count} 字，达到深度长文标准",
                     {"word_count": page.word_count})
        return _r("word_count_1000_plus", False, f"页面正文 {page.word_count} 字，未达到 1000 字深度标准",
                 {"word_count": page.word_count, "min_required": 1000})

    @staticmethod
    def check_paragraph_length_reasonable(page, context=None):
        import re
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("paragraph_length_reasonable", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        paragraphs = soup.find_all("p")
        if not paragraphs:
            return _r("paragraph_length_reasonable", True, "无段落可检测", {"paragraph_count": 0})
        long_paras = 0
        max_len = 0
        for p in paragraphs:
            text = p.get_text(strip=True)
            wc = len(re.findall(r'\b\w+\b', text))
            if wc > max_len:
                max_len = wc
            if wc > 300:
                long_paras += 1
        ok = long_paras == 0
        return _r(
            "paragraph_length_reasonable", ok,
            f"共有 {len(paragraphs)} 段，超过 300 字的长段落 {long_paras} 个，最长 {max_len} 字",
            {"paragraph_count": len(paragraphs), "long_paragraphs": long_paras, "max_length": max_len, "threshold": 300},
        )

    @staticmethod
    def check_avg_sentence_length(page, context=None):
        import re
        if not page.text_content:
            return _r("avg_sentence_length", True, "无正文内容")
        sentences = re.split(r'[。！？.!?]+', page.text_content)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return _r("avg_sentence_length", True, "无完整句子")
        total_words = 0
        for s in sentences:
            total_words += len(re.findall(r'\b\w+\b', s))
        avg = total_words / len(sentences)
        ok = avg <= 25
        return _r(
            "avg_sentence_length", ok,
            f"平均每句约 {avg:.1f} 字，共 {len(sentences)} 句",
            {"avg_sentence_length": round(avg, 2), "sentence_count": len(sentences), "threshold": 25},
        )

    @staticmethod
    def check_heading_hierarchy_correct(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("heading_hierarchy_correct", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        headings = []
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            level = int(tag.name[1])
            headings.append((tag.name, level))
        if not headings:
            return _r("heading_hierarchy_correct", True, "无标题结构")
        violations = []
        last_level = 0
        for idx, (name, level) in enumerate(headings):
            if last_level > 0 and level > last_level + 1:
                violations.append({"index": idx, "from": f"H{last_level}", "to": name})
            last_level = level
        ok = len(violations) == 0
        return _r(
            "heading_hierarchy_correct", ok,
            f"标题层级{'正确' if ok else f'存在 {len(violations)} 处跳级'}",
            {"heading_count": len(headings), "violations": violations},
        )

    @staticmethod
    def check_h2_has_multiple(page, context=None):
        n = len(page.h2_tags)
        if n >= 2:
            return _r("h2_has_multiple", True, f"页面有 {n} 个 H2 副标题，结构合理",
                     {"h2_count": n})
        return _r("h2_has_multiple", False, f"页面只有 {n} 个 H2 副标题，建议至少 2 个以上",
                 {"h2_count": n, "min_required": 2})

    @staticmethod
    def check_h3_usage_reasonable(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("h3_usage_reasonable", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        h3_tags = soup.find_all("h3")
        h2_tags = soup.find_all("h2")
        if not h3_tags:
            return _r("h3_usage_reasonable", True, "无 H3 标签，无需检查",
                     {"h2_count": len(h2_tags), "h3_count": 0})
        if not h2_tags and h3_tags:
            return _r("h3_usage_reasonable", False, "存在 H3 但没有 H2，层级不合理",
                     {"h2_count": 0, "h3_count": len(h3_tags)})
        content = soup.find("main") or soup.find("article") or soup.body
        if not content:
            content = soup
        ok = True
        details = []
        all_headings = content.find_all(["h2", "h3"])
        for i, tag in enumerate(all_headings):
            if tag.name == "h3":
                has_h2_before = False
                for prev in all_headings[:i]:
                    if prev.name == "h2":
                        has_h2_before = True
                        break
                if not has_h2_before:
                    ok = False
                    details.append("存在 H3 出现在任何 H2 之前")
                    break
        return _r(
            "h3_usage_reasonable", ok,
            f"H3 使用{'合理' if ok else '存在层级问题'}，共 {len(h2_tags)} 个 H2，{len(h3_tags)} 个 H3",
            {"h2_count": len(h2_tags), "h3_count": len(h3_tags), "details": details},
        )

    @staticmethod
    def check_keyword_first_paragraph(page, context=None):
        import re
        from bs4 import BeautifulSoup
        if not page.keywords or not page.html:
            return _r("keyword_first_paragraph", True, "未设置关键词或无 HTML，跳过检查")
        first_kw = page.keywords.split(",")[0].strip().lower()
        if not first_kw:
            return _r("keyword_first_paragraph", True, "无有效关键词")
        soup = BeautifulSoup(page.html, "html.parser")
        paragraphs = soup.find_all("p")
        first_para_text = ""
        if paragraphs:
            first_para_text = paragraphs[0].get_text(strip=True)
        else:
            first_para_text = page.text_content[:200] if page.text_content else ""
        if not first_para_text:
            return _r("keyword_first_paragraph", False, "首段无有效内容", {"keyword": first_kw})
        found = first_kw in first_para_text.lower()
        return _r(
            "keyword_first_paragraph", found,
            f"首段{'已出现' if found else '未出现'}主关键词「{first_kw}」",
            {"keyword": first_kw, "first_paragraph_length": len(first_para_text)},
        )

    @staticmethod
    def check_keyword_in_h2(page, context=None):
        if not page.keywords or not page.h2_tags:
            return _r("keyword_in_h2", True, "未设置关键词或无 H2，跳过检查")
        keywords = [k.strip().lower() for k in page.keywords.split(",") if k.strip()]
        if not keywords:
            return _r("keyword_in_h2", True, "无有效关键词")
        h2_texts = [h.lower() for h in page.h2_tags]
        matched = 0
        matched_h2 = []
        for kw in keywords[:3]:
            for idx, h2 in enumerate(h2_texts):
                if kw in h2 and page.h2_tags[idx] not in matched_h2:
                    matched += 1
                    matched_h2.append(page.h2_tags[idx])
        ok = matched > 0
        return _r(
            "keyword_in_h2", ok,
            f"H2 中{'包含' if ok else '未包含'}关键词，共匹配 {matched} 个 H2",
            {"h2_count": len(page.h2_tags), "matched_h2": matched, "matched_titles": matched_h2},
        )

    @staticmethod
    def check_keyword_density_not_zero(page, context=None):
        if page.word_count < 50 or not page.text_content:
            return _r("keyword_density_not_zero", True, "内容较少，跳过检查")
        keywords = page.keywords.split(",") if page.keywords else []
        keywords = [k.strip().lower() for k in keywords if k.strip()]
        if not keywords:
            return _r("keyword_density_not_zero", True, "未设置关键词，跳过检查")
        text_lower = page.text_content.lower()
        total = sum(text_lower.count(kw) for kw in keywords[:3])
        ok = total > 0
        density = (total / page.word_count) * 100 if page.word_count > 0 else 0
        return _r(
            "keyword_density_not_zero", ok,
            f"关键词在正文出现 {total} 次，密度约 {density:.2f}%" if ok else "主关键词在正文中未出现，密度为 0",
            {"occurrences": total, "density": round(density, 4)},
        )

    @staticmethod
    def check_keyword_stuffing_risk(page, context=None):
        if page.word_count < 50 or not page.text_content:
            return _r("keyword_stuffing_risk", True, "内容较少，跳过检查")
        keywords = page.keywords.split(",") if page.keywords else []
        keywords = [k.strip().lower() for k in keywords if k.strip()]
        if not keywords:
            return _r("keyword_stuffing_risk", True, "未设置关键词，跳过检查")
        text_lower = page.text_content.lower()
        total = sum(text_lower.count(kw) for kw in keywords[:3])
        density = (total / page.word_count) * 100 if page.word_count > 0 else 0
        ok = density <= 10
        return _r(
            "keyword_stuffing_risk", ok,
            f"关键词密度 {density:.2f}%，{'在安全范围' if ok else '超过 10%，疑似堆砌'}",
            {"density": round(density, 2), "threshold": 10, "occurrences": total},
        )

    @staticmethod
    def check_latent_semantic_keywords(page, context=None):
        if not page.keywords or page.word_count < 100:
            return _r("latent_semantic_keywords", True, "未设置关键词或内容不足，跳过检查")
        lsi_keywords = context.get("lsi_keywords", []) if context else []
        text_lower = page.text_content.lower()
        matched = [kw for kw in lsi_keywords if kw.lower() in text_lower]
        has_matched = len(matched) > 0
        return _r(
            "latent_semantic_keywords", has_matched,
            f"检测到 {len(matched)} 个语义相关词" if has_matched else "未检测到语义相关词（LSI），建议补充相关词汇",
            {"matched_count": len(matched), "matched_keywords": matched[:10]},
        )

    @staticmethod
    def check_image_count_reasonable(page, context=None):
        n = len(page.images)
        if page.word_count < 300:
            return _r("image_count_reasonable", True, "内容较短，图片数量不作要求",
                     {"image_count": n, "word_count": page.word_count})
        expected_min = max(1, page.word_count // 500)
        ok = n >= expected_min
        return _r(
            "image_count_reasonable", ok,
            f"页面有 {n} 张图片，{'配图充足' if ok else f'建议至少 {expected_min} 张配图'}",
            {"image_count": n, "word_count": page.word_count, "expected_min": expected_min},
        )

    @staticmethod
    def check_image_dimensions_set(page, context=None):
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        if not page.html:
            return _r("image_dimensions_set", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        imgs = soup.find_all("img")
        if not imgs:
            return _r("image_dimensions_set", True, "页面没有图片",
                     {"total": 0, "missing": 0})
        missing = 0
        for img in imgs:
            has_w = bool(img.get("width") and str(img.get("width")).strip())
            has_h = bool(img.get("height") and str(img.get("height")).strip())
            style = (img.get("style") or "").lower()
            has_w_style = "width:" in style
            has_h_style = "height:" in style
            if not (has_w or has_w_style) or not (has_h or has_h_style):
                missing += 1
        rate = (missing / len(imgs)) * 100
        ok = missing == 0
        return _r(
            "image_dimensions_set", ok,
            f"共 {len(imgs)} 张图片，{missing} 张缺少 width/height 属性（缺失率 {rate:.0f}%）",
            {"total": len(imgs), "missing": missing, "missing_rate": round(rate, 1)},
        )

    @staticmethod
    def check_image_lazy_loaded(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("image_lazy_loaded", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        imgs = soup.find_all("img")
        if len(imgs) < 2:
            return _r("image_lazy_loaded", True, "图片数量较少，懒加载不作要求",
                     {"total": len(imgs), "lazy_loaded": 0})
        lazy_loaded = 0
        for img in imgs:
            loading = (img.get("loading") or "").lower()
            if loading == "lazy":
                lazy_loaded += 1
        rate = (lazy_loaded / len(imgs)) * 100
        ok = rate >= 50
        return _r(
            "image_lazy_loaded", ok,
            f"共 {len(imgs)} 张图片，{lazy_loaded} 张启用懒加载（占比 {rate:.0f}%）",
            {"total": len(imgs), "lazy_loaded": lazy_loaded, "lazy_rate": round(rate, 1)},
        )

    @staticmethod
    def check_image_webp_format(page, context=None):
        if not page.images:
            return _r("image_webp_format", True, "页面没有图片",
                     {"total": 0, "webp_count": 0})
        webp_count = 0
        for img in page.images:
            src = (img.get("src") or "").lower()
            if ".webp" in src:
                webp_count += 1
        rate = (webp_count / len(page.images)) * 100 if page.images else 0
        ok = webp_count > 0
        return _r(
            "image_webp_format", ok,
            f"共 {len(page.images)} 张图片，{webp_count} 张使用 WebP 格式（占比 {rate:.0f}%）",
            {"total": len(page.images), "webp_count": webp_count, "webp_rate": round(rate, 1)},
        )

    @staticmethod
    def check_list_elements_used(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("list_elements_used", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        uls = soup.find_all("ul")
        ols = soup.find_all("ol")
        total = len(uls) + len(ols)
        ok = total > 0
        return _r(
            "list_elements_used", ok,
            f"页面使用了 {total} 个列表（ul: {len(uls)}, ol: {len(ols)}）" if ok else "页面未使用 ul/ol 列表组织内容",
            {"ul_count": len(uls), "ol_count": len(ols), "total": total},
        )

    @staticmethod
    def check_table_elements_used(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("table_elements_used", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        tables = soup.find_all("table")
        ok = len(tables) > 0
        return _r(
            "table_elements_used", ok,
            f"页面使用了 {len(tables)} 个 table 表格" if ok else "页面未使用 table 表格（对比性数据建议使用表格呈现）",
            {"table_count": len(tables)},
        )

    @staticmethod
    def check_blockquote_used(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("blockquote_used", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        quotes = soup.find_all("blockquote")
        q_tags = soup.find_all("q")
        total = len(quotes) + len(q_tags)
        ok = total > 0
        return _r(
            "blockquote_used", ok,
            f"使用了 {total} 处引用标记（blockquote: {len(quotes)}, q: {len(q_tags)}）" if ok else "未使用 blockquote/q 引用标记",
            {"blockquote_count": len(quotes), "q_count": len(q_tags), "total": total},
        )

    @staticmethod
    def check_video_embed_quality(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("video_embed_quality", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        video_tags = soup.find_all("video")
        iframes = soup.find_all("iframe")
        video_iframes = []
        video_platforms = ["youtube.com", "vimeo.com", "bilibili.com", "youku.com", "tudou.com", "qq.com/video", "player.bilibili"]
        for iframe in iframes:
            src = (iframe.get("src") or "").lower()
            for p in video_platforms:
                if p in src:
                    video_iframes.append(src)
                    break
        total = len(video_tags) + len(video_iframes)
        ok = total > 0
        return _r(
            "video_embed_quality", ok,
            f"嵌入了 {total} 个视频内容（video标签: {len(video_tags)}, iframe视频: {len(video_iframes)}）" if ok else "页面未嵌入任何视频内容",
            {"video_tag_count": len(video_tags), "video_iframe_count": len(video_iframes), "total": total},
        )

    @staticmethod
    def check_content_not_duplicate(page, context=None):
        dup_rate = context.get("duplicate_rate", 0) if context else 0
        dup_pages = context.get("duplicate_pages", []) if context else []
        threshold = 0.7
        ok = dup_rate < threshold
        return _r(
            "content_not_duplicate", ok,
            f"与站内页面重复度 {dup_rate*100:.0f}%，{'在可接受范围' if ok else f'高度相似页面 {len(dup_pages)} 个'}" if dup_rate > 0 else "未检测到站内重复内容",
            {"duplicate_rate": round(dup_rate, 4), "threshold": threshold, "duplicate_pages_count": len(dup_pages)},
        )

    @staticmethod
    def check_content_thin_page(page, context=None):
        if page.word_count < 200:
            return _r("content_thin_page", False, f"页面正文仅 {page.word_count} 字，属于薄内容页",
                     {"word_count": page.word_count, "threshold": 200})
        return _r("content_thin_page", True, f"页面正文 {page.word_count} 字，非薄内容页",
                 {"word_count": page.word_count, "threshold": 200})

    @staticmethod
    def check_content_iframe_not_abused(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("content_iframe_not_abused", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        iframes = soup.find_all("iframe")
        ok = len(iframes) <= 3
        return _r(
            "content_iframe_not_abused", ok,
            f"页面使用 {len(iframes)} 个 iframe，{'数量合理' if ok else 'iframe 使用过多，搜索引擎难以抓取'}",
            {"iframe_count": len(iframes), "threshold": 3},
        )

    @staticmethod
    def check_content_noscript_used(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("content_noscript_used", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        scripts = soup.find_all("script")
        noscripts = soup.find_all("noscript")
        if len(scripts) == 0:
            return _r("content_noscript_used", True, "页面不依赖 JavaScript，无需 noscript",
                     {"script_count": 0, "noscript_count": len(noscripts)})
        ok = len(noscripts) > 0
        return _r(
            "content_noscript_used", ok,
            f"有 {len(scripts)} 个 script，{len(noscripts)} 个 noscript 降级标签" if ok else f"页面有 {len(scripts)} 个 JS 脚本，但缺少 noscript 降级内容",
            {"script_count": len(scripts), "noscript_count": len(noscripts)},
        )

    @staticmethod
    def check_anchor_text_variety(page, context=None):
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse, urljoin
        if not page.html:
            return _r("anchor_text_variety", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        base_domain = ""
        if context and context.get("base_domain"):
            base_domain = context["base_domain"].lower()
        elif page.url:
            base_domain = urlparse(page.url).netloc.lower()
        anchor_texts = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            full_url = urljoin(page.url, href)
            parsed = urlparse(full_url)
            if not parsed.netloc:
                continue
            if base_domain and parsed.netloc.lower() == base_domain:
                text = a.get_text(strip=True)
                if text:
                    anchor_texts.append(text.lower())
        if len(anchor_texts) < 2:
            return _r("anchor_text_variety", True, "内链数量较少，锚文本多样化不作要求",
                     {"internal_link_count": len(anchor_texts)})
        unique_texts = len(set(anchor_texts))
        rate = unique_texts / len(anchor_texts)
        ok = rate >= 0.5
        return _r(
            "anchor_text_variety", ok,
            f"内链锚文本共 {len(anchor_texts)} 个，唯一值 {unique_texts} 个，多样化率 {rate*100:.0f}%",
            {"total": len(anchor_texts), "unique": unique_texts, "diversity_rate": round(rate, 2), "threshold": 0.5},
        )

    @staticmethod
    def check_external_links_authoritative(page, context=None):
        from urllib.parse import urlparse
        if not page.external_links:
            return _r("external_links_authoritative", True, "无外部链接，跳过检查",
                     {"external_count": 0})
        authoritative_tlds = [".gov", ".edu", ".org", ".ac.uk", ".gov.cn", ".edu.cn"]
        authoritative_domains = ["wikipedia.org", "baike.baidu.com", "zhihu.com", "github.com",
                                 "stackoverflow.com", "developer.mozilla.org", "google.com",
                                 "microsoft.com", "apple.com", "amazon.com", "researchgate.net",
                                 "pubmed.ncbi.nlm.nih.gov", "nature.com", "science.org"]
        authoritative_count = 0
        authoritative_urls = []
        for url in page.external_links:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            matched = False
            for tld in authoritative_tlds:
                if netloc.endswith(tld):
                    matched = True
                    break
            if not matched:
                for ad in authoritative_domains:
                    if netloc == ad or netloc.endswith("." + ad):
                        matched = True
                        break
            if matched:
                authoritative_count += 1
                authoritative_urls.append(url)
        rate = (authoritative_count / len(page.external_links)) * 100
        ok = authoritative_count > 0
        return _r(
            "external_links_authoritative", ok,
            f"外链共 {len(page.external_links)} 个，权威链接 {authoritative_count} 个（占比 {rate:.0f}%）" if page.external_links else "无外部链接",
            {"total": len(page.external_links), "authoritative_count": authoritative_count,
             "authoritative_rate": round(rate, 1), "authoritative_urls": authoritative_urls[:10]},
        )

    @staticmethod
    def check_broken_external_links(page, context=None):
        broken = context.get("broken_external_links", []) if context else []
        ok = len(broken) == 0
        return _r(
            "broken_external_links", ok,
            "未检测到失效外链" if ok else f"检测到 {len(broken)} 个失效外链（4xx/5xx）",
            {"broken_count": len(broken), "broken_links": broken[:10]},
        )

    @staticmethod
    def check_external_links_nofollow(page, context=None):
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse, urljoin
        if not page.html:
            return _r("external_links_nofollow", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        base_domain = ""
        if context and context.get("base_domain"):
            base_domain = context["base_domain"].lower()
        elif page.url:
            base_domain = urlparse(page.url).netloc.lower()
        external_count = 0
        nofollow_count = 0
        paid_patterns = ["广告", "推广", "赞助", "ad", "advertise", "sponsor", "partner", "affiliate"]
        suspected_paid = 0
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            full_url = urljoin(page.url, href)
            parsed = urlparse(full_url)
            if not parsed.netloc:
                continue
            if base_domain and parsed.netloc.lower() == base_domain:
                continue
            external_count += 1
            rel = " ".join(a.get("rel", [])).lower()
            has_nofollow = "nofollow" in rel or "sponsored" in rel or "ugc" in rel
            if has_nofollow:
                nofollow_count += 1
            link_text = a.get_text(strip=True).lower()
            is_suspected = any(p in link_text for p in paid_patterns)
            if is_suspected and not has_nofollow:
                suspected_paid += 1
        if external_count == 0:
            return _r("external_links_nofollow", True, "无外部链接",
                     {"external_count": 0})
        ok = suspected_paid == 0
        return _r(
            "external_links_nofollow", ok,
            f"外链共 {external_count} 个，加 nofollow/sponsored 有 {nofollow_count} 个，疑似付费但未加标记 {suspected_paid} 个",
            {"external_count": external_count, "nofollow_count": nofollow_count,
             "suspected_paid_without_nofollow": suspected_paid},
        )

    @staticmethod
    def check_content_no_flash(page, context=None):
        from bs4 import BeautifulSoup
        if not page.html:
            return _r("content_no_flash", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        flash_indicators = []
        objects = soup.find_all("object")
        for obj in objects:
            data = (obj.get("data") or "").lower()
            clsid = (obj.get("classid") or "").lower()
            type_ = (obj.get("type") or "").lower()
            if ".swf" in data or "shockwave" in clsid or "flash" in type_:
                flash_indicators.append(("object", data or clsid or type_))
        embeds = soup.find_all("embed")
        for emb in embeds:
            src = (emb.get("src") or "").lower()
            type_ = (emb.get("type") or "").lower()
            if ".swf" in src or "flash" in type_ or "shockwave" in type_:
                flash_indicators.append(("embed", src or type_))
        html_lower = page.html.lower()
        if "swfobject" in html_lower:
            flash_indicators.append(("script", "swfobject detected"))
        ok = len(flash_indicators) == 0
        return _r(
            "content_no_flash", ok,
            "未检测到 Flash 内容" if ok else f"检测到 {len(flash_indicators)} 处 Flash 相关内容",
            {"flash_indicators_count": len(flash_indicators), "flash_details": flash_indicators[:10]},
        )

    @staticmethod
    def check_internal_link_diversity(page, context=None):
        from urllib.parse import urlparse
        if not page.internal_links:
            return _r("internal_link_diversity", True, "无内部链接，跳过检查",
                     {"internal_count": 0, "unique_paths": 0})
        paths = set()
        for url in page.internal_links:
            parsed = urlparse(url)
            path = parsed.path.rstrip("/") or "/"
            paths.add(path)
        unique_count = len(paths)
        total = len(page.internal_links)
        ok = unique_count >= 2
        return _r(
            "internal_link_diversity", ok,
            f"内链共 {total} 个，指向 {unique_count} 个不同页面，{'分布较广' if ok else '指向页面过于集中'}",
            {"internal_count": total, "unique_paths": unique_count, "sample_paths": list(paths)[:10]},
        )

    @staticmethod
    def check_flesch_readable(page, context=None):
        import re
        if not page.text_content or page.word_count < 30:
            return _r("flesch_readable", True, "内容过少，可读性分析不适用")
        text = page.text_content
        sentences = re.split(r'[。！？.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        sentence_count = len(sentences) if sentences else 1
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words) if words else 1
        syllable_count = 0
        for word in words:
            w = word.lower()
            vowels = "aeiouāáǎàōóǒòēéěèīíǐìūúǔùü"
            count = 0
            prev_vowel = False
            for ch in w:
                is_vowel = ch in vowels
                if is_vowel and not prev_vowel:
                    count += 1
                prev_vowel = is_vowel
            if w.endswith("e") and count > 1:
                count -= 1
            syllable_count += max(1, count)
        if word_count == 0 or sentence_count == 0:
            return _r("flesch_readable", True, "无法计算可读性")
        avg_sentence_len = word_count / sentence_count
        avg_syllables = syllable_count / word_count if word_count > 0 else 1
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        if has_chinese:
            score = 100 - avg_sentence_len * 2
        else:
            score = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables)
        score = max(0, min(100, score))
        ok = score >= 60
        return _r(
            "flesch_readable", ok,
            f"可读性得分 {score:.1f}（{'较易阅读' if score >= 60 else '阅读难度较高'}），平均句长 {avg_sentence_len:.1f} 字",
            {"score": round(score, 2), "avg_sentence_length": round(avg_sentence_len, 2),
             "avg_syllables_per_word": round(avg_syllables, 2), "threshold": 60},
        )

    @staticmethod
    def check_content_has_summary(page, context=None):
        import re
        from bs4 import BeautifulSoup
        if page.word_count < 500:
            return _r("content_has_summary", True, "文章较短，总结段不作要求",
                     {"word_count": page.word_count, "threshold": 500})
        if not page.html:
            return _r("content_has_summary", True, "无 HTML 内容")
        soup = BeautifulSoup(page.html, "html.parser")
        content = soup.find("main") or soup.find("article") or soup.body
        if not content:
            content = soup
        paragraphs = content.find_all("p")
        if len(paragraphs) < 2:
            return _r("content_has_summary", False, "段落过少，无明显总结段结构",
                     {"paragraph_count": len(paragraphs)})
        last_paras = paragraphs[-min(2, len(paragraphs)):]
        summary_keywords = ["总之", "总而言之", "综上所述", "总的来说", "归纳起来", "总结一下",
                           "最后", "结论", "in conclusion", "to summarize", "to sum up",
                           "in summary", "overall"]
        has_summary = False
        last_para_texts = []
        for p in last_paras:
            text = p.get_text(strip=True)
            last_para_texts.append(text)
            text_lower = text.lower()
            wc = len(re.findall(r'\b\w+\b', text))
            for kw in summary_keywords:
                if kw.lower() in text_lower:
                    has_summary = True
                    break
            if wc >= 30 and len(paragraphs) >= 4 and not has_summary:
                h2_after = content.find_all("h2")
                for h2 in h2_after:
                    h2_text = h2.get_text(strip=True).lower()
                    if any(k in h2_text for k in ["总结", "结论", "summary", "conclusion"]):
                        has_summary = True
                        break
        return _r(
            "content_has_summary", has_summary,
            f"{'检测到' if has_summary else '未检测到'}文章结论/总结段，共 {len(paragraphs)} 段",
            {"paragraph_count": len(paragraphs), "last_paragraphs_preview": last_para_texts},
        )
