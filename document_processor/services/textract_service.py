import json
from dataclasses import dataclass
from decimal import Decimal

import boto3


@dataclass
class TextractOutput:
    raw_response: dict
    average_confidence: Decimal


class TextractService:
    def __init__(self, region_name=None):
        self.client = boto3.client("textract", region_name=region_name)

    def analyze_document(self, file_bytes: bytes) -> TextractOutput:
        response = self.client.analyze_document(
            Document={"Bytes": file_bytes},
            FeatureTypes=["FORMS", "TABLES"],
        )
        confidence_values = [
            Decimal(str(block.get("Confidence")))
            for block in response.get("Blocks", [])
            if block.get("Confidence") is not None
        ]
        avg_conf = sum(confidence_values) / len(confidence_values) if confidence_values else Decimal("0")
        return TextractOutput(raw_response=response, average_confidence=avg_conf.quantize(Decimal("0.01")))

    @staticmethod
    def serialize_response(response: dict) -> str:
        return json.dumps(response, default=str)
