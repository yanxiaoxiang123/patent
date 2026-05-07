import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  isStrictTemplate,
  isIPCTemplate,
  getMessageContent,
  shouldClearContextMessages,
  shouldUseTemplateId,
  buildRequestBody,
  type TemplateId,
  type AIRequestBody,
  type Message
} from '@/utils/templateProcessor'

/**
 * Template Processing Logic Tests
 *
 * User Story:
 * As a user, I want all four patent templates (id=1,2,3,5) to behave consistently,
 * so that the AI response follows the same pattern regardless of which template I choose.
 *
 * All templates should:
 * - Use template_id parameter
 * - Clear conversation history (contextMessages)
 * - Handle empty user message appropriately
 */

describe('Template Processing Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('isStrictTemplate', () => {
    it('should return true for template id=1 (普通案例审核)', () => {
      expect(isStrictTemplate(1)).toBe(true)
    })

    it('should return true for template id=3 (专案案例审核)', () => {
      expect(isStrictTemplate(3)).toBe(true)
    })

    it('should return true for template id=2 (专利审核指导)', () => {
      expect(isStrictTemplate(2)).toBe(true)
    })

    it('should return true for template id=5 (IPC 分类指导)', () => {
      expect(isStrictTemplate(5)).toBe(true)
    })

    it('should return false for null template id', () => {
      expect(isStrictTemplate(null)).toBe(false)
    })

    it('should return false for invalid template id', () => {
      expect(isStrictTemplate(99)).toBe(false)
    })

    it('should return false for template id=4 (not a valid template)', () => {
      expect(isStrictTemplate(4)).toBe(false)
    })
  })

  describe('isIPCTemplate', () => {
    it('should return true for template id=5', () => {
      expect(isIPCTemplate(5)).toBe(true)
    })

    it('should return false for template id=1', () => {
      expect(isIPCTemplate(1)).toBe(false)
    })

    it('should return false for template id=2', () => {
      expect(isIPCTemplate(2)).toBe(false)
    })

    it('should return false for template id=3', () => {
      expect(isIPCTemplate(3)).toBe(false)
    })

    it('should return false for null', () => {
      expect(isIPCTemplate(null)).toBe(false)
    })
  })

  describe('shouldClearContextMessages', () => {
    it('should return true for template 1', () => {
      expect(shouldClearContextMessages(1)).toBe(true)
    })

    it('should return true for template 2', () => {
      expect(shouldClearContextMessages(2)).toBe(true)
    })

    it('should return true for template 3', () => {
      expect(shouldClearContextMessages(3)).toBe(true)
    })

    it('should return true for template 5', () => {
      expect(shouldClearContextMessages(5)).toBe(true)
    })

    it('should return false for null template id', () => {
      expect(shouldClearContextMessages(null)).toBe(false)
    })

    it('should return false for invalid template id', () => {
      expect(shouldClearContextMessages(99)).toBe(false)
    })
  })

  describe('shouldUseTemplateId', () => {
    it('should return true for template 1', () => {
      expect(shouldUseTemplateId(1)).toBe(true)
    })

    it('should return true for template 2', () => {
      expect(shouldUseTemplateId(2)).toBe(true)
    })

    it('should return true for template 3', () => {
      expect(shouldUseTemplateId(3)).toBe(true)
    })

    it('should return true for template 5', () => {
      expect(shouldUseTemplateId(5)).toBe(true)
    })

    it('should return false for null template id', () => {
      expect(shouldUseTemplateId(null)).toBe(false)
    })
  })

  describe('getMessageContent', () => {
    describe('strict templates (1, 2, 3, 5)', () => {
      it('should return empty string when no text for template 1', () => {
        const content = getMessageContent(1, false)
        expect(content).toBe('')
      })

      it('should return empty string when no text for template 2', () => {
        const content = getMessageContent(2, false)
        expect(content).toBe('')
      })

      it('should return empty string when no text for template 3', () => {
        const content = getMessageContent(3, false)
        expect(content).toBe('')
      })

      it('should return empty string when no text for template 5', () => {
        const content = getMessageContent(5, false)
        expect(content).toBe('')
      })

      it('should return user prompt when has text', () => {
        const content = getMessageContent(1, true, '自定义问题')
        expect(content).toBe('自定义问题')
      })
    })

    describe('IPC template (5) special handling', () => {
      it('should return IPC-specific message when no text', () => {
        const content = getMessageContent(5, false)
        expect(content).toContain('IPC 分类')
      })

      it('should return user prompt when has text', () => {
        const content = getMessageContent(5, true, '关于IPC的特殊问题')
        expect(content).toBe('关于IPC的特殊问题')
      })
    })

    describe('no template (free chat)', () => {
      it('should return default guidance message when no template', () => {
        const content = getMessageContent(null, false)
        expect(content).toContain('整体概览')
      })

      it('should return user prompt when has text', () => {
        const content = getMessageContent(null, true, '自定义问题')
        expect(content).toBe('自定义问题')
      })
    })
  })

  describe('buildRequestBody', () => {
    const mockContextMessages: Message[] = [
      { role: 'user', content: '第一个问题' },
      { role: 'assistant', content: '第一个回答' }
    ]

    it('should include template_id for template 1', () => {
      const body = buildRequestBody(1, '', [])
      expect(body.template_id).toBe(1)
    })

    it('should include template_id for template 2', () => {
      const body = buildRequestBody(2, '', [])
      expect(body.template_id).toBe(2)
    })

    it('should include template_id for template 3', () => {
      const body = buildRequestBody(3, '', [])
      expect(body.template_id).toBe(3)
    })

    it('should include template_id for template 5', () => {
      const body = buildRequestBody(5, 'IPC question', [])
      expect(body.template_id).toBe(5)
    })

    it('should NOT include template_id when templateId is null', () => {
      const body = buildRequestBody(null, 'user message', mockContextMessages)
      expect(body.template_id).toBeUndefined()
    })

    it('should NOT include system prompt for strict templates', () => {
      const body = buildRequestBody(1, '', [])
      const hasSystemPrompt = body.messages.some(m => m.role === 'system')
      expect(hasSystemPrompt).toBe(false)
    })

    it('should include system prompt for non-strict templates', () => {
      const body = buildRequestBody(null, 'user message', mockContextMessages)
      const hasSystemPrompt = body.messages.some(m => m.role === 'system')
      expect(hasSystemPrompt).toBe(true)
    })

    it('should include session_id when provided', () => {
      const body = buildRequestBody(1, '', [], 'session-123')
      expect(body.session_id).toBe('session-123')
    })

    it('should include document_id when provided', () => {
      const body = buildRequestBody(1, '', [], null, 'doc-456')
      expect(body.document_id).toBe('doc-456')
    })

    it('should have correct model and stream settings', () => {
      const body = buildRequestBody(1, '', [])
      expect(body.model).toBe('qwen3:8b')
      expect(body.stream).toBe(true)
      expect(body.passthrough).toBe(false)
    })

    it('should have only user message for strict templates with empty context', () => {
      const body = buildRequestBody(1, 'user message', [])
      expect(body.messages.length).toBe(1)
      expect(body.messages[0].role).toBe('user')
      expect(body.messages[0].content).toBe('user message')
    })

    it('should preserve context messages for strict templates when provided', () => {
      const body = buildRequestBody(1, 'new message', mockContextMessages)
      expect(body.messages.length).toBe(3)
      expect(body.messages[0].role).toBe('user')
      expect(body.messages[1].role).toBe('assistant')
      expect(body.messages[2].role).toBe('user')
      expect(body.messages[2].content).toBe('new message')
    })
  })

  describe('Template Consistency', () => {
    it('all four templates should have consistent strict behavior', () => {
      const templates: TemplateId[] = [1, 2, 3, 5]
      const results = templates.map(id => ({
        templateId: id,
        isStrict: isStrictTemplate(id),
        usesTemplateId: shouldUseTemplateId(id),
        clearsContext: shouldClearContextMessages(id)
      }))

      // All templates should have the same behavior
      results.forEach(result => {
        expect(result.isStrict).toBe(true)
        expect(result.usesTemplateId).toBe(true)
        expect(result.clearsContext).toBe(true)
      })
    })

    it('template_id should be included in request for all four templates', () => {
      const templates: TemplateId[] = [1, 2, 3, 5]
      templates.forEach(templateId => {
        const body = buildRequestBody(templateId, '', [])
        expect(body.template_id).toBe(templateId)
      })
    })

    it('all four templates should not include system prompt', () => {
      const templates: TemplateId[] = [1, 2, 3, 5]
      templates.forEach(templateId => {
        const body = buildRequestBody(templateId, '', [])
        const hasSystemPrompt = body.messages.some(m => m.role === 'system')
        expect(hasSystemPrompt).toBe(false)
      })
    })
  })
})
