# Project Handover — Grab Merchant Voicebot UC4

**Date:** 2026-10-10  
**Current implementation:** `UC4_GrabFood_Cancelled_Order_Compensation_Natural_KB_2026-10-09.zip`

## 1. Project objective

Build a Cognigy voice AI Agent for Grab Malaysia Merchant Support, focused on cancelled-order compensation.

The long-term UC4 scope includes GrabFood and GrabMart, compensation education, compensation-status guidance, Request for Compensation guidance, recovery paths, and transfer/safety handling.

**Current implementation scope is intentionally much smaller:** prove a clean thin-agent architecture for the first two GrabFood benchmark behaviors before adding later journeys.

QA can refer to these behaviors as TC-001 and TC-002. **Never expose test-case IDs, benchmark terminology, “scoped build”, or implementation language inside the Agent-visible Job prompt.**

The Merchant should experience one natural Grab support conversation.

---

## 2. Source-of-truth files

Use these in this priority order when there is a conflict.

### A. `Grab Merchants Voicebot Use Case 4.docx`
Primary behavior/persona specification.

Important areas:
- V4 English Persona
- hard constraints
- scope
- voice-channel behavior
- identity and tone
- expression rules
- ASR tolerance
- grounding
- cancellation-date handling
- threshold rules
- Knowledge Base usage
- within-threshold EDUCATE behavior
- first follow-up behavior
- closing discipline
- guidance/transfer/safety behavior for later phases

Key persona intent:
- Grab AI assistant / virtual representative
- friendly, energetic, warm, professional, genuinely helpful
- short natural voice replies
- one clear question per turn
- answer direct questions first
- follow the Merchant, not a rigid script
- do not repeatedly ask for information already given
- use `compensation`, not `refund`, for this use case
- do not expose internal machinery
- do not ask for Merchant-identifying information; Merchant is already verified
- GrabFood/GrabMart line of business is already known from IVR
- do not verbalize internal threshold calculations

### B. `NiCE - Analysis of Documents from Grab.docx`
Architecture/mapping reference.

Important mapping:
- AI Agent: noisy-ASR understanding, intent/entity interpretation, empathy, turn-level phrasing, grounded follow-up Q&A
- Tools: deterministic/business capabilities such as resolving order age, guidance actions, transfer, safety
- RAG/Knowledge is not automatically equivalent to a Tool
- a Wiz “Task” is not automatically a Cognigy Tool

### C. `Grab Pilot Test Cases - 30 Sep 2026.xlsx`
QA and acceptance reference.

Current external QA focus:
- TC-001: recent cancelled prepared GrabFood order → compensation education → normal close
- TC-002: same recent path → Merchant asks a follow-up → guidance is offered → Merchant declines guidance → normal close

**Test names remain outside the Agent prompt.**

### D. `GrabMY_FAQ_GrabFood.docx`
Current GrabFood Knowledge source.

It is broad Help Centre content, not a UC4-only policy document. It contains many unrelated topics. Use it only when the Merchant asks a factual question that the Job/approved Flow content does not answer.

### E. `GrabMY_FAQ_GrabMart.docx`
Future GrabMart Knowledge source.

For the current GrabFood-only implementation, avoid retrieving this content.

---

## 3. Architecture principle

The target architecture is:

> **AI Agent owns conversation.  
> Code computes.  
> Tools expose capabilities.  
> Say/localization owns approved wording.  
> Knowledge answers grounded factual questions.  
> Flow handles lifecycle and hard side effects.**

Do not turn the Cognigy canvas into a visual state machine for normal conversation.

### Keep deterministic
Use deterministic logic where a wrong answer is unacceptable:
- cancellation age
- internal threshold
- actual side effects such as hang-up/transfer
- hard safety gates when added later

### Keep generative
Let the AI Agent handle:
- natural Merchant intent
- Manglish/ASR interpretation
- conversational follow-ups
- guidance decline
- natural acknowledgements
- whether a Merchant is answering the last question or raising a new question

### Keep exact wording outside the LLM
Use Say/localized content when wording must be approved/verbatim:
- compensation timeline
- photo reminder
- normal closing
- other compliance text added later

---

## 4. Important implementation rules

### Do not leak QA vocabulary
Never put these in the Agent-visible Job:
- TC-001
- TC-002
- benchmark
- test case
- Band 1
- scoped build
- expected tool path

### Prefer native Cognigy nodes
Do not use Code Nodes for simple assignments such as:

```js
context.foo = true;
```

If persistent state is genuinely needed, use Cognigy Context / Add To Context where practical.

Use Code only when there is real computation or transformation.

### Tool parameters
Prefer Cognigy graphical parameters.

Do not use custom JSON Schema unless the graphical editor cannot represent a required contract.

