import re
from collections import defaultdict

from ..models import ExtractedField, ExtractionRule


class ExtractionEngine:
    """Maps Textract output into ExtractedField rows using configurable rules."""

    def apply_rules(self, document, textract_response: dict):
        kv_pairs = self._extract_key_values(textract_response)
        table_cells = self._extract_tables(textract_response)
        line_text = self._extract_lines(textract_response)

        rules = (
            ExtractionRule.objects.filter(template_type=document.template_type, is_enabled=True)
            .select_related("template_type")
            .order_by("priority", "id")
        )

        created = []
        for rule in rules:
            if rule.rule_type == ExtractionRule.RuleType.FIELD:
                raw_value = self._resolve_field_value(rule, kv_pairs, line_text)
                if raw_value is None:
                    continue
                created.append(
                    ExtractedField.objects.create(
                        document=document,
                        extraction_rule=rule,
                        field_name=rule.target_field,
                        extracted_value=str(raw_value),
                        is_table_value=False,
                    )
                )
                continue

            values = table_cells.get(rule.table_index or 1, [])
            for value in values:
                created.append(
                    ExtractedField.objects.create(
                        document=document,
                        extraction_rule=rule,
                        field_name=rule.target_field,
                        extracted_value=str(value),
                        is_table_value=True,
                    )
                )
        return created

    def _resolve_field_value(self, rule, kv_pairs, lines):
        source_key = (rule.source_key or "").strip()
        direct = kv_pairs.get(source_key)
        if direct:
            return self._regex_extract(direct, rule.regex_pattern)

        normalized_key = self._normalize(source_key)
        for key, value in kv_pairs.items():
            if self._normalize(key) == normalized_key:
                return self._regex_extract(value, rule.regex_pattern)

        for line in lines:
            if normalized_key and normalized_key in self._normalize(line):
                return self._regex_extract(line, rule.regex_pattern)

        return None

    @staticmethod
    def _normalize(value):
        return re.sub(r"\s+", " ", str(value or "").lower()).strip()

    def _regex_extract(self, value, pattern):
        if not pattern:
            return value
        match = re.search(pattern, value or "")
        return match.group(1) if match and match.groups() else (match.group(0) if match else value)

    def _extract_lines(self, response):
        return [b.get("Text", "") for b in response.get("Blocks", []) if b.get("BlockType") == "LINE"]

    def _extract_key_values(self, response):
        blocks = response.get("Blocks", [])
        block_map = {block.get("Id"): block for block in blocks if block.get("Id")}

        keys = [
            block
            for block in blocks
            if block.get("BlockType") == "KEY_VALUE_SET" and "KEY" in block.get("EntityTypes", [])
        ]

        kv = {}
        for key_block in keys:
            key_text = self._collect_text(key_block, block_map)
            value_text = ""
            for relationship in key_block.get("Relationships", []):
                if relationship.get("Type") != "VALUE":
                    continue
                for value_id in relationship.get("Ids", []):
                    value_block = block_map.get(value_id)
                    if not value_block:
                        continue
                    value_text = self._collect_text(value_block, block_map)
            if key_text:
                kv[key_text] = value_text
        return kv

    def _extract_tables(self, response):
        blocks = response.get("Blocks", [])
        block_map = {block.get("Id"): block for block in blocks if block.get("Id")}
        tables = defaultdict(list)
        table_order = []

        for block in blocks:
            if block.get("BlockType") == "TABLE":
                table_order.append(block.get("Id"))

        for index, table_id in enumerate(table_order, start=1):
            table_block = block_map.get(table_id)
            if not table_block:
                continue
            for relation in table_block.get("Relationships", []):
                if relation.get("Type") != "CHILD":
                    continue
                for child_id in relation.get("Ids", []):
                    child = block_map.get(child_id)
                    if child and child.get("BlockType") == "CELL":
                        tables[index].append(self._collect_text(child, block_map))
        return tables

    def _collect_text(self, block, block_map):
        words = []
        for relation in block.get("Relationships", []):
            if relation.get("Type") != "CHILD":
                continue
            for child_id in relation.get("Ids", []):
                child = block_map.get(child_id)
                if not child:
                    continue
                if child.get("BlockType") == "WORD":
                    words.append(child.get("Text", ""))
                elif child.get("BlockType") == "SELECTION_ELEMENT" and child.get("SelectionStatus") == "SELECTED":
                    words.append("X")
        return " ".join(w for w in words if w).strip()
