"""NapCat 入站文本与 CQ 码解析辅助。"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

import base64
import re


_CQ_SEGMENT_PATTERN = re.compile(r"\[CQ:(?P<type>[a-zA-Z0-9_]+)(?P<params>(?:,[^\]]*)?)\]")


class NapCatInboundTextMixin:
    """封装入站纯文本与 CQ 码处理逻辑。"""

    def build_plain_text(self, raw_message: List[Dict[str, Any]], fallback_text: str) -> str:
        """从标准消息段中提取可展示的纯文本。

        Args:
            raw_message: 标准化后的消息段列表。
            fallback_text: 当无法拼出文本时使用的回退文本。

        Returns:
            str: 用于 Host 展示和命令判断的纯文本内容。
        """
        plain_text_parts: List[str] = []
        for item in raw_message:
            if not isinstance(item, Mapping):
                continue
            item_type = str(item.get("type") or "").strip()
            item_data = item.get("data")
            if item_type == "text":
                plain_text_parts.append(str(item_data or ""))
            elif item_type == "at" and isinstance(item_data, Mapping):
                plain_text_parts.append(f"@{item_data.get('target_user_id') or ''}")
            elif item_type == "reply":
                plain_text_parts.append("[reply]")
            elif item_type == "forward":
                plain_text_parts.append("[forward]")
            elif item_type in {"image", "emoji", "voice"}:
                plain_text_parts.append(f"[{item_type}]")

        plain_text = "".join(part for part in plain_text_parts if part).strip()
        return plain_text or fallback_text or "[unsupported]"

    def _parse_cq_message_text(self, message_text: str) -> List[Dict[str, Any]]:
        """将 CQ 码字符串解析为 OneBot 风格消息段列表。

        Args:
            message_text: NapCat 在字符串模式下返回的消息内容。

        Returns:
            List[Dict[str, Any]]: 解析后的 OneBot 风格消息段列表。
        """
        parsed_segments: List[Dict[str, Any]] = []
        current_index = 0

        for match in _CQ_SEGMENT_PATTERN.finditer(message_text):
            prefix_text = self._decode_cq_entities(message_text[current_index : match.start()])
            if prefix_text:
                parsed_segments.append({"type": "text", "data": {"text": prefix_text}})

            segment_type = str(match.group("type") or "").strip()
            segment_data = self._parse_cq_segment_data(match.group("params") or "")
            if segment_type:
                parsed_segments.append({"type": segment_type, "data": segment_data})
            current_index = match.end()

        suffix_text = self._decode_cq_entities(message_text[current_index:])
        if suffix_text:
            parsed_segments.append({"type": "text", "data": {"text": suffix_text}})

        return parsed_segments

    def _parse_cq_segment_data(self, raw_params: str) -> Dict[str, Any]:
        """解析单个 CQ 段中的参数串。

        Args:
            raw_params: 形如 ``,key=value,key2=value2`` 的原始参数字符串。

        Returns:
            Dict[str, Any]: 解析后的参数字典。
        """
        parsed_data: Dict[str, Any] = {}
        if not raw_params:
            return parsed_data

        for item in raw_params.lstrip(",").split(","):
            if not item or "=" not in item:
                continue
            key, value = item.split("=", 1)
            normalized_key = key.strip()
            if not normalized_key:
                continue
            decoded_value = self._decode_cq_entities(value)
            parsed_data[normalized_key] = self._normalize_numeric_segment_value(decoded_value)

        return parsed_data

    @staticmethod
    def _decode_cq_entities(text: str) -> str:
        """解码 CQ 码中的 HTML 风格转义实体。

        Args:
            text: 待解码的 CQ 文本。

        Returns:
            str: 解码后的普通文本。
        """
        return text.replace("&amp;", "&").replace("&#91;", "[").replace("&#93;", "]").replace("&#44;", ",")

    @staticmethod
    def _encode_binary(binary_data: bytes) -> str:
        """将二进制内容编码为 Base64 字符串。

        Args:
            binary_data: 待编码的二进制内容。

        Returns:
            str: Base64 编码字符串。
        """
        return base64.b64encode(binary_data).decode("utf-8")

    @staticmethod
    def _decode_binary(binary_base64: str) -> bytes:
        """将 Base64 字符串解码为二进制内容。

        Args:
            binary_base64: Base64 字符串。

        Returns:
            bytes: 解码后的二进制内容。
        """
        return base64.b64decode(binary_base64)

    @staticmethod
    def _normalize_numeric_segment_value(value: Any) -> Any:
        """将可安全识别的数字字符串转为整数。

        Args:
            value: 原始字段值。

        Returns:
            Any: 规范化后的字段值。
        """
        if isinstance(value, str):
            stripped_value = value.strip()
            if stripped_value.isdigit():
                return int(stripped_value)
            return stripped_value
        return value
