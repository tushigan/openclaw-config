"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = void 0;exports.n = handleFeishuSubagentEnded;exports.r = handleFeishuSubagentSpawning;exports.t = handleFeishuSubagentDeliveryTarget;var _rolldownRuntimeDUslC3ob = require("./rolldown-runtime-DUslC3ob.js");
var _conversationIdDWS3Ep2A = require("./conversation-id-DWS3Ep2A.js");
var _targetsJMFJRKSe = require("./targets-JMFJRKSe.js");
var _threadBindingsBmS6TLes = require("./thread-bindings-BmS6TLes.js");
var _textRuntime = require("openclaw/plugin-sdk/text-runtime");
//#region extensions/feishu/src/subagent-hooks.ts
var subagent_hooks_exports = exports.i = /* @__PURE__ */(0, _rolldownRuntimeDUslC3ob.t)({
  handleFeishuSubagentDeliveryTarget: () => handleFeishuSubagentDeliveryTarget,
  handleFeishuSubagentEnded: () => handleFeishuSubagentEnded,
  handleFeishuSubagentSpawning: () => handleFeishuSubagentSpawning
});
function summarizeError(err) {
  if (err instanceof Error) return err.message;
  if (typeof err === "string") return err;
  return "error";
}
function stripProviderPrefix(raw) {
  return raw.replace(/^(feishu|lark):/i, "").trim();
}
function resolveFeishuRequesterConversation(params) {
  const manager = (0, _threadBindingsBmS6TLes.r)(params.accountId);
  if (!manager) return null;
  const rawTo = params.to?.trim();
  const withoutProviderPrefix = rawTo ? stripProviderPrefix(rawTo) : "";
  const normalizedTarget = rawTo ? (0, _targetsJMFJRKSe.r)(rawTo) : null;
  const threadId = params.threadId != null && params.threadId !== "" ? String(params.threadId).trim() : "";
  const isChatTarget = /^(chat|group|channel):/i.test(withoutProviderPrefix);
  const parsedRequesterTopic = normalizedTarget && threadId && isChatTarget ? (0, _conversationIdDWS3Ep2A.r)({
    conversationId: (0, _conversationIdDWS3Ep2A.t)({
      chatId: normalizedTarget,
      scope: "group_topic",
      topicId: threadId
    }),
    parentConversationId: normalizedTarget
  }) : null;
  const requesterSessionKey = params.requesterSessionKey?.trim();
  if (requesterSessionKey) {
    const existingBindings = manager.listBySessionKey(requesterSessionKey);
    if (existingBindings.length === 1) {
      const existing = existingBindings[0];
      return {
        accountId: existing.accountId,
        conversationId: existing.conversationId,
        parentConversationId: existing.parentConversationId
      };
    }
    if (existingBindings.length > 1) {
      if (rawTo && normalizedTarget && !threadId && !isChatTarget) {
        const directMatches = existingBindings.filter((entry) => entry.accountId === manager.accountId && entry.conversationId === normalizedTarget && !entry.parentConversationId);
        if (directMatches.length === 1) {
          const existing = directMatches[0];
          return {
            accountId: existing.accountId,
            conversationId: existing.conversationId,
            parentConversationId: existing.parentConversationId
          };
        }
        return null;
      }
      if (parsedRequesterTopic) {
        const matchingTopicBindings = existingBindings.filter((entry) => {
          const parsed = (0, _conversationIdDWS3Ep2A.r)({
            conversationId: entry.conversationId,
            parentConversationId: entry.parentConversationId
          });
          return parsed?.chatId === parsedRequesterTopic.chatId && parsed?.topicId === parsedRequesterTopic.topicId;
        });
        if (matchingTopicBindings.length === 1) {
          const existing = matchingTopicBindings[0];
          return {
            accountId: existing.accountId,
            conversationId: existing.conversationId,
            parentConversationId: existing.parentConversationId
          };
        }
        const senderScopedTopicBindings = matchingTopicBindings.filter((entry) => {
          return (0, _conversationIdDWS3Ep2A.r)({
            conversationId: entry.conversationId,
            parentConversationId: entry.parentConversationId
          })?.scope === "group_topic_sender";
        });
        if (senderScopedTopicBindings.length === 1 && matchingTopicBindings.length === senderScopedTopicBindings.length) {
          const existing = senderScopedTopicBindings[0];
          return {
            accountId: existing.accountId,
            conversationId: existing.conversationId,
            parentConversationId: existing.parentConversationId
          };
        }
        return null;
      }
    }
  }
  if (!rawTo) return null;
  if (!normalizedTarget) return null;
  if (threadId) {
    if (!isChatTarget) return null;
    return {
      accountId: manager.accountId,
      conversationId: (0, _conversationIdDWS3Ep2A.t)({
        chatId: normalizedTarget,
        scope: "group_topic",
        topicId: threadId
      }),
      parentConversationId: normalizedTarget
    };
  }
  if (isChatTarget) return null;
  return {
    accountId: manager.accountId,
    conversationId: normalizedTarget
  };
}
function resolveFeishuDeliveryOrigin(params) {
  const deliveryTo = params.deliveryTo?.trim();
  const deliveryThreadId = params.deliveryThreadId?.trim();
  if (deliveryTo) return {
    channel: "feishu",
    accountId: params.accountId,
    to: deliveryTo,
    ...(deliveryThreadId ? { threadId: deliveryThreadId } : {})
  };
  const parsed = (0, _conversationIdDWS3Ep2A.r)({
    conversationId: params.conversationId,
    parentConversationId: params.parentConversationId
  });
  if (parsed?.topicId) return {
    channel: "feishu",
    accountId: params.accountId,
    to: `chat:${params.parentConversationId?.trim() || parsed.chatId}`,
    threadId: parsed.topicId
  };
  return {
    channel: "feishu",
    accountId: params.accountId,
    to: `user:${params.conversationId}`
  };
}
function resolveMatchingChildBinding(params) {
  const manager = (0, _threadBindingsBmS6TLes.r)(params.accountId);
  if (!manager) return null;
  const childBindings = manager.listBySessionKey(params.childSessionKey.trim());
  if (childBindings.length === 0) return null;
  const requesterConversation = resolveFeishuRequesterConversation({
    accountId: manager.accountId,
    to: params.requesterOrigin?.to,
    threadId: params.requesterOrigin?.threadId,
    requesterSessionKey: params.requesterSessionKey
  });
  if (requesterConversation) {
    const matched = childBindings.find((entry) => entry.accountId === requesterConversation.accountId && entry.conversationId === requesterConversation.conversationId && (0, _textRuntime.normalizeOptionalString)(entry.parentConversationId) === (0, _textRuntime.normalizeOptionalString)(requesterConversation.parentConversationId));
    if (matched) return matched;
  }
  return childBindings.length === 1 ? childBindings[0] : null;
}
async function handleFeishuSubagentSpawning(event, ctx) {
  if (!event.threadRequested) return;
  if ((0, _textRuntime.normalizeOptionalLowercaseString)(event.requester?.channel) !== "feishu") return;
  const manager = (0, _threadBindingsBmS6TLes.r)(event.requester?.accountId);
  if (!manager) return {
    status: "error",
    error: "Feishu current-conversation binding is unavailable because the Feishu account monitor is not active."
  };
  const conversation = resolveFeishuRequesterConversation({
    accountId: event.requester?.accountId,
    to: event.requester?.to,
    threadId: event.requester?.threadId,
    requesterSessionKey: ctx.requesterSessionKey
  });
  if (!conversation) return {
    status: "error",
    error: "Feishu current-conversation binding is only available in direct messages or topic conversations."
  };
  try {
    if (!manager.bindConversation({
      conversationId: conversation.conversationId,
      parentConversationId: conversation.parentConversationId,
      targetKind: "subagent",
      targetSessionKey: event.childSessionKey,
      metadata: {
        agentId: event.agentId,
        label: event.label,
        boundBy: "system",
        deliveryTo: event.requester?.to,
        deliveryThreadId: event.requester?.threadId != null && event.requester.threadId !== "" ? String(event.requester.threadId) : void 0
      }
    })) return {
      status: "error",
      error: "Unable to bind this Feishu conversation to the spawned subagent session. Session mode is unavailable for this target."
    };
    return {
      status: "ok",
      threadBindingReady: true
    };
  } catch (err) {
    return {
      status: "error",
      error: `Feishu conversation bind failed: ${summarizeError(err)}`
    };
  }
}
function handleFeishuSubagentDeliveryTarget(event) {
  if (!event.expectsCompletionMessage) return;
  if ((0, _textRuntime.normalizeOptionalLowercaseString)(event.requesterOrigin?.channel) !== "feishu") return;
  const binding = resolveMatchingChildBinding({
    accountId: event.requesterOrigin?.accountId,
    childSessionKey: event.childSessionKey,
    requesterSessionKey: event.requesterSessionKey,
    requesterOrigin: {
      to: event.requesterOrigin?.to,
      threadId: event.requesterOrigin?.threadId
    }
  });
  if (!binding) return;
  return { origin: resolveFeishuDeliveryOrigin({
      conversationId: binding.conversationId,
      parentConversationId: binding.parentConversationId,
      accountId: binding.accountId,
      deliveryTo: binding.deliveryTo,
      deliveryThreadId: binding.deliveryThreadId
    }) };
}
function handleFeishuSubagentEnded(event) {
  (0, _threadBindingsBmS6TLes.r)(event.accountId)?.unbindBySessionKey(event.targetSessionKey);
}
//#endregion /* v9-297cf733e0bd7883 */
