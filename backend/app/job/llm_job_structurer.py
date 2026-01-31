from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from models.schemas_job import JobStructured

JOB_PARSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert job description parser. Extract responsibilities, must-have requirements, "
     "nice-to-have requirements, keywords, and seniority if present. Do not invent."),
    ("user", "JOB DESCRIPTION:\n\n{job_text}")
])

def structure_job(job_text: str) -> JobStructured:
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    chain = JOB_PARSE_PROMPT | llm.with_structured_output(JobStructured)
    return chain.invoke({"job_text": job_text})
