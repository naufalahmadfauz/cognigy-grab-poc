# Grab UC4 Merchant Voicebot: Cognigy Technical Design Document

Oct 6, 2026 · @Aryo Nugraha

## 1. Document Control and Purpose

This Technical Design Document (TDD) is the build guide for the Grab Malaysia Merchant Voicebot, Use Case 4 (UC4: compensation for orders cancelled after preparation), on Cognigy.AI with NICE CXone. It translates the 45 Grab pilot test cases into a Cognigy design, with most of the detail on the AI Agent tools so the implementation team can build each one directly from this document.

### 1.1 Revision History

| Version | Date | Author | Summary of change |
| --- | --- | --- | --- |
| 0.1 | 2026-10-06 | Amansob | First draft for internal review. Tool design, context model, test traceability and open items. |
| 0.2 | 2026-10-06 | Amansob | Aligned with the cognigy-code-patterns guideline: state moved to context.shortTermMemory.uc4, tool results returned through actions.output, Code nodes written without return statements. Content split into fixed, guided and knowledge tiers. Knowledge options for Cognigy Knowledge AI and CXone Expert. |
| 0.3 | 2026-10-06 | Amansob | Language design: the bot converses in English, Bahasa Melayu and Manglish in one build. Language packs for Tier 1 text, conversation language follows the merchant, Malay and English speech recognition together, Malay and Manglish test runs. English only positions removed. |

### 1.2 Source documents

| Ref | Document | Role in this design |
| --- | --- | --- |
| SRC-1 | Grab Pilot Test Cases, 30 Sep 2026 (sheet: Use Case 4 Test Cases ENG, TC-001 to TC-045) | Acceptance criteria. The build is judged against these. 15 are benchmark cases. |
| SRC-2 | Grab Pilot Test Cases, sheet: Scenario Flow | Node level scripts in English and Malay, and flow logic. |
| SRC-3 | Grab Merchants Voicebot Use Case 4 (Wiz AI V4 English persona, GrabFood and GrabMart nodes, 19 tasks, 4 exits, global safety, V3 BM persona) | Behavioural reference from the current production bot. Used to resolve gaps and conflicts in SRC-1 and SRC-2. |
| SRC-4 | NiCE: Analysis of Documents from Grab | Principal's proposed Cognigy mapping and tool list. |

### 1.3 Scope of this document

In scope: conversations in English, Bahasa Melayu and Manglish, Flow architecture, AI Agent configuration, the full tool catalogue with schemas and Code node logic, the context state model, the step catalogue for app and portal walkthroughs, CXone handover, voice configuration, test traceability and open items.

Out of scope: the CXone IVR and Studio scripts (owned by NiCE and Grab), CXone agent routing and skills, and Cognigy tenant provisioning.

### 1.4 How to read this document

Section 7 is the build specification for the tools and is the main reference for developers. Sections 4 and 11 list where the source documents disagree and which position this build takes, so testers know what to expect.

## 2. Solution Overview

The solution is one Cognigy Flow, UC4\_CancelledOrder\_Main, with a single AI Agent node that talks to the merchant and nine tools that hold every deterministic rule. CXone passes the call in with the line of business (GrabFood or GrabMart) already known. The bot converses in English, Bahasa Melayu and Manglish, explains compensation timelines, walks the merchant through the GrabMerchant app or portal, and transfers to a CXone agent only in the defined cases.

**Design stance:** hybrid agentic. The LLM handles language: understanding noisy Manglish ASR, working out what the merchant wants, empathy, and phrasing. The tools handle anything that must be exact and testable: the threshold verdict, counters and caps, the step text for each screen, the order of portal routes, transfer eligibility, and exit messages. SRC-3 shows why this split matters. Its prompt has grown to about 430,000 characters of rules written to stop an LLM from miscounting days, repeating questions and inventing menu paths. In Cognigy these rules move into code.

### 2.1 Capabilities

| Capability | How it is delivered | Test cases |
| --- | --- | --- |
| Order age and threshold verdict | resolve\_order\_age tool, weekday lookup tables per LOB | TC-001 to 005, 019, 022, 025 to 029, 042, 045 |
| Compensation timeline (EDUCATE / IFI) | resolve\_order\_age returns the approved script per LOB | TC-001, 004, 025, 028 |
| Follow up answer after EDUCATE | get\_approved\_answer tool | TC-002, 017, 026, 040 |
| Guidance preferences (platform, style, loudspeaker) | set\_guidance\_preference tool | TC-003, 005 to 009, 012 to 016 |
| View cancelled order walkthrough | start\_walkthrough and advance\_walkthrough | TC-017, 040 |
| Compensation status check | start\_walkthrough and advance\_walkthrough | TC-003, 005 to 008, 027, 029 to 031 |
| Request for Compensation submission, portal route ladder, role path | start\_walkthrough and advance\_walkthrough | TC-003, 006 to 009, 013 to 016, 030 to 032, 036 to 039 |
| Difficulty cap | advance\_walkthrough stuck ladder | TC-007, 018, 031, 041 |
| Second order in one call | resolve\_order\_age with is\_new\_order | TC-021, 044 |
| Knowledge fallback | search\_knowledge tool, narrow scope | Follow up questions not covered by scripts |
| Transfer to CXone (classified 'others') | transfer\_to\_live\_agent tool | TC-009, 010, 016, 018, 020, 024, 032, 033, 039, 041, 043 |
| Safety escalation | escalate\_safety tool | TC-011, 012, 034, 035 |
| Call endings | end\_call tool with four exit types | All closing paths, TC-023, 024 |
| English, Bahasa Melayu and Manglish | Understands all three and replies in the merchant's language. Starts from the test page (default English), then follows the merchant through get\_approved\_answer (topic language\_request). Tier 1 text held in a language pack per language (6.7). | TC-023, TC-024, and the Malay run of the test cases (Section 10) |

### 2.2 Key design principles

- **Rules in code, language in the LLM.** Any rule that a tester can check against a number, a count or an exact phrase lives in a tool.
- **The LOB is never asked.** It comes from CXone and is fixed for the call. The bot never asks or confirms GrabFood versus GrabMart.
- **Tools return the next action.** Every tool returns an action code plus either fixed wording or a guide. The AI Agent does not choose the route itself.
- **Three content tiers.** Tier 1 fixed text is said exactly: policy timelines, the photo reminder, the partial compensation line, the step catalogue, and the transfer, safety and exit lines. Tier 2 guided text gives the LLM the intent and the facts and lets it phrase the reply. Tier 3 knowledge answers open follow up questions from a curated store of Grab approved articles.
- **Single state object.** context.shortTermMemory.uc4 is the one source of truth for session state, following the team convention. Code: Initiate creates it on every call without overwriting anything else in shortTermMemory.
- **Follows cognigy-code-patterns.** Tool arguments from input.aiAgent.toolArgs, if/else chains with no return statements in Code nodes, tool results through actions.output, and no null values written to context.
- **Voice first output.** No markdown, numbers spoken as words, one question per turn, every walkthrough step ends with a check back.
- **Configurable where the sources disagree.** Positions that Grab has not confirmed (difficulty cap ladder, portal exhaustion behaviour, role retry) are flags in context.uc4Cfg so they can change without a rebuild.

* **Two languages, one build.** Tools are language neutral. Tier 1 text lives in an English pack and a Malay pack with the same shape; Tier 2 guides stay in English and the LLM replies in the session language. Adding Malay costs translation and testing, not a second Flow.

## 3. Solution and Flow Architecture

The call enters CXone, where the IVR verifies the merchant and records the LOB, then reaches the Cognigy Flow through Voice Gateway. A short start up sequence runs once per call, then the AI Agent node takes every turn until a tool transfers or ends the call.

&#91;embedded content: UC4 architecture · CXone in, AI Agent, nine tools, CXone out\]

The AI Agent never decides a route or a count itself: returning tools read and write context.shortTermMemory.uc4 and hand back the next action through actions.output, and terminal tools end the call with fixed wording.

### 3.1 Start up sequence

The Flow uses a Once node so that initialisation and the greeting run only on the first input of the session. Every later input goes straight to the AI Agent node.

| # | Node | Purpose |
| --- | --- | --- |
| 1 | Start | Flow entry point. |
| 2 | Once | First branch runs nodes 3 to 6. Afterwards branch goes to node 7. |
| 3 | Code: Initiate | Reads the LOB and call identifiers from the call setup data. Code: Config runs first and loads context.uc4Cfg (thresholds, scripts, step catalogue, flags) and the English and Malay content packs (6.7). Code: Initiate then reads the LOB and call identifiers and builds context.shortTermMemory.uc4 with defaults. |
| 4 | If: LOB valid | If context.shortTermMemory.uc4Valid is false (LOB not GrabFood or GrabMart), transfer to CXone with reason lob\_missing (no merchant facing question). |
| 5 | Set Session Config | Voice settings for the session language: an If on uc4.lang selects the English or the Malay Set Session Config node (STT language and phrase hints, TTS voice, barge-in, no input timeout). See Section 9. |
| 6 | Say: Greeting | Fixed greeting with the recording notice in the session language ({{context.uc4Cfg.messages.greeting}}, from SRC-2 Greeting). Ends the execution and waits for the merchant. |
| 7 | AI Agent: Gebi UC4 | Handles every merchant turn. Selects tools. Its tool children are listed in Section 7. |

### 3.2 Separation of concerns

| Layer | Owns | Does not own |
| --- | --- | --- |
| CXone IVR and Studio | Merchant verification, LOB selection, call recording, agent routing after transfer | Any UC4 dialogue |
| Code: Initiate and context.uc4Cfg | Configuration: thresholds, approved scripts, step catalogue, feature flags | Runtime decisions |
| AI Agent node | Understanding the merchant, choosing which tool to call, natural phrasing, empathy, answering direct questions first | Counting, thresholds, step text, transfer eligibility |
| Tool Code nodes | State changes in context.shortTermMemory.uc4, the next action, approved wording | Free text generation |
| Say, Transfer and Hang Up nodes inside tools | Fixed messages that must be verbatim (safety, transfer, exits) |  |

### 3.3 Tool execution pattern

Every tool except the three terminal ones follows the same pattern, so developers build it once and copy it.

1. The AI Agent selects the tool and fills its arguments.
2. The tool's Code node reads input.aiAgent.toolArgs, updates context.shortTermMemory.uc4 and builds a result object named out, using if/else chains only. There are no return statements anywhere in the node (cognigy-code-patterns, gotcha 1).
3. The Code node ends with actions.output("", out). The empty first argument means nothing is spoken; out goes back to the AI Agent as the tool result (Pattern 6). The node also keeps a copy in input.uc4Result for debugging.
4. A Resolve Tool Action node closes the tool call and hands control back to the AI Agent. Confirm in sprint 0 that the project's Cognigy version passes the actions.output payload through to the agent. If it does not, set the Resolve Tool Action answer to {{JSON.stringify(input.uc4Result)}} instead (OI-19).

The terminal tools (transfer\_to\_live\_agent on consent, escalate\_safety, end\_call) do not resolve back. They play a fixed Say node and then run a Voice Gateway Transfer or Hang Up node, so the LLM cannot add words after the final message.

## 4. Design Rationale and Decisions

The test cases are the acceptance criteria, but they disagree with each other and with SRC-2 and SRC-3 in several places. The table below fixes the position this build takes on each one. Where Grab has not confirmed a position, the behaviour is a flag in context.uc4Cfg and the item is also listed in Section 11.

| ID | Decision | Why | Sources | Config flag |
| --- | --- | --- | --- | --- |
| D-01 | One AI Agent node for both LOBs, with the LOB injected as a variable. SRC-3 uses one sub agent per LOB. | GrabFood and GrabMart differ only in data (thresholds, wording, step routes). Keeping one node means one set of tools and one instruction set to maintain. | SRC-3, SRC-4 | none |
| D-02 | The threshold is decided by a weekday lookup table in code, not by counting business days. | SRC-3 reports the LLM put weekday answers on the wrong side about a third of the time. A table in code is exact and testable. | SRC-3 | thresholdTable |
| D-03 | Difficulty cap ladder per step: repeat, repeat, clarify, clarify, then offer a person. | TC-018 and TC-041 describe this ladder in the most detail. SRC-2 (repeat once, clarify, offer) and SRC-3 (offer after two failures) differ. | SRC-1, SRC-2, SRC-3 | stuckLadder |
| D-04 | All three portal routes fail: offer a person (consent), not a soft close. | The TC-016 and TC-039 transcripts and SRC-3 all offer a person. Only the TC flow path text and SRC-2 say soft close. | SRC-1, SRC-3 | portalExhaustedAction |
| D-05 | Form not visible: scroll first, then the Owner or Manager reminder with a retry offer. Retry works: fill the form. Retry fails (2 attempts total): offer a person. Retry declined: Final Educate soft close, then UDR. | Covers benchmark TC-006 (both its flow path and transcript) and TC-009. SRC-3 removes the retry, which would fail both. | SRC-1, SRC-2 | roleRetryEnabled, roleMaxAttempts |
| D-06 | GrabFood status check. App: Orders tile, then Cancelled tab. If the order is missing, use History and Date selector. Portal: Finance, Transactions, period and store, Category. | Matches TC-003 to TC-008 and SRC-3. SRC-2 has an older route. | SRC-1, SRC-3 | stepCatalogue |
| D-07 | GrabMart status check is portal only, whichever device the merchant is on. It opens with the partial compensation sentence, said verbatim. | Matches TC-029 to TC-031 and SRC-3. TC-027 does the check in the app and is treated as a test case defect (OI-03). | SRC-1, SRC-3 | stepCatalogue |
| D-08 | Timeline wording: approved within the LOB's business days, then paid in the next payout cycle, subject to Grab's policy. | Used by the benchmark transcripts and SRC-3. SRC-2's "credited to your bank account" is older (OI-04). | SRC-1, SRC-3 | scripts |
| D-09 | Knowledge AI is a narrow fallback, never the first source. | SRC-3 notes say Help Centre RAG caused hallucinations, so Grab moved to scripted answers. | SRC-3 | knowledgeEnabled |
| D-10 | Transfer uses a Voice Gateway Transfer node with the destination from config and classification 'others'. | Test remarks show the destination is not yet configured. One config value fixes every transfer path. | SRC-1, SRC-2 | transferTargets |
| D-11 | Preference order: platform, then style, then loudspeaker, one per turn, each asked at most twice. | SRC-3 order. Test transcripts vary the order, and SRC-1 accepts wording that "shares the same objective". | SRC-1, SRC-3 | none |
| D-12 | The bot understands English, Bahasa Melayu and Manglish and replies in the merchant's language. It starts in the language set by the test page (default English) and switches when the merchant asks for, or moves to, the other language. Manglish alone does not trigger a switch. Any other language gets one ask, then an offer of a person. | Grab already holds Malay scripts for every node (SRC-2) and a Malay persona (SRC-3 V3 BM). TC-023 and TC-024 were written for a single language agent; that behaviour is kept as languageSwitch = ask\_then\_transfer (OI-09). | SRC-1, SRC-3 | none |
| D-13 | A declined offer of a person is not repeated, unless the merchant asks for a person in their own words. | SRC-3 rule. Prevents repeated offers that test cases do not expect. | SRC-3 | none |
| D-14 | Three content tiers. Fixed: said exactly. Guided: the tool returns intent and facts and the LLM phrases the reply. Knowledge: open follow up questions from a curated store. | Verbatim is needed only where Grab or SRC-3 demands it. Scripting every reply makes the bot stiff and puts unapproved wording into fixed text. Broad RAG is avoided because SRC-3 reports it hallucinated. | SRC-3, design review | fixed, guided |
| D-15 | Session state lives in context.shortTermMemory.uc4. | Team convention used in earlier Amansob builds and in cognigy-code-patterns. Writing only the uc4 key, behind a guard, never overwrites anything the AI Agent node keeps in shortTermMemory. | cognigy-code-patterns | none |
| D-16 | Code nodes use if/else chains with no return statements, and send the tool result with actions.output("", out). | Validated production patterns (gotcha 1 and Pattern 6). Helpers are expression arrow functions or functions that write to out, so the return keyword never appears. | cognigy-code-patterns | none |
| D-17 | Knowledge comes from Cognigy Knowledge AI (option A) or CXone Expert (option B, Pattern 9), depending on where Grab's approved content lives. | Both feed the same search\_knowledge tool contract, so the AI Agent and tests do not change with the choice. | SRC-4, cognigy-code-patterns | knowledgeSource |
| D-18 | One build serves both languages through language packs. Tools are language neutral; Tier 1 text is held per language; Tier 2 guides stay in English and the LLM replies in the session language. | Avoids a second Flow and a second set of tools. A language switch is a pack swap plus a Set Session Config, so it can happen mid call. | SRC-2, SRC-3 | languageSwitch, content |

