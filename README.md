# Backend Failure Simulations

This repository is a back-to-basics learning path for backend development.

It is designed for two groups of people:

1. Beginners who want a gentle introduction to backend concepts.
2. Rusty developers who want a calm way to get back into practice.

The project starts small and stays practical. You learn one idea at a time, then use those ideas to build a simple system.

## What this repo is for

This repo is not a large framework and not a production template. It is a teaching project.

You will use it to:

- learn the basics of backend behavior
- see how common failures happen
- practice fixing one problem at a time
- build confidence by making small working things

## How to use it

Start here:

1. [docs/START_HERE.md](docs/START_HERE.md)
2. [docs/LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md)
3. [exercises/README.md](exercises/README.md)

Then move in this order:

1. Complete the exercises.
2. Read the system-building guide.
3. Build the authentication component.
4. Use the reference files only when you want to compare your work.

## Main folders

- [docs/](docs/) contains the guides, roadmap, and progress notes.
- [exercises/](exercises/) contains the beginner practice files.
- [components/](components/) contains the system-building phase.
- [reference/](reference/) contains finished examples.
- [tools/](tools/) contains scripts for running and testing the project.

## The learning path

Phase 1: learn the basics

1. Database connection pools
2. Network retries and timeouts
3. Rate limiting

Phase 2: build a small system

1. Authentication system
2. More components, only if you want to keep going

## Simple way to begin

```bash
pip install -r requirements.txt
code exercises/ex1_db_starter.py
```

Work through the TODOs, one method at a time, and run the file often.

## Helpful commands

```bash
python tools/launcher.py
python tools/test_scenarios.py
code docs/ROADMAP.md
code docs/MY_PROGRESS.md
```

## If you feel stuck

That is normal. Read the error, make one small change, and try again. The goal is steady progress, not speed.
