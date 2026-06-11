from .base import BaseCheck
from ..models import RuleResult, Severity, Weight, Category


def _r(rule_id, passed, message, details=None):
    return RuleResult(
        rule_id=rule_id, rule_name="",
        category=Category.STRUCTURED_DATA,
        severity=Severity.INFO, weight=Weight.LOW,
        passed=passed, message=message, fix_advice="",
        details=details or {},
    )


class StructuredDataChecks(BaseCheck):
    category = Category.STRUCTURED_DATA

    @staticmethod
    def check_json_ld(page, context=None):
        if not page.json_ld:
            return _r("json_ld_present", False, "页面没有 JSON-LD 结构化数据")
        types = []
        for item in page.json_ld:
            if isinstance(item, dict) and item.get("@type"):
                types.append(item["@type"])
        return _r("json_ld_present", True, f"页面有 {len(page.json_ld)} 个结构化数据块",
                 {"schema_types": types, "count": len(page.json_ld)})

    @staticmethod
    def check_schema_valid(page, context=None):
        if not page.json_ld:
            return _r("schema_valid", True, "无结构化数据，不适用")
        valid = 0
        invalid = 0
        for item in page.json_ld:
            if isinstance(item, dict) and "@type" in item:
                valid += 1
            else:
                invalid += 1
        if invalid > 0:
            return _r("schema_valid", False, f"有 {invalid} 个结构化数据块结构不完整",
                     {"valid": valid, "invalid": invalid})
        return _r("schema_valid", True, f"所有 {valid} 个结构化数据块结构完整",
                 {"valid": valid, "invalid": 0})

    @staticmethod
    def check_og_tags(page, context=None):
        required = ["og:title", "og:description", "og:image", "og:url"]
        missing = [t for t in required if t not in page.og_tags]
        if missing:
            return _r("og_tags", False, f"缺少 {len(missing)} 个必要 OG 标签：{', '.join(missing)}",
                     {"missing": missing, "present": list(page.og_tags.keys())})
        return _r("og_tags", True, "必要的 Open Graph 标签齐全",
                 {"present": list(page.og_tags.keys())})

    @staticmethod
    def check_twitter_card(page, context=None):
        if not page.twitter_tags:
            return _r("twitter_card", False, "页面没有 Twitter Card 标签")
        has_type = "twitter:card" in page.twitter_tags
        if not has_type:
            return _r("twitter_card", False, "缺少 twitter:card 类型定义")
        return _r("twitter_card", True, "Twitter Card 标签已配置",
                 {"present": list(page.twitter_tags.keys())})

    @staticmethod
    def check_breadcrumb_schema(page, context=None):
        has_schema = False
        for item in page.json_ld:
            if isinstance(item, dict) and item.get("@type") == "BreadcrumbList":
                has_schema = True
                break
        if page.has_breadcrumb and not has_schema:
            return _r("breadcrumb_schema", False, "有面包屑导航但缺少 Schema 标记")
        if has_schema:
            return _r("breadcrumb_schema", True, "面包屑导航已添加 Schema 标记")
        return _r("breadcrumb_schema", True, "无面包屑导航，不适用")

    @staticmethod
    def check_article_schema(page, context=None):
        has_article = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and "article" in t.lower():
                    has_article = True
                    break
        if page.word_count > 500 and not has_article:
            return _r("article_schema", False, "长内容页面建议添加 Article Schema")
        return _r("article_schema", True, "检测通过")

    @staticmethod
    def check_org_schema(page, context=None):
        has_org = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and ("organization" in t.lower() or "website" in t.lower()):
                    has_org = True
                    break
        return _r(
            "org_schema", has_org,
            "有站点级结构化数据" if has_org else "建议添加 Organization 或 Website 结构化数据",
        )

    @staticmethod
    def check_faq_schema(page, context=None):
        has_faq = False
        for item in page.json_ld:
            if isinstance(item, dict) and item.get("@type") == "FAQPage":
                has_faq = True
                break
        return _r(
            "faq_schema", has_faq,
            "有 FAQ 结构化数据" if has_faq else "如适用可添加 FAQ 结构化数据以获得富结果展示",
        )

    @staticmethod
    def check_rich_results_eligibility(page, context=None):
        types = []
        for item in page.json_ld:
            if isinstance(item, dict) and item.get("@type"):
                types.append(item["@type"])
        eligible = len(types) > 0
        return _r(
            "rich_results_eligibility", eligible,
            f"有 {len(types)} 种 Schema 类型可能支持富结果" if eligible else "无结构化数据，无法获得富结果展示",
            {"schema_types": types},
        )

    @staticmethod
    def check_jsonld_single_type_consistent(page, context=None):
        if not page.json_ld:
            return _r("jsonld_single_type_consistent", True, "无 JSON-LD，不适用")
        valid = 0
        invalid = 0
        invalid_details = []
        for idx, item in enumerate(page.json_ld):
            if isinstance(item, dict) and item.get("@type"):
                valid += 1
            else:
                invalid += 1
                invalid_details.append({"index": idx, "reason": "缺少 @type 或类型非法"})
        if invalid > 0:
            return _r(
                "jsonld_single_type_consistent", False,
                f"有 {invalid} 个 JSON-LD 块缺少合法的 @type 字段",
                {"valid": valid, "invalid": invalid, "details": invalid_details},
            )
        return _r(
            "jsonld_single_type_consistent", True,
            f"所有 {valid} 个 JSON-LD 块均包含合法的 @type 字段",
            {"valid": valid, "invalid": 0},
        )

    @staticmethod
    def check_jsonld_context_correct(page, context=None):
        if not page.json_ld:
            return _r("jsonld_context_correct", True, "无 JSON-LD，不适用")
        valid = 0
        invalid = 0
        invalid_details = []
        valid_contexts = {"https://schema.org", "http://schema.org", "https://schema.org/", "http://schema.org/"}
        for idx, item in enumerate(page.json_ld):
            if isinstance(item, dict):
                ctx = item.get("@context", "")
                if isinstance(ctx, str) and ctx in valid_contexts:
                    valid += 1
                else:
                    invalid += 1
                    invalid_details.append({"index": idx, "context": ctx})
            else:
                invalid += 1
                invalid_details.append({"index": idx, "reason": "不是字典对象"})
        if invalid > 0:
            return _r(
                "jsonld_context_correct", False,
                f"有 {invalid} 个 JSON-LD 块的 @context 不正确",
                {"valid": valid, "invalid": invalid, "details": invalid_details},
            )
        return _r(
            "jsonld_context_correct", True,
            f"所有 {valid} 个 JSON-LD 块的 @context 均正确",
            {"valid": valid, "invalid": 0},
        )

    @staticmethod
    def check_jsonld_no_duplicate_blocks(page, context=None):
        if not page.json_ld:
            return _r("jsonld_no_duplicate_blocks", True, "无 JSON-LD，不适用")
        type_counts = {}
        for item in page.json_ld:
            if isinstance(item, dict) and item.get("@type"):
                t = item.get("@type")
                if isinstance(t, list):
                    for sub_t in t:
                        type_counts[sub_t] = type_counts.get(sub_t, 0) + 1
                else:
                    type_counts[t] = type_counts.get(t, 0) + 1
        duplicates = {k: v for k, v in type_counts.items() if v > 1}
        if duplicates:
            return _r(
                "jsonld_no_duplicate_blocks", False,
                f"发现 {len(duplicates)} 种重复声明的 Schema 类型",
                {"duplicates": duplicates},
            )
        return _r(
            "jsonld_no_duplicate_blocks", True,
            "JSON-LD 无重复定义",
            {"types": list(type_counts.keys())},
        )

    @staticmethod
    def check_jsonld_not_empty(page, context=None):
        if not page.json_ld:
            return _r("jsonld_not_empty", True, "无 JSON-LD，不适用")
        filled = 0
        empty = 0
        empty_details = []
        common_fields = {"name", "description", "image", "headline", "url", "title", "text", "author"}
        for idx, item in enumerate(page.json_ld):
            if isinstance(item, dict):
                keys = set(k for k in item.keys() if not k.startswith("@"))
                has_content = bool(keys & common_fields) or len(keys) >= 2
                if has_content:
                    filled += 1
                else:
                    empty += 1
                    empty_details.append({"index": idx, "type": item.get("@type", ""), "fields": list(keys)})
            else:
                empty += 1
        if empty > 0:
            return _r(
                "jsonld_not_empty", False,
                f"有 {empty} 个 JSON-LD 块为空壳（只有 type 无实际字段）",
                {"filled": filled, "empty": empty, "details": empty_details},
            )
        return _r(
            "jsonld_not_empty", True,
            f"所有 {filled} 个 JSON-LD 块均包含实际字段",
            {"filled": filled, "empty": 0},
        )

    @staticmethod
    def check_microdata_format_used(page, context=None):
        if not page.html:
            return _r("microdata_format_used", True, "无 HTML 内容，不适用")
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.html, "html.parser")
            has_itemscope = bool(soup.find(attrs={"itemscope": True}))
            has_itemtype = bool(soup.find(attrs={"itemtype": True}))
            has_microdata = has_itemscope or has_itemtype
            if has_microdata:
                count = len(soup.find_all(attrs={"itemscope": True}))
                return _r(
                    "microdata_format_used", True,
                    f"页面使用了 Microdata 格式标记（{count} 个 itemscope）",
                    {"count": count},
                )
            return _r("microdata_format_used", True, "页面未使用 Microdata 格式")
        except Exception:
            return _r("microdata_format_used", True, "解析 HTML 失败，不适用")

    @staticmethod
    def check_rdfa_format_used(page, context=None):
        if not page.html:
            return _r("rdfa_format_used", True, "无 HTML 内容，不适用")
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.html, "html.parser")
            has_vocab = bool(soup.find(attrs={"vocab": True}))
            has_typeof = bool(soup.find(attrs={"typeof": True}))
            has_property = bool(soup.find(attrs={"property": True}))
            has_rdfa = has_vocab or has_typeof or has_property
            if has_rdfa:
                typeof_count = len(soup.find_all(attrs={"typeof": True}))
                return _r(
                    "rdfa_format_used", True,
                    f"页面使用了 RDFa 格式标记（{typeof_count} 个 typeof）",
                    {"typeof_count": typeof_count, "has_vocab": has_vocab},
                )
            return _r("rdfa_format_used", True, "页面未使用 RDFa 格式")
        except Exception:
            return _r("rdfa_format_used", True, "解析 HTML 失败，不适用")

    @staticmethod
    def check_product_schema_present(page, context=None):
        has_product = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and "product" in t.lower():
                    has_product = True
                    break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and "product" in sub_t.lower():
                            has_product = True
                            break
        return _r(
            "product_schema_present", has_product,
            "有 Product 产品 Schema" if has_product else "如为产品页建议添加 Product Schema",
        )

    @staticmethod
    def check_review_schema_present(page, context=None):
        has_review = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str):
                    tl = t.lower()
                    if "review" in tl or "aggregaterating" in tl:
                        has_review = True
                        break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and ("review" in sub_t.lower() or "aggregaterating" in sub_t.lower()):
                            has_review = True
                            break
        return _r(
            "review_schema_present", has_review,
            "有 Review/评论 Schema" if has_review else "如有评论内容建议添加 Review Schema",
        )

    @staticmethod
    def check_rating_schema_in_range(page, context=None):
        if not page.json_ld:
            return _r("rating_schema_in_range", True, "无 JSON-LD，不适用")
        ratings_checked = 0
        ratings_invalid = 0
        invalid_details = []

        def _check_rating(obj, path=""):
            nonlocal ratings_checked, ratings_invalid
            if isinstance(obj, dict):
                t = obj.get("@type", "")
                if isinstance(t, str) and ("rating" in t.lower() or "review" in t.lower()):
                    rv = obj.get("ratingValue")
                    wr = obj.get("worstRating")
                    br = obj.get("bestRating")
                    if rv is not None:
                        ratings_checked += 1
                        try:
                            rv_f = float(rv)
                            wr_f = float(wr) if wr is not None else 0.0
                            br_f = float(br) if br is not None else 5.0
                            if rv_f < wr_f or rv_f > br_f:
                                ratings_invalid += 1
                                invalid_details.append({
                                    "path": path,
                                    "ratingValue": rv,
                                    "worstRating": wr,
                                    "bestRating": br,
                                    "reason": f"评分 {rv} 不在范围 [{wr_f}, {br_f}] 内",
                                })
                        except (ValueError, TypeError):
                            ratings_invalid += 1
                            invalid_details.append({
                                "path": path,
                                "reason": "评分数值格式非法",
                            })
                for k, v in obj.items():
                    _check_rating(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    _check_rating(v, f"{path}[{i}]")

        for idx, item in enumerate(page.json_ld):
            _check_rating(item, f"json_ld[{idx}]")

        if ratings_invalid > 0:
            return _r(
                "rating_schema_in_range", False,
                f"有 {ratings_invalid} 处 Rating 评分超出合理范围",
                {"checked": ratings_checked, "invalid": ratings_invalid, "details": invalid_details},
            )
        if ratings_checked == 0:
            return _r("rating_schema_in_range", True, "未发现 Rating 字段，不适用")
        return _r(
            "rating_schema_in_range", True,
            f"所有 {ratings_checked} 处 Rating 评分均在合理范围内",
            {"checked": ratings_checked, "invalid": 0},
        )

    @staticmethod
    def check_event_schema_present(page, context=None):
        has_event = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and "event" in t.lower():
                    has_event = True
                    break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and "event" in sub_t.lower():
                            has_event = True
                            break
        return _r(
            "event_schema_present", has_event,
            "有 Event 活动 Schema" if has_event else "如为活动页建议添加 Event Schema",
        )

    @staticmethod
    def check_course_schema_present(page, context=None):
        has_course = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and "course" in t.lower():
                    has_course = True
                    break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and "course" in sub_t.lower():
                            has_course = True
                            break
        return _r(
            "course_schema_present", has_course,
            "有 Course 课程 Schema" if has_course else "如为教育课程页建议添加 Course Schema",
        )

    @staticmethod
    def check_job_schema_present(page, context=None):
        has_job = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and "jobposting" in t.lower():
                    has_job = True
                    break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and "jobposting" in sub_t.lower():
                            has_job = True
                            break
        return _r(
            "job_schema_present", has_job,
            "有 JobPosting 职位 Schema" if has_job else "如为招聘页建议添加 JobPosting Schema",
        )

    @staticmethod
    def check_sitelinks_searchbox(page, context=None):
        has_website = False
        has_search_action = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and t.lower() == "website":
                    has_website = True
                    potential_action = item.get("potentialAction")
                    if isinstance(potential_action, dict):
                        pa_type = potential_action.get("@type", "")
                        if isinstance(pa_type, str) and "searchaction" in pa_type.lower():
                            has_search_action = True
                    elif isinstance(potential_action, list):
                        for act in potential_action:
                            if isinstance(act, dict):
                                pa_type = act.get("@type", "")
                                if isinstance(pa_type, str) and "searchaction" in pa_type.lower():
                                    has_search_action = True
                                    break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and sub_t.lower() == "website":
                            has_website = True
                            break
        eligible = has_website and has_search_action
        if eligible:
            return _r(
                "sitelinks_searchbox", True,
                "已配置 WebSite + SearchAction，支持 Sitelinks Searchbox",
            )
        details = {"has_website": has_website, "has_search_action": has_search_action}
        if not has_website:
            return _r(
                "sitelinks_searchbox", False,
                "缺少 WebSite 类型结构化数据",
                details,
            )
        return _r(
            "sitelinks_searchbox", False,
            "WebSite 中缺少 SearchAction 配置",
            details,
        )

    @staticmethod
    def check_corporate_contact(page, context=None):
        has_org = False
        has_contact = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                is_org = False
                if isinstance(t, str) and "organization" in t.lower():
                    is_org = True
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and "organization" in sub_t.lower():
                            is_org = True
                            break
                if is_org:
                    has_org = True
                    contact = item.get("contactPoint")
                    if isinstance(contact, dict):
                        has_contact = True
                    elif isinstance(contact, list) and len(contact) > 0:
                        has_contact = True
        eligible = has_org and has_contact
        if eligible:
            return _r(
                "corporate_contact", True,
                "已配置 Organization + ContactPoint 企业联系信息",
            )
        details = {"has_organization": has_org, "has_contact_point": has_contact}
        if not has_org:
            return _r(
                "corporate_contact", False,
                "缺少 Organization 类型结构化数据",
                details,
            )
        return _r(
            "corporate_contact", False,
            "Organization 中缺少 ContactPoint 联系信息",
            details,
        )

    @staticmethod
    def check_logo_schema_present(page, context=None):
        has_org = False
        has_logo = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                is_org = False
                if isinstance(t, str) and "organization" in t.lower():
                    is_org = True
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and "organization" in sub_t.lower():
                            is_org = True
                            break
                if is_org:
                    has_org = True
                    if item.get("logo"):
                        has_logo = True
        if has_org and has_logo:
            return _r(
                "logo_schema_present", True,
                "Organization 中已声明 logo",
            )
        details = {"has_organization": has_org, "has_logo": has_logo}
        if not has_org:
            return _r(
                "logo_schema_present", False,
                "缺少 Organization 类型结构化数据",
                details,
            )
        return _r(
            "logo_schema_present", False,
            "Organization 中未声明 logo 字段",
            details,
        )

    @staticmethod
    def check_carousel_markup_valid(page, context=None):
        has_itemlist = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and t.lower() == "itemlist":
                    has_itemlist = True
                    break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and sub_t.lower() == "itemlist":
                            has_itemlist = True
                            break
        return _r(
            "carousel_markup_valid", has_itemlist,
            "已配置 ItemList Carousel 轮播标记" if has_itemlist else "如为列表页可添加 ItemList 轮播标记",
        )

    @staticmethod
    def check_howto_schema_present(page, context=None):
        has_howto = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and "howto" in t.lower():
                    has_howto = True
                    break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and "howto" in sub_t.lower():
                            has_howto = True
                            break
        return _r(
            "howto_schema_present", has_howto,
            "有 HowTo 教程步骤 Schema" if has_howto else "如为教程类页面建议添加 HowTo Schema",
        )

    @staticmethod
    def check_recipe_schema_present(page, context=None):
        has_recipe = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and "recipe" in t.lower():
                    has_recipe = True
                    break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and "recipe" in sub_t.lower():
                            has_recipe = True
                            break
        return _r(
            "recipe_schema_present", has_recipe,
            "有 Recipe 食谱 Schema" if has_recipe else "如为食谱页建议添加 Recipe Schema",
        )

    @staticmethod
    def check_video_schema_present(page, context=None):
        has_video = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                if isinstance(t, str) and "videoobject" in t.lower():
                    has_video = True
                    break
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and "videoobject" in sub_t.lower():
                            has_video = True
                            break
        return _r(
            "video_schema_present", has_video,
            "有 VideoObject 视频 Schema" if has_video else "如含视频内容建议添加 VideoObject Schema",
        )

    @staticmethod
    def check_social_profile_sameas(page, context=None):
        has_org = False
        has_sameas = False
        for item in page.json_ld:
            if isinstance(item, dict):
                t = item.get("@type", "")
                is_org = False
                if isinstance(t, str) and ("organization" in t.lower() or "person" in t.lower()):
                    is_org = True
                if isinstance(t, list):
                    for sub_t in t:
                        if isinstance(sub_t, str) and ("organization" in sub_t.lower() or "person" in sub_t.lower()):
                            is_org = True
                            break
                if is_org:
                    has_org = True
                    sameas = item.get("sameAs")
                    if isinstance(sameas, list) and len(sameas) > 0:
                        has_sameas = True
                    elif isinstance(sameas, str) and sameas.strip():
                        has_sameas = True
        eligible = has_org and has_sameas
        if eligible:
            return _r(
                "social_profile_sameas", True,
                "已通过 sameAs 声明社交媒体链接",
            )
        details = {"has_org_or_person": has_org, "has_sameAs": has_sameas}
        if not has_org:
            return _r(
                "social_profile_sameas", False,
                "缺少 Organization/Person 类型结构化数据",
                details,
            )
        return _r(
            "social_profile_sameas", False,
            "Organization/Person 中缺少 sameAs 社交账号链接",
            details,
        )

    @staticmethod
    def check_speakable_property_present(page, context=None):
        has_speakable = False
        for item in page.json_ld:
            if isinstance(item, dict):
                if "speakable" in item:
                    has_speakable = True
                    break
                t = item.get("@type", "")
                if isinstance(t, str) and ("article" in t.lower() or "newsarticle" in t.lower()):
                    if item.get("speakable"):
                        has_speakable = True
                        break
        return _r(
            "speakable_property_present", has_speakable,
            "已配置 speakable 属性，支持语音朗读" if has_speakable else "新闻类页面可配置 speakable 属性",
        )

    @staticmethod
    def check_mainentity_of_page(page, context=None):
        has_mainentity = False
        for item in page.json_ld:
            if isinstance(item, dict):
                if "mainEntityOfPage" in item:
                    has_mainentity = True
                    break
                main_entity = item.get("mainEntity")
                if isinstance(main_entity, dict) and "mainEntityOfPage" in main_entity:
                    has_mainentity = True
                    break
        return _r(
            "mainentity_of_page", has_mainentity,
            "已通过 mainEntityOfPage 指明主实体" if has_mainentity else "建议使用 mainEntityOfPage 声明页面对应主实体",
        )