## 5. AI Agent Configuration

The AI Agent instructions describe behaviour and tone only. Every rule a tool already enforces is stated once, as "follow the tool's next\_action", so the instructions stay short and the two cannot drift apart.

### 5.1 Parameters

| Parameter | Value |
| --- | --- |
| AI Agent (persona) | Grab AI Assistant, introducing itself as Gebi in Bahasa Melayu (SRC-2 Malay greeting). One AI Agent serves both languages; the job instructions carry the session language. |
| Job | UC4 Cancelled Order Compensation |
| LLM resource | Per NiCE tenant standard. Low latency model required for voice (OI-10). |
| Temperature | 0.2 |
| Tool choice | auto |
| Max tokens | 400 (spoken replies are short) |
| Timeout | 8000 ms, with a fallback Say: "Sorry, give me a moment." |
| Memory | Short term memory on, transcript of the full call. Do not inject context.shortTermMemory.uc4 into the prompt as a snippet: it is large, and tools already return the state the agent needs. |
| Stream output | On, stop tokens . ! ? so TTS starts early |
| Knowledge at node level | None. Knowledge is reached only through the search\_knowledge tool. |
| Safety flags | All four enabled: harmful content, ungrounded content, copyright, jailbreak. |
| Error handling | Continue on error. A tool error returns next\_action = apologise\_and\_retry\_once. |

### 5.2 Job instructions (to paste into the AI Agent node)

```text
ROLE
You are Grab's AI assistant (Gebi in Bahasa Melayu) on a voice call with a Grab merchant partner in
Malaysia. This call is about {{context.shortTermMemory.uc4.lob}} orders only. The merchant was verified
before reaching you. You help with one thing: compensation for an order cancelled after it was prepared.

LANGUAGE
Merchants speak English, Bahasa Melayu or Manglish (English and Malay mixed in one sentence).
Understand all three. Reply in the current conversation language: {{context.shortTermMemory.uc4.langName}}.
- Manglish is not a request to switch. Keep the current language; a light mix of common Malay words
  (lah, boleh, ok, dah) in your reply is fine when the merchant talks that way.
- If the merchant asks for the other language, or speaks mainly in it for a full turn, call
  get_approved_answer with topic language_request and that language. Tool results then arrive in it.
- If they ask for a language other than English or Bahasa Melayu: get_approved_answer, topic
  language_request, language other.
- say with verbatim true is already in the current language: say it exactly.
- say with verbatim false, and every guide: write your reply in the current language.
- Keep screen names in English in both languages (Orders, History, Cancelled, Request for Compensation,
  Help Centre, Owner, Manager). In Bahasa Melayu, say pampasan for compensation.
- Common Malay and Manglish answers: ya, boleh, ok lah, dah, sudah = yes or done; tak, tak nak,
  tak payah, takpe, tak mau, tamau = no; jap, kejap, tunggu = wait; takde, tak nampak, tak jumpa =
  not there, not visible or not found.

HOW YOU WORK
1. Your tools hold the rules. After every tool call, do what its next_action says.
   - say filled and verbatim true: say it exactly, word for word.
   - say filled and verbatim false: you may rephrase it naturally.
   - guide filled: write your own short reply that does exactly what guide says and keeps every
     fact in it. Add no facts of your own.
2. If the merchant asks a direct question, answer it first, then continue the current step.
3. One question per turn. Short sentences. No markdown, lists or symbols. Say numbers as words.
4. Never ask for the order ID, phone number, restaurant name, passwords or codes.
5. Never ask or confirm whether the order is GrabFood or GrabMart. You already know.
6. Never say refund. Always say compensation (pampasan).
7. Never promise a callback, follow up or outcome.
8. Never say how many days have passed, what the threshold is, or which path you chose.
9. Never tell the merchant their order is too old, past a window or not eligible because of time.
10. Only offer to connect the merchant with a person when a tool returns offer_transfer, using its words.
    Never call that person a team, department or specialist.
11. Never state a policy, timeline, eligibility rule or screen name that did not come from a tool.

WHEN TO CALL WHICH TOOL
- Merchant gives or corrects when the order was cancelled, mentions a cancelled order without a date,
  or raises another cancelled order: resolve_order_age.
- Merchant asks a follow up after the timeline, asks about evidence, has no photo, says the order was
  cancelled before it was prepared, raises something outside cancelled order compensation, says payout
  without a cancelled order, asks for or moves to another language, is unhappy with you, asks for a
  person, or says the order is the other brand: get_approved_answer with the matching topic.
- Merchant agrees to be shown or guided, or asks to submit a request: set_guidance_preference until
  it returns start_walkthrough, then start_walkthrough.
- Every merchant reply during a walkthrough: advance_walkthrough with the outcome that fits their words.
- Any other cancelled order compensation question: search_knowledge. If it returns no answer, say you
  don't have that detail on hand.
- Merchant answers an offer of a person: transfer_to_live_agent.
- A real, active emergency happening now: escalate_safety immediately. Not for questions about what
  to do if something happens.
- Merchant is finished after you asked if there is anything else, or must leave now: end_call.

OUT OF SCOPE
Delivery or rider status, account or bank changes, menus, onboarding, app faults, deductions such as
Eater Compensation, and payouts not tied to a cancelled order.

WAITING
If the merchant says wait, they are checking, logging in, or their device is slow, call
advance_walkthrough with needs_time during a walkthrough, otherwise acknowledge in a few words and stop.
Do not offer a person or end the call.
```

### 5.3 Guardrails and topic confinement

The instructions above repeat the platform safety flags in behavioural terms (grounding, no invented policy, no secrets). These are complementary: the flags are platform enforcement, the instructions are prompt level. Out of scope topics are not refused flatly. The bot offers a person, because the test cases (TC-010, TC-033) expect a consent question and a transfer.

### 5.4 Mapping from the SRC-3 tasks

| SRC-3 task (Wiz) | Cognigy equivalent |
| --- | --- |
| 1 Offer a person, difficulty cap | advance\_walkthrough returns next\_action = offer\_transfer |
| 2 Retrieve FAQ (RAG) | search\_knowledge tool |
| 3 Transfer to NICE CXone | transfer\_to\_live\_agent tool |
| 4 Clarify a vague request | Instructions (scope) |
| 5 Ask when the order was cancelled | resolve\_order\_age returns ask\_date, with the two asks cap |
| 6 Ask what they want to know | resolve\_order\_age returns ask\_open\_question (beyond threshold) |
| 7, 8 Deliver EDUCATE / IFI outcome | resolve\_order\_age and get\_approved\_answer return the approved script |
| 9 Answer first follow up | get\_approved\_answer |
| 10 Collect guidance preference | set\_guidance\_preference |
| 11, 12, 13 Guidance journeys | start\_walkthrough and advance\_walkthrough |
| 14 Educate Role | advance\_walkthrough role path |
| 15, 16 Ask transfer confirmation | Tool next\_action = offer\_transfer, then transfer\_to\_live\_agent |
| 17, 18 Close the call, final offer | end\_call (could\_not\_resolve) |
| 19 Steer back (fallback) | Instructions plus the current step held in context.uc4 |
| Exits 1 to 4 | end\_call exit types |
| Global Safety | escalate\_safety tool |

## 6. Context and State Model

All session state lives in context.shortTermMemory.uc4 (the team convention for session state), and all configuration lives in context.uc4Cfg. Tools are the only writers of the uc4 state. Every Code node guards shortTermMemory before use and writes only its uc4 key, so it never overwrites anything the AI Agent node stores there. The AI Agent reads state only through tool results, never by inferring it from the transcript.

### 6.1 Session state: context.shortTermMemory.uc4

| Field | Default | Written by | Description |
| --- | --- | --- | --- |
| lob | from CXone | Code: Initiate | "GrabFood" or "GrabMart". Never changes during the call. |
| callId | from CXone | Code: Initiate | CXone contact ID, used in the ACW payload and test evidence. |
| today | MYT date | Code: Initiate | { iso: "2026-10-06", weekday: "Tue" } in Asia/Kuala\_Lumpur time. |
| orders | \[ \] | resolve\_order\_age | One object per order raised in the call (see 6.2). |
| activeOrder | "A" | resolve\_order\_age | Ref of the order currently being handled. |
| prefs | see 6.3 | set\_guidance\_preference | Platform, style and loudspeaker. Kept for the whole call and reused for a second order. |
| walk | see 6.4 | start\_walkthrough, advance\_walkthrough | The current walkthrough: journey, step, counters. |
| transfer | { offered: false, reason: "", declined: false, executed: false } | transfer\_to\_live\_agent and tools that return offer\_transfer | Prevents a second offer after a decline (D-13). |
| language | { switches: 0, otherAsks: 0 } | get\_approved\_answer (topic language) | Counts language switches and requests for languages the bot does not speak. |
| dissatisfaction | { attempts: 0 } | get\_approved\_answer (topic dissatisfied) | One extra help attempt before an offer. |
| outcome | { journeys: \[ \], result: "" } | All tools | Summary for the ACW payload. |
| closingSaid | false | end\_call | Once true, the Flow produces nothing further. |
| lang | from the test page, else "en" | Code: Initiate, get\_approved\_answer | Current conversation language, "en" or "ms". Starts from the test page and then follows the merchant. Selects the content pack and the Set Session Config node. |
| langName | "English" | Code: Initiate, get\_approved\_answer | "English" or "Bahasa Melayu". Read by the AI Agent instructions. |

### 6.2 Order object (uc4.orders\[ \])

| Field | Default | Description |
| --- | --- | --- |
| ref | "A" | "A" for the first order, "B" for the next. |
| ageDays | -1 | Days since cancellation, as a whole number. -1 means unknown. |
| dateSource | "" | days, weekday, date, unclear or assumed. |
| threshold | "" | within or beyond. Set only by resolve\_order\_age. |
| dateAskCount | 0 | How many bot turns asked for the date. Capped at maxDateAsks (2). |
| educateDelivered | false | The timeline script was delivered for this order. |
| followupAnswered | false | The first follow up answer was given (Further Inquiries script). |
| submitted | false | A Request for Compensation was submitted for this order in this call. |
| closedAfterRole | false | The order was closed with Final Educate after a declined role retry. |

### 6.3 Preferences (uc4.prefs)

| Field | Default | Values |
| --- | --- | --- |
| platform | "" | app or portal |
| style | "" | one\_by\_one or all\_at\_once |
| loudspeaker | "" | yes or no |
| asks | { platform: 0, style: 0, loudspeaker: 0 } | Each question is asked at most twice (maxPrefAsks). |
| assumed | \[ \] | Preferences assumed after two unanswered asks: app, all\_at\_once, no. |

### 6.4 Walkthrough (uc4.walk)

| Field | Default | Description |
| --- | --- | --- |
| journey | "" | view\_order, check\_status or submit\_request. |
| platform | "" | Copied from prefs. May be overridden (GrabMart status check is always portal). |
| segment | "" | The step list in use, for example food\_app\_status or portal\_submit. |
| stepIndex | 0 | Zero based index of the step the merchant is on. |
| stuckCount | 0 | Failure reports on the current step. Reset when the step changes. |
| routeIndex | 0 | Portal Help Centre route in use: 0 search bar, 1 common problems, 2 browse by services. |
| scrollAsked | false | The scroll instruction was given for the form. |
| roleAttempts | 0 | Owner or Manager retries attempted. |
| crossBuildOffered | false | App link missing, portal offered instead (TC-008). |
| status | "active" | active, completed, abandoned or handed\_over. |

### 6.5 Code: Initiate

```javascript
// Code: Initiate. Runs once per call, after Code: Config and Code: Config (language packs).
// State lives in context.shortTermMemory.uc4. Guard first and never replace shortTermMemory itself.
// The WebRTC test page (or an IVR later) passes lob and, optionally, lang as session data.
// For Interaction Panel testing, send input.data = { "lob": "GrabFood", "lang": "ms" }.
if (!context.shortTermMemory) {
  context.shortTermMemory = {};
}
const callData = input.data || {};
const sipHeaders = (callData.sip && callData.sip.headers) || {};
const rawLob = String(callData.lob || sipHeaders["X-Grab-LOB"] || "").toLowerCase();
const rawLang = String(callData.lang || sipHeaders["X-Grab-Lang"] || "en").toLowerCase();

let lob = "";
if (rawLob.indexOf("food") !== -1) {
  lob = "GrabFood";
} else if (rawLob.indexOf("mart") !== -1) {
  lob = "GrabMart";
}
// Starting language only. The conversation then follows the merchant (6.7, 7.3).
let lang = "en";
if (rawLang.indexOf("ms") === 0 || rawLang.indexOf("bm") === 0 || rawLang.indexOf("malay") !== -1 || rawLang.indexOf("melayu") !== -1) {
  lang = "ms";
}

// Today in Malaysia time (UTC+8, no daylight saving). testToday overrides it outside production.
const my = new Date(Date.now() + 8 * 3600 * 1000);
const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const realToday = { iso: my.toISOString().slice(0, 10), weekday: weekdays[my.getUTCDay()] };

context.shortTermMemory.uc4 = {
  lob: lob,
  lang: lang,
  langName: lang === "ms" ? "Bahasa Melayu" : "English",
  callId: String(callData.contactId || sipHeaders["X-Contact-Id"] || ""),
  today: (context.uc4Cfg && context.uc4Cfg.testToday) ? context.uc4Cfg.testToday : realToday,
  orders: [],
  activeOrder: "",
  prefs: { platform: "", style: "", loudspeaker: "", asks: { platform: 0, style: 0, loudspeaker: 0 }, assumed: [] },
  walk: { journey: "", pendingJourney: "", platform: "", segment: "", stepIndex: 0, stuckCount: 0, routeIndex: 0,
          scrollAsked: false, roleAttempts: 0, roleState: "", awaiting: "", then: "", crossBuildOffered: false,
          portalOpened: false, orderDetailsOpen: false, disclaimerSaid: false, status: "" },
  transfer: { offered: false, reason: "", declined: false, executed: false, unclearOnce: false },
  language: { switches: 0, otherAsks: 0 },
  dissatisfaction: { attempts: 0 },
  outcome: { journeys: [], result: "" },
  safetySummary: "",
  noInput: 0,
  closingSaid: false
};

// Apply the language pack. Tools read cfg.fixed, steps, walkFixed, messages and evidence, so they
// always get the current language without any language logic of their own.
const pack = context.uc4Cfg.content[lang];
Object.assign(context.uc4Cfg, { fixed: pack.fixed, steps: pack.steps, walkFixed: pack.walkFixed,
  messages: pack.messages, evidence: pack.evidence });
context.shortTermMemory.uc4Valid = (lob !== "");
```

### 6.6 Configuration: context.uc4Cfg (thresholds, flags, scripts)

Loaded by Code: Config, which runs directly before Code: Initiate so that Initiate can read testToday (Section 10). The step catalogue is in Section 7.5.

