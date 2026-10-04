"""Customer-request extraction using OpenRouter or a deterministic fallback."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any


ALLOWED_UNITS = {"piece", "box", "carton"}
CHINESE_QUANTITY = re.compile(r"(?<!\d)(\d+)\s*(支|个|盒|箱)")
APPROXIMATE_QUANTITY = re.compile(
    r"大概|大约|约\s*\d|左右|差不多|roughly|approximately|approx\.?|about\s+\d|around\s+\d",
    re.IGNORECASE,
)
SPEC_WITH_ALTERNATIVE_LENGTH = re.compile(
    r"M\s*\d{1,2}\s*[-X×*]\s*\d{2,3}\s*[/／]\s*\d{2,3}",
    re.IGNORECASE,
)
PLACEHOLDERS = {
    "{{SPEC}}",
    "{{QUANTITY}}",
    "{{UNIT}}",
    "{{TOTAL_PIECES}}",
    "{{TOTAL_PRICE}}",
    "{{DISCOUNT_PERCENT}}",
}


@dataclass
class Extraction:
    standard: str | None
    diameter: str | None
    length_mm: int | None
    quantity: int | None
    unit: str | None
    needs_clarification: bool
    clarification_reason: str
    reply_template: str
    extraction_method: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_unit(raw: str) -> str | None:
    value = raw.lower().strip()
    mapping = {
        "支": "piece",
        "个": "piece",
        "pc": "piece",
        "pcs": "piece",
        "piece": "piece",
        "pieces": "piece",
        "盒": "box",
        "box": "box",
        "boxes": "box",
        "箱": "carton",
        "carton": "carton",
        "cartons": "carton",
        "ctn": "carton",
        "ctns": "carton",
    }
    return mapping.get(value)


def extract_with_rules(text: str) -> Extraction:
    normalized = text.upper().replace("×", "X").replace("*", "X")
    sku_match = re.search(r"(?<![A-Z0-9])(M\s*\d{1,2})\s*[-X]\s*(\d{2,3})(?!\d)", normalized)
    diameter = re.sub(r"\s+", "", sku_match.group(1)) if sku_match else None
    length_mm = int(sku_match.group(2)) if sku_match else None

    standard_match = re.search(r"\bDIN\s*933\b", normalized)
    standard = "DIN933" if standard_match or sku_match else None

    quantity_match = re.search(
        r"(?<!M)(\d+)\s*(CARTONS?|CTNS?|BOX(?:ES)?|PIECES?|PCS?|PC|箱|盒|支|个)",
        normalized,
        re.IGNORECASE,
    )
    quantity = int(quantity_match.group(1)) if quantity_match else None
    unit = _normalize_unit(quantity_match.group(2)) if quantity_match else None

    missing = []
    if not diameter or length_mm is None:
        missing.append("an exact diameter and length, such as M16x50")
    if quantity is None or unit is None:
        missing.append("a quantity with unit: pieces, boxes, or cartons")
    needs_clarification = bool(missing)
    reason = "Please provide " + " and ".join(missing) + "." if missing else ""

    return Extraction(
        standard=standard,
        diameter=diameter,
        length_mm=length_mm,
        quantity=quantity,
        unit=unit,
        needs_clarification=needs_clarification,
        clarification_reason=reason,
        reply_template=(
            "Thank you for your enquiry. We can offer {{SPEC}} for {{QUANTITY}} {{UNIT}} "
            "({{TOTAL_PIECES}} pieces) at a total of CNY {{TOTAL_PRICE}} after a "
            "{{DISCOUNT_PERCENT}}% discount. Please let us know if you would like to proceed."
        ),
        extraction_method="rules",
    )


def extract_with_openrouter(
    text: str,
    allowed_skus: list[str],
    api_key: str,
    model: str,
    timeout_seconds: int = 45,
) -> Extraction:
    schema = {
        "name": "fastquote_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "standard": {"type": ["string", "null"]},
                "diameter": {"type": ["string", "null"]},
                "length_mm": {"type": ["integer", "null"]},
                "quantity": {"type": ["integer", "null"]},
                "unit": {"type": ["string", "null"], "enum": ["piece", "box", "carton", None]},
                "needs_clarification": {"type": "boolean"},
                "clarification_reason": {"type": "string"},
                "reply_template": {"type": "string"},
            },
            "required": [
                "standard", "diameter", "length_mm", "quantity", "unit",
                "needs_clarification", "clarification_reason", "reply_template"
            ],
            "additionalProperties": False,
        },
    }
    system_prompt = (
        "You extract a fastener quotation request. Do not calculate or invent any price. "
        "The application uses one internal DIN933 A2 catalog. Customers are not expected to "
        "state DIN933 or A2. When an exact listed diameter and length such as M16x50 is present, "
        "set standard to DIN933 and do not ask the customer for the standard or material. "
        "Only use piece, box, or carton as unit. Chinese 箱 means carton, 盒 means box, "
        "and 支 means piece. Never guess a missing unit. Set needs_clarification=true when "
        "product, length, quantity, or unit is missing, approximate, or ambiguous; keep it "
        "true even if you can make a plausible guess. A request with two possible lengths "
        "needs clarification. The reply_template must be concise business English and "
        "include {{SPEC}}, {{QUANTITY}}, {{UNIT}}, and {{TOTAL_PRICE}}. It may use only "
        "these placeholders: " + ", ".join(sorted(PLACEHOLDERS)) + ". "
        "Never put a numeric price in the template. Never mention gross margin, the 10% threshold, "
        "manager approval, or any internal approval result. Available SKUs: " + ", ".join(allowed_skus)
    )
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "response_format": {"type": "json_schema", "json_schema": schema},
    }
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:8765",
            "X-Title": "FastQuote PE6201 Demo",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter returned HTTP {exc.code}: {detail[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter connection failed: {exc.reason}") from exc

    try:
        parsed = json.loads(body["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("OpenRouter returned an invalid structured response.") from exc

    unit = parsed.get("unit")
    if unit is not None and unit not in ALLOWED_UNITS:
        parsed["needs_clarification"] = True
        parsed["clarification_reason"] = "The quantity unit could not be verified."
        parsed["unit"] = None

    template = parsed.get("reply_template", "")
    used_placeholders = set(re.findall(r"\{\{[A-Z_]+\}\}", template))
    exposes_internal_rules = re.search(r"\b(?:margin|approval)\b|10\s*%", template, re.IGNORECASE)
    if (
        not {"{{SPEC}}", "{{QUANTITY}}", "{{UNIT}}", "{{TOTAL_PRICE}}"}.issubset(used_placeholders)
        or
        used_placeholders - PLACEHOLDERS
        or re.search(r"(?:CNY|RMB|¥)\s*\d", template, re.IGNORECASE)
        or exposes_internal_rules
    ):
        template = extract_with_rules(text).reply_template

    diameter = parsed.get("diameter")
    length_mm = parsed.get("length_mm")
    quantity = parsed.get("quantity")
    standard = parsed.get("standard")
    if not standard and diameter and length_mm is not None:
        standard = "DIN933"

    needs_clarification = bool(parsed.get("needs_clarification"))
    clarification_reason = str(parsed.get("clarification_reason", ""))
    explicit_quantities = CHINESE_QUANTITY.findall(text)
    if explicit_quantities:
        explicit_units = {_normalize_unit(raw_unit) for _, raw_unit in explicit_quantities}
        if len(explicit_units) > 1:
            needs_clarification = True
            clarification_reason = "Please confirm the quantity unit for this order."
        else:
            explicit_quantity, raw_unit = explicit_quantities[0]
            if len({int(value) for value, _ in explicit_quantities}) > 1:
                needs_clarification = True
                clarification_reason = "Please confirm the quantity for this order."
            else:
                quantity = int(explicit_quantity)
                unit = _normalize_unit(raw_unit)
    if SPEC_WITH_ALTERNATIVE_LENGTH.search(text) or len(re.findall(
        r"M\s*\d{1,2}\s*[-X×*]\s*\d{2,3}(?!\d)", text, re.IGNORECASE
    )) > 1:
        needs_clarification = True
        clarification_reason = "Please confirm one exact diameter and length for the quotation."
    elif APPROXIMATE_QUANTITY.search(text):
        needs_clarification = True
        clarification_reason = "Please confirm the exact quantity or specification."
    elif (
        re.search(r"[,，]\s*\d+\s*(?:[,，。.!?]|$)", text)
        and not re.search(r"支|个|盒|箱|\b(?:pieces?|pcs?|boxes?|cartons?|ctns?)\b", text, re.IGNORECASE)
    ):
        needs_clarification = True
        clarification_reason = "Please provide the quantity unit: pieces, boxes, or cartons."
    elif not all([diameter, length_mm is not None, quantity is not None, unit]):
        needs_clarification = True
        clarification_reason = clarification_reason or "Please confirm the product and quantity."

    return Extraction(
        standard=standard,
        diameter=diameter,
        length_mm=length_mm,
        quantity=quantity,
        unit=unit,
        needs_clarification=needs_clarification,
        clarification_reason=clarification_reason,
        reply_template=template,
        extraction_method=f"openrouter:{model}",
    )

