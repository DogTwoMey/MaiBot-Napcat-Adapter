"""NapCat 入站消息编解码。"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple
from uuid import uuid4

import hashlib
import time

from ...qq_emoji_list import QQ_FACE
from ...services import NapCatQueryService
from .cards import NapCatInboundCardMixin
from .text import NapCatInboundTextMixin


class NapCatInboundCodec(NapCatInboundCardMixin, NapCatInboundTextMixin):
    """NapCat 入站消息编码器。"""

    def __init__(self, logger: Any, query_service: NapCatQueryService) -> None:
        """初始化入站消息编码器。

        Args:
            logger: 插件日志对象。
            query_service: QQ 查询服务。
        """
        self._logger = logger
        self._query_service = query_service

    async def build_message_dict(
        self,
        payload: Mapping[str, Any],
        self_id: str,
        sender_user_id: str,
        sender: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """构造 Host 侧可接受的 ``MessageDict``。

        Args:
            payload: NapCat 原始消息事件。
            self_id: 当前机器人账号 ID。
            sender_user_id: 发送者用户 ID。
            sender: 发送者信息字典。

        Returns:
            Dict[str, Any]: 规范化后的 ``MessageDict``。
        """
        message_type = str(payload.get("message_type") or "").strip() or "private"
        group_id = str(payload.get("group_id") or "").strip()
        group_name = str(payload.get("group_name") or "").strip() or (f"group_{group_id}" if group_id else "")
        user_nickname = str(sender.get("nickname") or sender.get("card") or sender_user_id).strip() or sender_user_id
        user_cardname = str(sender.get("card") or "").strip() or None

        raw_message, is_at = await self.convert_segments(payload, self_id)
        raw_message_text = str(payload.get("raw_message") or "").strip()
        if not raw_message:
            raw_message = [{"type": "text", "data": raw_message_text or "[unsupported]"}]

        plain_text = self.build_plain_text(raw_message, raw_message_text)
        timestamp_seconds = payload.get("time")
        if not isinstance(timestamp_seconds, (int, float)):
            timestamp_seconds = time.time()

        additional_config: Dict[str, Any] = {"self_id": self_id, "napcat_message_type": message_type}
        if group_id:
            additional_config["platform_io_target_group_id"] = group_id
        else:
            additional_config["platform_io_target_user_id"] = sender_user_id

        message_info: Dict[str, Any] = {
            "user_info": {
                "user_id": sender_user_id,
                "user_nickname": user_nickname,
                "user_cardname": user_cardname,
            },
            "additional_config": additional_config,
        }
        if group_id:
            message_info["group_info"] = {"group_id": group_id, "group_name": group_name}

        message_id = str(payload.get("message_id") or f"napcat-{uuid4().hex}").strip()
        return {
            "message_id": message_id,
            "timestamp": str(float(timestamp_seconds)),
            "platform": "qq",
            "message_info": message_info,
            "raw_message": raw_message,
            "is_mentioned": is_at,
            "is_at": is_at,
            "is_emoji": False,
            "is_picture": False,
            "is_command": plain_text.startswith("/"),
            "is_notify": False,
            "session_id": "",
            "processed_plain_text": plain_text,
            "display_message": plain_text,
        }

    async def convert_segments(self, payload: Mapping[str, Any], self_id: str) -> Tuple[List[Dict[str, Any]], bool]:
        """将 OneBot 消息段转换为 Host 消息段结构。

        Args:
            payload: OneBot 原始消息事件。
            self_id: 当前机器人账号 ID。

        Returns:
            Tuple[List[Dict[str, Any]], bool]: 转换后的消息段列表，以及是否 @ 到当前机器人。
        """
        message_payload = payload.get("message")
        if isinstance(message_payload, str):
            parsed_message_payload = self._parse_cq_message_text(message_payload)
            if parsed_message_payload:
                message_payload = parsed_message_payload
            else:
                normalized_text = self._decode_cq_entities(message_payload).strip()
                return ([{"type": "text", "data": normalized_text}] if normalized_text else []), False

        if not isinstance(message_payload, list):
            return [], False

        converted_segments: List[Dict[str, Any]] = []
        is_at = False
        for segment in message_payload:
            if not isinstance(segment, Mapping):
                continue

            segment_type = str(segment.get("type") or "").strip()
            segment_data = segment.get("data", {})
            if not isinstance(segment_data, Mapping):
                segment_data = {}

            if segment_type == "text":
                if text_value := str(segment_data.get("text") or ""):
                    converted_segments.append({"type": "text", "data": text_value})
                continue

            if segment_type == "at":
                if target_user_id := str(segment_data.get("qq") or "").strip():
                    converted_segments.append(
                        {
                            "type": "at",
                            "data": {
                                "target_user_id": target_user_id,
                                "target_user_nickname": None,
                                "target_user_cardname": None,
                            },
                        }
                    )
                    if self_id and target_user_id == self_id:
                        is_at = True
                continue

            if segment_type == "reply":
                if reply_segment := await self._build_reply_segment(segment_data):
                    converted_segments.append(reply_segment)
                continue

            if segment_type == "face":
                converted_segments.append(self._build_face_text_segment(segment_data))
                continue

            if segment_type == "image":
                converted_segments.append(await self._build_image_like_segment(segment_data, is_emoji=False))
                continue

            if segment_type == "record":
                converted_segments.append(await self._build_record_segment(segment_data))
                continue

            if segment_type == "video":
                converted_segments.append(self._build_video_text_segment(segment_data))
                continue

            if segment_type == "file":
                converted_segments.append(self._build_file_text_segment(segment_data))
                continue

            if segment_type == "json":
                converted_segments.extend(await self._build_json_segments(segment_data))
                continue

            if segment_type == "forward":
                if forward_segment := await self._build_forward_segment(segment_data):
                    converted_segments.append(forward_segment)
                continue

            if segment_type in {"xml", "share"}:
                converted_segments.append({"type": "text", "data": f"[{segment_type}]"})

        return converted_segments, is_at

    async def _build_reply_segment(self, segment_data: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        """构造回复消息段。

        Args:
            segment_data: OneBot ``reply`` 段的 ``data`` 字典。

        Returns:
            Optional[Dict[str, Any]]: 转换后的回复消息段；缺少消息 ID 时返回 ``None``。
        """
        target_message_id = str(segment_data.get("id") or "").strip()
        if not target_message_id:
            return None

        message_detail = await self._query_service.get_message_detail(target_message_id)
        reply_payload: Dict[str, Any] = {"target_message_id": target_message_id}
        if message_detail is not None:
            sender = message_detail.get("sender", {})
            if not isinstance(sender, Mapping):
                sender = {}
            reply_payload["target_message_content"] = str(message_detail.get("raw_message") or "").strip() or None
            reply_payload["target_message_sender_id"] = (
                str(message_detail.get("user_id") or sender.get("user_id") or "").strip() or None
            )
            reply_payload["target_message_sender_nickname"] = str(sender.get("nickname") or "").strip() or None
            reply_payload["target_message_sender_cardname"] = str(sender.get("card") or "").strip() or None

        return {"type": "reply", "data": reply_payload}

    async def _build_image_like_segment(
        self,
        segment_data: Mapping[str, Any],
        is_emoji: bool,
    ) -> Dict[str, Any]:
        """构造图片或表情消息段。

        Args:
            segment_data: OneBot ``image`` 段的 ``data`` 字典。
            is_emoji: 是否按表情组件处理。

        Returns:
            Dict[str, Any]: 转换后的图片或表情消息段。
        """
        subtype = self._normalize_numeric_segment_value(segment_data.get("sub_type"))
        actual_is_emoji = is_emoji or (subtype is not None and subtype not in {0, 4, 9})

        image_url = str(segment_data.get("url") or "").strip()
        binary_data = await self._query_service.download_binary(image_url)
        if not binary_data:
            return {"type": "text", "data": "[emoji]" if actual_is_emoji else "[image]"}

        return {
            "type": "emoji" if actual_is_emoji else "image",
            "data": "",
            "hash": hashlib.sha256(binary_data).hexdigest(),
            "binary_data_base64": self._encode_binary(binary_data),
        }

    async def _build_record_segment(self, segment_data: Mapping[str, Any]) -> Dict[str, Any]:
        """构造语音消息段。

        Args:
            segment_data: OneBot ``record`` 段的 ``data`` 字典。

        Returns:
            Dict[str, Any]: 转换后的语音或占位文本消息段。
        """
        file_name = str(segment_data.get("file") or "").strip()
        file_id = str(segment_data.get("file_id") or "").strip() or None
        if not file_name:
            return {"type": "text", "data": "[voice]"}

        record_detail = await self._query_service.get_record_detail(file_name=file_name, file_id=file_id)
        if record_detail is None:
            return {"type": "text", "data": "[voice]"}

        record_base64 = str(record_detail.get("base64") or "").strip()
        if not record_base64:
            return {"type": "text", "data": "[voice]"}

        try:
            binary_data = self._decode_binary(record_base64)
        except Exception:
            return {"type": "text", "data": "[voice]"}

        return {
            "type": "voice",
            "data": "",
            "hash": hashlib.sha256(binary_data).hexdigest(),
            "binary_data_base64": self._encode_binary(binary_data),
        }

    def _build_face_text_segment(self, segment_data: Mapping[str, Any]) -> Dict[str, Any]:
        """构造 QQ 原生表情文本段。

        Args:
            segment_data: OneBot ``face`` 段的 ``data`` 字典。

        Returns:
            Dict[str, Any]: 转换后的文本消息段。
        """
        face_id = str(segment_data.get("id") or "").strip()
        face_text = QQ_FACE.get(face_id, "[表情]")
        return {"type": "text", "data": face_text}

    def _build_video_text_segment(self, segment_data: Mapping[str, Any]) -> Dict[str, Any]:
        """构造视频消息的可读文本段。

        Args:
            segment_data: OneBot ``video`` 段的 ``data`` 字典。

        Returns:
            Dict[str, Any]: 转换后的文本消息段。
        """
        file_name = str(segment_data.get("file") or "").strip()
        file_size = str(segment_data.get("file_size") or "").strip()
        parts: List[str] = []
        if file_name:
            parts.append(f"文件: {file_name}")
        if file_size:
            parts.append(f"大小: {file_size}")
        if parts:
            return {"type": "text", "data": f"[视频] {'，'.join(parts)}"}
        return {"type": "text", "data": "[视频]"}

    def _build_file_text_segment(self, segment_data: Mapping[str, Any]) -> Dict[str, Any]:
        """构造文件消息的可读文本段。

        Args:
            segment_data: OneBot ``file`` 段的 ``data`` 字典。

        Returns:
            Dict[str, Any]: 转换后的文本消息段。
        """
        file_name = str(segment_data.get("file") or segment_data.get("name") or "").strip()
        file_size = str(segment_data.get("file_size") or "").strip()
        file_url = str(segment_data.get("url") or "").strip()
        text_parts: List[str] = []
        if file_name:
            text_parts.append(file_name)
        if file_size:
            text_parts.append(f"大小: {file_size}")
        file_text = "[文件]"
        if text_parts:
            file_text = f"[文件] {'，'.join(text_parts)}"
        if file_url:
            file_text = f"{file_text}，链接: {file_url}"
        return {"type": "text", "data": file_text}

    async def _build_forward_segment(self, segment_data: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        """构造合并转发消息段。

        Args:
            segment_data: OneBot ``forward`` 段的 ``data`` 字典。

        Returns:
            Optional[Dict[str, Any]]: 转换后的合并转发消息段；失败时返回 ``None``。
        """
        message_id = str(segment_data.get("id") or "").strip()
        if not message_id:
            return None

        forward_detail = await self._query_service.get_forward_message(message_id)
        if forward_detail is None:
            return {"type": "text", "data": "[forward]"}

        messages = forward_detail.get("messages", [])
        if not isinstance(messages, list):
            return {"type": "text", "data": "[forward]"}

        forward_nodes: List[Dict[str, Any]] = []
        for forward_message in messages:
            if not isinstance(forward_message, Mapping):
                continue
            raw_content = forward_message.get("content", [])
            content_segments = await self._convert_forward_content(raw_content, "")
            sender = forward_message.get("sender", {})
            if not isinstance(sender, Mapping):
                sender = {}
            forward_nodes.append(
                {
                    "user_id": str(sender.get("user_id") or sender.get("uin") or "").strip() or None,
                    "user_nickname": str(sender.get("nickname") or sender.get("name") or "未知用户"),
                    "user_cardname": str(sender.get("card") or "").strip() or None,
                    "message_id": str(forward_message.get("message_id") or uuid4().hex),
                    "content": content_segments or [{"type": "text", "data": "[empty]"}],
                }
            )

        if not forward_nodes:
            return {"type": "text", "data": "[forward]"}
        return {"type": "forward", "data": forward_nodes}

    async def _convert_forward_content(self, raw_content: Any, self_id: str) -> List[Dict[str, Any]]:
        """转换转发节点内部的消息段列表。

        Args:
            raw_content: 转发节点原始内容。
            self_id: 当前机器人账号 ID。

        Returns:
            List[Dict[str, Any]]: 转换后的消息段列表。
        """
        pseudo_payload: Dict[str, Any] = {"message": raw_content}
        segments, _ = await self.convert_segments(pseudo_payload, self_id)
        return segments