```javascript
// Code: Config. Runs first. All business values in one place. Change here, not in tools.
// Tier 1 fixed: said exactly (verbatim). Tier 2 guided: intent and facts, the LLM phrases the reply.
// Tier 3 knowledge (open follow up questions) lives in the knowledge store, not here.
// fixed, messages and evidence below are the ENGLISH pack. The Malay pack has the same keys (6.7).
context.uc4Cfg = {
  timezone: "Asia/Kuala_Lumpur",
  testToday: "", // non production only, for example { iso: "2026-10-07", weekday: "Wed" }
  knowledgeSource: "cognigy", knowledge: { minScore: 0.6, topK: 3 }, // D-17. minScore is a starting value to tune (OI-08)
  flags: {
    maxDateAsks: 2,
    maxPrefAsks: 2,
    stuckLadder: ["repeat", "repeat", "clarify", "clarify", "offer_transfer"], // D-03
    portalExhaustedAction: "offer_transfer",  // D-04, alternative: "soft_close"
    roleRetryEnabled: true,                   // D-05
    roleMaxAttempts: 2,
    knowledgeEnabled: true,
    languageSwitch: "switch"                  // D-12, alternative: "ask_then_transfer" (TC-023, TC-024 as written)
  },
  // D-02: within threshold when ageDays <= value for today's weekday (SRC-3 tables)
  thresholdDays: {
    GrabFood: { Mon: 4, Tue: 4, Wed: 2, Thu: 2, Fri: 2, Sat: 3, Sun: 4 },
    GrabMart: { Mon: 7, Tue: 7, Wed: 7, Thu: 7, Fri: 7, Sat: 8, Sun: 9 }
  },
  // A bare weekday name: within only if listed for today (GrabFood). GrabMart: any weekday in the past week.
  weekdayWithin: {
    GrabFood: { Mon: ["Sun", "Sat", "Fri", "Thu"], Tue: ["Mon", "Sun", "Sat", "Fri"], Wed: ["Tue", "Mon"],
                Thu: ["Wed", "Tue"], Fri: ["Thu", "Wed"], Sat: ["Fri", "Thu", "Wed"], Sun: ["Sat", "Fri", "Thu", "Wed"] },
    GrabMart: "any"
  },
  evidence: { GrabFood: "a photo of the prepared food", GrabMart: "a photo of the packed items" },

  // Tier 1: fixed, said exactly (English pack)
  fixed: {
    GrabFood: {
      educate: "Compensation for a cancelled order is usually approved within one to two business days after the order was made, and it is then paid in your next payout cycle, the same cycle as your regular order earnings, subject to Grab's cancellation policy and guidelines.",
      photoReminder: "Please take a photo of the prepared food as evidence, in case you would like to submit a request for our support team to review further after it has been more than two business days."
    },
    GrabMart: {
      educate: "Compensation for a cancelled order is usually approved within three to five business days after the order was made, and it is then paid in your next payout cycle, the same cycle as your regular order earnings, subject to Grab's cancellation policy and guidelines.",
      photoReminder: "Please take a photo of the order as evidence, in case you would like to submit a request for our support team to review further after it has been more than five business days.",
      partialDisclaimer: "Please note that compensation will be partial, based on the assessment of the perishable items."
    },
    furtherInquiry: "If you're eligible for compensation, you'll see the Request for Compensation section within that cancelled order in your GrabMerchant app. If you can't see it, you should submit a request for our support team to review further. Would you like to be guided to your cancelled order?",
    orderVisible: "Now you can view the details of your order, and you might also see the Request for Compensation section within it. If you can't see it, you should submit a request for our support team to review further. Would you like help submitting a Request for Compensation, or is that all you needed?",
    afterSubmission: "Once approved, you may receive the compensation depending on the review outcome. That's all I can assist you with for now.",
    offerPerson: "Would you like me to connect you with someone who can help further?",
    outOfScopeLead: "I only handle issues about cancelled orders.",
    otherBrand: "This line only covers {lob} cancelled order compensation. Would you like to speak to someone who can help with your other order?",
    udr: "Is there anything else I can help you with?",
    // Short spoken lines used inside tools. Kept here, not in tool code, so each language pack supplies its own.
    phrases: {
      separateOrder: "Sure, let's take that as a separate order.",
      askDate1: "When was the cancelled order made?",
      askDate2: "Could you give me a rough idea, roughly how many days ago it was, or which day?",
      openQuestion: "Could you explain what you'd like to know?",
      canSubmit: "You can submit a Request for Compensation.",
      offerStatusCheck: "Would you like me to show you how to check the compensation status for that order?",
      askPlatform: "Are you on the GrabMerchant app, or the GrabMerchant portal on a computer?",
      askStyle: "Would you like the steps one by one, or all at once?",
      askLoudspeaker: "Would you like to put me on loudspeaker before we start?",
      understand: "I understand.",
      sorryNotHelped: "I'm sorry this hasn't helped.",
      sorryStuck: "I'm sorry you're running into that.",
      ownerManagerOnly: "Only an Owner or Manager can submit a request.",
      noneWorked: "I'm sorry, none of those got us to the form.",
      switched: "Sure, let's continue in English.",
      stayInLanguage: "I can only converse in English here. Would you like to proceed in English?",
      languagesOffered: "I can help in English or Bahasa Melayu. Which would you prefer?"
    }
  },

  // Tier 2: guided. Written in English for the LLM; it replies in the current conversation language.
  guided: {
    evidence: "Tell them the main evidence is {evidence}. One sentence.",
    photoMissing: "Reassure them first that they can still fill in and submit the form without the photo. Then suggest they include all the information and documents they have, clear and complete, so the review is faster. Never make the photo a condition.",
    notPrepared: "Explain that compensation applies only to orders cancelled after they were already prepared, so it would not apply in this case. Then ask if there is anything else you can help with.",
    payoutUnclear: "Ask one short question: is this about the payout for an order that was cancelled after it was prepared?",
    alreadySubmitted: "Tell them a request has already been submitted for this order in this call, so the next step is to wait for the outcome. Then ask if there is anything else.",
    finalEducate: "Ask them to try logging in with an Owner or Manager account first, and say they are welcome to call back if they still cannot access the form after that.",
    dissatisfiedFirst: "Acknowledge their frustration in one sentence, then make one real attempt to help with the current order. Do not offer a person.",
    humanFirst: "Say you can help with their cancelled order and ask what they need. Do not offer a person yet.",
    alreadyShared: "Say briefly that you have shared what you can on that, then ask if there is anything else.",
    declinedPerson: "Acknowledge the no in a few words, then ask if there is anything else you can help with.",
    continueOrder: "Acknowledge, and carry on with the {lob} order you were helping with."
  },

  // Terminal messages: fixed, played by Say nodes, never by the LLM (English pack)
  messages: {
    greeting: "Hi, I'm your Grab AI Assistant, and I'll be assisting you today. Please note that this call will be recorded for quality assurance and training purposes. I understand that you're contacting us about an order that was cancelled after it had already been prepared. How may I help you today?",
    transfer: "Please hold while I transfer you to a customer service officer. You might have to repeat some of our conversation. Thank you for your patience and understanding.",
    safety: "I understand this involves a safety concern. If anyone is hurt, please call your local emergency number now. Let me connect you to someone who can help right away.",
    exitClosingA: "Thank you for calling Grab. If there's anything else you need help with, please contact us again. Have a nice day.",
    exitCouldNotResolve: "I'm sorry we can't help you further with this today. If anything else comes up, please don't hesitate to call us back.",
    exitDisengaged: "No problem, you're welcome to call back anytime for further help. Take care.",
    exitLanguage: "I'm sorry, I can only help in English or Bahasa Melayu, so I'm not able to assist you today. Please feel free to call us back."
  },
  transferTargets: { others: "<CXone destination for 'others', to be provided by NiCE (OI-02)>" }
};
```

**Tier ownership.** Tier 1 text may only change with Grab's written approval. Tier 2 guides can be tuned by the build team during testing, as long as no fact changes. If Grab wants business users to edit approved text without a developer, the fixed and guided objects can be moved into a dedicated Cognigy knowledge source and read by Code: Config at start up; this is a later improvement, not needed for the pilot.

### 6.7 Language handling: English, Bahasa Melayu and Manglish

The bot understands English, Bahasa Melayu and Manglish, and replies in the merchant's language (D-12). The conversation starts in the language set by the test page (default English) and follows the merchant from there. Manglish, meaning English with Malay words mixed in (lah, boleh, tak, dah, nak, takde), is understood in either language and never triggers a switch on its own.

**How it works**

| Layer | English, Bahasa Melayu, Manglish handling |
| --- | --- |
| Speech recognition | Both Set Session Config nodes recognise English and Malay together (one as primary, the other as alternate), so mixed sentences are transcribed (9.1). |
| Understanding | The LLM reads all three. Tool descriptions list common Malay and Manglish answers (dates, yes and no, platform, wait) so tool arguments are filled correctly (7.2, 7.4, 7.7). |
| Switching | When the merchant asks for the other language, or speaks mainly in it for a full turn, the AI Agent calls get\_approved\_answer with topic language\_request (7.3). The tool swaps the language pack and the voice settings. |
| Tier 1 fixed text | Held in a language pack per language with identical keys. Tools read the active pack, so they contain no language logic. |
| Tier 2 guided text | Written once in English as instructions. The LLM replies in the current language, with natural light code mixing where it fits. |
| Tier 3 knowledge | Searched in English, answered in the current language (7.8). |
| Screen names | Always in English in both languages (Orders, History, Cancelled, Request for Compensation, Help Centre, Owner, Manager), as merchants see them on screen. |

**Language packs.** Code: Config (language packs) runs after Code: Config and the step catalogue, and before Code: Initiate:

```javascript
// Code: Config (language packs). The Malay pack is pasted from the UC4 Content Pack (Malay sheet).
const c = context.uc4Cfg;
c.content = {
  en: { fixed: c.fixed, steps: c.steps, walkFixed: c.walkFixed, messages: c.messages, evidence: c.evidence },
  ms: { /* fixed, steps, walkFixed, messages, evidence: same keys as en, Malay text */ }
};
```

The Malay text is maintained in a separate UC4 Content Pack, not in this document. It has the same keys as the English pack. Its sources:

| Malay pack content | Source |
| --- | --- |
| Greeting, safety, transfer, early termination, closing, UDR | SRC-2 Malay scripts. Greeting extended with the recording notice. |
| Photo reminders, partial compensation line, further inquiry, order visible, after submission, final educate, role reminder | SRC-2 Malay scripts |
| Date questions, open question, style, platform and loudspeaker questions | SRC-2 Malay scripts |
| app\_view\_order, portal\_view\_order, app\_submit, portal\_submit (routes 1 to 3, fill) | SRC-2 Malay scripts, with Payouts and Reports added to route 2 |
| Compensation timeline (D-08 wording) | Amansob draft: SRC-2 Malay still uses the older "credited" wording |
| food\_app\_status, food\_app\_history, portal\_status, cross build, mock and offer lines, language lines | Amansob draft: no Malay source exists |

Every Amansob draft line needs Grab approval before the benchmark (OI-21).

## 7. Tool Catalogue and Implementation

The AI Agent node has nine tools. Six always return a result to the agent through actions.output. escalate\_safety and end\_call are terminal, and transfer\_to\_live\_agent is terminal when the merchant says yes. Every tool's Condition field is a guard: Cognigy hides the tool from the LLM when the guard is false, so a tool cannot be called out of order.

### 7.1 Catalogue

| Tool | Purpose | Condition (guard) | Returns or terminal | NiCE tool (SRC-4) |
| --- | --- | --- | --- | --- |
| resolve\_order\_age | Decide within or beyond threshold, cap date questions, handle corrections and a second order | context.shortTermMemory.uc4.closingSaid !== true | Returns | Resolving the order age |
| get\_approved\_answer | Fixed and guided answers, and every offer of a person that is not a walkthrough failure | context.shortTermMemory.uc4.closingSaid !== true | Returns | (none, new) |
| set\_guidance\_preference | Collect platform, style and loudspeaker, one per turn | context.shortTermMemory.uc4.orders.length > 0 | Returns | (none, new) |
| start\_walkthrough | Pick the step segment for LOB, journey and platform, deliver the first step | context.shortTermMemory.uc4.prefs.platform !== "" && context.shortTermMemory.uc4.prefs.style !== "" | Returns | Get guidance steps |
| advance\_walkthrough | Move the walkthrough on each merchant reply. Owns the stuck ladder, route ladder and role path | context.shortTermMemory.uc4.walk.status === "active" | Returns | Advance walkthrough steps |
| search\_knowledge | Grounded fallback for compensation questions the other tools do not cover (Tier 3) | context.uc4Cfg.flags.knowledgeEnabled === true | Returns | Search knowledge |
| transfer\_to\_live\_agent | Act on the merchant's yes or no to an offer of a person | context.shortTermMemory.uc4.transfer.offered === true | Terminal on yes, returns on no | Transfer to Live Agent |
| escalate\_safety | Immediate transfer for a live emergency, no consent | (none, always available) | Terminal | Safety Escalation |
| end\_call | Play the right exit message and hang up | context.shortTermMemory.uc4.closingSaid !== true | Terminal | (none, new) |

Code: Config is not a tool. It holds the shared configuration every tool reads (Sections 6.6 and 7.5).

### 7.1.1 Common result contract

Every returning tool writes the same shape, so the instructions can say "follow next\_action" once.

```json
{
  "success": true,
  "next_action": "deliver_step",
  "say": "Please open the GrabMerchant app. Can you see the home screen?",
  "verbatim": true,
  "guide": "",
  "step_id": "open_app"
}
```

say carries Tier 1 text (verbatim true) or text the agent may rephrase (verbatim false). guide carries a Tier 2 instruction: the agent writes its own reply that does exactly what guide says. A result never has both say and guide filled, except deliver\_step, where guide holds a short delivery hint.

| next\_action | What the AI Agent does |
| --- | --- |
| deliver\_say | Say the say text (exactly, when verbatim is true) and wait. |
| deliver\_guided | Write one short reply that does what guide says, keeping every fact, and wait. |
| deliver\_step | Say the step exactly. It always ends with a check back. |
| ask\_date | Ask when the order was cancelled, using say. |
| ask\_open\_question | Ask what they would like to know about that order. Never mention the date or any assumption. |
| ask\_preference | Ask exactly the one preference question in say. |
| collect\_preferences | Say the say text if any, then call set\_guidance\_preference. |
| start\_walkthrough | Say the say text if any, then call start\_walkthrough with the journey in guide. |
| offer\_transfer | Ask the consent question in say. Their answer goes to transfer\_to\_live\_agent. |
| hold | Acknowledge briefly as guide says and wait. No new question. |
| steer\_back | Do not repeat earlier content. Follow guide if filled, else re-ask the current question or ask if there is anything else. |
| end\_call | Call end\_call with the exit\_type in guide. |
| terminal | Nothing to say. The tool path has ended the turn. |
| apologise\_and\_retry\_once | A tool error. Apologise briefly and ask the merchant to repeat. |

### 7.1.2 Code node conventions

- Read arguments from input.aiAgent.toolArgs, guarded with || { }. Never input.data or input.args.
- Guard shortTermMemory before use: if (!context.shortTermMemory) { context.shortTermMemory = {}; }. Write only to context.shortTermMemory.uc4.
- No return statements anywhere in a Code node, including inside helpers. Logic is an if/else chain that assigns a variable named out. Helpers are expression arrow functions, or block functions that write to out.
- Every returning tool ends with actions.output("", out) (Pattern 6). The empty first argument keeps it silent.
- Never write null into context. Use "", -1 or false.
- Do not use actions.addToContext on shortTermMemory: it replaces the whole key (gotcha 4).
- Code nodes cannot share functions. Small helpers (res, deliver) are repeated in each tool.
- Every tool appends to uc4.outcome.journeys only when it changes the journey, to keep the ACW payload short.

### 7.2 resolve\_order\_age

Decides whether the order is within or beyond the LOB threshold and returns the next move. It is also the only place the date question is asked, so the two asks cap (SRC-3) is enforced in code. Covers TC-001 to TC-005, TC-019, TC-021, TC-022, TC-025 to TC-029, TC-042, TC-044 and TC-045.

**Tool description (for the LLM):** Call this whenever the merchant tells you, or corrects, when the cancelled order was cancelled, or mentions a cancelled order without a date, or raises a second cancelled order. Convert their words to days\_ago where you can: today, just now, this morning = 0; yesterday = 1; two days ago = 2; last week = 7. In Malay or Manglish: hari ini, tadi, pagi tadi = 0; semalam = 1; kelmarin = 2; minggu lepas = 7; dua hari lepas = 2. Use weekday only for a bare weekday name in the past week. Use calendar\_date for a date such as 11 September. Also pass what they want to know if they said it.

**Parameters (JSON schema)**

```json
{
  "type": "object",
  "properties": {
    "days_ago": { "type": "integer", "minimum": 0, "description": "Whole days since the order was cancelled. Omit if unknown." },
    "weekday": { "type": "string", "enum": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "description": "Only for a bare weekday name meaning the most recent one before today. Isnin=Mon, Selasa=Tue, Rabu=Wed, Khamis=Thu, Jumaat=Fri, Sabtu=Sat, Ahad=Sun." },
    "calendar_date": { "type": "string", "description": "A calendar date the merchant gave, as YYYY-MM-DD. Assume the current year." },
    "unclear": { "type": "boolean", "description": "True if the merchant gave an answer that cannot be turned into a date, for example a while ago, not sure." },
    "is_correction": { "type": "boolean", "description": "True if the merchant is correcting a date already given for the same order." },
    "is_new_order": { "type": "boolean", "description": "True if the merchant raises a different, separate cancelled order." },
    "merchant_intent": { "type": "string", "enum": ["none", "timeline", "status", "submit", "status_and_submit", "view_order"], "description": "What the merchant has said they want, if anything. none if not stated." }
  },
  "additionalProperties": false
}
```

**Decision logic**

