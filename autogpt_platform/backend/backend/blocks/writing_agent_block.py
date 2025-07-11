from enum import Enum
from typing import Any, List

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.blocks.llm import (
    AIStructuredResponseGeneratorBlock,
    LlmModel,
    LLMProviderName,
    TEST_CREDENTIALS,
    TEST_CREDENTIALS_INPUT,
)
from backend.util.text import TextFormatter

fmt = TextFormatter()


# Enums for different writing configurations
class WritingStyle(str, Enum):
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    ACADEMIC = "academic"
    CASUAL = "casual"
    PERSUASIVE = "persuasive"
    TECHNICAL = "technical"
    JOURNALISTIC = "journalistic"
    HUMOROUS = "humorous"


class WritingFormat(str, Enum):
    ARTICLE = "article"
    BLOG_POST = "blog_post"
    EMAIL = "email"
    LETTER = "letter"
    ESSAY = "essay"
    STORY = "story"
    REPORT = "report"
    PROPOSAL = "proposal"
    REVIEW = "review"
    SOCIAL_MEDIA_POST = "social_media_post"
    SCRIPT = "script"
    POEM = "poem"


class WritingTone(str, Enum):
    FORMAL = "formal"
    INFORMAL = "informal"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"
    INSPIRATIONAL = "inspirational"
    NEUTRAL = "neutral"
    ENTHUSIASTIC = "enthusiastic"


class WritingLength(str, Enum):
    SHORT = "short"  # 100-300 words
    MEDIUM = "medium"  # 300-800 words
    LONG = "long"  # 800-2000 words
    EXTENDED = "extended"  # 2000+ words


AICredentials = CredentialsMetaInput[LLMProviderName, "api_key"]


