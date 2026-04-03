"""NapCat 出站消息编解码。"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple

from .segment_encoder import NapCatOutboundSegmentEncoder


class NapCatOutboundCodec:
    """NapCat 出站消息编码器。"""

    def __init__(self) -> None:
        """初始化出站消息编码器。"""
        self._segment_encoder = NapCatOutboundSegmentEncoder()

    def build_outbound_action(
        self,
        message: Mapping[str, Any],
        route: Mapping[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """为 Host 出站消息构造 OneBot 动作。

        Args:
            message: Host 侧标准 ``MessageDict``。
            route: Platform IO 路由信息。

        Returns:
            Tuple[str, Dict[str, Any]]: 动作名称与参数字典。

        Raises:
            ValueError: 当私聊出站缺少目标用户 ID 时抛出。
        """
        message_info = message.get("message_info", {})
        if not isinstance(message_info, Mapping):
            message_info = {}

        group_info = message_info.get("group_info", {})
        if not isinstance(group_info, Mapping):
            group_info = {}

        additional_config = message_info.get("additional_config", {})
        if not isinstance(additional_config, Mapping):
            additional_config = {}

        raw_message = message.get("raw_message", [])
        segments = self._segment_encoder.convert_segments(raw_message)

        if target_group_id := str(
            group_info.get("group_id") or additional_config.get("platform_io_target_group_id") or ""
        ).strip():
            return "send_group_msg", {"group_id": target_group_id, "message": segments}

        target_user_id = str(
            additional_config.get("platform_io_target_user_id")
            or additional_config.get("target_user_id")
            or route.get("target_user_id")
            or ""
        ).strip()
        if not target_user_id:
            raise ValueError("Outbound private message is missing target_user_id")

        return "send_private_msg", {"message": segments, "user_id": target_user_id}