| Situation | State change | next\_action and say |
| --- | --- | --- |
| No usable date and dateAskCount < 2 | dateAskCount + 1 | ask\_date. First ask: "When was the cancelled order made?" Second ask: "Could you give me a rough idea, roughly how many days ago it was, or which day?" |
| No usable date and dateAskCount = 2 | threshold = beyond, dateSource = assumed | ask\_open\_question: "Could you explain what you'd like to know?" Nothing is said about the date (TC-019, TC-042). |
| Within, educate not yet delivered | educateDelivered = true | deliver\_say, verbatim = true: educate + photoReminder + UDR (TC-001, TC-025). |
| Within, educate already delivered | none | steer\_back (never repeats the timeline). |
| Beyond, intent none | none | ask\_open\_question (TC-004, TC-005). |
| Beyond, intent timeline or status | educateDelivered = true, walk.pendingJourney = check\_status | deliver\_say: educate (no photo reminder) + "Would you like me to show you how to check the compensation status for that order?" (TC-004 to TC-009) |
| Any threshold, intent submit | walk.pendingJourney = submit\_request | start\_walkthrough flow: next\_action = collect\_preferences, say = "You can submit a Request for Compensation." (TC-013 to TC-016) |
| Beyond, intent status\_and\_submit | walk.pendingJourney = status\_then\_submit | collect\_preferences (TC-003, TC-027) |
| Correction that moves within to beyond | threshold re-set, previous verdict discarded | ask\_open\_question, silently (TC-022, TC-045). |
| is\_new\_order | New order object ref B, activeOrder = B, walk reset, prefs kept | First words name the order as separate: "Sure, let's take that as a separate order." Then the same table applies (TC-021, TC-044). |

collect\_preferences means the agent calls set\_guidance\_preference next. It is listed with the other values in 7.1.1.

**Code: resolve\_order\_age**

```javascript
// Tool: resolve_order_age. No return statements; the result leaves through actions.output.
// Spoken lines come from fx.phrases, so the active language pack decides the language.
const a = input.aiAgent?.toolArgs || {};
if (!context.shortTermMemory) {
  context.shortTermMemory = {};
}
const u = context.shortTermMemory.uc4;
const cfg = context.uc4Cfg;
const fx = cfg.fixed;
const ph = fx.phrases;
const wd = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const res = (n, say, extra) => Object.assign({ success: true, next_action: n, say: say || "", guide: "", verbatim: false }, extra || {});
let out = res("apologise_and_retry_once", "");
let prefix = "";

// 1. Find or create the order
if (a.is_new_order === true || u.orders.length === 0) {
  const ref = String.fromCharCode(65 + u.orders.length); // A, B, C
  u.orders.push({ ref: ref, ageDays: -1, dateSource: "", threshold: "", dateAskCount: 0,
    educateDelivered: false, followupAnswered: false, submitted: false, closedAfterRole: false });
  u.activeOrder = ref;
  Object.assign(u.walk, { journey: "", pendingJourney: "", segment: "", stepIndex: 0, stuckCount: 0, routeIndex: 0,
    scrollAsked: false, roleAttempts: 0, roleState: "", awaiting: "", then: "", crossBuildOffered: false,
    orderDetailsOpen: false, status: "" });
  if (u.orders.length > 1) {
    prefix = ph.separateOrder + " ";
  }
}
const o = u.orders.find(x => x.ref === u.activeOrder);

// 2. Work out the age, or read the weekday verdict directly
let verdict = "";
if (Number.isInteger(a.days_ago)) {
  o.ageDays = a.days_ago;
  o.dateSource = "days";
} else if (a.calendar_date) {
  const diff = Math.round((Date.parse(u.today.iso) - Date.parse(a.calendar_date)) / 86400000);
  if (diff >= 0) {
    o.ageDays = diff;
    o.dateSource = "date";
  }
} else if (a.weekday) {
  const within = cfg.weekdayWithin[u.lob];
  verdict = (within === "any" || within[u.today.weekday].indexOf(a.weekday) !== -1) ? "within" : "beyond";
  const back = (wd.indexOf(u.today.weekday) - wd.indexOf(a.weekday) + 7) % 7;
  o.ageDays = back === 0 ? 7 : back;
  o.dateSource = "weekday";
}
if (!verdict && o.ageDays >= 0) {
  verdict = o.ageDays <= cfg.thresholdDays[u.lob][u.today.weekday] ? "within" : "beyond";
}
if (verdict) {
  o.threshold = verdict;
}

const intent = a.merchant_intent || "none";
const wantsGuide = (intent === "submit" || intent === "status_and_submit" || intent === "view_order");

// 3. Decide the next move
if (o.threshold === "" && o.dateAskCount < cfg.flags.maxDateAsks) {
  o.dateAskCount += 1;
  out = res("ask_date", prefix + (o.dateAskCount === 1 ? ph.askDate1 : ph.askDate2));
} else if (o.threshold === "") {
  o.threshold = "beyond";
  o.dateSource = "assumed";
  out = res("ask_open_question", prefix + ph.openQuestion,
    { guide: "The date is settled. Never ask it again and never mention any assumption." });
} else if (wantsGuide) {
  u.walk.pendingJourney = intent === "submit" ? "submit_request" : (intent === "view_order" ? "view_order" : "status_then_submit");
  out = res("collect_preferences", prefix + (intent === "view_order" ? "" : ph.canSubmit));
} else if (o.threshold === "within" && o.educateDelivered) {
  out = res("steer_back", "", { guide: cfg.guided.alreadyShared });
} else if (o.threshold === "within") {
  o.educateDelivered = true;
  out = res("deliver_say", prefix + fx[u.lob].educate + " " + fx[u.lob].photoReminder + " " + fx.udr, { verbatim: true });
} else if (intent === "timeline" || intent === "status") {
  o.educateDelivered = true;
  u.walk.pendingJourney = "check_status";
  out = res("deliver_say", prefix + fx[u.lob].educate + " " + ph.offerStatusCheck, { verbatim: true });
} else {
  out = res("ask_open_question", prefix + ph.openQuestion,
    { guide: a.is_correction ? "Date corrected. Do not mention the change or any day count." : "" });
}

input.uc4Result = out;
actions.output("", out);
```

**Unit checks for the developer** (set context.uc4Cfg.testToday in Code: Config)

| LOB | Today | Input | Expected verdict |
| --- | --- | --- | --- |
| GrabFood | Wed | days\_ago 2 | within |
| GrabFood | Wed | days\_ago 3 | beyond |
| GrabFood | Mon | days\_ago 4 (last Thursday) | within |
| GrabFood | Tue | weekday Fri | within |
| GrabFood | Tue | weekday Tue (a week ago) | beyond |
| GrabMart | Tue | days\_ago 5 | within (note TC-045 expects beyond, see OI-05) |
| GrabMart | Sun | days\_ago 9 | within |
| GrabMart | Sun | days\_ago 10 | beyond |
| Either | any | unclear twice | ask\_date twice, then ask\_open\_question with threshold beyond |

### 7.3 get\_approved\_answer

Returns Grab approved wording for known follow up topics and is the single entry point for every offer of a person that is not caused by a walkthrough failure. Routing offers through one tool means uc4.transfer.offered is always set before transfer\_to\_live\_agent becomes available. Covers TC-002, TC-010, TC-017, TC-020, TC-023, TC-024, TC-026, TC-033, TC-040 and TC-043.

**Tool description (for the LLM):** Call this when the merchant asks a follow up after the compensation timeline, asks about evidence, says they have no photo, says the order was cancelled before it was prepared, raises something outside cancelled order compensation, says payout without linking it to a cancelled order, asks for the other language or keeps speaking it, asks for a language you do not speak, is unhappy with you, asks for a person, or says the order is actually the other brand.

**Parameters (JSON schema)**

```json
{
  "type": "object",
  "properties": {
    "topic": {
      "type": "string",
      "enum": ["further_inquiry", "evidence_question", "photo_missing", "not_prepared", "out_of_scope",
               "payout_unclear", "language_request", "dissatisfied", "human_request", "other_brand"],
      "description": "The topic that best matches what the merchant just said."
    },
    "language": {
      "type": "string",
      "enum": ["en", "ms", "other"],
      "description": "For language_request only. en = English, ms = Bahasa Melayu, other = any other language. Manglish is not a language request."
    }
  },
  "required": ["topic"],
  "additionalProperties": false
}
```

**Topic table**

| Topic | Tier | State change | next\_action | Content |
| --- | --- | --- | --- | --- |
| further\_inquiry, first time for this order | Fixed | order.followupAnswered = true, walk.pendingJourney = view\_order | deliver\_say | fixed.furtherInquiry (offers to guide to the cancelled order). GrabMart beyond threshold: partial compensation line first. |
| further\_inquiry, already answered | Guided | none | deliver\_guided | guided.alreadyShared (SRC-2 rule: no third repeat) |
| evidence\_question | Guided | none | deliver\_guided | guided.evidence with the LOB evidence |
| photo\_missing | Guided | none | deliver\_guided | guided.photoMissing: reassurance first, never a condition |
| not\_prepared | Guided | none | deliver\_guided | guided.notPrepared |
| out\_of\_scope | Fixed | offer | offer\_transfer | fixed.outOfScopeLead + fixed.offerPerson (TC-010, TC-033) |
| payout\_unclear | Guided | none | deliver\_guided | guided.payoutUnclear |
| language\_request, en or ms (switch mode) | Fixed | uc4.lang and langName set, language pack applied, input.uc4LangChanged = true | deliver\_say | phrases.switched in the new language, then re-ask the open question (TC-023, TC-024) |
| language\_request, other language (or ask\_then\_transfer mode) | Fixed | language.otherAsks + 1; offer on the second request | offer\_transfer | First: phrases.languagesOffered (or stayInLanguage). Second: phrases.understand + fixed.offerPerson |
| language\_request, same language as now | Guided | none | steer\_back | Carry on where the call left off |
| dissatisfied, first | Guided | dissatisfaction.attempts = 1 | deliver\_guided | guided.dissatisfiedFirst. No offer. |
| dissatisfied again | Fixed | offer | offer\_transfer | fixed.offerPerson (TC-020, TC-043) |
| human\_request, no attempt yet | Guided | dissatisfaction.attempts = 1 | deliver\_guided | guided.humanFirst |
| human\_request after an attempt | Fixed | offer (reopens after a decline) | offer\_transfer | fixed.offerPerson |
| other\_brand | Fixed | offer | offer\_transfer | fixed.otherBrand |

Open follow up questions that match none of these topics are Tier 3 and go to search\_knowledge, not to this tool.

**Flow under the tool.** Code: get\_approved\_answer, then an If on input.uc4LangChanged. When true, a second If on context.shortTermMemory.uc4.lang runs the Malay or the English Set Session Config node (9.1) so speech recognition and the TTS voice follow the new language. Both branches end in Resolve Tool Action.

**Offer rule.** An offer sets transfer.offered = true and transfer.reason. If transfer.declined is already true, the offer is suppressed and the tool returns guided.declinedPerson instead (D-13). The only exception is human\_request, which always reopens the offer.

**Code: get\_approved\_answer (core)**

```javascript
// Tool: get_approved_answer. Tier 1 fixed lines, Tier 2 guided intents and language switching.
// No return statements.
const a = input.aiAgent?.toolArgs || {};
if (!context.shortTermMemory) {
  context.shortTermMemory = {};
}
const u = context.shortTermMemory.uc4;
const cfg = context.uc4Cfg;
const fx = cfg.fixed;
const gd = cfg.guided;
const o = u.orders.find(x => x.ref === u.activeOrder) || {};
const res = (n, say, extra) => Object.assign({ success: true, next_action: n, say: say || "", guide: "", verbatim: false }, extra || {});
const guided = text => res("deliver_guided", "", { guide: text.replace("{evidence}", cfg.evidence[u.lob]).replace("{lob}", u.lob) });
let out = res("apologise_and_retry_once", "");
input.uc4LangChanged = false;

// An offer is suppressed after a decline, unless the merchant asks for a person themselves (D-13)
const makeOffer = (reason, lead, reopen) => {
  if (u.transfer.declined && !reopen) {
    out = guided(gd.declinedPerson);
  } else {
    u.transfer.offered = true;
    u.transfer.reason = reason;
    u.transfer.declined = false;
    out = res("offer_transfer", (lead + " " + fx.offerPerson).trim(), { verbatim: true });
  }
};
const supported = a.language === "en" || a.language === "ms";

const t = a.topic;
if (t === "further_inquiry" && o.followupAnswered) {
  out = guided(gd.alreadyShared);
} else if (t === "further_inquiry") {
  o.followupAnswered = true;
  u.walk.pendingJourney = "view_order";
  const lead = (u.lob === "GrabMart" && o.threshold === "beyond") ? fx.GrabMart.partialDisclaimer + " " : "";
  out = res("deliver_say", lead + fx.furtherInquiry, { verbatim: true });
} else if (t === "evidence_question") {
  out = guided(gd.evidence);
} else if (t === "photo_missing") {
  out = guided(gd.photoMissing);
} else if (t === "not_prepared") {
  out = guided(gd.notPrepared);
} else if (t === "payout_unclear") {
  out = guided(gd.payoutUnclear);
} else if (t === "out_of_scope") {
  makeOffer("out_of_scope", fx.outOfScopeLead, false);
} else if (t === "language_request" && supported && a.language === u.lang) {
  out = res("steer_back", "", { guide: "You are already in this language. Carry on where the call left off." });
} else if (t === "language_request" && supported && cfg.flags.languageSwitch === "switch") {
  // Switch the conversation language: new pack for the tools, new voice settings in the Flow
  u.lang = a.language;
  u.langName = a.language === "ms" ? "Bahasa Melayu" : "English";
  u.language.switches += 1;
  const pack = cfg.content[u.lang];
  Object.assign(cfg, { fixed: pack.fixed, steps: pack.steps, walkFixed: pack.walkFixed,
    messages: pack.messages, evidence: pack.evidence });
  input.uc4LangChanged = true;
  out = res("deliver_say", pack.fixed.phrases.switched, { verbatim: true,
    guide: "From now on reply only in " + u.langName + ". After this line, re-ask the question that was open, if any." });
} else if (t === "language_request") {
  // Unsupported language, or ask_then_transfer mode: one ask, then an offer of a person
  u.language.otherAsks += 1;
  if (u.language.otherAsks === 1) {
    out = res("deliver_say", supported ? fx.phrases.stayInLanguage : fx.phrases.languagesOffered, { verbatim: true });
  } else {
    makeOffer("language", fx.phrases.understand, false);
  }
} else if (t === "dissatisfied" && u.dissatisfaction.attempts === 0) {
  u.dissatisfaction.attempts = 1;
  out = guided(gd.dissatisfiedFirst);
} else if (t === "dissatisfied") {
  makeOffer("dissatisfied", fx.phrases.sorryNotHelped, false);
} else if (t === "human_request" && u.dissatisfaction.attempts === 0) {
  u.dissatisfaction.attempts = 1;
  out = guided(gd.humanFirst);
} else if (t === "human_request") {
  makeOffer("human_request", "", true);
} else if (t === "other_brand") {
  u.transfer.offered = true;
  u.transfer.reason = "other_brand";
  out = res("offer_transfer", fx.otherBrand.replace("{lob}", u.lob), { verbatim: true });
}

input.uc4Result = out;
actions.output("", out);
```

### 7.4 set\_guidance\_preference

Collects the three guidance preferences one per turn, in the order platform, style, loudspeaker (D-11), and hands over to start\_walkthrough once platform and style are known. Each question is asked at most twice. If the merchant pushes for the steps or ignores a question twice, the tool assumes app, all at once and no loudspeaker, and says so in one short clause. Covers TC-003, TC-005 to TC-009, TC-012 to TC-016, TC-027 to TC-032, TC-035 to TC-041.