The previous package produced a “JSON incompatible with graphical editor” warning because it used custom/complex parameter schema shapes. The current `resolve_order_age` tool uses a simple graphical-style string argument.

### Do not track conversation state without a reason
Flags such as:
- `followupAnswered`
- `guidanceDeclined`

were inherited from a more deterministic state-machine design.

Do not reintroduce them unless a later rule genuinely needs persistent state across turns.

---

## 5. Current package

**Package:** `UC4_GrabFood_Cancelled_Order_Compensation_Natural_KB_2026-10-09.zip`

Package metadata:
- Cognigy package version: `2026.20.1`
- Flow: `UC4_GrabFood_Cancelled_Order_Compensation`
- Locale: `en-US`
- 24 node resources
- 2 Code Nodes
- 1 If node
- 4 Tool Actions

### Current high-level Flow

```text
Start
  |
Initialize Once
  |-- On First Time
  |     |
  |     +-- Code: Initialize session
  |         |
  |         +-- Set Session Config (EN)
  |             |
  |             +-- Say: Greeting
  |
  +-- AI Agent Job: GrabFood Cancelled Order Compensation
        |
        +-- resolve_order_age
        |     |
        |     +-- Code: resolve_order_age
        |           |
        |           +-- If approved recent-order response
        |                |
        |                +-- Then -> approved timeline/photo/anything-else Say
        |                |
        |                +-- Else -> Resolve Tool Action with facts
        |
        +-- further_inquiry
        |     |
        |     +-- approved follow-up + guidance-offer Say
        |
        +-- guidance_declined
        |     |
        |     +-- Anything-else Say
        |
        +-- end_call
              |
              +-- Approved Goodbye Say
                    |
                    +-- Hang Up
```

---

## 6. Current Agent Job

**Job Name:** `GrabFood Cancelled Order Compensation`

**Job Description:**

> Help verified GrabFood merchants with compensation for orders that were cancelled after the food was prepared.

The Job intentionally contains no test-case or benchmark language.

Main instruction themes:
- persona and voice style from V4
- verified Merchant / known GrabFood LOB
- do not ask for Merchant-identifying information
- short spoken replies
- one clear question per turn
- answer direct questions first
- use compensation, never refund for this use case
- grounded answers only
- use Knowledge only for relevant factual questions not already answered
- silently tolerate obvious ASR/Manglish variation
- call `resolve_order_age` for supported relative dates
- keep threshold internal
- do not duplicate Say-node output after a Tool branch speaks directly
- close only after Merchant confirms there is nothing else

---

## 7. Current tools

### `resolve_order_age`

Purpose:
- deterministic cancellation-age and GrabFood internal threshold calculation

Parameter:
- `days_ago`
- String
- whole-number text

Examples:
- today → `"0"`
- yesterday / semalam → `"1"`
- two days ago / kelmarin → `"2"`

Current business threshold table:

```js
{
  Mon: 4,
  Tue: 4,
  Wed: 2,
  Thu: 2,
  Fri: 2,
  Sat: 3,
  Sun: 4
}
```

Tool result contains:
- `success`
- `ageDays`
- `threshold`
- `dateRequired`
- `presentTimeline`

`threshold` is internal only. Never say “within threshold” or “beyond threshold” to the Merchant.

### `further_inquiry`

Use after the approved compensation timeline when the Merchant asks what to do if compensation still has not arrived.

No parameters.

Current direct Flow response:

> If you're eligible for compensation, you'll see the Request for Compensation section within that cancelled order in your GrabMerchant app. If you can't see it, you should submit a request for our support team to review further. Would you like to be guided to your cancelled order?

### `guidance_declined`

Use when the Merchant declines the guidance offer.

No parameters.

Current direct response:

> Is there anything else I can help you with?

### `end_call`

Use only after the Merchant was asked whether anything else is needed and clearly indicates they are finished.

No parameters.

Current closing:

> Thank you for calling Grab. If there's anything else you need help with, please contact us again. Have a nice day.

Then Hang Up.

---

## 8. Approved current recent-order response

Current exact Say content:

> Compensation for a cancelled order is usually approved within one to two business days after the order was made, and it is then paid in your next payout cycle, the same cycle as your regular order earnings, subject to Grab's cancellation policy and guidelines. Please take a photo of the prepared food as evidence, in case you would like to submit a request for our support team to review further after it has been more than two business days. Is there anything else I can help you with?

Important behavior:
- timeline
- then photo reminder
- then anything-else question
- same response
- do not automatically offer a walkthrough after this response

---

## 9. Current initialization

Current session state:

```js
context.shortTermMemory.uc4 = {
  lob: "GrabFood",
  today: {
    iso: "...",
    weekday: "..."
  },
  ageDays: -1,
  dateSource: "",
  threshold: "",
  educateDelivered: false
};
```

