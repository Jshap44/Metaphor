"""Inspectable lightweight generative-agent architecture; no paid API needed."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import exp
from collections import Counter
import re


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))

@dataclass
class Memory:
    text: str
    importance: float = 0.5
    kind: str = "observation"
    created: int = 0

@dataclass
class SurveyAgent:
    persona: dict
    memories: list[Memory] = field(default_factory=list)
    tick: int = 0
    reflection_every: int = 4

    def observe(self, text, importance=0.5, kind="observation"):
        self.tick += 1
        self.memories.append(Memory(text=str(text), importance=float(importance), kind=kind, created=self.tick))
        if kind == "observation" and self.reflection_every > 0:
            count = sum(m.kind == "observation" for m in self.memories)
            if count % self.reflection_every == 0:
                self.reflect()

    def retrieve(self, query, k=4):
        q = tokens(query)
        ranked = []
        for memory in self.memories:
            t = tokens(memory.text)
            relevance = len(t & q) / max(1, len(t | q))
            recency = exp(-0.08 * (self.tick - memory.created))
            score = 0.55 * relevance + 0.25 * recency + 0.20 * memory.importance
            ranked.append((score, memory))
        return [m for _, m in sorted(ranked, key=lambda pair: pair[0], reverse=True)[:k]]

    def reflect(self):
        recent = [m for m in self.memories if m.kind == "observation"][-self.reflection_every:]
        if not recent:
            return "No observations available"
        # Explicit evidence-based summary; does not hallucinate beliefs or attitudes.
        sentences = [m.text.strip().replace("\n", " ")[:180] for m in recent]
        summary = "Recent observations: " + " | ".join(sentences)
        self.observe(summary, importance=0.8, kind="reflection")
        return summary

    def plan(self, stimulus, question=""):
        memories = self.retrieve(stimulus + " " + question)
        steps = ["Review the persona demographics without assuming unrecorded beliefs",
                 "Read the presented stimulus and survey question",
                 "Retrieve relevant observations and reflections",
                 "Use a calibrated, task-specific predictive model when available",
                 "Record the response as simulated, not as an observed human answer"]
        return {"steps": steps, "relevant_memories": [m.text for m in memories]}

    def react(self, stimulus, question="", predictor=None, row=None):
        plan = self.plan(stimulus, question)
        self.observe(f"Presented: {stimulus[:400]} Question: {question[:200]}", 0.7)
        output = predictor(row) if predictor is not None and row is not None else {
            "response": None, "warning": "No classifier supplied; agent stores, retrieves, reflects, and plans only."}
        self.observe(f"Simulated output: {output.get('response')}", 0.6)
        return {"persona": self.persona, "plan": plan, "prediction": output,
                "memory_count": len(self.memories)}
