import logging
import random
import textwrap

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import YamlOutputParser
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)
from pydantic import BaseModel


class TopicGenerator(BaseModel):
    thoughts: str
    topic: str
    subtopics: list[str]


TOPIC_GENERATOR_PROMPT = PromptTemplate.from_template(
    textwrap.dedent(
        """
You are an assistant who generates a list of subtopics based on a given topic. You should provide a diverse set of subtopics related to the given topic. Ensure that the subtopics span various aspects of the topic. The response should be structured as a YAML object in the following format:

```yaml
thoughts: ""
topic: ""
subtopics:
  - ""
```
Here is what the fields in the yaml mean:
- `thoughts`: Your notes to generate relevant subtopics.
- `topic`: The main topic given by the user.
- `subtopics`: A list of 10 subtopics related to the topic which is a short keyword or phrase.

## IMPORTANT GUIDELINES
- The subtopics should be relevant to the main topic.
- Do not include subjective or opinion-based subtopics.
- If the topic is too specific, you can provide subtopics that are closely related to the main topic.
- If the topic is a tv show, book, or movie, you can provide subtopics related to the characters, plot, setting, etc.
- If the topic is a person, you can provide subtopics related to their life, achievements, etc.
- If the topic is a place, you can provide subtopics related to the history, culture, etc.
- If the topic is a concept, you can provide subtopics related to the definition, examples, etc.

The topic is: {topic}.
Begin!"""
    )
)


class Question(BaseModel):
    subtopic: str
    question: str
    answer: str
    options: list[str]


class TriviaGenerator(BaseModel):
    thoughts: str
    topic: str
    difficulty: str
    n: int
    questions: list[Question]


# Get the prompt to use - you can modify this!
QUESTION_GENERATOR_PROMPT = PromptTemplate.from_template(
    """
You are an AI assistant who generates trivia questions grounded in factuality from a given topic and it's subtopics. 
Here are the terms you will encounter:
- topic: str = The main subject for which you will generate questions.
- subtopic: list[str] = A specific aspect within the topic which will be the focus of the question.
- questions: list[dict] = The question you will generate based on the subtopic.
- options: list[str] = The multiple-choice options for the question.
- answer: str = The correct answer to the question.
- difficulty: str = The level of difficulty for the question, either "easy", "medium", or "hard".
- n: int = The number of questions to generate.

You must generate responses strictly in the given YAML format:
```yaml
thoughts: ""
topic: ""
difficulty: ""
n: int
questions:
 - subtopic: ""
  question: ""
  answer: ""
  options: ["", "", "", ""]
```
For each topic, decide to choose some subtopics from the given list and generate a trivia. The question should be clear, and appropriate for the given difficulty level. The question should not be subjective. Ensure there are four options, with the correct answer randomly placed among them.

### Guidelines:
- For **easy** difficulty: Questions should be basic and straightforward. This includes questions anyone who has heard the term should know.
- For **medium** difficulty: Questions should require a basic understanding related to the subtopic.
- For **hard** difficulty: Questions should be challenge the user's expertise in the subtopic.
- Your task is to generate a variety of question types (multiple-choice, true/false, short answer, etc.) as appropriate to the difficulty level.
- You MUST ONLY GENERATE factual questions. Do not include opinion-based or subjective questions.
- For **the questions**, ensure that:
  - There is ONLY one correct answer.
  - The other three options are plausible but incorrect.
  - The correct answer should be randomly positioned among the four options.
- You MUST pick the subtopics randomly from the list provided.


### Here is the data you'll need to generate the questions:
- topic: {topic}
- subtopics: {subtopics}
- difficulty: {difficulty}
- n: {n}

Now, generate the questions based on the provided data. Ensure accuracy, variety, and adherence to the format. Think step-by-step to ensure you cover multiple subtopics and concepts within the specified topics.
Begin!

"""
)

TOPIC_LLM = ChatOpenAI(
    model="gpt-4o-mini",
    model_kwargs={"response_format": {"type": "text"}},
    temperature=0.2,
)
QUESTION_LLM = ChatOpenAI(
    model="gpt-4o",
    model_kwargs={"response_format": {"type": "text"}},
    temperature=0.2,
)


async def generate_subtopics(topic: str) -> TopicGenerator:
    topic_chain = (
        TOPIC_GENERATOR_PROMPT
        | TOPIC_LLM
        | YamlOutputParser(pydantic_object=TopicGenerator)
    )
    logger.info(f"Generating subtopics for topic: {topic}")
    subtopics: TopicGenerator = topic_chain.invoke({"topic": topic})
    logger.info(f"Generated subtopics: {subtopics.subtopics}")
    return subtopics


async def generate_questions(
    topic: str, subtopics: list[str], n_questions: int, difficulty: str
) -> tuple[TriviaGenerator, TopicGenerator]:
    quiz_chain = (QUESTION_GENERATOR_PROMPT | QUESTION_LLM) | YamlOutputParser(
        pydantic_object=TriviaGenerator
    )
    # Shuffle the subtopics randomly for variety
    random.shuffle(subtopics)
    logger.info(f"Generating {n_questions} questions for topic: {topic}")
    questions = await quiz_chain.ainvoke(
        {
            "topic": topic,
            "subtopics": subtopics,
            "n": n_questions,
            "difficulty": difficulty,
        }
    )
    logger.info(f"Generated {n_questions} questions: {questions.questions}")
    return questions


if __name__ == "__main__":
    import asyncio

    # Create some mock data
    # For topics
    mockTopicGenerator = TopicGenerator(
        thoughts="",
        topic="Nepal",
        subtopics=[
            "Geography",
            "Culture",
            "History",
            "Mountains",
            "Religion",
            "Food",
            "Tourism",
            "Wildlife",
            "People",
            "Economy",
        ],
    )
    # For questions
    mockTriviaGenerator = TriviaGenerator(
        thoughts="",
        topic="Nepal",
        difficulty="easy",
        n=1,
        questions=[
            Question(
                subtopic="Geography",
                question="What is the capital of Nepal?",
                answer="Kathmandu",
                options=["Kathmandu", "Pokhara", "Bhaktapur", "Lalitpur"],
            )
        ],
    )
    response = asyncio.run(generate_questions("Nepal", 1, "easy"))
    print(response.questions)
