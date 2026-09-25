import json
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
from content.models import AIUsage
import nh3

logger = logging.getLogger(__name__)


class AIRateLimiter:
    """
    Per-user rate limiter for AI requests to prevent resource abuse and manage LLM costs.
    """
    @staticmethod
    def is_rate_limited(user_id: int, action: str = 'general', limit: Optional[int] = None) -> bool:
        if limit is None:
            limit = getattr(settings, 'AI_RATE_LIMIT_PER_MINUTE', 20)
        cache_key = f"ai_rate_limit_{user_id}_{action}"
        current_count = cache.get(cache_key, 0)
        return current_count >= limit

    @staticmethod
    def increment(user_id: int, action: str = 'general', timeout: int = 60) -> int:
        cache_key = f"ai_rate_limit_{user_id}_{action}"
        current_count = cache.get(cache_key, 0)
        if current_count == 0:
            cache.set(cache_key, 1, timeout=timeout)
            return 1
        else:
            try:
                new_count = cache.incr(cache_key)
            except ValueError:
                cache.set(cache_key, 1, timeout=timeout)
                new_count = 1
            return new_count


class AIService:
    """
    Reusable server-side AI Service Layer for OpenRouter LLM gateway integration.
    Abstracts provider credentials, rate limiting, structured outputs, and local NLP fallbacks.
    """

    def __init__(self, model: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None):
        self.api_key = getattr(settings, 'OPENROUTER_API_KEY', '')
        self.base_url = getattr(settings, 'OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1').rstrip('/')
        self.model = model or getattr(settings, 'AI_MODEL', 'openai/gpt-4o-mini')
        self.temperature = temperature if temperature is not None else getattr(settings, 'AI_TEMPERATURE', 0.7)
        self.max_tokens = max_tokens or getattr(settings, 'AI_MAX_TOKENS', 2000)
        self.provider = getattr(settings, 'AI_PROVIDER', 'openrouter')

    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes a server-side request to OpenRouter API gateway.
        Returns response dict containing 'content', 'usage', and 'raw'.
        """
        if not self.api_key:
            logger.info("OPENROUTER_API_KEY not configured. Invoking local fallback.")
            return {'error': 'NO_API_KEY', 'content': None, 'usage': {}}

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://blogsmonkey.com",
            "X-Title": "Blogs Monkey Editorial SaaS",
            "Content-Type": "application/json"
        }

        try:
            json_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=30) as response:
                resp_bytes = response.read()
                data = json.loads(resp_bytes.decode('utf-8'))
                
                content = data['choices'][0]['message']['content'] if 'choices' in data and data['choices'] else ''
                usage = data.get('usage', {})
                return {
                    'content': content,
                    'usage': usage,
                    'model': data.get('model', self.model),
                    'error': None
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8') if e.fp else str(e)
            logger.error(f"OpenRouter HTTPError {e.code}: {err_body}")
            return {'error': f"HTTP_{e.code}", 'content': None, 'detail': err_body, 'usage': {}}
        except Exception as e:
            logger.error(f"OpenRouter Request Exception: {str(e)}")
            return {'error': 'NETWORK_ERROR', 'content': None, 'detail': str(e), 'usage': {}}

    def _record_usage(
        self,
        user,
        feature: str,
        result: Dict[str, Any],
        error_msg: str = ''
    ):
        """
        Logs AI usage stats into database for cost monitoring & usage metrics.
        """
        if not user or not user.is_authenticated:
            return

        usage = result.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
        
        # Estimate cost ($0.15 / 1M prompt, $0.60 / 1M completion for gpt-4o-mini baseline)
        approx_cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)

        status_str = 'error' if result.get('error') else 'success'
        if error_msg:
            status_str = 'error'

        try:
            AIUsage.objects.create(
                user=user,
                feature=feature,
                model=result.get('model', self.model),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                approx_cost=approx_cost,
                status=status_str,
                error_message=error_msg or (result.get('error') or '')
            )
        except Exception as e:
            logger.warning(f"Failed to record AI usage: {str(e)}")

    def chat(self, user_message: str, history: List[Dict[str, str]] = None, context: Dict[str, Any] = None, user=None) -> Dict[str, Any]:
        """
        Feature 1: Interactive AI Writing Companion Chat
        """
        system_prompt = (
            "You are an expert AI Writing Companion for an editorial SaaS platform called Blogs Monkey. "
            "Your role is to help authors think, outline, brainstorm, and refine their writing cleanly without taking over their voice. "
            "Be concise, actionable, encouraging, and structured. "
            "Format your responses cleanly with standard headings, numbered lists, and bullet points. Avoid excessive symbol clutter."
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Append optional article context
        if context:
            ctx_str = "CURRENT ARTICLE CONTEXT:\n"
            if context.get('title'):
                ctx_str += f"- Title: {context['title']}\n"
            if context.get('selected_text'):
                ctx_str += f"- Selected Text: \"{context['selected_text']}\"\n"
            if context.get('content_excerpt'):
                ctx_str += f"- Content Excerpt: {context['content_excerpt'][:500]}...\n"
            messages.append({"role": "system", "content": ctx_str})

        # Append conversation history
        if history:
            for msg in history[-6:]:  # Keep last 6 exchanges for context window optimization
                if msg.get('role') in ('user', 'assistant') and msg.get('content'):
                    messages.append({"role": msg['role'], "content": msg['content']})

        messages.append({"role": "user", "content": user_message})

        res = self._call_llm(messages)
        if user:
            self._record_usage(user, 'chat', res)

        if res.get('error'):
            # Fallback output
            fallback_text = f"I am here to help you refine your ideas on '{context.get('title', 'your article') if context else 'your article'}'. Try asking for an outline, brainstorming angles, or section ideas!"
            return {
                'response': fallback_text,
                'is_fallback': True,
                'status': 'available'
            }

        return {
            'response': res['content'],
            'is_fallback': False,
            'status': 'success'
        }

    def brainstorm(self, topic: str, context: Dict[str, Any] = None, user=None) -> Dict[str, Any]:
        """
        Feature 1: Brainstorming angles, subtopics, and perspectives
        """
        prompt = (
            f"Brainstorm 5 unique, compelling article angles and subtopics for an article about: '{topic}'.\n"
            "Format as structured JSON with fields: 'topic', 'angles' (list of objects with 'title', 'hook', 'target_audience')."
        )

        messages = [
            {"role": "system", "content": "You are a senior publishing strategist. Always output valid JSON."},
            {"role": "user", "content": prompt}
        ]

        res = self._call_llm(messages, json_mode=True)
        if user:
            self._record_usage(user, 'brainstorm', res)

        if not res.get('error') and res.get('content'):
            try:
                parsed = json.loads(res['content'])
                return {'data': parsed, 'is_fallback': False}
            except json.JSONDecodeError:
                pass

        # Fallback heuristic
        fallback_data = {
            'topic': topic,
            'angles': [
                {'title': f'Beginner Guide to {topic}', 'hook': f'A step-by-step introduction to understanding {topic}.', 'target_audience': 'Beginners'},
                {'title': f'Why {topic} Matters in 2026', 'hook': f'Key trends and industry shifts impacting {topic}.', 'target_audience': 'Professionals'},
                {'title': f'Common Pitfalls in {topic}', 'hook': f'Top mistakes developers & writers make with {topic} and how to fix them.', 'target_audience': 'Practitioners'},
                {'title': f'Building Production-Ready {topic}', 'hook': f'Architectural principles and actionable patterns.', 'target_audience': 'Senior Engineers'},
                {'title': f'The Future of {topic}', 'hook': f'Predictions and emerging technologies in this space.', 'target_audience': 'Decision Makers'}
            ]
        }
        return {'data': fallback_data, 'is_fallback': True}

    def generate_outline(self, topic: str, article_type: str = 'general', context: Dict[str, Any] = None, user=None) -> Dict[str, Any]:
        """
        Feature 1: Article Outline Generator
        """
        prompt = (
            f"Generate a professional publishing outline for an article titled/about: '{topic}'.\n"
            f"Article Format Style: {article_type}.\n"
            "Format as structured JSON with schema:\n"
            "{\n"
            "  \"title\": \"string\",\n"
            "  \"estimated_reading_time\": \"string\",\n"
            "  \"sections\": [\n"
            "     {\"heading\": \"string\", \"level\": \"h2\", \"talking_points\": [\"point1\", \"point2\"]}\n"
            "  ]\n"
            "}"
        )

        messages = [
            {"role": "system", "content": "You are an expert editorial outline architect. Output strict JSON."},
            {"role": "user", "content": prompt}
        ]

        res = self._call_llm(messages, json_mode=True)
        if user:
            self._record_usage(user, 'outline', res)

        if not res.get('error') and res.get('content'):
            try:
                parsed = json.loads(res['content'])
                return {'data': parsed, 'is_fallback': False}
            except json.JSONDecodeError:
                pass

        # Fallback Heuristic Outline
        fallback_outline = {
            'title': topic or 'Untitled Article',
            'estimated_reading_time': '5 min read',
            'sections': [
                {'heading': 'Introduction', 'level': 'h2', 'talking_points': ['Overview of the problem statement', 'Why this topic is critical now']},
                {'heading': 'Key Concepts & Fundamentals', 'level': 'h2', 'talking_points': ['Core terminology', 'Primary architecture or framework']},
                {'heading': 'Step-by-Step Practical Implementation', 'level': 'h2', 'talking_points': ['Prerequisites', 'Code snippet or workflow setup', 'Best practices']},
                {'heading': 'Common Challenges & Solutions', 'level': 'h2', 'talking_points': ['Debugging common errors', 'Performance optimization tips']},
                {'heading': 'Conclusion', 'level': 'h2', 'talking_points': ['Summary of key takeaways', 'Next steps and further reading']}
            ]
        }
        return {'data': fallback_outline, 'is_fallback': True}

    def suggest_improvements(self, text: str, action: str, context: Dict[str, Any] = None, user=None) -> Dict[str, Any]:
        """
        Feature 1: Selection Text Actions (Explain, Improve, Expand, Simplify, Examples, Counterpoints)
        """
        action_instructions = {
            'explain': 'Explain this concept clearly and concisely with simple analogies.',
            'improve': 'Improve readability, clarity, and tone while preserving the original meaning.',
            'expand': 'Expand this point with deeper insight, context, and detail.',
            'simplify': 'Simplify this text into clear, easy-to-digest prose.',
            'examples': 'Provide 2-3 practical, concrete examples illustrating this point.',
            'counterpoints': 'Suggest alternative perspectives or potential trade-offs to consider.'
        }
        instruction = action_instructions.get(action.lower(), 'Refine and improve this text.')

        prompt = (
            f"Selected Text: \"{text}\"\n"
            f"Task: {instruction}\n"
            "Return concise, beautifully written output."
        )

        messages = [
            {"role": "system", "content": "You are a world-class senior copy editor and writing partner."},
            {"role": "user", "content": prompt}
        ]

        res = self._call_llm(messages)
        if user:
            self._record_usage(user, f'selection_{action}', res)

        if not res.get('error') and res.get('content'):
            return {'result': res['content'], 'action': action, 'is_fallback': False}

        # Fallback
        return {
            'result': f"[{action.upper()} SUGGESTION]: {text}",
            'action': action,
            'is_fallback': True
        }

    def format_article(self, content: str, title: str = "", mode: str = "smart", user=None) -> Dict[str, Any]:
        """
        Feature 2: AI Article Formatting Assistant (Semantic Analysis + JSON Schema Response)
        """
        prompt = (
            "Analyze and format the following article content into a professional editorial publishing structure.\n"
            f"Title: {title}\n"
            f"Content:\n{content[:3000]}\n\n"
            "Respond ONLY with a JSON object containing:\n"
            "{\n"
            "  \"article_type\": \"tutorial|opinion|listicle|case_study|general\",\n"
            "  \"article_type_label\": \"string\",\n"
            "  \"suggestions\": [{\"type\": \"string\", \"title\": \"string\", \"message\": \"string\"}],\n"
            "  \"suggested_takeaways\": [\"point1\", \"point2\", \"point3\"],\n"
            "  \"seo_suggestions\": {\"seo_title\": \"string\", \"seo_description\": \"string\"},\n"
            "  \"structure_improvements\": [\"change1\", \"change2\"]\n"
            "}"
        )

        messages = [
            {"role": "system", "content": "You are an expert article formatter and structural editor. Always return strict valid JSON."},
            {"role": "user", "content": prompt}
        ]

        res = self._call_llm(messages, json_mode=True)
        if user:
            self._record_usage(user, 'format_article', res)

        if not res.get('error') and res.get('content'):
            try:
                parsed = json.loads(res['content'])
                return {'ai_analysis': parsed, 'is_fallback': False}
            except json.JSONDecodeError:
                pass

        # Return fallback flag for local AIAssistant engine
        return {'ai_analysis': None, 'is_fallback': True}