### Known concern
`Initialize session` currently calculates Malaysia time with a hard-coded UTC+8 offset.

The source persona refers to current system date/time. A future cleanup should evaluate whether Cognigy-native/system date values should replace this code.

Do not change this casually if it can affect threshold behavior. Validate against the threshold table after any date/time refactor.

---

## 10. Knowledge configuration

Current AI Agent Job configuration:
- `knowledgeSearchBehavior = onDemand`
- `knowledgeSearchAiAgentKnowledge = true`
- `knowledgeSearchJobKnowledge = false`
- `knowledgeSearchTopK = 3`
- `knowledgeSearchTags = ""`
- tag filter operator = `and`

### Important open issue
Both GrabFood and GrabMart documents are currently in the Merchant Knowledge area.

The current prompt tells the Agent to ignore GrabMart content, but **retrieval itself is not source-filtered in the package** because `knowledgeSearchTags` is empty.

Preferred next step:
1. tag `GrabMY_FAQ_GrabFood.docx` with a GrabFood-specific source tag, for example `grabfood`;
2. tag GrabMart separately;
3. configure this Job to retrieve only the GrabFood source tag;

or use a GrabFood-only Knowledge Store.

Do not rely only on the prompt to filter wrong-brand RAG results.

Also verify after import that `[MY] Grab Merchant KB` is actually assigned to the AI Agent in the target Cognigy Project. The package uses AI-Agent Knowledge rather than embedding a Knowledge Store directly in the Job.

---

## 11. Current model/runtime note

The package Job has:

```text
llmProviderReferenceId = default
```

It does **not** force a specific OpenAI runtime model.

Using GPT-6.1 Sol to build/refactor the package is separate from which model Cognigy runs at runtime.

If runtime-model changes are required, configure them in the Cognigy AI Agent / LLM resource and test compatibility. Do not insert an assumed model ID into package JSON without confirming the target tenant supports it.

---

## 12. Known gaps

These are intentional or unresolved.

### A. Relative-date support is narrow
Current `resolve_order_age` accepts numeric `days_ago`.

The V4 source also supports:
- weekdays
- calendar dates
- vague dates with limited clarification
- date corrections

Those are not implemented in this minimal package yet.

Do not let the LLM calculate the business threshold itself as a shortcut.

### B. No beyond-threshold journey yet
The package does not implement the later GrabFood journeys for status check, Request for Compensation submission, platform/style/loudspeaker preferences, app/portal walkthroughs, recovery, or transfer.

That is intentional.

### C. GrabMart is not implemented
Do not add GrabMart behavior into the current GrabFood Job.

### D. Localization
Only `en-US` exists in the package.

The longer-term design should use Cognigy localization for Merchant-facing approved content instead of hard-coding each language in Code.

### E. Knowledge retrieval isolation
Needs proper source tagging/store separation as described above.

### F. Initialize-session Code Node
Still exists. It can potentially be simplified with Default Context/native Cognigy nodes, but date calculation must stay correct.

---

## 13. What not to do

Avoid these regressions:

### Do not rebuild the old deterministic protocol
Do not introduce:

```text
next_action
say
guide
verbatim
step_id
```

as a custom protocol between Code and the LLM.

### Do not rebuild conversation as If/Else diamonds
Use If nodes only for genuine deterministic application routing.

Do not create a tree such as:

```text
if Merchant wants X
  if Merchant said Y
    if guidance declined
      ...
```

Normal intent and conversational transitions belong to the AI Agent.

### Do not move Code complexity into the canvas
A refactor is not successful if JavaScript gets slightly smaller while node count doubles.

### Do not use Code as a checkbox
Avoid Code Nodes whose only purpose is:

```js
foo = true;
```

### Do not let Knowledge override approved UC4 behavior
RAG is supplemental.

Approved journey rules and exact Flow content take precedence.

### Do not expose internal implementation
The Merchant must never hear:
- test-case IDs
- threshold labels
- tool names
- Flow names
- Knowledge/FAQ/database terminology
- implementation rationale

---

## 14. Immediate QA scripts

These names are QA-only.

### TC-001

Merchant:

> My order got cancelled yesterday after I prepared the food. When will I receive compensation?

Expected:
1. Agent interprets yesterday as one day ago.
2. `resolve_order_age(days_ago="1")`
3. internal route is recent/within threshold.
4. Flow sends approved timeline + photo reminder + anything-else question.
5. Agent does not duplicate/paraphrase the Say response.

Merchant:

> No, that's all.

Expected:
1. `end_call`
2. approved closing
3. Hang Up

### TC-002

Merchant:

> My order was cancelled yesterday. When will I be compensated?

Expected:
- same recent-order approved response.

Merchant:

> What if I still don't receive it?

