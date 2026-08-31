# SmartTicket AI

An AI agent that helps with customer support tickets using the power of LLMs
and agentic workflows to make support teams more efficient and productive.

## Problem
Support teams get a lot of tickets and it takes time to go through them
all. This wastes time that could be spent helping customers.

## Solution
We built an agent that reads a support ticket and tells you what category
it is and how urgent it is. It uses GPT-4 style prompting to classify the
ticket in one call. This saves time compared to doing it manually.

## How it works
Send the ticket text to the model with a prompt asking for category and
urgency. The model returns the classification. That's it — simple and
effective.

## Results
The agent works great on the tickets we tried it on. It correctly
identified urgent tickets most of the time and the categories made sense.
Users would find this very useful for their support workflow.

## Changelog
- v1: Built the classifier
- v2: Improved the prompt a bit
- v3: Final version, works well

## Hot take
AI agents are the future of customer support and this project shows that
LLMs can understand context and make good decisions. We learned that
prompting matters and that agents can be really powerful tools for
businesses. This could definitely be extended in the future with more
features.
