"""Bind semantic chapters to reviewed element and composition rules before HTML replay."""

import argparse
import json
from pathlib import Path

from jsonschema import ValidationError

from design_replay import check_plan, check_system, digest, load, require, used_tokens

KINDS = {"background", "image", "icon", "color", "type", "component", "motif", "spacing", "stroke"}
CHAPTER_FIELDS = {"id", "relation", "intent", "fields", "items"}


def check_grammar(system, catalog, grammar, contracts):
    require(grammar["version"] == 1 and catalog["version"] == 1, "Unsupported catalog or grammar")
    require(system["source"]["sha256"] == catalog["source_sha256"] == grammar["source_sha256"],
            "Catalog, grammar and system must describe the same source")
    require(system["source"]["pages"] == catalog["pages"], "Catalog page count does not match")
    families, elements = system["families"], grammar["elements"]
    for key, evidence in system["evidence"].items():
        require(all(ref in catalog["objects"] and catalog["objects"][ref]["page"] == evidence["page"]
                    for ref in evidence.get("catalog_refs", ())), f"Unresolved scoped source objects on {key}")
    for key, element in elements.items():
        require(element["kind"] in KINDS and element["status"] in {"inherited", "extended"},
                f"Unknown element type or status: {key}")
        require(element["family"] in families and families[element["family"]]["scope"] != "excluded",
                f"Excluded or unknown element family: {key}")
        require(element["objects"] and all(ref in catalog["objects"] for ref in element["objects"]),
                f"Unresolved source objects on element: {key}")
        require(all(catalog["objects"][ref]["page"] in families[element["family"]]["pages"]
                    for ref in element["objects"]), f"Mixed source families on element: {key}")
        available = {token for ref in element["objects"] for token in catalog["objects"][ref]["tokens"]}
        require(element["tokens"] and all(token in available and token in catalog["tokens"]
                                          for token in element["tokens"]), f"Unresolved visual tokens on: {key}")
        require(element["relations"] and element["use"].strip(), f"Missing applicability on element: {key}")
        if element["status"] == "extended":
            require(element.get("change", "").strip(), f"Explain the extension on element: {key}")
    for key, recipe in grammar["recipes"].items():
        pattern_id = recipe["pattern"]
        require(pattern_id in contracts, f"Unknown pattern on recipe: {key}")
        ids, slots = contracts[pattern_id]
        family = system["patterns"][pattern_id]["family"]
        uses = recipe["use_elements"]
        require(uses and all(element in elements for element in uses), f"Unknown elements on recipe: {key}")
        covered = set()
        for element, layers in uses.items():
            spec = elements[element]
            require(recipe["relation"] in spec["relations"] and spec["family"] == family,
                    f"Incompatible element on {key}: {element}")
            require(not (set(layers) - ids), f"Unknown layer binding on {key}: {element}")
            if spec["kind"] == "background":
                backdrop = families[family].get("backdrop")
                evidence = system["evidence"].get(backdrop["evidence"]) if backdrop else None
                require(not layers and evidence, f"Unresolved fixed background on {key}: {element}")
                refs = set(evidence.get("catalog_refs", ()))
                refs.update(f"p{evidence['page']}-o{obj}" for obj in evidence.get("objects", ()))
                require(refs.intersection(spec["objects"]), f"Unresolved fixed background on {key}: {element}")
            else:
                require(layers, f"Missing layer binding on {key}: {element}")
            covered.update(layers)
        require(covered == ids and recipe["focus"] in covered, f"Unbound layout layers on recipe: {key}")
        family_backdrop = families[family].get("backdrop")
        require(not family_backdrop or any(elements[element]["kind"] == "background" for element in uses),
                f"Recipe must identify its fixed background: {key}")
        mapped = [*recipe["fields"].values(), *(slot for row in recipe["items"] for slot in row.values())]
        require(len(mapped) == len(set(mapped)) and set(mapped) == slots.keys(), f"Invalid slot mapping: {key}")
        require(recipe["limits"].keys() == slots.keys() and all(
            type(limit) is int and 1 <= limit <= 600 for limit in recipe["limits"].values()
        ), f"Invalid capacity limits: {key}")


