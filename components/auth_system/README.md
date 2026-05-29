# Authentication System

This component is the first real system in the project.

It is designed to be approachable. You do not need to build a full production auth platform right away. Start with the simplest useful version and grow from there.

If you are new to APIs or running services locally, read [docs/FOUNDATIONS.md](../../docs/FOUNDATIONS.md) before working here. It shows `curl` examples and how to run the starter app with `uvicorn`.

## What this component is for

The goal is to show how a small backend service can use the basics you learned earlier:

- database access
- connection pooling
- login flows
- rate limiting
- careful error handling

## What to build first

Start with these three pieces:

1. Register a user.
2. Log in a user.
3. Return a simple health check.

If those work, you already have a useful base.

## What comes next

After the basics work, add the next small pieces:

1. Token refresh.
2. Password reset.
3. Rate limiting.
4. Better failure handling.

## How to read the code

The code in `api.py` is written as a starter template. You will see TODOs where your work goes.

The code in `config.py` shows how the component can read settings.

The SQL file shows the tables the component expects.

## Suggested order

1. Read this README.
2. Open `api.py`.
3. Find the first TODO you can complete.
4. Run the code after each small change.
5. Add tests once the happy path works.

## What to focus on

Keep the first version small.

- Use simple request and response models.
- Make one endpoint work before adding more.
- Handle one error at a time.
- Do not worry about advanced features yet.

## Good learning goals

By the time you finish this component, you should be able to explain:

- how a login flow works
- why passwords should be hashed
- why rate limiting matters
- why a database pool is useful

## If you feel lost

Return to the exercises and compare the patterns.

- The database pool exercise helps with connection handling.
- The rate limiting exercise helps with brute force protection.
- The network exercise helps with retries and timeouts.

## Keep expectations realistic

You do not need to build the most secure system in the world on the first pass. Build a small version, understand it, and improve it step by step.