class CreativeWritingAgentBlock(Block):
    class Input(BlockSchema):
        topic: str = SchemaField(
            description="The main topic or subject to write about",
            placeholder="Enter the topic for your writing...",
        )
        writing_style: WritingStyle = SchemaField(
            title="Writing Style",
            default=WritingStyle.PROFESSIONAL,
            description="Choose the writing style that best fits your needs",
        )
        writing_format: WritingFormat = SchemaField(
            title="Writing Format",
            default=WritingFormat.ARTICLE,
            description="Select the format for your written content",
        )
        writing_tone: WritingTone = SchemaField(
            title="Writing Tone",
            default=WritingTone.CONVERSATIONAL,
            description="Set the tone of voice for your writing",
        )
        target_length: WritingLength = SchemaField(
            title="Target Length",
            default=WritingLength.MEDIUM,
            description="Specify the desired length of the content",
        )
        target_audience: str = SchemaField(
            title="Target Audience",
            default="general audience",
            description="Describe who will be reading this content",
            placeholder="e.g., business professionals, students, general public...",
        )
        key_points: List[str] = SchemaField(
            title="Key Points",
            default_factory=list,
            description="Optional: Specific points or arguments to include in the writing",
            advanced=True,
        )
        additional_context: str = SchemaField(
            title="Additional Context",
            default="",
            description="Any additional context, requirements, or instructions",
            advanced=True,
        )
        model: LlmModel = SchemaField(
            title="LLM Model",
            default=LlmModel.GPT4O,
            description="The language model to use for writing generation",
            advanced=True,
        )
        credentials: AICredentials = CredentialsField(
            description="API key for the LLM provider",
            discriminator="model",
            discriminator_mapping={
                model.value: model.metadata.provider for model in LlmModel
            },
        )
        include_outline: bool = SchemaField(
            title="Include Outline",
            default=False,
            description="Generate an outline along with the main content",
            advanced=True,
        )
        max_tokens: int | None = SchemaField(
            advanced=True,
            default=None,
            description="The maximum number of tokens to generate",
        )

    class Output(BlockSchema):
        content: str = SchemaField(description="The generated written content")
        outline: str = SchemaField(description="Content outline (if requested)")
        word_count: int = SchemaField(
            description="Approximate word count of the generated content"
        )
        writing_summary: dict[str, Any] = SchemaField(
            description="Summary of writing parameters used"
        )
        prompt: list = SchemaField(description="The prompt sent to the language model")
        error: str = SchemaField(
            description="Error message if content generation failed"
        )

    def __init__(self):
        super().__init__(
            id="7c8b2f5a-4e9d-4a3b-8f7e-2c6b5d8e9f1a",
            description="Advanced writing agent that creates high-quality content in various styles, formats, and tones using AI assistance",
            categories={BlockCategory.AI, BlockCategory.TEXT},
            input_schema=CreativeWritingAgentBlock.Input,
            output_schema=CreativeWritingAgentBlock.Output,
            test_input={
                "topic": "The Future of Artificial Intelligence in Education",
                "writing_style": WritingStyle.ACADEMIC,
                "writing_format": WritingFormat.ARTICLE,
                "writing_tone": WritingTone.AUTHORITATIVE,
                "target_length": WritingLength.MEDIUM,
                "target_audience": "educators and technology professionals",
                "credentials": TEST_CREDENTIALS_INPUT,
                "model": LlmModel.GPT4O,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[
                ("content", str),
                ("word_count", int),
                ("writing_summary", dict),
                ("prompt", list),
            ],
            test_mock={
                "llm_call": lambda input_data, credentials: {
                    "content": "Artificial Intelligence is transforming education by personalizing learning experiences and automating administrative tasks. As we look to the future, AI technologies promise to revolutionize how students learn and how educators teach, creating more efficient and effective educational systems.",
                    "word_count": 42,
                }
            },
        )

    def _get_length_guidance(self, length: WritingLength) -> str:
        """Get word count guidance based on target length."""
        length_guides = {
            WritingLength.SHORT: "approximately 100-300 words",
            WritingLength.MEDIUM: "approximately 300-800 words",
            WritingLength.LONG: "approximately 800-2000 words",
            WritingLength.EXTENDED: "approximately 2000+ words",
        }
        return length_guides.get(length, "moderate length")

    def _build_writing_prompt(self, input_data: Input) -> str:
        """Build a comprehensive writing prompt based on input parameters."""

        # Base prompt structure
        prompt_parts = [
            f"Write a {input_data.writing_style.value} {input_data.writing_format.value} about '{input_data.topic}'."
        ]

        # Add tone and audience specifications
        prompt_parts.append(
            f"Use a {input_data.writing_tone.value} tone and write for {input_data.target_audience}."
        )

        # Add length guidance
        length_guidance = self._get_length_guidance(input_data.target_length)
        prompt_parts.append(f"The content should be {length_guidance}.")

        # Add specific format requirements
        format_requirements = {
            WritingFormat.ARTICLE: "Structure the article with a compelling headline, introduction, main body with clear sections, and conclusion.",
            WritingFormat.BLOG_POST: "Write in a blog style with an engaging introduction, informative content, and a call-to-action conclusion.",
            WritingFormat.EMAIL: "Format as a professional email with subject line, greeting, body, and appropriate closing.",
            WritingFormat.LETTER: "Follow formal letter structure with proper salutation, body paragraphs, and closing.",
            WritingFormat.ESSAY: "Structure as an essay with introduction, thesis statement, body paragraphs with supporting evidence, and conclusion.",
            WritingFormat.STORY: "Create a narrative with character development, setting, plot, and resolution.",
            WritingFormat.REPORT: "Format as a professional report with executive summary, findings, analysis, and recommendations.",
            WritingFormat.PROPOSAL: "Structure as a business proposal with problem statement, solution, benefits, and implementation plan.",
            WritingFormat.REVIEW: "Provide balanced analysis with pros, cons, and overall assessment.",
            WritingFormat.SOCIAL_MEDIA_POST: "Create engaging, shareable content appropriate for social media platforms.",
            WritingFormat.SCRIPT: "Write in script format with character names, dialogue, and stage directions.",
            WritingFormat.POEM: "Create poetic content with attention to rhythm, imagery, and emotional impact.",
        }

        if input_data.writing_format in format_requirements:
            prompt_parts.append(format_requirements[input_data.writing_format])

        # Add key points if provided
        if input_data.key_points:
            key_points_str = ", ".join(input_data.key_points)
            prompt_parts.append(
                f"Make sure to address these key points: {key_points_str}."
            )

        # Add additional context
        if input_data.additional_context:
            prompt_parts.append(f"Additional context: {input_data.additional_context}")

        # Style-specific guidance
        style_guidance = {
            WritingStyle.PROFESSIONAL: "Maintain clarity, use industry-appropriate terminology, and ensure error-free grammar.",
            WritingStyle.CREATIVE: "Use vivid imagery, varied sentence structure, and engaging storytelling techniques.",
            WritingStyle.ACADEMIC: "Include evidence-based arguments, proper citations (when applicable), and scholarly vocabulary.",
            WritingStyle.CASUAL: "Write in a relaxed, conversational manner with everyday language.",
            WritingStyle.PERSUASIVE: "Use compelling arguments, emotional appeals, and strong calls to action.",
            WritingStyle.TECHNICAL: "Focus on accuracy, use precise terminology, and include step-by-step explanations.",
            WritingStyle.JOURNALISTIC: "Follow the inverted pyramid structure with factual, objective reporting.",
            WritingStyle.HUMOROUS: "Incorporate appropriate humor, wit, and entertaining elements.",
        }

        if input_data.writing_style in style_guidance:
            prompt_parts.append(style_guidance[input_data.writing_style])

        # Final quality instructions
        prompt_parts.append(
            "Ensure the content is original, well-structured, engaging, and appropriate for the specified audience and purpose."
        )

        return " ".join(prompt_parts)

    async def llm_call(
        self,
        input_data: AIStructuredResponseGeneratorBlock.Input,
        credentials: APIKeyCredentials,
    ) -> dict:
        """Make LLM call using the structured response generator."""
        block = AIStructuredResponseGeneratorBlock()
        response = await block.run_once(input_data, "response", credentials=credentials)
        return response

    async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            # Build the writing prompt
            writing_prompt = self._build_writing_prompt(input_data)

            # Prepare output format for structured response
            output_format = {
                "content": "The complete written content based on the specifications",
                "word_count": "Approximate number of words in the content",
            }

            # Add outline to output format if requested
            if input_data.include_outline:
                output_format["outline"] = "A structured outline of the content"

            # Prepare LLM input
            llm_input = AIStructuredResponseGeneratorBlock.Input(
                prompt=writing_prompt,
                expected_format=output_format,
                model=input_data.model,
                credentials=input_data.credentials,
                max_tokens=input_data.max_tokens,
                sys_prompt="You are an expert writing assistant capable of creating high-quality content in various styles and formats.",
            )

            # Generate content
            response = await self.llm_call(llm_input, credentials)

            # Extract results
            content = response.get("content", "")
            word_count = response.get("word_count", len(content.split()))
            outline = response.get("outline", "")

            # Create writing summary
            writing_summary = {
                "topic": input_data.topic,
                "style": input_data.writing_style.value,
                "format": input_data.writing_format.value,
                "tone": input_data.writing_tone.value,
                "target_length": input_data.target_length.value,
                "target_audience": input_data.target_audience,
                "model_used": input_data.model.value,
                "key_points_included": (
                    len(input_data.key_points) if input_data.key_points else 0
                ),
            }

            # Yield outputs
            yield "content", content
            if outline:
                yield "outline", outline
            yield "word_count", word_count
            yield "writing_summary", writing_summary
            yield "prompt", [{"role": "user", "content": writing_prompt}]

        except Exception as e:
            error_msg = f"Failed to generate writing content: {str(e)}"
            yield "error", error_msg
            raise RuntimeError(error_msg)


class WritingPromptGeneratorBlock(Block):
    class Input(BlockSchema):
        writing_type: WritingFormat = SchemaField(
            title="Writing Type",
            default=WritingFormat.ARTICLE,
            description="Type of writing to generate prompts for",
        )
        difficulty_level: str = SchemaField(
            title="Difficulty Level",
            default="intermediate",
            description="Difficulty level: beginner, intermediate, or advanced",
        )
        subject_area: str = SchemaField(
            title="Subject Area",
            default="general",
            description="Subject area or topic category",
            placeholder="e.g., technology, business, education, health...",
        )
        num_prompts: int = SchemaField(
            title="Number of Prompts",
            default=5,
            description="Number of writing prompts to generate",
            ge=1,
            le=20,
        )
        model: LlmModel = SchemaField(
            title="LLM Model",
            default=LlmModel.GPT4O,
            description="The language model to use",
            advanced=True,
        )
        credentials: AICredentials = CredentialsField(
            description="API key for the LLM provider",
            discriminator="model",
            discriminator_mapping={
                model.value: model.metadata.provider for model in LlmModel
            },
        )

    class Output(BlockSchema):
        prompts: List[str] = SchemaField(
            description="List of generated writing prompts"
        )
        prompt_item: str = SchemaField(description="Individual writing prompt")
        prompt: list = SchemaField(description="The prompt sent to the language model")
        error: str = SchemaField(
            description="Error message if prompt generation failed"
        )

    def __init__(self):
        super().__init__(
            id="9e1f8c4b-6d3a-4f8b-9e2c-7a5b8d4e1f9c",
            description="Generate creative writing prompts for various writing formats and difficulty levels",
            categories={BlockCategory.AI, BlockCategory.TEXT},
            input_schema=WritingPromptGeneratorBlock.Input,
            output_schema=WritingPromptGeneratorBlock.Output,
            test_input={
                "writing_type": WritingFormat.STORY,
                "difficulty_level": "intermediate",
                "subject_area": "science fiction",
                "num_prompts": 3,
                "credentials": TEST_CREDENTIALS_INPUT,
                "model": LlmModel.GPT4O,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[
                ("prompts", list),
                ("prompt_item", str),
                ("prompt", list),
            ],
            test_mock={
                "llm_call": lambda input_data, credentials: {
                    "prompts": [
                        "Write a story about a time traveler who discovers they can only travel to moments of great historical significance.",
                        "Create a narrative about an AI that develops emotions but must hide this from its creators.",
                        "Tell the story of the last human on Earth who discovers they're not actually alone.",
                    ]
                }
            },
        )

    async def llm_call(
        self,
        input_data: AIStructuredResponseGeneratorBlock.Input,
        credentials: APIKeyCredentials,
    ) -> dict:
        """Make LLM call using the structured response generator."""
        block = AIStructuredResponseGeneratorBlock()
        response = await block.run_once(input_data, "response", credentials=credentials)
        return response

    async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            # Build prompt for generating writing prompts
            prompt = f"""Generate {input_data.num_prompts} creative and engaging writing prompts for {input_data.writing_type.value} writing.

Subject area: {input_data.subject_area}
Difficulty level: {input_data.difficulty_level}

The prompts should be:
- Inspiring and thought-provoking
- Appropriate for the {input_data.difficulty_level} level
- Relevant to the {input_data.subject_area} subject area
- Varied in theme and approach
- Suitable for {input_data.writing_type.value} format

Provide diverse and creative prompts that will challenge writers and spark their imagination."""

            # Prepare LLM input
            llm_input = AIStructuredResponseGeneratorBlock.Input(
                prompt=prompt,
                expected_format={"prompts": "List of creative writing prompts"},
                list_result=True,
                model=input_data.model,
                credentials=input_data.credentials,
                sys_prompt="You are a creative writing instructor who specializes in generating inspiring and educational writing prompts.",
            )

            # Generate prompts
            response = await self.llm_call(llm_input, credentials)
            prompts = response.get("prompts", [])

            # Ensure we have a list
            if isinstance(prompts, str):
                prompts = [prompts]
            elif not isinstance(prompts, list):
                prompts = []

            # Yield outputs
            yield "prompts", prompts
            for prompt_item in prompts:
                yield "prompt_item", prompt_item
            yield "prompt", [{"role": "user", "content": prompt}]

        except Exception as e:
            error_msg = f"Failed to generate writing prompts: {str(e)}"
            yield "error", error_msg
            raise RuntimeError(error_msg)