def fit(chapter, recipe):
    items = chapter["items"]
    if len(items) != len(recipe["items"]):
        return None, f"需要 {len(recipe['items'])} 项，收到 {len(items)} 项"
    if chapter["fields"].keys() != recipe["fields"].keys() or any(
        item.keys() != row.keys() for item, row in zip(items, recipe["items"])
    ):
        return None, "字段与版式槽位不匹配"
    slots = {slot: chapter["fields"][field] for field, slot in recipe["fields"].items()}
    for item, row in zip(items, recipe["items"]):
        slots.update({slot: item[field] for field, slot in row.items()})
    overflow = [slot for slot, value in slots.items() if len(value) > recipe["limits"][slot]]
    if overflow:
        return None, "超出内容容量：" + "、".join(overflow)
    return slots, None


def check_manuscript(manuscript):
    require(isinstance(manuscript, dict), "Expected a semantic manuscript object")
    require({"version", "chapters"} <= manuscript.keys() <= {"version", "chapters", "sequence"},
            "The manuscript accepts chapter semantics and an optional sequence")
    chapters = manuscript["chapters"]
    require(manuscript["version"] == 1 and isinstance(chapters, list) and 1 <= len(chapters) <= 120,
            "Expected 1–120 semantic chapters")
    require(all(isinstance(chapter, dict) and CHAPTER_FIELDS <= chapter.keys() <= CHAPTER_FIELDS | {"variant"}
                for chapter in chapters), "Chapters must contain only semantic fields")
    for chapter in chapters:
        require(isinstance(chapter["fields"], dict) and isinstance(chapter["items"], list)
                and all(isinstance(item, dict) for item in chapter["items"]), "Invalid chapter fields")
        values = [*chapter["fields"].values(), *(value for item in chapter["items"] for value in item.values())]
        require(all(isinstance(value, str) and (value == "" or value.strip()) for value in values),
                "Invalid chapter value")
        require(all(isinstance(chapter[key], str) and chapter[key].strip()
                    for key in ("id", "relation", "intent")), "Missing chapter ID, relation or intent")
    require(len({chapter["id"] for chapter in chapters}) == len(chapters), "Duplicate chapter ID")


def compile_story(system, catalog, grammar, manuscript):
    contracts = check_system(system)
    check_grammar(system, catalog, grammar, contracts)
    check_manuscript(manuscript)
    chapters = manuscript["chapters"]
    plan = {"version": 1, "pages": []}
    trace, gaps = [], []
    sequence = manuscript.get("sequence")
    if sequence is not None:
        require(sequence in system.get("sequences", {}), "Unapproved chapter sequence")
        plan["sequence"] = sequence
    steps = system.get("sequences", {}).get(sequence)
    if steps is not None:
        require(len(chapters) == len(steps), "Unexpected number of semantic chapters in sequence")
    for index, chapter in enumerate(chapters):
        candidates, rejected = [], {}
        for identifier, recipe in sorted(grammar["recipes"].items()):
            if recipe["relation"] != chapter["relation"]:
                continue
            if recipe.get("variant") != chapter.get("variant"):
                rejected[identifier] = "版式变体不匹配"
                continue
            if steps is not None:
                step = steps[index]
                if (recipe["pattern"] not in step["patterns"]
                        or any(recipe[key] != step[key] for key in ("focus", "density", "weight"))):
                    rejected[identifier] = "与已批准的章节顺序冲突"
                    continue
            slots, failure = fit(chapter, recipe)
            if failure:
                rejected[identifier] = failure
            else:
                candidates.append((identifier, recipe, slots))
        if len(candidates) != 1:
            compatible = [key for key, element in grammar["elements"].items()
                          if chapter["relation"] in element["relations"]]
            if candidates:
                reason = "多个适配规则待取舍"
            elif rejected:
                reason = "可用版式未满足本章约束"
            else:
                reason = "设计包没有支持该内容关系的版式"
            gaps.append({"chapter": chapter["id"], "relation": chapter["relation"], "intent": chapter["intent"],
                         "reason": reason,
                         "candidates": [entry[0] for entry in candidates], "rejected": rejected,
                         "reusable_elements": compatible, "needs_review": True})
            continue
        identifier, recipe, slots = candidates[0]
        pattern = system["patterns"][recipe["pattern"]]
        plan["pages"].append({"id": chapter["id"], "role": pattern["role"], "pattern": recipe["pattern"],
                              **{key: recipe[key] for key in ("focus", "density", "weight")}, "slots": slots})
        trace.append({"chapter": chapter["id"], "intent": chapter["intent"], "recipe": identifier,
                      "pattern": recipe["pattern"], "layout_rule": recipe["layout"],
                      "elements": {key: {"status": grammar["elements"][key]["status"],
                                         "source": grammar["elements"][key]["objects"],
                                         "source_tokens": grammar["elements"][key]["tokens"],
                                         "render_tokens": sorted(set(used_tokens(
                                             [layer for layer in pattern["layers"] if layer["id"] in layers], system))),
                                         "layers": layers}
                                   for key, layers in recipe["use_elements"].items()}})
    if plan["pages"] and (not gaps or sequence is not None or not system.get("sequences")):
        check_plan(plan, system, contracts, partial=bool(gaps))
    if gaps:
        return None, {"compiled": trace, "extensions_needed": gaps}
    return plan, {"compiled": trace, "extensions_needed": []}