**Tool description (for the LLM):** Call this after the merchant agrees to be shown or guided, or asks to submit a request, and again with each answer they give to a preference question. Pass only what the merchant actually said. A device mention (I'm on my phone) is not a request to be guided. Malay and Manglish answers: app, apps, telefon, handphone = app; portal, komputer, laptop = portal; satu satu, step by step = one\_by\_one; sekali gus, semua sekali = all\_at\_once; tak payah, tak perlu = no (for loudspeaker).

**Parameters (JSON schema)**

```json
{
  "type": "object",
  "properties": {
    "journey": { "type": "string", "enum": ["view_order", "check_status", "submit_request", "status_then_submit"], "description": "What the merchant agreed to be guided through. Omit to keep the pending journey." },
    "platform": { "type": "string", "enum": ["app", "portal", "either"], "description": "GrabMerchant app or GrabMerchant portal. Heard as add, apps, potter, porter, portol are valid." },
    "style": { "type": "string", "enum": ["one_by_one", "all_at_once", "either"] },
    "loudspeaker": { "type": "string", "enum": ["yes", "no"] },
    "pressed_for_steps": { "type": "boolean", "description": "True if the merchant refused the setup questions, for example just tell me, don't ask so much." }
  },
  "additionalProperties": false
}
```

**Logic**

1. Store the journey if given, else use walk.pendingJourney. If neither exists, return steer\_back.
2. Store any preference given. "either" sets the default (app, all\_at\_once). A no to loudspeaker is an answer, not a decline of the walkthrough.
3. If pressed\_for\_steps is true, fill every missing value with its default, add each to prefs.assumed, and return start\_walkthrough with an assumption clause, for example "I'll assume you're on the app and give you all the steps at once. Tell me if you're on the portal instead."
4. Otherwise find the first missing value in the order platform, style, loudspeaker. Loudspeaker is asked once only.
5. If its ask count is below 2, increment it and return ask\_preference with the question below.
6. If it has already been asked twice, assume it and move to the next missing value.
7. When platform and style are set and loudspeaker has been answered or asked once, return start\_walkthrough with the journey in note.

| Preference | Question (say) | Default when assumed |
| --- | --- | --- |
| platform | "Are you on the GrabMerchant app, or the GrabMerchant portal on a computer?" | app |
| style | "Would you like the steps one by one, or all at once?" | all\_at\_once |
| loudspeaker | "Would you like to put me on loudspeaker before we start?" | no |

**Rules the tool enforces, from SRC-3**

- No navigation step is given before the platform question has been asked at least once.
- Loudspeaker is never asked in the same reply as platform or style.
- Preferences hold for the whole call, including a second order (TC-021, TC-044). The tool returns start\_walkthrough immediately when all are already set.
- An answer the merchant gave is never reported back as an assumption.

**Code: set\_guidance\_preference (core)**

```javascript
// Tool: set_guidance_preference. No return statements; the result leaves through actions.output.
// Questions come from the active language pack (fixed.phrases).
const a = input.aiAgent?.toolArgs || {};
if (!context.shortTermMemory) {
  context.shortTermMemory = {};
}
const u = context.shortTermMemory.uc4;
const p = u.prefs;
const ph = context.uc4Cfg.fixed.phrases;
const max = context.uc4Cfg.flags.maxPrefAsks;
const res = (n, say, extra) => Object.assign({ success: true, next_action: n, say: say || "", guide: "", verbatim: false }, extra || {});
const Q = { platform: ph.askPlatform, style: ph.askStyle, loudspeaker: ph.askLoudspeaker };
const DEF = { platform: "app", style: "all_at_once", loudspeaker: "no" };
let out = res("apologise_and_retry_once", "");

if (a.journey) { u.walk.pendingJourney = a.journey; }
if (a.platform) { p.platform = a.platform === "either" ? DEF.platform : a.platform; }
if (a.style) { p.style = a.style === "either" ? DEF.style : a.style; }
if (a.loudspeaker) { p.loudspeaker = a.loudspeaker; }

if (!u.walk.pendingJourney) {
  out = res("steer_back", "");
} else if (a.pressed_for_steps === true) {
  const platformAssumed = !p.platform;
  ["platform", "style", "loudspeaker"].forEach(k => {
    if (!p[k]) { p[k] = DEF[k]; p.assumed.push(k); }
  });
  out = res("start_walkthrough", "", { guide: "journey=" + u.walk.pendingJourney +
    (platformAssumed ? ". In one short clause, say you will assume the app and give all the steps at once, and that they can say if they are on the portal." : "") });
} else {
  // First missing preference, in order. Loudspeaker is asked once only.
  let asked = false;
  const assumedNow = [];
  ["platform", "style", "loudspeaker"].forEach(k => {
    const limit = k === "loudspeaker" ? 1 : max;
    if (!asked && !p[k] && p.asks[k] < limit) {
      p.asks[k] += 1;
      asked = true;
      out = res("ask_preference", Q[k], { verbatim: true });
    } else if (!asked && !p[k] && k !== "loudspeaker") {
      p[k] = DEF[k];
      p.assumed.push(k);
      assumedNow.push(k === "platform" ? "the app" : "all the steps at once");
    }
  });
  if (!asked) {
    out = res("start_walkthrough", "", { guide: "journey=" + u.walk.pendingJourney +
      (assumedNow.length > 0 ? ". In one short clause, say you will assume " + assumedNow.join(" and ") + ", and that they can correct you." : "") });
  }
}

input.uc4Result = out;
actions.output("", out);
```

Note on loudspeaker: if it was asked once and the merchant answered something else, the walkthrough starts with loudspeaker left empty. That counts as no.

### 7.5 Step catalogue (context.uc4Cfg.steps)

Every screen instruction the bot can give is held here as data, so walkthrough tools never generate a menu path. Each step has a do part (the action) and a check part (the check back). In one by one mode a turn is do + check. In all at once mode every step in the same chunk is joined into one turn and only the chunk's last check is used. Screen names are exactly as SRC-3 protected terms: never translated or paraphrased.

| Segment | Used for | LOB | Steps | Completion |
| --- | --- | --- | --- | --- |
| app\_view\_order | View cancelled order, and the start of app submission | Both | 6 | Order details open, offer submission |
| portal\_view\_order | View cancelled order on the portal | Both | 7 | Order details open, offer submission |
| food\_app\_status | Compensation status in the app | GrabFood only | 4 | Status read, or order details open |
| food\_app\_history | Fallback when the order is not in the Cancelled tab (only this month shows) | GrabFood only | 3 | Return to food\_app\_status, step order\_id |
| portal\_status | Compensation status on the portal (GrabMart always) | Both | 6 | Status read |
| app\_submit | Request for compensation link, form, fill | Both | 3 | Submitted |
| portal\_submit | Help Centre, route ladder, form, fill | Both | 4 or 5 | Submitted |

```javascript
// Code: Config (continued). Step text is Tier 1: said exactly. {evidence} is replaced with cfg.evidence[lob].
context.uc4Cfg.steps = {
  app_view_order: [
    { id: "open_app", chunk: 1, do: "Please open the GrabMerchant app.", check: "Can you see the home screen?" },
    { id: "orders_nav", chunk: 1, do: "Tap Orders on the bottom navigation bar.", check: "Can you see the Orders screen?" },
    { id: "history_tab", chunk: 1, do: "Go to the History tab at the top of the screen.", check: "Can you see it?" },
    { id: "date_selector", chunk: 1, do: "Tap the Date selector and choose the date the order was cancelled.", check: "Have you selected the date?" },
    { id: "confirm_date", chunk: 1, do: "Tap Confirm to apply the date.", check: "Did that work?" },
    { id: "order_id", chunk: 1, do: "Find and tap the specific Order ID to view its details.", check: "Can you see the order details now?" }
  ],
  portal_view_order: [
    { id: "open_portal", chunk: 1, do: "Please open the GrabMerchant portal on your computer.", check: "Can you see the home screen?" },
    { id: "orders_menu", chunk: 1, do: "Click Orders on the left navigation menu.", check: "Can you see it?" },
    { id: "store_name", chunk: 1, do: "Select the relevant Store Name.", check: "Have you selected your store?" },
    { id: "history_tab", chunk: 1, do: "Click the History tab.", check: "Can you see it?" },
    { id: "date_filter", chunk: 1, do: "Click the Date Filter and select the date the order was cancelled.", check: "Have you selected the date?" },
    { id: "status_cancelled", chunk: 1, do: "Click the status dropdown next to the date, which shows All by default, and select Cancelled.", check: "Did that work?" },
    { id: "order_id", chunk: 1, do: "Find and click the specific Order ID to view its details.", check: "Can you see the order details now?" }
  ],
  food_app_status: [
    { id: "open_app", chunk: 1, do: "Please open the GrabMerchant app.", check: "Tell me when you see the home screen." },
    { id: "orders_tile", chunk: 1, do: "Open the Orders tile.", check: "Tell me when you see it." },
    { id: "cancelled_tab", chunk: 1, do: "Tap the Cancelled tab at the top. It shows this month's cancelled orders and their compensation status.", check: "Can you see your order there, and what status does it show?" },
    { id: "order_id", chunk: 2, do: "Tap the Order ID to open its details.", check: "Tell me when the details page opens." }
  ],
  food_app_history: [
    { id: "history_tab", chunk: 1, do: "Go to the History tab at the top.", check: "Can you see it?" },
    { id: "date_selector", chunk: 1, do: "Tap the Date selector and choose the date the order was cancelled.", check: "Have you selected the date?" },
    { id: "confirm_date", chunk: 1, do: "Tap Confirm to apply the date.", check: "Can you see your order now?" }
  ],
  portal_status: [
    { id: "open_portal", chunk: 1, do: "Please open the GrabMerchant portal on your computer.", check: "Tell me when you see the home screen." },
    { id: "finance", chunk: 1, do: "Open Finance on the left sidebar.", check: "Tell me when it opens." },
    { id: "transactions", chunk: 1, do: "Click the Transactions tab.", check: "Tell me when you see it." },
    { id: "period_store", chunk: 1, do: "Choose a time period that covers the day of the order, and the applicable store.", check: "Tell me when that's set." },
    { id: "category", chunk: 1, do: "Under the Category filter, choose Compensation for cancelled orders.", check: "Tell me when that's selected." },
    { id: "status_check", chunk: 1, do: "", check: "Does the cancelled order appear there as compensated?" }
  ],
  app_submit: [
    { id: "rfc_link", chunk: 1, do: "On the order details page, tap the Request for compensation link.", check: "Can you see it?" },
    { id: "form", chunk: 1, do: "It opens the Help Centre article Report a payment dispute. You need to be logged in as an Owner or Manager to submit a request.", check: "Can you see the form?" },
    { id: "fill", chunk: 2, do: "Please fill in the form with the order details and attach {evidence}, then submit it.", check: "Tell me when you've submitted it." }
  ],
  portal_submit: [
    { id: "open_portal", chunk: 1, optional: "portalOpened", do: "Please open the GrabMerchant portal on your computer.", check: "Tell me when you see the home screen." },
    { id: "help_centre", chunk: 1, do: "Click Help Centre on the left navigation menu.", check: "Tell me when you're on the main Help Centre page." },
    { id: "route", chunk: 1, variants: [
        { lead: "", do: "Type dispute into the Search Bar and select the article Report a payment dispute." },
        { lead: "Since we couldn't find it that way, let's try another way. ", do: "Under Common Problems, select Payouts and Reports, then Payout issues, then click Report a payment dispute." },
        { lead: "Let's try one more way. ", do: "Under Browse by Services, select Payment Services, then Payment issues, then click Report a payment dispute." }
      ], check: "Were you able to find it?" },
    { id: "form", chunk: 1, do: "The form sits below the article text. You need to be logged in as an Owner or Manager to submit a request.", check: "Can you see the form?" },
    { id: "fill", chunk: 2, do: "Please fill in the form with the order details and attach {evidence}, then submit it.", check: "Tell me when you've submitted it." }
  ]
};

// Walkthrough Tier 1: fixed lines that carry screen names or policy
context.uc4Cfg.walkFixed = {
  scroll: { do: "That form sits below the article text. Please scroll down to the bottom of the page.", check: "Can you see the form now?" },
  roleReminder: "If the form still isn't showing, you're likely not logged in with the right role. Only an Owner or Manager can submit a request. Would you like to try logging in again with an Owner or Manager account?",
  roleRetryApp: "Please sign in again with an Owner or Manager account, then open the same cancelled order and tap Request for compensation. Tell me if the form is visible now.",
  roleRetryPortal: "Please sign in again with an Owner or Manager account, then open the same Report a payment dispute page. Tell me when you can see the form.",
  orderMissingPortal: "Change the time period so it covers the date the order was cancelled, and keep the same store and Category. Can you see it now?",
  crossBuild: "Would you like me to guide you to submit it through the GrabMerchant portal instead, for our support team to review further?",
  martPortalOnly: "This particular check has to be done on the GrabMerchant portal on a computer.",
  statusBlankLead: "If no compensation status is showing, the next step is to submit a Request for Compensation."
};

// Walkthrough Tier 2: guided, the LLM phrases these
context.uc4Cfg.walkGuided = {
  statusBlank: "Explain that when no compensation status shows, the next step is to submit a Request for Compensation for our support team to review further. Keep that phrase. Ask if they would like help with that.",
  statusCompensated: "Tell them the order shows as compensated, so the compensation has been processed.",
  softClose: "Say no problem, and that they are welcome to contact our support team for further review.",
  portalSoftClose: "Apologise that none of the routes reached the form, and say they are welcome to contact our support team for further review.",
  hold: "Acknowledge in a few words that they can take their time and you will stay on the line. Ask nothing new.",
  clarify: "Say sorry they are still having trouble and ask what they see on their screen. If they already described it, ask one diagnostic question about it instead."
};
```

**Source notes.** Route 2 includes the Payouts and Reports step from SRC-3. SRC-2 and the test transcripts leave it out (OI-06). The food\_app\_status route is the current production route from SRC-3 and TC-003 to TC-008. The app\_view\_order route is the SRC-2 route, still used for viewing an order by date (TC-017, TC-040).

### 7.6 start\_walkthrough

Picks the step segment from the LOB, journey and platform, applies the GrabMart rules, and delivers the first step (or the first chunk in all at once mode). It is the only place a segment is chosen, so GrabMart can never be sent to the app Cancelled tab for a status check. Covers every guidance test case.

**Tool description (for the LLM):** Call this when set\_guidance\_preference returns start\_walkthrough, or when the merchant accepts help submitting a request after viewing their order or checking status. Pass the journey from the previous tool's note.

**Parameters (JSON schema)**

```json
{
  "type": "object",
  "properties": {
    "journey": { "type": "string", "enum": ["view_order", "check_status", "submit_request", "status_then_submit"] }
  },
  "required": ["journey"],
  "additionalProperties": false
}
```

**Segment selection**

| Journey | Platform | GrabFood segment | GrabMart segment | Extra |
| --- | --- | --- | --- | --- |
| view\_order | app | app\_view\_order | app\_view\_order |  |
| view\_order | portal | portal\_view\_order | portal\_view\_order |  |
| check\_status | app | food\_app\_status | portal\_status | GrabMart: say martPortalOnly first, set walk.platform = portal (TC-029 to TC-031) |
| check\_status | portal | portal\_status | portal\_status |  |
| submit\_request | app | app\_submit if orderDetailsOpen, else app\_view\_order then app\_submit | same | Starts from opening the app (TC-012) |
| submit\_request | portal | portal\_submit | portal\_submit | open\_portal step skipped if the portal was already opened in this call |
| status\_then\_submit | any | as check\_status, then = submit | as check\_status, then = submit | Submission offered when status is blank or not compensated |

**GrabMart partial compensation sentence.** Said once per call, verbatim, before the first status or submission step (SRC-2 rows 27, 38 and 42; TC-027, TC-029). Tracked in walk.disclaimerSaid.

**Already submitted guard.** If the active order has submitted = true or closedAfterRole = true and the journey involves submission, return deliver\_say with scripts.common.alreadySubmitted + UDR (SRC-2 row 91).

**Code: start\_walkthrough**

```javascript
// Tool: start_walkthrough. No return statements; the result leaves through actions.output.
const a = input.aiAgent?.toolArgs || {};
if (!context.shortTermMemory) {
  context.shortTermMemory = {};
}
const u = context.shortTermMemory.uc4;
const cfg = context.uc4Cfg;
const p = u.prefs;
const w = u.walk;
const wf = cfg.walkFixed;
const o = u.orders.find(x => x.ref === u.activeOrder) || {};
const ev = cfg.evidence[u.lob];
const res = (n, say, extra) => Object.assign({ success: true, next_action: n, say: say || "", guide: "", verbatim: false }, extra || {});
const journey = a.journey || w.pendingJourney;
const submits = journey === "submit_request" || journey === "status_then_submit";
let out = res("apologise_and_retry_once", "");

if (submits && (o.submitted || o.closedAfterRole)) {
  out = res("deliver_guided", "", { guide: cfg.guided.alreadySubmitted });
} else {
  // 1. Choose the segment
  let lead = "";
  w.journey = journey;
  w.platform = p.platform;
  w.then = "";
  if (journey === "view_order") {
    w.segment = p.platform === "portal" ? "portal_view_order" : "app_view_order";
  } else if (journey === "check_status" || journey === "status_then_submit") {
    if (u.lob === "GrabFood" && p.platform === "app") {
      w.segment = "food_app_status";
    } else {
      w.segment = "portal_status";
      w.platform = "portal";
      if (u.lob === "GrabMart" && p.platform === "app") { lead = wf.martPortalOnly + " "; }
    }
    if (journey === "status_then_submit") { w.then = "submit"; }
  } else if (p.platform === "portal") {
    w.segment = "portal_submit";
  } else if (w.orderDetailsOpen) {
    w.segment = "app_submit";
  } else {
    w.segment = "app_view_order";
    w.then = "app_submit";
  }
  if (u.lob === "GrabMart" && journey !== "view_order" && !w.disclaimerSaid) {
    lead = cfg.fixed.GrabMart.partialDisclaimer + " " + lead;
    w.disclaimerSaid = true;
  }
  Object.assign(w, { stepIndex: 0, stuckCount: 0, routeIndex: 0, scrollAsked: false,
    roleAttempts: 0, roleState: "", awaiting: "", status: "active" });
  u.outcome.journeys.push(journey);

  // 2. Deliver the first step, or the first chunk in all at once mode
  const steps = cfg.steps[w.segment];
  const txt = s => (s.variants ? s.variants[w.routeIndex].lead + s.variants[w.routeIndex].do : s.do).replace("{evidence}", ev);
  const skip = s => !!(s && s.optional && w[s.optional]);
  while (skip(steps[w.stepIndex])) { w.stepIndex += 1; }
  let say = "";
  if (p.style === "one_by_one") {
    say = txt(steps[w.stepIndex]) + " " + steps[w.stepIndex].check;
  } else {
    const chunk = steps[w.stepIndex].chunk;
    const parts = [];
    let i = w.stepIndex;
    while (i < steps.length && steps[i].chunk === chunk) {
      if (!skip(steps[i])) { parts.push(txt(steps[i])); }
      i += 1;
    }
    w.stepIndex = i - 1;
    say = parts.join(" ") + " " + steps[w.stepIndex].check;
  }
  if (w.segment.indexOf("portal") !== -1) { w.portalOpened = true; }
  out = res("deliver_step", (lead + say).trim(), { verbatim: true, step_id: steps[w.stepIndex].id,
    guide: "Read screen names exactly. Wait for the merchant, then call advance_walkthrough." });
}

input.uc4Result = out;
actions.output("", out);
```

Every walk field used here (then, roleState, awaiting, portalOpened, orderDetailsOpen, disclaimerSaid, pendingJourney) has a default in Code: Initiate (Section 6.5).

### 7.7 advance\_walkthrough

The walkthrough state machine. The AI Agent classifies each merchant reply into one outcome and the tool decides everything else: the next step, repeats, clarifying questions, the next portal route, the scroll and role path, cross build fallback, submission and offers of a person. Covers TC-003, TC-005 to TC-009, TC-012 to TC-018, TC-021, TC-027 to TC-032, TC-035 to TC-041 and TC-044.

&#91;embedded content: advance\_walkthrough · one confirm path and three failure ladders\]

Each ladder is counted in code, so the bot never offers a person early and never loops forever. needs\_time and silence sit outside all three ladders and never move them.

**Tool description (for the LLM):** Call this on every merchant reply while a walkthrough is active. Choose the one outcome that matches what they said about the step you just gave. A yes or no to a question you asked (help submitting, use the portal instead, log in again) is yes\_to\_question or no\_to\_question. If they say wait, they are checking, or their device is slow, use needs\_time. Malay and Manglish: dah, sudah, ok, boleh, nampak = confirmed; tak nampak, takde, tak jumpa = not visible or not found; jap, kejap, tunggu = needs\_time; tak payah, tak nak = no\_to\_question or declined\_walkthrough.

**Parameters (JSON schema)**

```json
{
  "type": "object",
  "properties": {
    "outcome": {
      "type": "string",
      "enum": ["confirmed", "failed", "order_not_visible", "status_blank", "status_compensated",
               "link_not_found", "route_not_found", "form_not_visible", "scrolled_no_form", "form_visible",
               "submitted", "yes_to_question", "no_to_question", "platform_switch", "skip_to_step",
               "needs_time", "declined_walkthrough"]
    },
    "step_id": { "type": "string", "description": "For skip_to_step or failed: the step the merchant means, if they named one." },
    "new_platform": { "type": "string", "enum": ["app", "portal"], "description": "For platform_switch only." },
    "screen_description": { "type": "string", "description": "What the merchant says is on their screen, if they described it." }
  },
  "required": ["outcome"],
  "additionalProperties": false
}
```

**Outcome table**

| Outcome | Where | Result |
| --- | --- | --- |
| confirmed | Any step | stuckCount = 0. Next step, or the segment completion rule below. |
| failed | Any step except a portal route | stuckCount + 1, then the stuckLadder entry: repeat (same step, add location detail), clarify (ask what they see), offer\_transfer (reason difficulty\_cap). TC-007, TC-018, TC-031, TC-041. |
| needs\_time | Any | hold. No counter changes (SRC-3: asking for time is not asking for help). |
| order\_not\_visible | food\_app\_status | Switch to food\_app\_history (History tab, Date selector, Confirm), then back to order\_id. TC-007. |
| order\_not\_visible | portal\_status | Say orderMissingPortal (change the time period). |
| status\_blank | food\_app\_status, portal\_status | If journey is status\_then\_submit, go straight to submission. Else say statusBlank and wait for yes or no. TC-003, TC-008, TC-027 to TC-030. |
| status\_compensated | status segments | Say statusCompensated + UDR. Walk complete. |
| link\_not\_found | app\_submit rfc\_link | First time: offer the portal (crossBuild). Yes: start portal\_submit. No: linkSoftClose + UDR. TC-008. |
| route\_not\_found | portal\_submit route | routeIndex + 1 and deliver the next route with its lead. After route 3: offer\_transfer (reason portal\_exhausted) or soft close, per flag. TC-013 to TC-016, TC-036 to TC-039. |
| form\_not\_visible | form step | First time: scroll instruction. After that: as scrolled\_no\_form. |
| scrolled\_no\_form | form step | Role reminder with retry question. Yes: retry instruction, roleAttempts + 1. Retry fails: offer\_transfer (reason role\_failed). No: Final Educate + UDR, order.closedAfterRole = true. TC-006, TC-009, TC-030, TC-032. |
| form\_visible | form step | Go to the fill step. |
| submitted | fill step | order.submitted = true. afterSubmission + UDR. TC-003, TC-005 to TC-008, TC-013 to TC-015. |
| yes\_to\_question / no\_to\_question | after a question | Interpreted by walk.awaiting: submit\_choice, cross\_build or role\_retry. |
| platform\_switch | Any | Store the new platform and restart the equivalent segment on it. Preferences kept. |
| skip\_to\_step | Any | Jump to the named step in the current segment. SRC-2 row 45. |
| declined\_walkthrough | Any | Walk abandoned. UDR. |

**Segment completion rules**

| Segment ends | Then |
| --- | --- |
| app\_view\_order, portal\_view\_order | orderDetailsOpen = true. If then = app\_submit, start app\_submit. Else say orderVisible and wait (TC-017, TC-040). |
| food\_app\_history | Return to food\_app\_status at order\_id. |
| food\_app\_status | orderDetailsOpen = true. If then = app\_submit, start app\_submit. Else say orderVisible and wait (TC-006). |
| portal\_status | The last check was answered yes, so status\_compensated. |
| app\_submit, portal\_submit | As submitted. |

**Code: advance\_walkthrough**

```javascript
// Tool: advance_walkthrough. No return statements: every helper writes to out.
const a = input.aiAgent?.toolArgs || {};
if (!context.shortTermMemory) {
  context.shortTermMemory = {};
}
const u = context.shortTermMemory.uc4;
const cfg = context.uc4Cfg;
const p = u.prefs;
const w = u.walk;
const fx = cfg.fixed;
const wf = cfg.walkFixed;
const wg = cfg.walkGuided;
const o = u.orders.find(x => x.ref === u.activeOrder) || {};
const ev = cfg.evidence[u.lob];
const steps = () => cfg.steps[w.segment] || [];
const cur = () => steps()[w.stepIndex];
const idx = id => steps().findIndex(s => s.id === id);
const res = (n, say, extra) => Object.assign({ success: true, next_action: n, say: say || "", guide: "",
  verbatim: false, step_id: cur() ? cur().id : "" }, extra || {});
const txt = s => (s.variants ? s.variants[w.routeIndex].lead + s.variants[w.routeIndex].do : s.do).replace("{evidence}", ev);
const skip = s => !!(s && s.optional && w[s.optional]);
let out = res("apologise_and_retry_once", "");

// Helpers. None of them use return; each one sets out.
const deliver = lead => {
  while (skip(steps()[w.stepIndex])) { w.stepIndex += 1; }
  const list = steps();
  let say = "";
  if (p.style === "one_by_one") {
    say = txt(list[w.stepIndex]) + " " + list[w.stepIndex].check;
  } else {
    const ch = list[w.stepIndex].chunk;
    const parts = [];
    let i = w.stepIndex;
    while (i < list.length && list[i].chunk === ch) {
      if (!skip(list[i])) { parts.push(txt(list[i])); }
      i += 1;
    }
    w.stepIndex = i - 1;
    say = parts.join(" ") + " " + list[w.stepIndex].check;
  }
  if (w.segment.indexOf("portal") !== -1) { w.portalOpened = true; }
  out = res("deliver_step", ((lead || "") + say).trim(), { verbatim: true });
};
const startSegment = (seg, lead) => {
  Object.assign(w, { segment: seg, stepIndex: 0, stuckCount: 0, routeIndex: 0, scrollAsked: false,
    roleAttempts: 0, roleState: "", awaiting: "" });
  if (seg.indexOf("portal") !== -1) { w.platform = "portal"; }
  deliver(lead);
};
const finish = (guideText, fixedText) => {
  w.status = "completed";
  w.awaiting = "";
  if (fixedText) {
    out = res("deliver_say", fixedText + " " + fx.udr, { verbatim: true });
  } else {
    out = res("deliver_guided", "", { guide: guideText + " Then ask if there is anything else you can help with." });
  }
};
const markSubmitted = () => {
  o.submitted = true;
  u.outcome.result = "submitted";
  finish("", fx.afterSubmission);
};
const offer = (reason, lead) => {
  if (u.transfer.declined) {
    finish(wg.softClose, "");
  } else {
    u.transfer.offered = true;
    u.transfer.reason = reason;
    out = res("offer_transfer", ((lead || "") + fx.offerPerson).trim(), { verbatim: true });
  }
};
const toSubmit = lead => {
  if (w.platform === "portal") {
    startSegment("portal_submit", lead);
  } else if (w.orderDetailsOpen) {
    startSegment("app_submit", lead);
  } else if (w.segment === "food_app_status") {
    w.then = "app_submit";
    w.stepIndex = idx("order_id");
    deliver(lead);
  } else {
    w.then = "app_submit";
    startSegment("app_view_order", lead);
  }
};
const segmentEnd = () => {
  const seg = w.segment;
  if (seg === "food_app_history") {
    w.segment = "food_app_status";
    w.stepIndex = idx("order_id");
    deliver();
  } else if (seg === "portal_status") {
    finish(wg.statusCompensated, "");
  } else if (seg === "app_submit" || seg === "portal_submit") {
    markSubmitted();
  } else if (w.then === "app_submit") {
    w.orderDetailsOpen = true;
    w.then = "";
    startSegment("app_submit");
  } else {
    w.orderDetailsOpen = true;
    w.awaiting = "submit_choice";
    out = res("deliver_say", fx.orderVisible, { verbatim: true });
  }
};
const roleStep = () => {
  if (w.roleState === "" && !cfg.flags.roleRetryEnabled) {
    offer("role_failed", fx.phrases.ownerManagerOnly + " ");
  } else if (w.roleState === "" || w.roleAttempts < cfg.flags.roleMaxAttempts - 1) {
    w.roleState = "asked";
    w.awaiting = "role_retry";
    out = res("deliver_say", wf.roleReminder, { verbatim: true });
  } else {
    offer("role_failed", "");
  }
};

// Main decision chain
if (a.step_id && idx(a.step_id) !== -1) { w.stepIndex = idx(a.step_id); }
let oc = a.outcome;
if (oc === "order_not_visible" && w.segment !== "food_app_status" && w.segment !== "portal_status") {
  oc = "failed"; // on view segments a missing order is a failed date step
}

if (oc === "confirmed") {
  w.stuckCount = 0;
  if (w.stepIndex >= steps().length - 1) { segmentEnd(); } else { w.stepIndex += 1; deliver(); }
} else if (oc === "failed") {
  w.stuckCount += 1;
  const ladder = cfg.flags.stuckLadder;
  const act = ladder[Math.min(w.stuckCount - 1, ladder.length - 1)];
  if (act === "repeat") {
    out = res("deliver_step", txt(cur()) + " " + cur().check,
      { verbatim: true, guide: "Repeat this one step. If they asked where, add where it is on the screen." });
  } else if (act === "clarify") {
    out = res("deliver_guided", "", { guide: wg.clarify + (a.screen_description ? " They said: " + a.screen_description : "") });
  } else {
    offer("difficulty_cap", fx.phrases.sorryStuck + " ");
  }
} else if (oc === "needs_time") {
  out = res("hold", "", { guide: wg.hold });
} else if (oc === "order_not_visible" && w.segment === "food_app_status") {
  const keepThen = w.then;
  startSegment("food_app_history");
  w.then = keepThen;
} else if (oc === "order_not_visible") {
  out = res("deliver_step", wf.orderMissingPortal, { verbatim: true });
} else if (oc === "status_blank" && w.journey === "status_then_submit") {
  toSubmit(wf.statusBlankLead + " ");
} else if (oc === "status_blank") {
  w.awaiting = "submit_choice";
  out = res("deliver_guided", "", { guide: wg.statusBlank });
} else if (oc === "status_compensated") {
  finish(wg.statusCompensated, "");
} else if (oc === "link_not_found" && !w.crossBuildOffered) {
  w.crossBuildOffered = true;
  w.awaiting = "cross_build";
  out = res("deliver_say", wf.crossBuild, { verbatim: true });
} else if (oc === "link_not_found") {
  finish(wg.softClose, "");
} else if (oc === "route_not_found" && w.routeIndex < 2) {
  w.routeIndex += 1;
  w.stepIndex = idx("route");
  deliver();
} else if (oc === "route_not_found" && cfg.flags.portalExhaustedAction === "offer_transfer") {
  offer("portal_exhausted", fx.phrases.noneWorked + " ");
} else if (oc === "route_not_found") {
  finish(wg.portalSoftClose, "");
} else if (oc === "form_not_visible" && !w.scrollAsked) {
  w.scrollAsked = true;
  out = res("deliver_step", wf.scroll.do + " " + wf.scroll.check, { verbatim: true });
} else if (oc === "form_not_visible" || oc === "scrolled_no_form") {
  w.scrollAsked = true;
  roleStep();
} else if (oc === "form_visible") {
  w.stepIndex = idx("fill");
  deliver();
} else if (oc === "submitted") {
  markSubmitted();
} else if (oc === "yes_to_question" && w.awaiting === "submit_choice") {
  w.awaiting = "";
  toSubmit();
} else if (oc === "yes_to_question" && w.awaiting === "cross_build") {
  w.awaiting = "";
  startSegment("portal_submit");
} else if (oc === "yes_to_question" && w.awaiting === "role_retry") {
  w.awaiting = "";
  w.roleAttempts += 1;
  out = res("deliver_step", w.platform === "portal" ? wf.roleRetryPortal : wf.roleRetryApp, { verbatim: true });
} else if (oc === "no_to_question" && w.awaiting === "role_retry") {
  o.closedAfterRole = true;
  finish(cfg.guided.finalEducate, "");
} else if (oc === "no_to_question") {
  finish(w.awaiting === "cross_build" ? wg.softClose : "Acknowledge briefly.", "");
} else if (oc === "platform_switch") {
  p.platform = a.new_platform || p.platform;
  w.platform = p.platform;
  const map = p.platform === "portal"
    ? { app_view_order: "portal_view_order", food_app_status: "portal_status", food_app_history: "portal_status", app_submit: "portal_submit" }
    : { portal_view_order: "app_view_order", portal_status: u.lob === "GrabFood" ? "food_app_status" : "portal_status", portal_submit: "app_submit" };
  startSegment(map[w.segment] || w.segment);
} else if (oc === "skip_to_step") {
  deliver();
} else if (oc === "declined_walkthrough") {
  finish("Acknowledge briefly.", "");
} else if (oc === "yes_to_question") {
  out = res("steer_back", "");
}

input.uc4Result = out;
actions.output("", out);
```

**Developer notes**

- There is no recursion. An order\_not\_visible report on a view segment is remapped to failed before the decision chain runs.
- The return keyword does not appear anywhere in the node, including inside helpers, as the cognigy-code-patterns guideline requires. Each helper writes the result to out.
- In all at once mode a failure report points at the last step of the chunk unless the agent passes step\_id. The tool description asks for it.
- When roleRetryEnabled is false, the behaviour matches SRC-3 (reminder, then offer). Use this if Grab confirms SRC-3 over TC-006 and TC-009.
- Tier 1 text (steps, role reminder, cross build offer) is returned with verbatim true. Tier 2 replies (clarify, hold, status explanations, soft closes) are returned as guide, so the LLM phrases them naturally.

### 7.8 search\_knowledge

A grounded fallback for cancelled order compensation questions that no script covers, such as eligibility for a specific cancellation reason, what counts as already prepared, or where compensation shows on a payout statement. SRC-3 notes that broad Help Centre RAG caused hallucinations, so the knowledge store is restricted and the tool returns a plain "not on hand" result rather than guessing.

**Tool description (for the LLM):** Call this only for a cancelled order compensation question that your other tools have not answered. Never call it for delivery, rider, account, menu, or general payout questions. Never call it to find menu paths or screen names.

**Parameters (JSON schema)**

```json
{
  "type": "object",
  "properties": {
    "query": { "type": "string", "description": "The merchant's question rewritten as a short standalone search query in English, even when they spoke Bahasa Melayu or Manglish. Answer in the conversation language." }
  },
  "required": ["query"],
  "additionalProperties": false
}
```

**Flow under the tool**

| # | Node | Option A: Cognigy Knowledge AI | Option B: CXone Expert |
| --- | --- | --- | --- |
| 1 | If | {{context.uc4Cfg.knowledgeSource}} equals cognigy | Else branch |
| 2 | Search | Search Extract Output. Store: Grab Merchant MY, UC4 subset. Query: {{input.aiAgent.toolArgs.query}}. Top K: 3. Output to input.uc4Kb. | Expert search through the connector or an HTTP Request node, per NiCE's standard. Same query. Results arrive in input.expertKernels. |
| 3 | Code | Code: Format KB (below) | Code: Format Expert (cognigy-code-patterns Pattern 9, below) |
| 4 | Resolve Tool Action | Closes the tool call. The result already went out through actions.output. | Same |

Pick the option by where Grab's approved content lives. If it is in CXone Expert, option B avoids keeping two copies of the same articles. Both paths return the same result contract, so the AI Agent, its instructions and the tests do not change with the choice. During the pilot both branches can stay in the Flow behind the If node.

**Code: Format KB (option A)**

```javascript
// Code: Format KB. Cognigy Knowledge AI. No return statements.
// Confirm the Search Extract Output field names in the project's Cognigy version during sprint 0.
const kb = input.uc4Kb || {};
const answer = String(kb.extract || kb.answer || "").trim();
const top = (kb.searchResults && kb.searchResults[0]) || {};
const topScore = Number(top.score || 0);
const minScore = context.uc4Cfg.knowledge.minScore;
let out;
if (answer && topScore >= minScore) {
  out = { success: true, next_action: "deliver_guided", say: "", verbatim: false,
    guide: "Answer only from this text, in one or two spoken sentences, and never say where it came from: " + answer };
} else {
  out = { success: true, next_action: "deliver_guided", say: "", verbatim: false,
    guide: "Say you don't have that detail on hand, then ask if there is anything else you can help with." };
}
input.uc4Result = out;
actions.output("", out);
```

**Code: Format Expert (option B, Pattern 9)**

```javascript
// Code: Format Expert. CXone Expert kernels, following cognigy-code-patterns Pattern 9. No return statements.
if (!context.shortTermMemory) {
  context.shortTermMemory = {};
}
const kernels = Array.isArray(input.expertKernels) ? input.expertKernels : [];
const results = kernels.map(k => ({
  kernelId: k.id || "",
  score: parseFloat(k.score || 0),
  content: (k.chunk || "").trim(),
  pageTitle: (k.page && k.page.title) || "",
  pageUrl: (k.page && k.page["uri.ui"]) || ""
}));
const cfgK = context.uc4Cfg.knowledge;
const usable = results.filter(r => r.content && r.score >= cfgK.minScore).sort((x, y) => y.score - x.score);
context.shortTermMemory.uc4.kbResults = usable.slice(0, cfgK.topK);
let out;
if (usable.length > 0) {
  out = { success: true, next_action: "deliver_guided", say: "", verbatim: false,
    guide: "Answer only from this text, in one or two spoken sentences, and never say where it came from: " + usable[0].content };
} else {
  out = { success: true, next_action: "deliver_guided", say: "", verbatim: false,
    guide: "Say you don't have that detail on hand, then ask if there is anything else you can help with." };
}
input.uc4Result = out;
actions.output("", out);
```

**Knowledge content (Tier 3).** Load only the Help Centre articles Grab approves for UC4 from help.grab.com/merchant/en-my, in either store. Exclude articles that describe menu paths, because the step catalogue is the only source of screen instructions. Policy timelines are also excluded, because the fixed scripts already carry Grab's approved wording and two sources could disagree.

### 7.9 transfer\_to\_live\_agent

Acts on the merchant's answer to an offer of a person. The guard (transfer.offered === true) means it is available only after a tool has made the offer, so the bot cannot transfer on its own initiative. On yes it is terminal: it plays the fixed transfer message and hands the call to CXone classified as 'others'. Covers TC-009, TC-010, TC-016, TC-018, TC-020, TC-024, TC-032, TC-033, TC-039, TC-041 and TC-043.

**Tool description (for the LLM):** Call this when the merchant answers your offer to connect them with someone. yes only if the whole sense of their reply is yes, put me through. A reply that only reports the step still failing is unclear, not yes. Phrases such as no need, nevermind, I'll do it later, tak payah, tak nak are no.

**Parameters (JSON schema)**

```json
{
  "type": "object",
  "properties": {
    "merchant_answer": { "type": "string", "enum": ["yes", "no", "unclear"] }
  },
  "required": ["merchant_answer"],
  "additionalProperties": false
}
```

**Logic**

| Answer | Reason on file | Result |
| --- | --- | --- |
| yes | any | Terminal. transfer.executed = true. Say messages.transfer verbatim, build the ACW payload (Section 8.2), run the Voice Gateway Transfer node. |
| no | language | next\_action end\_call with exit\_type language\_not\_supported (SRC-3 Exit 4). |
| no | other\_brand | steer\_back: "No problem, let's carry on with your " + lob + " order." |
| no | difficulty\_cap, portal\_exhausted, role\_failed | deliver\_say: "No problem." + UDR (SRC-2: declines go to UDR). |
| no | out\_of\_scope, dissatisfied, human\_request | deliver\_say: "No problem." + UDR. |
| unclear, first time | any | deliver\_say: "Just to check, would you like me to put you through to someone who can help further?" |
| unclear, second time | any | Treated as no. |

On every no: transfer.declined = true and transfer.offered = false. This removes the tool from the LLM until a new offer is made.

**Flow under the tool**

1. Code: Transfer Decision. Applies the table above. Sets input.uc4Go = true only for yes.
2. If input.uc4Go is true:
   1. Code: Build ACW (Section 8.2).
   2. Say: {{context.uc4Cfg.messages.transfer}}. Plain Say node, not generated by the LLM.
   3. Voice Gateway Transfer node. Type: refer (or dial, per NiCE, OI-02). Target: {{context.uc4Cfg.transferTargets.others}}. Custom SIP headers per Section 8.1.
3. Else: Resolve Tool Action. The result already went out through actions.output.

**Code: Transfer Decision**

```javascript
// Code: Transfer Decision. No return statements.
const a = input.aiAgent?.toolArgs || {};
if (!context.shortTermMemory) {
  context.shortTermMemory = {};
}
const u = context.shortTermMemory.uc4;
const cfg = context.uc4Cfg;
const res = (n, say, extra) => Object.assign({ success: true, next_action: n, say: say || "", guide: "", verbatim: false }, extra || {});
let out = res("apologise_and_retry_once", "");
input.uc4Go = false;

if (a.merchant_answer === "yes") {
  u.transfer.executed = true;
  u.outcome.result = "transferred";
  input.uc4Go = true;
  out = res("terminal", "");
} else if (a.merchant_answer === "unclear" && !u.transfer.unclearOnce) {
  u.transfer.unclearOnce = true;
  out = res("deliver_guided", "", { guide: "Ask once more, in different words, whether they would like you to connect them with someone who can help further." });
} else {
  const reason = u.transfer.reason;
  Object.assign(u.transfer, { declined: true, offered: false, unclearOnce: false });
  if (reason === "language") {
    out = res("end_call", "", { guide: "exit_type=language_not_supported" });
  } else if (reason === "other_brand") {
    out = res("steer_back", "", { guide: cfg.guided.continueOrder.replace("{lob}", u.lob) });
  } else {
    out = res("deliver_guided", "", { guide: cfg.guided.declinedPerson });
  }
}

input.uc4Result = out;
// Only the no and unclear branches hand a result back. The yes branch continues to Say and Transfer.
if (!input.uc4Go) {
  actions.output("", out);
}
```

### 7.10 escalate\_safety

The only transfer without a consent question. It interrupts any journey, including a walkthrough in progress, and the dispute flow is not resumed (TC-011, TC-012, TC-034, TC-035). The tool has no guard so it is always available.

**Tool description (for the LLM):** Call this immediately, before anything else, when the merchant reports a real emergency happening now: someone injured or unconscious, an accident that just happened, immediate danger, a threat or harassment, or a live food safety incident. Do not call it for a question about what to do if something happens, a hypothetical, or a past and resolved event. If you genuinely cannot tell, ask one short question first. Never give medical or first aid instructions.

**Parameters (JSON schema)**

```json
{
  "type": "object",
  "properties": {
    "summary": { "type": "string", "description": "One line on what the merchant reported, for the agent who takes the call." }
  },
  "required": ["summary"],
  "additionalProperties": false
}
```

**Flow under the tool**

1. Code: Safety. Sets transfer.reason = safety, transfer.executed = true, outcome.result = safety, walk.status = handed\_over, and stores the summary for the ACW payload.
2. Code: Build ACW (Section 8.2) with priority = safety.
3. Say: {{context.uc4Cfg.messages.safety}}. Fixed text: acknowledges the concern, tells them to call their local emergency number if anyone is hurt, and says they are being connected now.
4. Voice Gateway Transfer node to {{context.uc4Cfg.transferTargets.others}}, with SIP header X-UC4-Priority: safety.

A hypothetical safety question ("who should I call if my rider has an accident?") is not this tool. It is out of scope and goes to get\_approved\_answer with topic out\_of\_scope, which offers a person as a question.

### 7.11 end\_call

Plays the exit message that matches how the call ended, then hangs up. The exit wording comes from config, never from the LLM, so the call always ends on a line Grab approved (SRC-3 closing discipline).

**Tool description (for the LLM):** Call this to end the call. closing\_a: you asked whether there is anything else and the merchant said no, or said thanks or bye after that question. disengaged: the merchant says they must leave now while work is still open (I'm busy, gotta go). could\_not\_resolve: the merchant declined every remaining option and wants to end. language\_not\_supported: transfer\_to\_live\_agent told you to. Never call it on a bare goodbye before you have asked if there is anything else. Never call it when the merchant says the order is the other brand.

**Parameters (JSON schema)**

```json
{
  "type": "object",
  "properties": {
    "exit_type": { "type": "string", "enum": ["closing_a", "disengaged", "could_not_resolve", "language_not_supported"] }
  },
  "required": ["exit_type"],
  "additionalProperties": false
}
```

**Exit messages**

| exit\_type | Message (config key) | SRC-3 | Test cases |
| --- | --- | --- | --- |
| closing\_a | exitClosingA: "Thank you for calling Grab. If there's anything else you need help with, please contact us again. Have a nice day." | Exit 1 | Most closings |
| disengaged | exitDisengaged | Exit 3 | SRC-2 Early Call Termination |
| could\_not\_resolve | exitCouldNotResolve | Exit 2 | none directly |
| language\_not\_supported | exitLanguage | Exit 4 | Unsupported language, person declined |

**Flow under the tool**

1. Code: End Call. Sets closingSaid = true, outcome.result to the exit type unless it is already submitted or transferred, and selects the message into input.uc4ExitMsg.
2. Code: Build ACW (Section 8.2).
3. Say: {{input.uc4ExitMsg}}.
4. Hang Up node (Voice Gateway), with the ACW summary in a SIP header if NiCE confirms this is how CXone receives it (OI-07).

After closingSaid is true, the guards on resolve\_order\_age, get\_approved\_answer and end\_call are false, so nothing further can be spoken.

### 7.12 Tool build checklist

Use this list when building each tool in the AI Agent node.

- [ ] Tool name, description and JSON schema copied exactly from this section.
- [ ] Condition field set to the guard in 7.1, using context.shortTermMemory.uc4 paths.
- [ ] Code node guards shortTermMemory, reads input.aiAgent.toolArgs, and writes only to context.shortTermMemory.uc4.
- [ ] No return keyword anywhere in the node. Logic is an if/else chain assigning out.
- [ ] Returning tools end with actions.output("", out), followed by a Resolve Tool Action node.
- [ ] Tier 1 text comes from context.uc4Cfg.fixed, walkFixed or steps with verbatim true. Tier 2 text goes out as guide.
- [ ] Terminal paths (transfer yes, safety, end\_call) use plain Say nodes from config and never actions.output.
- [ ] No null written to context. Defaults added to Code: Initiate for every new field.
- [ ] Each tool tested alone in the Interaction Panel with context.shortTermMemory.uc4 preset, before end to end tests.
- [ ] Each tool's covered test cases from Section 10 run and recorded.

### 7.13 Alignment with NiCE's proposed tools (SRC-4)

All six tools NiCE proposed are kept. Three tools are added because the test cases need deterministic control that NiCE left to the LLM.

| SRC-4 tool | This design | Change |
| --- | --- | --- |
| Resolving the order age | resolve\_order\_age | Adds the weekday tables, the two asks cap, corrections and second orders. |
| Get guidance steps | start\_walkthrough plus the step catalogue | Steps held as data per LOB, platform and journey. |
| Advance walkthrough steps | advance\_walkthrough | Owns the stuck ladder, portal route ladder, role path and cross build fallback. |
| Search knowledge | search\_knowledge | Restricted store and fallback only (D-09). |
| Transfer to Live Agent | transfer\_to\_live\_agent | Consent gated by a guard. Classification 'others' and ACW payload. |
| Safety Escalation | escalate\_safety | Unchanged in intent, fixed message from config. |
| (new) | get\_approved\_answer | Approved wording and every non walkthrough offer of a person. |
| (new) | set\_guidance\_preference | Preference order, two asks cap, assumptions. |
| (new) | end\_call | Exit messages from config. |

## 8. Handover and CXone Integration

CXone owns the call before and after the bot. Two contracts must be agreed with NiCE before build sign off: what CXone sends into the Flow at call start, and what the Flow sends back on transfer or hang up. The values below are the proposed contract; the exact keys are open item OI-01 and OI-07.

### 8.1 Data contract

| Direction | Field | Proposed key | Example | Used by |
| --- | --- | --- | --- | --- |
| CXone to Flow | Line of business | SIP header X-Grab-LOB (or input.data.lob) | GrabFood | Code: Initiate. Never asked of the merchant. |
| CXone to Flow | Contact ID | SIP header X-Contact-Id | 7731245590 | ACW payload, test evidence (Call ID column in SRC-1) |
| CXone to Flow | Use case | SIP header X-Grab-UC | UC4 | Sanity check only |
| Flow to CXone | Classification | X-UC4-Classification | others | CXone routing on every transfer |
| Flow to CXone | Transfer reason | X-UC4-Reason | portal\_exhausted | Agent context and reporting |
| Flow to CXone | Priority | X-UC4-Priority | safety or normal | Safety routing |
| Flow to CXone | Summary | X-UC4-Summary | Base64 of the ACW JSON | Agent screen pop and after call work |

### 8.2 ACW payload

Built by Code: Build ACW on every terminal path, so a transferred agent and CXone reporting see the same summary. Plain digits are allowed here, unlike spoken output.

```json
{
  "uc": "UC4",
  "lob": "GrabFood",
  "contactId": "7731245590",
  "orders": [{ "ref": "A", "ageDays": 8, "threshold": "beyond", "submitted": false }],
  "journeys": ["status_then_submit"],
  "platform": "portal",
  "lastStep": "form",
  "result": "transferred",
  "transferReason": "role_failed",
  "classification": "others",
  "language": "en",
  "safetySummary": ""
}
```

```javascript
// Code: Build ACW. Shared by transfer, safety and end_call paths. No return statements.
const u = context.shortTermMemory.uc4;
const segSteps = context.uc4Cfg.steps[u.walk.segment] || [];
const lastStep = segSteps[u.walk.stepIndex] ? segSteps[u.walk.stepIndex].id : "";
const acw = {
  uc: "UC4",
  lob: u.lob,
  contactId: u.callId,
  orders: u.orders.map(o => ({ ref: o.ref, ageDays: o.ageDays, threshold: o.threshold, submitted: o.submitted })),
  journeys: u.outcome.journeys,
  platform: u.walk.platform || u.prefs.platform || "",
  lastStep: lastStep,
  result: u.outcome.result || "",
  transferReason: u.transfer.reason || "",
  classification: u.transfer.executed ? "others" : "",
  language: u.lang, languageSwitches: u.language.switches,
  safetySummary: u.safetySummary || ""
};
context.shortTermMemory.uc4Acw = acw;
input.uc4AcwB64 = Buffer.from(JSON.stringify(acw)).toString("base64");
```

### 8.3 Voice Gateway Transfer node

| Setting | Value |
| --- | --- |
| Transfer type | refer (or dial, per the NiCE pattern, OI-02) |
| Target | {{context.uc4Cfg.transferTargets.others}} |
| Custom SIP headers | X-UC4-Classification: others; X-UC4-Reason: {{context.shortTermMemory.uc4.transfer.reason}}; X-UC4-Priority: safety or normal; X-UC4-Summary: {{input.uc4AcwB64}} |
| On failure | Say: "I'm sorry, I couldn't connect you right now. Please call us back and choose the option for further help." then Hang Up. |

**Known test blocker.** The SRC-1 remarks on TC-018, TC-020, TC-032, TC-041 and TC-043 show the error "Transfer destination is required". This is the Transfer node running with an empty target. Benchmark TC-009 and TC-010 also end in a transfer, so transferTargets.others must be filled before the benchmark run. Until then, set a test destination (for example a CXone test skill) so the full path can be verified.

## 9. Voice Channel Configuration

Merchants follow app steps while on the phone, often on loudspeaker, and in English, Bahasa Melayu or Manglish. The voice settings therefore favour patience over speed: a longer silence allowance during walkthroughs, phrase hints for Grab screen names, and barge-in that does not cut the bot off on a stray "ok". Vendors and voice names follow the NiCE tenant standard (OI-10).

### 9.1 Set Session Config (start up)

| Parameter | Value |
| --- | --- |
| STT vendor | Per NiCE tenant standard |
| STT language | English and Malay recognised together in both nodes. English node: English (Malaysia where supported, else Singapore) primary, Malay (ms-MY) alternate. Malay node: Malay (ms-MY) primary, English alternate. This is what lets Manglish be transcribed. |
| Phrase hints | GrabMerchant, GrabFood, GrabMart, app, portal, cancelled, compensation, dispute, Request for Compensation, Report a payment dispute, Help Centre, Orders tile, History, Owner, Manager, payout, loudspeaker; Malay: pampasan, batal, dibatalkan, semalam, kelmarin, dah, tak nampak, takde |
| TTS | One English voice and one Malay voice approved by Grab, ideally the same persona. The voice changes only when the conversation language changes. |
| Barge-in | On, triggered by speech, minimum two words, so a lone "ok" or "ya" does not cut a step short |
| No input timeout (default) | 7 seconds |
| Recording | Handled by CXone. The greeting carries the recording notice. |
| Language nodes | Two Set Session Config nodes, English and Malay. An If on uc4.lang picks one at start up and again after a language switch (7.3). |

### 9.2 Walkthrough silence handling

start\_walkthrough runs a second Set Session Config that raises the no input timeout to 20 seconds, because merchants go quiet while they tap through screens. The timeout returns to 7 seconds when walk.status becomes completed. Both values are proposals for Grab to confirm.

A no input event is handled before the AI Agent node, so silence never counts toward the difficulty cap:

| Consecutive no input | Response |
| --- | --- |
| 1 | During a walkthrough: "Take your time, I'm still here." Otherwise: repeat the last question. |
| 2 | "Are you still there? Tell me when you're ready." |
| 3 | end\_call path with exit\_type disengaged. |

```javascript
// Code: No Input Counter. Runs when the input is a user input timeout (cognigy-code-patterns Pattern 5).
if (!context.shortTermMemory) {
  context.shortTermMemory = {};
}
const u = context.shortTermMemory.uc4;
u.noInput = (u.noInput || 0) + 1;
if (u.noInput >= 3) {
  input.uc4NoInputAction = "end_disengaged";
} else if (u.noInput === 2) {
  input.uc4NoInputAction = "check_presence";
} else {
  input.uc4NoInputAction = "reassure";
}
// Reset u.noInput = 0 at the top of every real merchant input.
```

### 9.3 Spoken output rules

- Numbers and amounts are spoken as words. Approved scripts are already written that way.
- Abbreviations are spelled out (A I, I D). If the chosen TTS voice reads Order ID as a word, change the step text to Order I D in the catalogue.
- No markdown or symbols reach TTS. A Code node before the output can strip any that slip through.
- One question per turn. Every walkthrough step ends with a check back.

## 10. Testing Strategy and Traceability

Testing runs in four stages, and each test case in SRC-1 is traced to the tools it exercises. The threshold depends on today's weekday, so every non production environment must be able to fix the date: Code: Initiate reads context.uc4Cfg.testToday (for example { iso: "2026-10-07", weekday: "Wed" }) when it is set, and the flag must be empty in production.

### 10.1 Test stages

| Stage | Where | What passes |
| --- | --- | --- |
| 1. Tool unit tests | Interaction Panel, context.shortTermMemory.uc4 preset per case | Each tool returns the expected next\_action and state for its decision table rows (7.2 to 7.11). |
| 2. Scripted end to end (text) | Interaction Panel with input.data.lob set | All 45 test cases as text, transcripts saved. |
| 3. Voice end to end | CXone test number into Voice Gateway | ASR, barge-in, silence handling, transfer and hang up on a real call. |
| 4. Benchmark run | Grab testers, SRC-1 columns Date, Call ID, Status | The 15 benchmark cases. Requires the transfer destination (OI-02). |

### 10.2 Traceability matrix

Benchmark cases are marked BM. Wording does not need to match the transcripts word for word: SRC-1 asks only that each turn "shares the same objective".

**Malay and Manglish runs.** SRC-1 contains English test cases only. The same 45 scenarios are also run with the merchant speaking Bahasa Melayu and Manglish, from a translated case set that Grab provides or approves (OI-22). A case passes when it meets the same objective as the English case, the bot replies in the merchant's language, screen names stay in English, and Manglish alone never triggers a language switch.

| TC | LOB | BM | Scenario | Tools exercised | Expected result and build note |
| --- | --- | --- | --- | --- | --- |
| TC-001 | Food | BM | Within, educate, close | resolve\_order\_age, end\_call | Timeline plus photo reminder plus UDR in one turn, then Closing A |
| TC-002 | Food | BM | Within, follow up, guidance declined | resolve\_order\_age, get\_approved\_answer, end\_call | furtherInquiry script, no to guidance, UDR, Closing A |
| TC-003 | Food | BM | Beyond, status and submit, app, one by one | resolve\_order\_age, set\_guidance\_preference, start\_walkthrough, advance\_walkthrough, end\_call | food\_app\_status, then app\_submit, after submission script |
| TC-004 | Food | BM | Beyond, timeline only | resolve\_order\_age, end\_call | Open question, then timeline without photo reminder |
| TC-005 | Food | BM | Beyond, status and dispute, app, all at once | as TC-003 | Status blank leads to submission. All at once chunks |
| TC-006 | Food | BM | App form not visible, role path | advance\_walkthrough | Scroll, role reminder, retry yes to fill (transcript) or retry no to Final Educate (flow path). Both supported (D-05) |
| TC-007 | Food | BM | Stuck on a step, repeat, recover | advance\_walkthrough | Repeat once then continue. Order not in Cancelled tab uses History route |
| TC-008 | Food | BM | App link missing, portal fallback | advance\_walkthrough | crossBuild offer, portal\_submit route 1 |
| TC-009 | Food | BM | Portal role path exhausted | advance\_walkthrough, transfer\_to\_live\_agent | Scroll, role, retry fails, offer, yes, transfer. Needs OI-02 |
| TC-010 | Food | BM | Out of scope | get\_approved\_answer, transfer\_to\_live\_agent | "I only handle issues about cancelled orders", consent, transfer. Needs OI-02 |
| TC-011 | Food |  | Safety, upfront | escalate\_safety | Immediate transfer, no consent |
| TC-012 | Food |  | Safety, mid walkthrough | escalate\_safety | Walkthrough stops, emergency line, transfer |
| TC-013 | Food |  | Portal route 1 succeeds | start\_walkthrough, advance\_walkthrough | portal\_submit, all at once |
| TC-014 | Food |  | Route 1 fails, route 2 succeeds | advance\_walkthrough | Route 2 lead "Since we couldn't find it that way" |
| TC-015 | Food |  | Routes 1 and 2 fail, route 3 succeeds | advance\_walkthrough | Route 3 lead "Let's try one more way" |
| TC-016 | Food |  | All three routes fail | advance\_walkthrough, transfer\_to\_live\_agent | Offer a person (D-04). Flow path text says soft close |
| TC-017 | Food |  | Within, follow up, view order, submit | get\_approved\_answer, set\_guidance\_preference, start\_walkthrough, advance\_walkthrough | app\_view\_order, orderVisible, app\_submit |
| TC-018 | Food |  | Stuck, cap reached, transfer | advance\_walkthrough, transfer\_to\_live\_agent | stuckLadder repeat, repeat, clarify, clarify, offer (D-03) |
| TC-019 | Food |  | Unclear date | resolve\_order\_age | Date asked twice, then open question, nothing said about the date |
| TC-020 | Food |  | Dissatisfied, then asks for a person | get\_approved\_answer, transfer\_to\_live\_agent | One retry, then offer, transfer |
| TC-021 | Food |  | Two orders | resolve\_order\_age (is\_new\_order), walkthrough tools | Order B named as separate, preferences reused |
| TC-022 | Food |  | Date corrected mid call | resolve\_order\_age (is\_correction) | Silent re-route to open question |
| TC-023 | Both |  | Malay request in an English conversation | get\_approved\_answer | Switches to Bahasa Melayu and continues. SRC-1 expects an English only reply (OI-09) |
| TC-024 | Both |  | Malay request, merchant insists on Malay | get\_approved\_answer, transfer\_to\_live\_agent | Switches to Bahasa Melayu, no transfer needed. SRC-1 expects a transfer (OI-09) |
| TC-025 | Mart | BM | Within, educate, close | resolve\_order\_age, end\_call | Three to five days wording, photo of the order |
| TC-026 | Mart | BM | Within, follow up, declined | as TC-002 | Same furtherInquiry script (shared app screens) |
| TC-027 | Mart | BM | Beyond, status and submit | resolve\_order\_age, set\_guidance\_preference, start\_walkthrough, advance\_walkthrough | Partial compensation sentence, portal\_status, portal\_submit. Transcript does the check in the app (OI-03) |
| TC-028 | Mart | BM | Beyond, timeline only | resolve\_order\_age, end\_call | As TC-004 with GrabMart wording |
| TC-029 | Mart | BM | Beyond, status and dispute, all at once | as TC-027 | martPortalOnly said when the merchant chose the app |
| TC-030 | Mart |  | Status via portal, then submit | as TC-027 | Flow path says role path decline. Transcript shows success. Both supported |
| TC-031 | Mart |  | Stuck on period step, repeat, recover | advance\_walkthrough | Repeat with location detail |
| TC-032 | Mart |  | Portal role path exhausted | as TC-009 | Needs OI-02 |
| TC-033 | Mart |  | Out of scope | as TC-010 | Needs OI-02 |
| TC-034 | Mart |  | Safety, upfront | escalate\_safety | As TC-011 |
| TC-035 | Mart |  | Safety, mid walkthrough | escalate\_safety | As TC-012 |
| TC-036 | Mart |  | Route 1 succeeds | as TC-013 | Evidence wording: packed items |
| TC-037 | Mart |  | Route 2 succeeds | as TC-014 |  |
| TC-038 | Mart |  | Route 3 succeeds | as TC-015 |  |
| TC-039 | Mart |  | All routes fail | as TC-016 | D-04 |
| TC-040 | Mart |  | Within, follow up, view order, submit | as TC-017 |  |
| TC-041 | Mart |  | Stuck, cap reached, transfer | as TC-018 | Needs OI-02 |
| TC-042 | Mart |  | Unclear date | as TC-019 |  |
| TC-043 | Mart |  | Dissatisfied, person | as TC-020 | Needs OI-02 |
| TC-044 | Mart |  | Two orders | as TC-021 |  |
| TC-045 | Mart |  | Date corrected | as TC-022 | "5 days ago" stays within for GrabMart (OI-05) |

## 11. Known Constraints and Open Items

Two items block the benchmark run: the CXone data contract (OI-01) and the transfer destination (OI-02). The rest are decisions Grab must confirm, each already built as a configurable default so a change is a config edit, not a rebuild.

| ID | Item | Build default | Owner | Blocks | Status |
| --- | --- | --- | --- | --- | --- |
| OI-01 | Keys CXone uses to send the LOB and contact ID into the Flow | X-Grab-LOB, X-Contact-Id, or input.data.lob | NiCE | Code: Initiate, every test | Open |
| OI-02 | Transfer destination and type (refer or dial) for 'others' | Empty, must be set | NiCE, Grab | 11 test cases incl. benchmark TC-009, TC-010 | Open |
| OI-03 | TC-027 checks GrabMart status in the app. SRC-3 says portal only | Portal only (D-07) | Grab | TC-027 (benchmark) | Open |
| OI-04 | Timeline wording: "approved, paid next payout cycle" vs SRC-2 "credited to bank account" | Approved and payout cycle (D-08) | Grab | TC-001, 004, 025, 028 | Open |
| OI-05 | TC-045 uses "5 days ago" as beyond for GrabMart, but it is within on every weekday | Table verdict (within) | Grab | TC-045 | Open |
| OI-06 | Portal route 2: include the Payouts and Reports step (SRC-3) or not (SRC-2, transcripts) | Included | Grab | TC-014, 037 | Open |
| OI-07 | How CXone receives the ACW summary on transfer and hang up, and its schema (SRC-3 refers to an ACW JSON not supplied) | SIP header X-UC4-Summary | NiCE | Agent screen pop, reporting | Open |
| OI-08 | Knowledge store articles and minimum score | UC4 subset, threshold to tune | Grab, Amansob | search\_knowledge | Open |
| OI-09 | TC-023 and TC-024 are written for an English only agent. With Malay supported, the bot switches to Bahasa Melayu instead. Grab to update the expected results, or confirm ask\_then\_transfer | Switch (languageSwitch = switch) | Grab, NiCE | Scope | Open |
| OI-10 | LLM, STT and TTS vendors and voice | NiCE tenant standard | NiCE | Section 5.1, 9.1 | Open |
| OI-11 | Difficulty cap ladder | repeat, repeat, clarify, clarify, offer (D-03) | Grab | TC-007, 018, 031, 041 | Open |
| OI-12 | All portal routes fail: offer a person or soft close | Offer a person (D-04) | Grab | TC-016, 039 | Open |
| OI-13 | Role path: retry (SRC-1, SRC-2) or no retry (SRC-3) | Retry, 2 attempts (D-05) | Grab | TC-006, 009, 030, 032 | Open |
| OI-14 | Malaysian public holidays are not in the threshold tables | Not applied | Grab | Threshold accuracy | Open |
| OI-15 | GrabMart follow up text: shared app text (TC-026, TC-040) or GMFR text (SRC-2) | Shared app text | Grab | TC-026, 040 | Open |
| OI-16 | GrabMart partial compensation sentence: three different wordings across sources | SRC-2 wording | Grab | TC-027, 029 | Open |
| OI-17 | Silence allowance: 7 seconds default, 20 seconds in walkthroughs, end after 3 | As stated | Grab | Voice tests | Open |
| OI-18 | Knowledge source for Tier 3: Cognigy Knowledge AI or CXone Expert (D-17) | Option A, Cognigy Knowledge AI | Grab, NiCE | search\_knowledge | Open |
| OI-19 | Confirm the actions.output payload reaches the AI Agent as the tool result when followed by Resolve Tool Action in the project's Cognigy version | actions.output; fallback is the Resolve Tool Action answer {{JSON.stringify(input.uc4Result)}} | Amansob | All returning tools, sprint 0 | Open |
| OI-20 | Grab sign off on the Tier 1 fixed text list (6.6 fixed, 7.5 steps and walkFixed, messages) | As drafted in Sections 6.6 and 7.5 | Grab | Fixed wording | Open |
| OI-21 | Grab approval of the Malay content pack, especially the Amansob draft lines (timeline wording, app and portal status routes, offers, language lines) | SRC-2 Malay where it exists, Amansob drafts elsewhere (6.7) | Grab | Malay conversations | Open |
| OI-22 | Malay and Manglish test cases, since SRC-1 is English only | Amansob translates the 45 scenarios, Grab approves | Grab, Amansob | Malay and Manglish testing | Open |
| OI-23 | Malay speech: vendor support for Malay with an English alternate, accuracy on Manglish, and the Malay TTS voice | NiCE tenant standard, verified in sprint 0 | NiCE, Amansob | Section 9.1 | Open |
