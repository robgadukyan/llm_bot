# Title
Transformers for NLP: Why Attention Replaced Recurrence

# Audience and Duration
Audience: BA NLP students  
Duration: 60 minutes  
Language: English

# Learning Objectives
By the end of the lesson, students will be able to:
1. Explain why self-attention helps model relationships between tokens without processing them strictly one by one [Slide 2].
2. Identify the main parts of a Transformer encoder block: multi-head attention, feed-forward layer, residual connection, and normalization [Slide 3].
3. Describe a basic fine-tuning workflow with train/validation/test splits and evaluation metrics [Slide 4].
4. Compare slide-based concepts with external readings on attention and Transformer architecture [Web].

# Timed Teaching Plan
| Time | Activity | Purpose | Grounding |
|---:|---|---|---|
| 0-5 min | Warm-up question: "Why might RNNs be slow for long sequences?" | Activate prior knowledge | [Slide 1] |
| 5-15 min | Explain the motivation for attention replacing recurrence | Introduce the central problem | [Slide 1], [Slide 2] |
| 15-30 min | Walk through self-attention using query/key/value intuition | Build conceptual understanding | [Slide 2] |
| 30-40 min | Explain encoder block components and why multi-head attention is useful | Connect parts into architecture | [Slide 3] |
| 40-50 min | Fine-tuning mini-case: adapt a pretrained Transformer to sentiment classification | Apply architecture to a task | [Slide 4] |
| 50-57 min | Student exercise in pairs | Check understanding | [Slide 2-4] |
| 57-60 min | Exit ticket and recap | Consolidate learning | [Slide 1-4] |

# Worked Example
Sentence: "The bank raised interest rates because inflation increased."  
Ask students to choose which words should attend strongly to "rates". Expected answer: "bank", "raised", and "inflation" may be relevant because they help determine the economic meaning of the sentence [Slide 2].

# Student Exercise
In pairs, students draw a mini attention map for the sentence: "The student used the model to classify the review." They must choose one target token, identify three tokens it should attend to, and explain why. Then they map the process to a Transformer encoder block [Slide 2], [Slide 3].

# Recap / Exit Ticket
Students answer in one minute:
1. What problem does self-attention solve?
2. What are two components inside a Transformer encoder block?
3. Why do we keep validation and test sets separate during fine-tuning?

# Supporting Web Resources
1. [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - Original Transformer paper; useful for connecting the lecture to the primary source. Justification: supports the architecture introduced in the slides. [Web]
2. [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) - Visual explanation of attention and encoder-decoder structure. Justification: useful for students who need diagrams. [Web]
3. [Hugging Face NLP Course](https://huggingface.co/learn/nlp-course/) - Practical introduction to Transformer models and fine-tuning. Justification: supports applied practice after the lecture. [Web]

# Grounding Notes
- Claims about self-attention, Q/K/V intuition, and attention weights are grounded in Slide 2.
- Claims about encoder blocks are grounded in Slide 3.
- Claims about fine-tuning and evaluation are grounded in Slide 4.
- External readings are marked as [Web] and should be checked live by the bot during the actual run.

# Email Body
Dear colleague,

Please find below the generated teaching package for the lecture "Transformers for NLP: Why Attention Replaced Recurrence." It includes learning objectives, a timed teaching plan, a worked example, a student exercise, recap questions, supporting web resources, and grounding notes.

Best regards,
Agentic Telegram Teaching Assistant

---

# Agent Revision Checklist
- Timing check: The timed plan totals exactly 60 minutes.
- Grounding check: Key claims are marked with slide references or web markers.
- Missing information: The instructor may add course-specific examples or grading expectations.
- Final quality verdict: Suitable for a short undergraduate NLP lecture after instructor review.
