"""NapCat 消息与互动 API 端点。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from maibot_sdk import API

from .support import NapCatApiIdInput, NapCatApiParamsInput, NapCatApiSupportMixin


class NapCatMessageApiMixin(NapCatApiSupportMixin):
    """NapCat 消息、互动与 AI 相关 API。"""

    @API("adapter.napcat.message.send_poke", description="发送戳一戳", version="1", public=True)
    async def api_send_poke(
        self,
        qq_id: NapCatApiIdInput,
        group_id: Optional[NapCatApiIdInput] = None,
    ) -> Dict[str, Any]:
        """发送戳一戳。

        Args:
            qq_id: 目标用户号。
            group_id: 可选群号。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        normalized_group_id: Optional[int] = None
        if group_id is not None and str(group_id).strip():
            normalized_group_id = self._normalize_positive_int(group_id, "group_id")
        return await self._require_query_service().send_poke(
            user_id=self._normalize_positive_int(qq_id, "qq_id"),
            group_id=normalized_group_id,
        )

    @API("adapter.napcat.message.delete_msg", description="撤回消息", version="1", public=True)
    async def api_delete_msg(self, message_id: NapCatApiIdInput) -> Dict[str, Any]:
        """撤回消息。

        Args:
            message_id: 消息 ID。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._require_query_service().delete_message(
            message_id=self._normalize_positive_int(message_id, "message_id")
        )

    @API("adapter.napcat.message.send_group_ai_record", description="发送群 AI 语音", version="1", public=True)
    async def api_send_group_ai_record(
        self,
        group_id: NapCatApiIdInput,
        character: object,
        text: object,
    ) -> Dict[str, Any]:
        """发送群 AI 语音。

        Args:
            group_id: 群号。
            character: 角色标识。
            text: 语音文本。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._require_query_service().send_group_ai_record(
            group_id=self._normalize_positive_int(group_id, "group_id"),
            character=self._normalize_non_empty_string(character, "character"),
            text=self._normalize_non_empty_string(text, "text"),
        )

    @API("adapter.napcat.message.set_msg_emoji_like", description="给消息贴表情", version="1", public=True)
    async def api_set_msg_emoji_like(
        self,
        message_id: NapCatApiIdInput,
        emoji_id: NapCatApiIdInput,
        set: bool = True,
    ) -> Dict[str, Any]:
        """给消息贴表情或取消表情。

        Args:
            message_id: 消息 ID。
            emoji_id: 表情 ID。
            set: 是否设置为已贴表情。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._require_query_service().set_message_emoji_like(
            message_id=self._normalize_positive_int(message_id, "message_id"),
            emoji_id=self._normalize_positive_int(emoji_id, "emoji_id"),
            set_like=bool(set),
        )

    @API("adapter.napcat.message.get_msg", description="获取消息详情", version="1", public=True)
    async def api_get_msg(self, message_id: NapCatApiIdInput) -> Optional[Dict[str, Any]]:
        """获取消息详情。

        Args:
            message_id: 消息 ID。

        Returns:
            Optional[Dict[str, Any]]: 消息详情字典；失败时返回 ``None``。
        """
        return await self._require_query_service().get_message_detail(
            str(self._normalize_positive_int(message_id, "message_id"))
        )

    @API("adapter.napcat.message.get_forward_msg", description="获取合并转发消息", version="1", public=True)
    async def api_get_forward_msg(self, message_id: object) -> Optional[Dict[str, Any]]:
        """获取合并转发消息详情。

        Args:
            message_id: 合并转发消息 ID。

        Returns:
            Optional[Dict[str, Any]]: 合并转发消息详情；失败时返回 ``None``。
        """
        return await self._require_query_service().get_forward_message(
            self._normalize_non_empty_string(message_id, "message_id")
        )

    @API("adapter.napcat.message.ark_share_group", description="分享群 (Ark)", version="1", public=True)
    async def api_action_ark_share_group(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``ArkShareGroup`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("ArkShareGroup", params)

    @API("adapter.napcat.message.ark_share_peer", description="分享用户 (Ark)", version="1", public=True)
    async def api_action_ark_share_peer(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``ArkSharePeer`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("ArkSharePeer", params)

    @API(
        "adapter.napcat.message.click_inline_keyboard_button", description="点击内联键盘按钮", version="1", public=True
    )
    async def api_action_click_inline_keyboard_button(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``click_inline_keyboard_button`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("click_inline_keyboard_button", params)

    @API("adapter.napcat.message.fetch_emoji_like", description="获取表情点赞详情", version="1", public=True)
    async def api_action_fetch_emoji_like(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``fetch_emoji_like`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("fetch_emoji_like", params)

    @API("adapter.napcat.message.forward_friend_single_msg", description="转发单条消息", version="1", public=True)
    async def api_action_forward_friend_single_msg(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``forward_friend_single_msg`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("forward_friend_single_msg", params)

    @API("adapter.napcat.message.forward_group_single_msg", description="转发单条消息", version="1", public=True)
    async def api_action_forward_group_single_msg(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``forward_group_single_msg`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("forward_group_single_msg", params)

    @API("adapter.napcat.message.friend_poke", description="发送戳一戳", version="1", public=True)
    async def api_action_friend_poke(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``friend_poke`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("friend_poke", params)

    @API("adapter.napcat.message.get_ai_record", description="获取 AI 语音", version="1", public=True)
    async def api_action_get_ai_record(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``get_ai_record`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("get_ai_record", params)

    @API("adapter.napcat.message.get_emoji_likes", description="获取消息表情点赞列表", version="1", public=True)
    async def api_action_get_emoji_likes(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``get_emoji_likes`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("get_emoji_likes", params)

    @API("adapter.napcat.message.get_friend_msg_history", description="获取好友历史消息", version="1", public=True)
    async def api_action_get_friend_msg_history(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``get_friend_msg_history`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("get_friend_msg_history", params)

    @API("adapter.napcat.message.get_group_msg_history", description="获取群历史消息", version="1", public=True)
    async def api_action_get_group_msg_history(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``get_group_msg_history`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("get_group_msg_history", params)

    @API("adapter.napcat.message.mark_all_as_read", description="标记所有消息已读", version="1", public=True)
    async def api_action_mark_all_as_read(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``_mark_all_as_read`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("_mark_all_as_read", params)

    @API("adapter.napcat.message.mark_group_msg_as_read", description="标记群聊已读", version="1", public=True)
    async def api_action_mark_group_msg_as_read(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``mark_group_msg_as_read`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("mark_group_msg_as_read", params)

    @API("adapter.napcat.message.mark_msg_as_read", description="标记消息已读 (Go-CQHTTP)", version="1", public=True)
    async def api_action_mark_msg_as_read(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``mark_msg_as_read`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("mark_msg_as_read", params)

    @API("adapter.napcat.message.mark_private_msg_as_read", description="标记私聊已读", version="1", public=True)
    async def api_action_mark_private_msg_as_read(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``mark_private_msg_as_read`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("mark_private_msg_as_read", params)

    @API("adapter.napcat.message.send_ark_share", description="分享用户 (Ark)", version="1", public=True)
    async def api_action_send_ark_share(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``send_ark_share`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("send_ark_share", params)

    @API("adapter.napcat.message.send_forward_msg", description="发送合并转发消息", version="1", public=True)
    async def api_action_send_forward_msg(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``send_forward_msg`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("send_forward_msg", params)

    @API("adapter.napcat.message.send_group_ark_share", description="分享群 (Ark)", version="1", public=True)
    async def api_action_send_group_ark_share(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``send_group_ark_share`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("send_group_ark_share", params)

    @API("adapter.napcat.message.send_group_forward_msg", description="发送群合并转发消息", version="1", public=True)
    async def api_action_send_group_forward_msg(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``send_group_forward_msg`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("send_group_forward_msg", params)

    @API("adapter.napcat.message.send_msg", description="发送消息", version="1", public=True)
    async def api_action_send_msg(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``send_msg`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("send_msg", params)

    @API(
        "adapter.napcat.message.send_private_forward_msg", description="发送私聊合并转发消息", version="1", public=True
    )
    async def api_action_send_private_forward_msg(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``send_private_forward_msg`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("send_private_forward_msg", params)

    @API("adapter.napcat.message.send_private_msg", description="发送私聊消息", version="1", public=True)
    async def api_action_send_private_msg(self, params: NapCatApiParamsInput = None) -> Dict[str, Any]:
        """调用 NapCat 的 ``send_private_msg`` 动作。

        Args:
            params: 传递给 NapCat 的动作参数字典；具体字段请参考 NapCat 官方文档。

        Returns:
            Dict[str, Any]: NapCat 返回的原始响应字典。
        """
        return await self._call_napcat_action("send_private_msg", params)