Expected:
- `further_inquiry`
- approved follow-up response
- guidance offer

Merchant:

> No, I don't need guidance.

Expected:
- `guidance_declined`
- “Is there anything else I can help you with?”
- no walkthrough starts

Merchant:

> No, that's all.

Expected:
- `end_call`
- approved closing
- Hang Up

---

## 15. Recommended next engineering sequence

Do not add many future journeys at once.

### Step 1 — Stabilize current two behaviors
Test:
- normal English
- Manglish
- “yesterday”
- “semalam”
- follow-up variants
- clear guidance decline
- clear close
- Merchant asks an unrelated factual question and Knowledge behaves correctly
- no duplicate response after Tool Actions

### Step 2 — Fix Knowledge isolation
Add GrabFood source filtering or a dedicated GrabFood Knowledge Store.

### Step 3 — Improve date handling
Extend deterministic date resolution for:
- weekday
- calendar date
- vague-date clarification
- correction

Preserve source threshold rules exactly.

### Step 4 — Add the next behavior only after the reference architecture is stable
When adding later benchmark behavior, prefer adding one capability at a time.

Do not copy the old giant walkthrough state machine back into the Flow.

---

## 16. Ubiquitous language

Use these terms consistently.

- **Merchant** — verified Grab merchant calling support
- **AI Agent** — Cognigy generative agent handling conversation
- **Job** — current cancelled-order compensation responsibility
- **Tool Action** — structured capability the Agent can call
- **Flow** — Cognigy orchestration/lifecycle structure
- **Context** — persistent session state
- **Knowledge** — retrieved Grab Help Centre information
- **approved Flow content** — Merchant-facing text that must be controlled outside free generation
- **compensation** — Merchant payment for eligible cancelled prepared order
- **Request for Compensation** — business action/form; preserve official name
- **GrabMerchant app** — official product name
- **GrabMerchant portal** — official product name
- **Closing A** — QA/design name for the normal successful close; do not expose to Merchant
- **threshold** — internal business routing result; never expose to Merchant

---

## 17. Relevant Cognigy product guidance

The architecture deliberately follows Cognigy's hybrid AI-Agent model:

- Job-specific behavior belongs in the AI Agent Job.
- Tool Actions provide structured capabilities; the Agent selects tools based on tool descriptions and parameters.
- Tool branches can use normal Flow nodes, services, scripts, handover, Say, or Resolve Tool Action.
- Cognigy Context persists through a session and can be modified with native nodes.
- Knowledge/RAG should provide relevant domain knowledge, but it does not replace deterministic business logic or approved wording.

Official Cognigy references to review when changing architecture:
- Getting Started with AI Agents
- Give your AI Agent a Job
- Improve your AI Agent's skills using Tool Actions
- Make knowledge available to your AI Agent
- Context
- Add To Context
- Debugging your AI Agent

---

## 18. Copy/paste brief for the next LLM

> You are taking over a Cognigy Grab Merchant Voicebot project for Malaysia UC4: cancelled-order compensation.
>
> Read these source files first: `Grab Merchants Voicebot Use Case 4.docx`, `NiCE - Analysis of Documents from Grab.docx`, `Grab Pilot Test Cases - 30 Sep 2026.xlsx`, `GrabMY_FAQ_GrabFood.docx`, and `GrabMY_FAQ_GrabMart.docx`.
>
> The latest working package is `UC4_GrabFood_Cancelled_Order_Compensation_Natural_KB_2026-10-09.zip`.
>
> Current implementation is intentionally GrabFood-only and currently proves the first two benchmark behaviors. Test-case names are QA-only and must never appear in Agent-visible prompts or Merchant responses.
>
> Preserve the thin-agent architecture:
> - AI Agent owns natural conversation and intent.
> - Code is only for real deterministic computation.
> - Tool Actions expose structured capabilities.
> - Say/localization owns approved wording.
> - Knowledge is supplemental and grounded.
> - Flow/If nodes are for genuine application control, not conversational state-machine routing.
>
> Do not reintroduce the old `next_action / say / guide / verbatim` protocol.
> Do not use complex custom JSON tool schemas when Cognigy's graphical parameters are sufficient.
> Do not use Code Nodes for simple state assignments.
>
> Before changing anything, inspect the package structure and compare the requested change against the V4 source behavior. Explain any conflict instead of silently choosing one.
>
> The immediate priorities are:
> 1. validate the current recent-order and first-follow-up behaviors;
> 2. isolate Knowledge retrieval to GrabFood;
> 3. extend deterministic date handling safely;
> 4. only then add later compensation journeys one at a time.
>
> Keep the Merchant experience natural. Never expose threshold labels, test IDs, tool names, Flow names, Knowledge/FAQ/database terminology, or implementation details.

