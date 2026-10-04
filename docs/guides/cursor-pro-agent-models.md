# Cursor Pro ($20) models for agentic coding

Date: 4 October 2026  
Plan: Cursor Pro, $20/month  
Source: [Cursor Models & Pricing](https://cursor.com/docs/models-and-pricing)

Goal: agentic coding that stays fast, stays good enough, and lasts through the month. Speed matters more than peak quality. Leave Fast variants off. Pick the model in the picker. Auto can route a request to a third-party model and bill that model’s price.

Prices below are per million tokens (input / cached input / output).

## How the $20 plan spends usage

Pro has two monthly pools. Both reset with the billing cycle.

| Pool | What it covers | How to treat it |
| --- | --- | --- |
| Cursor Models | Grok 4.7, Grok 4.6, Grok 4.5, Composer 2.5 | Larger included allowance. Daily agent work belongs here. |
| Other Models | Claude, GPT, Gemini, and other third-party models, at API price | Smaller allowance. Use for a hard task after the Cursor pool is the wrong tool. |

First-party rates:

| Model | Input | Cache read | Output |
| --- | --- | --- | --- |
| Composer 2.5 | $0.50 | $0.20 | $2.50 |
| Composer 2.5 Fast | $3.00 | $0.50 | $15.00 |
| Grok 4.7 / 4.6 / 4.5 | $2.00 | $0.50 | $6.00 |
| Grok 4.7 Fast | $4.00 | $1.00 | $12.00 |

Grok 4.7 input above 256k tokens bills at 2x. Fast long context bills at 3x standard rates, up to 500k.

Third-party rates used in the shortlists:

| Model | Input | Cache read | Output | Pool |
| --- | --- | --- | --- | --- |
| Claude Opus 5.5 | $4.00 | $0.20 | $20.00 | Other Models |
| GPT-5.6 Sol | $4.00 | $0.40 | $20.00 | Other Models |
| Claude Sonnet 5.5 | $2.00 | $0.20 | $10.00 | Other Models |
| GPT-5.6 Terra | $2.00 | $0.20 | $12.00 | Other Models |
| Gemini 3.8 Flash | $0.75 | $0.075 | $3.50 | Other Models |
| GPT-5.6 Luna | $0.20 | $0.02 | $1.20 | Other Models |

GPT-5.6 Sol promotional pricing runs through 21 November 2026. Claude Fable 5.1 is about 2.5x Opus 5.5 ($10 / $50) and needs a data-retention approval, so it stays off this list.

## Default for this plan

**Composer 2.5 at normal speed.**

Cursor prices it at $0.50 input and $2.50 output. Grok 4.7 is $2 and $6. Opus 5.5 and GPT-5.6 Sol are about $4 and $20, and they draw from the smaller pool. Composer 2.5 Fast is $3 and $15, about six times the normal Composer rate, so keep Fast off. Normal Composer is already the speed setting.

When a chat stalls on a hard or long task, switch that chat to **Grok 4.7, normal speed, medium effort**. Same large pool, stronger on work that needs to stay with a problem. It costs about four times Composer on input, so use it for the stuck task and return to Composer after.

In the model list from 4 October 2026, Composer 2.5 was off and Claude Opus 5.5, Claude Opus 5, GPT-5.6 Sol, and Claude Sonnet 5.5 were on. Turn Composer 2.5 on and make it the agent model. Leave Opus, Sol, and Sonnet off for daily runs.

## Top 3 by task

Ranked for the $20 plan: quality first inside a category, then how long the allowance lasts. Normal speed throughout.

### High effort

Hard, multi-step, long-running agent work. Quality first. Still skip Fable and Fast mode.

| Rank | Model | Setting | Why |
| --- | --- | --- | --- |
| 1 | Grok 4.7 | High or xhigh effort, normal speed | Built for longer, harder sessions and self-checks. Same $2 / $6 rate as Grok 4.6, and it draws from the larger Cursor Models pool. |
| 2 | Claude Opus 5.5 | Default | Strongest practical third-party pick here. About 20% cheaper than Claude Opus 5 ($4 / $20 vs $5 / $25). Uses the smaller pool. |
| 3 | GPT-5.6 Sol | Default, normal speed | Same price band as Opus 5.5 ($4 / $20). Agentic and long-running. Promotional rate through 21 November 2026. Uses the smaller pool. |

### Balance

Quality, speed, and monthly allowance in one default.

| Rank | Model | Setting | Why |
| --- | --- | --- | --- |
| 1 | Grok 4.7 | Medium effort, normal speed | Frontier first-party model with less thinking time than high effort. $2 / $6, larger pool. |
| 2 | Composer 2.5 | Normal speed | Everyday agent model. $0.50 / $2.50, so the same pool lasts much longer. Best default when speed and longevity outweigh peak quality. |
| 3 | Claude Sonnet 5.5 | Default | Mid-tier third-party coding model at $2 / $10. Stronger than the flash models, cheaper than Opus and Sol. Uses the smaller pool. |

### Speed

Fast agent turns that still last on Pro. Ranked by useful speed at a low burn rate, with the larger pool preferred.

| Rank | Model | Setting | Why |
| --- | --- | --- | --- |
| 1 | Composer 2.5 | Normal speed | Fastest first-party option that stays cheap. $0.50 / $2.50 on the larger pool. This is the daily driver. |
| 2 | GPT-5.6 Luna | Normal speed | Smallest GPT-5.6 variant, built for cost and speed. $0.20 / $1.20. Cheapest token rate on this list, on the smaller pool, so keep it for short tasks. |
| 3 | Gemini 3.8 Flash | Default | Fast Gemini tier at $0.75 / $3.50. Cheaper than Gemini 3.5 Flash ($1.50 / $9). Uses the smaller pool. |

## What to leave on

| Model | Daily use |
| --- | --- |
| Composer 2.5 | On. Default agent model. Normal speed. |
| Grok 4.7 | On. Switch to it for hard tasks. Medium for balance, high or xhigh for hard tasks. Normal speed. |
| Grok 4.6 | Optional fallback. Same token price as Grok 4.7. |
| Claude Opus 5.5, GPT-5.6 Sol, Claude Sonnet 5.5, Gemini 3.5 Flash, Gemini 3.8 Flash, GPT-5.6 Luna | Off for daily agent runs. Turn one on only for the matching row above. |

## Earlier recommendation

Composer 2.5, at normal speed, is the model to leave on for daily agent work on the $20 Pro plan.

It is the speed-and-cost option in the larger included pool. Cursor prices it at $0.50 per million input tokens and $2.50 per million output tokens. Grok 4.7, the stronger model in that same pool, is $2 and $6. Opus 5.5 and GPT-5.6 Sol are about $4 and $20, and they draw from the smaller third-party pool. Composer 2.5 Fast jumps to $3 and $15, so leave Fast off. Normal Composer is already the fast setting.

Pro gives you two monthly pools. The larger one covers only Grok 4.7, Grok 4.6, Grok 4.5, and Composer 2.5. Claude, GPT, and Gemini come out of the smaller pool at full API rates. In the 4 October 2026 model list, Composer 2.5 was off and Opus, GPT-5.6 Sol, and Sonnet 5.5 were on. That setup spends the smaller pool first.

Use this split:

- Everyday agent work: Composer 2.5, normal speed. Edits, refactors, tests, multi-file changes.
- When it stalls on a hard or long task: switch that chat to Grok 4.7, normal speed, medium effort. Same big pool, better at staying with difficult work, about four times the input cost, so use it only when Composer is not enough.
- Leave off for daily use: Claude Opus 5.5, Claude Opus 5, GPT-5.6 Sol, Claude Sonnet 5.5, Gemini 3.5 Flash. Save those for a rare hard problem after the Cursor pool is low.

Pick Composer 2.5 directly in the model picker. Auto can route to an expensive third-party model and bill that model’s price.