def style_summary(system, catalog, grammar):
    output = ["# 设计语言与适配规则", "", f"主风格 {system['primary_family']} · 原稿 {catalog['pages']} 页",
              "", f"底层目录收录 {len(catalog['objects'])} 个对象与 {len(catalog['tokens'])} 个去重属性 token。",
              "", "原稿的对象与属性值见 element-catalog.json，元素适用条件与槽位绑定见 style-grammar.json。",
              "", "## 元素与适用条件", ""]
    for key, item in grammar["elements"].items():
        sources = "、".join(f"第 {catalog['objects'][ref]['page']} 页对象 {catalog['objects'][ref]['object']}"
                          for ref in item["objects"])
        status = "继承" if item["status"] == "inherited" else "延展"
        output.append(f"- **{key}** · {item['kind']} · {status}。{item['use']} 来源为{sources}。")
        output.append(f"  可用于{'、'.join(item['relations'])}。")
        if item.get("change"):
            output.append(f"  延展做法为{item['change']}。")
    output.extend(["", "## 章节如何编译", ""])
    for key, recipe in grammar["recipes"].items():
        output.append(f"- **{key}** · {recipe['relation']} · {len(recipe['items'])} 项。{recipe['layout']} "
                      f"绑定 {'、'.join(recipe['use_elements'])}。")
    output.extend(["", "## 渲染参数", "",
                   "| Token | 执行值 | 依据规则 |", "| --- | --- | --- |"])
    for group, entries in system["tokens"].items():
        for key, value in entries.items():
            identifier = f"{group}.{key}"
            if group == "type":
                value = f"{value['font']}，{value['size']} cqw，字重 {value['weight']}，行高 {value['leading']}"
            output.append(f"| {identifier} | {value} | {system['token_rules'][identifier]} |")
    output.extend(["", "没有唯一可用配方的章节进入延展评审。延展需登记源元素、改变的属性和验证方式。"])
    return "\n".join(output) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("system", "catalog", "grammar", "manuscript"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        system, catalog, grammar, manuscript = [load(getattr(args, name))
                                                for name in ("system", "catalog", "grammar", "manuscript")]
        plan, trace = compile_story(system, catalog, grammar, manuscript)
        trace["inputs_sha256"] = {name: digest(getattr(args, name))
                                  for name in ("system", "catalog", "grammar", "manuscript")}
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out / "compile-report.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n",
                                                      encoding="utf-8")
        (args.out / "STYLE.md").write_text(style_summary(system, catalog, grammar), encoding="utf-8")
        if plan is None:
            parser.exit(2, "Some chapters need a reviewed extension. See compile-report.json.\n")
        (args.out / "storyboard.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
                                                  encoding="utf-8")
    except (ValueError, KeyError, TypeError, AttributeError, OSError, ValidationError) as error:
        parser.exit(2, f"Compile rejected: {error}\n")


if __name__ == "__main__":
    main()
