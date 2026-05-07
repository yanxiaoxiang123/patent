import { ref } from "vue";
import { shallowMount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SimplePatentChat from "@/views/SimplePatentChat.vue";

vi.mock("element-plus", () => ({
  ElMessage: {
    warning: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@element-plus/icons-vue", () => ({
  Files: {},
}));

vi.mock("ant-design-vue", () => ({
  Badge: {},
  Button: {},
  Flex: {},
  Typography: {},
}));

vi.mock("@ant-design/icons-vue", () => ({
  CloudUploadOutlined: {},
  CloseOutlined: {},
  PaperClipOutlined: {},
  PlusOutlined: {},
}));

vi.mock("ant-design-x-vue", () => ({
  Attachments: {},
  Conversations: {},
  Prompts: {},
  Sender: {},
  Welcome: {},
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    initUser: vi.fn(),
    isAdmin: false,
  }),
}));

vi.mock("@/composables/useThinking", () => ({
  useThinking: () => ({
    toggleThinking: vi.fn(),
    isThinkingVisible: vi.fn(() => false),
    streamingThinkingExpanded: { value: false },
    toggleStreamingThinking: vi.fn(),
  }),
}));

vi.mock("@/composables/useChatSession", () => ({
  useChatSession: () => ({
    sessions: ref([]),
    currentSessionId: ref(null),
    messages: ref([]),
    loadSessions: vi.fn(),
    createSession: vi.fn(),
    deleteSession: vi.fn(),
    refreshSessions: vi.fn(),
    switchSession: vi.fn(),
  }),
}));

vi.mock("@/composables/useFileUpload", () => ({
  useFileUpload: () => ({
    uploadedFiles: ref([]),
    attachmentItems: ref([]),
    isAttachmentsReady: ref(true),
    isAttachmentsParsing: ref(false),
    handleAttachmentCustomRequest: vi.fn(),
    handleAttachmentRemove: vi.fn(),
    handleAttachmentsChange: vi.fn(),
    loadUploadedFiles: vi.fn(),
  }),
}));

vi.mock("@/composables/useCopyToClipboard", () => ({
  useClipboard: () => ({
    copy: vi.fn(),
  }),
}));

describe("SimplePatentChat layout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the sidebar toggle inside the top bar instead of overlaying the page corner", () => {
    const wrapper = shallowMount(SimplePatentChat, {
      global: {
        mocks: {
          $router: {
            push: vi.fn(),
          },
        },
        stubs: {
          Transition: false,
          TransitionGroup: false,
          MessageBubble: true,
          Welcome: true,
          Prompts: true,
          Sender: true,
          Attachments: true,
          Conversations: true,
          Badge: true,
          Button: true,
          Flex: true,
          Typography: true,
          "Typography.Text": true,
          "Typography.Title": true,
          "Sender.Header": true,
          "el-button": true,
          "el-dialog": true,
          "el-form": true,
          "el-form-item": true,
          "el-select": true,
          "el-option": true,
          "el-tooltip": true,
          "el-icon": true,
        },
      },
    });

    expect(wrapper.find(".chat-top-bar .sidebar-toggle").exists()).toBe(true);
    expect(wrapper.find(".patent-chat > .sidebar-toggle").exists()).toBe(false);
  });
});
