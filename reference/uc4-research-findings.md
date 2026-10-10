# UC4 current-package research findings

Research date: **2026-10-09**. The supplied handover is dated 2026-10-10; its date is preserved rather than treated as the research execution date. ([Handover], heading.)

## Executive assessment

**Preserve the thin-agent design, but do not treat the supplied package as accepted.** The archive contains the intended recent-order, first-follow-up, decline, and closing capabilities; however, its resolver returns `presentTimeline` while its If condition reads `presentWithinTimeline`. This is a concrete artifact-contract mismatch on the shared TC-001/TC-002 education path, not an observed Cognigy call failure. ([Archive], `nodeData/5183d8e98b3e8cad1357a98c`, `nodeData/7869c69224e9b13ed36138e3`; [QA], **Use Case 4 Test Cases (ENG)**!D2:E3.)

The safest immediate sequence is: resolve that contract/delivery-state discrepancy; verify imported dependencies and runtime model; obtain a decision on the V4-versus-QA first-follow-up conflict; prove the two conversations in text and voice; isolate GrabFood retrieval; then expand deterministic dates without adding the later journeys. These recommendations follow the identified discrepancies and the handover's deliberately small scope. ([Handover], §§2, 12, 15; [V4], ¶¶534–539, 580–590; [C-Agent], **Grounding Knowledge**, **Advanced**.)

### Evidence boundaries

- **Confirmed in archive:** serialized configuration, wording, graph links, resource inventory, and the inconsistent result/condition names. References to archive entries below mean entries inside `reference/existing.zip`, not separately committed source files. ([Archive], `index.json`, `chart/b1db677d163f9cb42c1597c6`, `nodeData/*`.)
- **Spec conflict or omission:** comparison with the prioritized documents; this does not establish what a model actually says. The handover prioritizes V4, then NiCE analysis, then QA, then the GrabFood/GrabMart FAQs. ([Handover], §2.)
- **Tenant/runtime-only:** import success and reference resolution; external Agent persona/Knowledge assignment; actual LLM/provider; ASR/TTS, recording, duplicate output, tool choice, and real hang-up. Those resources or execution evidence are not present in this archive. ([Archive], complete entry inventory; [C-Packages], **Restrictions**, **Package Import**; [C-Agent], **Parent Node**; [C-Hangup], **Description**.)

This is research, static inspection, and isolated local Code/condition evaluation only: no package edits, tenant import, live calls, or runtime acceptance were performed. Local DOCX/XLSX inspection used ZIP/XML extraction under `/tmp/opencode/uc4-research`. Paragraph citations count top-level `w:p` elements in the original `word/document.xml`, including empty paragraphs; table citations count top-level tables and their rows. Spreadsheet citations identify original sheets/cells.

Context7 resolved `/cognigy/documentation`; its results were followed to first-party product pages. The archive declares **2026.20.1**; the current release page identifies 2026.20.1 as released October 6, 2026, and current Agent/Packages pages are marked updated in 2026.20. These are current documentation, not a frozen guarantee of the target tenant's behavior. ([Archive], `index.json`; [C-Release], **2026.20.1**; [C-Agent], version badge; [C-Packages], version badge.)

### Executed local verification

Python inspected the ZIP/graph, and Node.js **v24.21.0** evaluated the archive's actual Code Nodes and condition in isolated `vm` contexts. The results below are local experiments, **not Cognigy execution or acceptance evidence**. ([Archive], complete inventory, chart, initializer, resolver, and If entries cited below.)

| Check | Observed result |
| --- | --- |
| Archive/graph integrity | ZIP CRC and all 30 JSON entries passed; 24 nodes matched 24 chart relations, with no dangling chart targets or cycles. Both Code Nodes' `code` and `transpiled` values match. This does not validate Cognigy's import schema. ([Archive], complete inventory and chart.) |
| Threshold arithmetic | **35/35** fixtures matched the package/V4 lookup: every weekday, with integer ages zero through that day's cutoff plus one, using fresh state. ([Archive], resolver; [V4], ¶¶349–358.) |
| Exported recent-order predicate | All **28/28** recent fixtures produced `presentTimeline=true`, but evaluating `input.uc4Result.presentWithinTimeline === true` returned false. Friday/yesterday also set `educateDelivered=true` despite that false predicate. Verify the selected If mode after import. ([Archive], resolver/If; [C-If], **Condition Field**, **Rule Editor**.) |
| Counterfactual minimal alignment | Replacing only the predicate's field name in memory with `presentTimeline` routed **35/35** fixtures as intended: 28 recent true, seven beyond false. The ZIP was not changed; tenant verification remains necessary. ([Archive], resolver/If.) |
| Malaysia date conversion | **14/14** initialization fixtures matched Node's `Intl.DateTimeFormat` date and weekday for `Asia/Kuala_Lumpur`: October 9–15, 2026, immediately before and at 16:00 UTC. The current UTC+8 conversion showed no date/offset failure in these checks. This does not address its Once-only snapshot. ([Archive], initializer and Once/chart.) |

## 1. Actual inventory and handover drift

| Item | Evidence and finding |
| --- | --- |
| Supplied artifact | `reference/existing.zip`, SHA-256 `a65b128132a56c74706f4a8c698e5a3e4778446595445ced9053c6dba5f6b012`. Its internal name is `Flow-UC4_GrabFood_Cancelled_Order_Compensation_Natural_KB_2026-10-09`; the handover names a differently named ZIP. Internal naming is consistent with the handover, but byte identity with that other file is not established. ([Archive], bytes and `index.json`; [Handover], §§1, 5.) |
| Resource inventory | 30 entries: `index.json`, one each of chart/Flow/Flow settings/Flow state/Locale, and **24 node resources**. Nodes include one Job, four Tool Actions, two Code Nodes, one If, one Resolve Tool Action, five Say Nodes, and one Voice Gateway Hang Up. Counts match the handover. ([Archive], complete entry inventory and `nodeData/*`; [Handover], §5.) |
| Flow/Locale | `UC4_GrabFood_Cancelled_Order_Compensation`; only `en-US` is supplied. The voice session node separately selects Microsoft STT `en-SG` and includes `semalam`/`kelmarin` hints; this is configuration, not proof of recognition quality. ([Archive], `flow/9dc96d579469f6c5c11e1357`, `locale/6ac8aceffc96b65c1a46a615`, `nodeData/0291dd21ef4b899a7529f6a9`.) |
| Missing deployment dependencies | No AI Agent, Knowledge Store/Source/chunk, LLM, connection, or Endpoint resource entries are supplied. The Job references Agent `4be64f69-32da-50bb-870f-3063ce8900e6`, selects `llmProviderReferenceId="default"`, and uses Agent Knowledge. `partial=false` and `missingTypes=[]` do not prove those external references resolve after import. ([Archive], inventory, `index.json`, `nodeData/0c5395041693f7f16ce0b238`.) |
| Routing discrepancy absent from handover | The resolver creates `input.uc4Result.presentTimeline`; the If's selected serialized condition is `input.uc4Result.presentWithinTimeline === true` (`type="condition"`). Its retained graphical rule also contains `1 eq 1`; inspect the active editor mode after import rather than assuming that retained rule fixes the contract. The condition expression is false for the result object the resolver creates. ([Archive], resolver and If entries above; [C-If], **Condition Field**, **Rule Editor**.) |
| “Delivered” is premature | The resolver sets `educateDelivered=true` before the If/Say executes. Follow-up and guidance-decline tools become eligible on this flag, even though the artifact has not yet emitted its approved education. V4 says to mark the order once the education is delivered. ([Archive], `nodeData/5183d8e98b3e8cad1357a98c`, `nodeData/2829140dcba75380654053f1`, `nodeData/149c4522c45ac41e2b19d2e2`; [V4], ¶537.) |
| Knowledge claim needs qualification | Empty `knowledgeSearchTags` confirms no Job-level tag filter. Both FAQs being in `[MY] Grab Merchant KB` is a **handover claim**, not an archive observation: this ZIP contains no Knowledge resources or Agent assignment. ([Archive], Job config/inventory; [Handover], §10.) |

The intended graph is initialization/greeting → Job → age resolver → If → approved education **or** facts returned through Resolve Tool Action; the other three tools lead to follow-up Say, decline Say, and closing Say → Hang Up. This is present structurally, but the age-to-Say predicate is inconsistent. ([Archive], `chart/b1db677d163f9cb42c1597c6` and the nodes referenced there.)

## 2. Current two behaviors: static coverage, not acceptance

| Behavior | Present | Blocker or remaining proof |
| --- | --- | --- |
| **TC-001:** yesterday → education → normal close | Job instructions map yesterday/semalam to `days_ago="1"`; resolver has the V4 threshold table; approved timeline/photo/anything-else Say exists; `end_call` leads to approved goodbye and Hang Up. ([Archive], Job, `nodeData/6615cf642771422f561ad414`, resolver, `nodeData/db5fa70940859820ffeeedb8`, `nodeData/bb259293c002be9372c40ab4`, `nodeData/4465b95f217b838898752947`, `nodeData/1631fcee5b8c41aa8fc690b7`; [QA], D2:E2.) | The shared If mismatch must be resolved before the intended approved response can be credited as covered. Correct tool selection, exactly one spoken response, closing consent interpretation, and actual call termination require tenant traces/audio. ([Archive], resolver/If; [C-Agent], **Tool Settings**, **Storage and Streaming Options**; [C-Hangup].) |
| **TC-002:** same education → non-receipt question → guidance declined → normal close | `further_inquiry` sends the fixed eligibility/request/guidance offer; `guidance_declined` sends only “Is there anything else I can help you with?”; prompt distinguishes a no to guidance from a no to anything else. ([Archive], `nodeData/2829140dcba75380654053f1`, `nodeData/0953992353fa81f79a0646e0`, `nodeData/149c4522c45ac41e2b19d2e2`, `nodeData/fb47e3e5ced17d99965a5444`, Job **CLOSING**; [QA], D3:E3.) | Same education blocker, plus the first-follow-up source conflict below. The tool remains available whenever `educateDelivered` is true; no first-follow-up repeat cap appears in its condition or the Job. V4 calls for a once-per-order first explanation, then steering back on repeat. ([Archive], tool condition and Job **FOLLOW-UP**; [V4], ¶580, ¶588.) |

**Prompt hygiene is good locally:** the Job name, description, and instructions contain none of the handover's prohibited `TC-001`, `TC-002`, `benchmark`, `test case`, `Band 1`, `scoped build`, or `expected tool path` strings. Do not copy this report's QA vocabulary into the Job; inspect the external persona/merged system prompt separately. ([Archive], Job config; [Handover], §§1, 4; [C-Agent], **Instructions and Context**, **Debug Settings**.)

## 3. Business/source adherence and conflicts

### Preserve these supported elements

- **Verified identity and known GrabFood:** the Job prohibits collecting Merchant identifiers/secrets or asking whether the order is GrabFood. This matches V4's IVR premise. It does not itself verify the caller or establish the actual upstream routing. ([Archive], Job **MERCHANT CONTEXT**; [V4], ¶4, ¶40, ¶42, ¶165.)
- **Voice persona and grounding:** short spoken replies, one question, answer direct questions first, tolerate ASR/Manglish, say compensation rather than refund, and keep internal machinery hidden are represented in the Job. ([Archive], Job **CONVERSATION**, **TERMINOLOGY**, **GROUNDING**, **SPEECH UNDERSTANDING**; [V4], ¶¶33–46, 60–63, 112–147.)
- **Recent-order wording:** the Say contains approval within one to two **business days**, then the **next payout cycle**, then V4's exact prepared-food photo reminder, then its exact anything-else question, with no unsolicited walkthrough. Its rephrase mode is `none`. ([Archive], `nodeData/db5fa70940859820ffeeedb8`; [V4], ¶¶534–539; [C-Say], **AI-Enhanced Output**.)
- **Normal closing:** the goodbye matches V4 Closing A, followed by a real Hang Up node, not just generated “goodbye.” Immediate hang-up is disabled. The Job requires the prior anything-else question and a clear finished reply. ([Archive], closing tool/Say/Hang Up entries; [V4], ¶¶322, 868–870; [C-Hangup], **Description**, **Enable Immediate Hangup**.)

### Do not silently resolve these source conflicts

1. **Timeline:** QA's **Scenario Flow**!B23 describes money credited to the bank within one to two working days; **Use Case 4 Test Cases (ENG)**!E2:E3 instead separates approval and payout. V4 explicitly separates one-to-two-business-day approval from the next payout cycle. Keep the V4/package wording; do not “fix” it to the older bank-credit script. QA's E1 explicitly allows nonverbatim scripts with the same objective. ([QA], those cells; [V4], ¶534, ¶590; [Handover], §2; [Archive], education Say.)
2. **First follow-up:** the package's fixed app-specific response closely matches QA E3 and the handover. V4 ¶588, however, restricts the Request for Compensation section sentence to an **app Merchant**, distinguishes portal handling, and says that after telling them to submit a request the offered help should be request-submission guidance. The fixed Say always refers to “your GrabMerchant app” and offers the cancelled-order walkthrough without knowing the platform. V4 ¶537 also has a general recent-follow-up cancelled-order offer, while ¶588 expressly qualifies the request case. **Ask the owner to approve the minimal current-follow-up interpretation/wording against V4; matching QA alone is insufficient.** ([Archive], `nodeData/0953992353fa81f79a0646e0`; [QA], E3; [Handover], §7; [V4], ¶537, ¶588.)
3. **Photo reminder:** V4 ¶582 contains a general statement that outcome messages never volunteer a photo, conflicting with ¶534's explicit “EVERY within-threshold delivery” rule. Preserve the specific recent-order reminder required by ¶534 and QA E2/E3; record the internal document conflict rather than deleting the reminder. ([V4], ¶534, ¶582; [QA], E2:E3; [Handover], §8.)

### Boundaries the narrow build does not prove

- The four tools do not implement accepted-guidance walkthroughs, beyond-threshold journeys, safety transfer, human transfer, or the other-brand offer/transfer path. These are declared deferred in the handover, but V4 safety and wrong-brand rules apply at every turn. **Recommendation:** keep this artifact to controlled validation until those hard constraints are demonstrably handled here or upstream; never promise a transfer that no configured capability performs. ([Archive], four Tool Action descriptions/graph; [Handover], §12; [V4], ¶¶18–31.)
- The current follow-up instruction answers arrival/evidence questions, but does not generally require the V4 guidance offer after every substantive first follow-up or enforce the repeat cap. Test both before adding persistent flags; only add a narrow guard if the required behavior cannot be made reliable from the conversation transcript. ([Archive], Job **FOLLOW-UP**; [V4], ¶537, ¶580, ¶588; [Handover], §4.)
- V4 requires a clear negative eligibility answer when cancellation happened **before preparation**, special handling for future dates, and its exact non-disclosing line if pressed about internal date calculation. These explicit behaviors are not in the supplied Job/tool descriptions; external Agent instructions may supply them, which cannot be audited here. ([Archive], Job/tool configs; [V4], ¶466, ¶468, ¶482.)
- Only `en-US` is packaged, but the external Agent's automatic language-detection configuration is unavailable. Verify English-only behavior for Malay words/date/decline expressions; V4's Malay-language-request and transfer journey is separate from understanding those words. ([Archive], Locale and external Agent reference; [V4], ¶¶287–303; [C-Manage], **Speaking Style → Language Configuration**.)

## 4. Dates: retain the business rule, expand the deterministic capability safely

The current code compares integer age against this **inclusive calendar-day lookup**, keyed by today's weekday. It matches V4; it is not a generic business-day counter and must not subtract weekends again. ([Archive], resolver `thresholdDays` and `ageDays <= ...`; [V4], ¶¶346–360.)

| Today | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Recent when age ≤ | 4 | 4 | 2 | 2 | 2 | 3 | 4 |

Current limitations and safe next research/engineering decisions:

- **Input contract:** only one graphical-compatible String, `days_ago`, is supplied. The LLM maps obvious relative wording; Code computes the threshold. Weekdays/calendar dates have no structured input contract. Extend this same capability with simple parameters describing the date actually heard; do not ask the LLM to perform calendar subtraction or invent a numeric age for ambiguity. ([Archive], `nodeData/6615cf642771422f561ad414`, Job **CANCELLATION DATE**; [C-Agent], **Tool → Parameters**; [V4], ¶¶359, 362–377.)
- **Defensive validation:** isolated execution accepted empty/whitespace strings and `null` as age zero, and `"1.0"`, `"1e0"`, `"+1"`, and `"0x1"` as age one because the resolver uses `Number(...)`. Missing arguments, negative/fractional values, and `"yesterday"` were rejected. The tool's String schema can constrain some actual calls, but blank strings still meet its type; validate whole-number text in computational Code rather than relying on the description. After a valid call, an invalid call returns the prior age/threshold with `success=false` and `dateRequired=true`; consumers must respect those status fields. These are directly supplied sandbox arguments, not observed model tool calls. ([Archive], resolver and age tool schema.)
- **Bare weekdays:** use V4's dedicated weekday table. Today's named weekday means the prior week's occurrence, not today; “today”/“this morning” are different. Explicit earlier-week qualifications use the day-count rule. General task prose also says to count weekdays, but the dedicated rule and ¶532 specifically prohibit that generative shortcut. Encode/test the dedicated table rather than carrying both contradictory instructions into prompts. ([V4], ¶¶362–377, 482, 530–532.)
- **Calendar dates:** deterministically compare a validated past date with the agreed Malaysia-local current date, then apply the lookup. The spec gives ordinal/date examples but does not fully define missing-year or impossible-date interpretation; settle those policies before guessing. Future dates have their own non-compensation/check-date response. ([V4], ¶377, ¶468, ¶486; [Handover], §§9, 12.)
- **Ambiguity:** hedged numeric counts are answers; “a few days”/“a couple of days” are not automatically two. One clarification is allowed after a vague answer; the date question is capped at two assistant turns, then the beyond path is chosen silently. The current Job has only generic clarification instructions, not these date-specific limits. Add only the minimum tracking necessary to enforce that cap, not a canvas conversation state machine. ([V4], ¶¶336–344, 479–482, 503–519; [Archive], Job **SPEECH UNDERSTANDING**, **CANCELLATION DATE**; [Handover], §§3–4, 13.)
- **Corrections/delivery state:** numeric calls can overwrite `ageDays`/`threshold`, but `educateDelivered` remains a single session-level Boolean; full correction and separate-order semantics are not established. V4 requires silent recalculation and per-order delivery caps. Prove correction handling before claiming expanded date support; do not introduce Merchant-ID collection to track it. ([Archive], initialization/resolver; [V4], ¶382, ¶482, ¶537; [Handover], §12.)
- **Time source:** initialization derives a date with `Date.now()+8h` and stores it once. A call crossing local midnight continues using its opening weekday unless something else refreshes it. Cognigy documents `input.currentTime` as the input-reception timestamp, including ISO date and offset; those docs do not establish that its day/weekday is already Malaysia-local. Prefer a testable, explicit Malaysia-date boundary recomputed for resolution; verify the actual offset/zone before replacing the existing conversion. ([Archive], `nodeData/b980ad6a932aa23366c0ffa7`, resolver; [C-Input], **currentTime Object**; [V4], ¶16, ¶314, ¶347.)

## 5. Official-supported architecture and product limitations

### Agent, Job, tools, and approved output

- **Persona is how; Job is what:** Cognigy explicitly distinguishes reusable/task-agnostic persona from Job logic at an AI Agent Node. Job instructions supplement Agent instructions. Preserve one Job for this responsibility; later consolidate shared voice/persona rules only after inspecting the external Agent, rather than deleting the currently visible safeguards blindly. ([C-Persona], **Concepts**, **Key Principles**; [C-Agent], **Parent Node → AI Agent**; [Archive], Job **ROLE**.)
- **Regular Tool Actions are capabilities, not one tool per Wiz task:** Cognigy executes the branch below the selected tool; descriptions guide selection, arguments are in `input.aiAgent.toolArgs`, and Condition controls availability. Graphical String/Number/Boolean/Array/Object parameters are documented; String enums are supported graphically. The archive's simple `days_ago` JSON shape mirrors Cognigy's official simple-schema example. Serialization as JSON does **not** prove it was authored in the custom editor or that a warning will appear; verify graphical round-trip in the target version. ([C-Agent], **Child Nodes → Tool**, **Examples → Tool**; [Archive], age tool; [NiCE], ¶¶5–9, 12–24.)
- **Execution and resolution are different:** a selected regular tool runs its Flow branch. Resolve Tool Action supplies an answer to the Agent for further processing; it is not the Merchant-facing Say. Cognigy's documented exit-tool example deliberately ends in Say **without** Resolve so execution does not return to the Agent on that turn. Thus the direct education/follow-up/decline Says and closing Say → Hang Up are a supported pattern; do not add Resolve indiscriminately after them. ([C-Agent], **Child Nodes → Tool**, **Avoiding Infinite Loops when Tool Choice is Required → Option 2**; [C-Resolve], **Description**; [Archive], chart.)
- **Duplicate-generation proof is still needed:** the Job streams generated output; the direct Say branches contain no Resolve, but actual preambles, streaming/tool-call behavior, transcript continuity on the next input, and voice playback must be checked with the chosen runtime. Prompt “do not duplicate” instructions are not acceptance evidence. Keep approved Says unrephrased and visible in the transcript so the following no is interpretable. ([Archive], Job streaming settings, Say `preventTranscript=false`/rephrase `none`, chart; [C-Agent], **Storage and Streaming Options**, **Debug Settings**; [C-Say], **Exclude from Transcript**, **AI-Enhanced Output**.)
- **Hang Up is the side effect:** Voice Gateway's node instructs the gateway to end the call; its immediate option bypasses queued operations. The archive disables that option, which is consistent with its preceding approved Say, but completed playback and call termination still require real voice verification. ([C-Hangup]; [Archive], closing Say/Hang Up/graph; [V4], ¶322, ¶870.)

### Context and initialization

Context persists across a session. Native Add To Context supports nested keys and Simple assignment; objects require preservation of type. Default Context initializes the **starting** Flow's session; switching to another Flow does not automatically apply that Flow's defaults unless the documented absorption behavior is used. Therefore the initialization Code can potentially be simplified for static defaults, but removing it solely because defaults were placed on a UC4 Flow reached from IVR may break initialization. Keep real date computation deterministic and avoid overwriting upstream verification/context. ([C-Context], **Default Context**; [C-Add], **Parameters**, **Storing an Object**; [Archive], Flow `context={}`, initialization; [Handover], §§4, 9.)

### Knowledge isolation and import

The archive selects `onDemand`, Agent Knowledge true, Job Knowledge false, Top K three, empty tags. Cognigy calls the corresponding user-facing mode **When Required**, where the Agent decides when to query; Agent Knowledge uses the Store assigned to the Agent, while Job Knowledge selects a Job-specific Store. Source tags filter retrieval, with AND requiring **all tags on a Source**, not one tag on each of several Sources. ([Archive], Job Knowledge config; [C-Agent], **Grounding Knowledge**.)

**Recommendation:** choose either a verified `grabfood` Source tag plus that Job filter, or a GrabFood-only Store explicitly assigned to this Job/Agent. Do not rely solely on “ignore GrabMart” in the prompt. A GrabFood tag isolates the brand, **not UC4 topics**: the supplied GrabFood document includes menu management, consumer refunds, and a large-order weekly-update answer. Its content is not an alternate compensation-window spec. The GrabMart document begins with catalogue/inventory content. Keep topic relevance and V4-approved policy precedence even after source isolation. ([C-Tags], **Working with Source Tags**; [C-Agent], **Grounding Knowledge**; [Food FAQ], ¶46, ¶¶154–155, ¶¶318–324; [Mart FAQ], table 2 row 1, ¶¶3–16; [V4], ¶¶308, 432–438; [Handover], §§2, 10, 13.)

Cognigy Packages can carry Agents, Stores, and LLMs, but this one does not. Official docs warn that newer-to-older imports can error, Extensions must be installed, Locales must be mapped, and imported Knowledge Stores require matching embedding models or recreated Sources. They also advise against importing Knowledge resources into production because knowledge may be temporarily unavailable. Verify those dependencies in an isolated target Project, including `[MY] Grab Merchant KB` assignment and chunk/source tags; do not infer setup from the package name or `partial=false`. ([C-Packages], **Restrictions**, **Package Import**, **Map Locales**, embedding-model footnote; [Archive], inventory; [Handover], §10.)

### Actual runtime LLM

`llmProviderReferenceId="default"` means the **Project's Generative AI Settings** model, not the model used by the coding/research assistant. No particular OpenAI model is forced here; `customModelOptions={}`. Verify the resolved provider/model/connection and AI Agent feature support in the tenant. Cognigy supports a same-provider model override in Custom Options, but an assumed model identifier is not a deployment guarantee. ([Archive], Job config; [C-Agent], **Advanced → LLM**, **Custom Options → Forcing Model Versions**; [C-Models], introduction; [Handover], §11.)

There is a concrete **conditional compatibility risk**: the Job has `maxTokens=350`, `temperature=0.3`, and `advancedIgnoreDeprecatedParameters=false`. Current docs say the legacy completion-token/temperature fields are deprecated from 2026.18 and may fail for models that do not support them. Inspect the actual default model before changing these settings; do not presume an error or blindly select a newer model. Also verify the eight-second LLM timeout and the silent `errorHandling="continue"`/empty-error-message path under failure. ([Archive], Job config; [C-Agent], deprecation warning, **Advanced**, **Error Handling**.)

## 6. Prioritized recommendations

1. **P0 — Current-path integrity:** align the resolver/If contract in a subsequent authorized change; mark education only on the approved-output path; verify it remains retriable when delivery has not occurred. Keep the one deterministic If, four narrow capabilities, and approved Say texts. ([Archive], resolver/If/tool gates; [V4], ¶537; [Handover], §§3–5.)
2. **P0 — Import/runtime prerequisites:** resolve Agent/LLM/Knowledge/Locale/Voice Gateway dependencies in a test Project; confirm the actual model accepts the selected fields and inspect the merged prompt. Do not run acceptance against an assumed inherited configuration. ([Archive], inventory/Job; [C-Packages]; [C-Agent], **Advanced**, **Debug Settings**.)
3. **P0 — Source approval and two-behavior proof:** resolve the app-specific first-follow-up ambiguity with the owner and test close-versus-guidance-decline, repeats, and one output per turn. Do not offer unsupported walkthroughs to unattended callers. ([V4], ¶537, ¶580, ¶588, ¶868; [QA], D2:E3; [Handover], §§12, 14–15.)
4. **P1 — Retrieval boundary:** add verified GrabFood source isolation or a dedicated Store; test actual returned source names/chunks and a no-answer case. Keep RAG supplemental; do not place all FAQ text or QA scripts into the Job. ([C-Agent], **Grounding Knowledge**, **Debug Settings**; [C-Tags]; [V4], ¶308, ¶438; [Handover], §§4, 10, 13.)
5. **P1 — Dates next, not all journeys:** expand the deterministic date capability and minimum ambiguity/correction tracking; cover weekday/date/midnight boundaries before extending status/form/guidance journeys. Prefer native Context for straightforward state writes, but do not double the canvas to eliminate useful computational Code. ([V4], ¶¶336–377, 479–482; [C-Context]; [C-Add]; [Handover], §§4, 12–15.)

No custom `next_action/say/guide/verbatim/step_id` protocol or giant conversation state machine is needed for these recommendations; both the handover and NiCE mapping favor a conversational Agent with deterministic capabilities and separate approved output/Knowledge. ([Handover], §§3, 13; [NiCE], ¶¶5–9, 12–24.)

## 7. Small executable acceptance checklist

### Read-only archive-contract check

Run from the repo root. It checks the resolver's result fields against the If references and should fail on the inspected archive. It is **not** a Cognigy import/runtime test. ([Archive], resolver/If entries.)

```bash
python - <<'PY'
import json, re, zipfile
with zipfile.ZipFile('reference/existing.zip') as z:
    def config(resource):
        return json.loads(z.read(resource))['localizedData'][0]['config']
    resolver = config('nodeData/5183d8e98b3e8cad1357a98c')['code']
    predicate = config('nodeData/7869c69224e9b13ed36138e3')['condition']['condition']
    result = resolver.split('input.uc4Result = {', 1)[1].split('};', 1)[0]
    keys = set(re.findall(r'^\s+(\w+)(?::|,?$)', result, re.M))
    used = set(re.findall(r'input\.uc4Result\.(\w+)', predicate))
    print('Result fields:', sorted(keys))
    print('If references:', sorted(used))
    assert used <= keys, f'If reads absent fields: {sorted(used - keys)}'
PY
```

### Tenant scripts and acceptance assertions

Use new sessions, the actual configured model, debug tool/Knowledge traces, and recorded output/audio. These scripts are QA-only. Cognigy documents Job/tool/Knowledge debugging; V4/QA define the expected conversation objectives. ([C-Agent], **Debug Settings**; [V4], ¶¶534–590, 868–870; [QA], D2:E3.)

- [ ] **TC-001:** “My order got cancelled yesterday after I prepared the food. When will I receive compensation?” → `resolve_order_age("1")` → one approved timeline/photo/anything-else response; “No, that's all” → one approved closing → actual Hang Up. Repeat with “semalam lah.” No identifier/brand re-check, internal threshold, generated duplicate, or unsolicited guidance. ([Handover], §14; [V4], ¶40, ¶165, ¶534, ¶535, ¶868.)
- [ ] **TC-002:** same first turn → “What if I still don't receive it?” → owner-approved first follow-up and one guidance offer; “No, I don't need guidance” / “tak payah” → only anything-else, **not** Hang Up; “No, that's all” → approved closing and actual Hang Up. Repeat the factual follow-up and verify the first-explanation cap. ([QA], E3; [V4], ¶331, ¶580, ¶588, ¶868.)
- [ ] **Retrieval:** ask a relevant fact the Job does not hold, inspect every returned Source, and verify GrabFood-only retrieval. Test missing/irrelevant information, consumer-refund and GrabMart-topic contamination, and acknowledgement-only input; no guessed policy, wrong-brand window, or FAQ narration. Use a fixture whose factual answer can be traced to an approved original paragraph. ([V4], ¶¶34–37, 308, 436–438; [C-Agent], **Grounding Knowledge**, **Log Knowledge Results**; [Food FAQ], ¶¶154–155, 318–324.)
- [ ] **Deterministic boundaries:** for each weekday, test age zero, that row's boundary, and boundary plus one; invalid/blank/future input must not invent an age. When date expansion is authorized, add today's named weekday versus “today,” each bare weekday/Malay alias, earlier-week qualification, calendar month/year/leap boundaries, vague-date cap, legitimate corrections, and Malaysia-midnight crossings. ([V4], ¶¶349–377, 468, 479–482; [Archive], initialization/resolver.)
- [ ] **Lifecycle/failure:** ensure greeting is emitted once, approved education is marked only on its output path, next-turn transcript includes the direct Says, and provider/timeout errors do not leave unexplained silence. Test audio completion before hang-up, barge-in, and no-input behavior with real voice; the serialized settings alone do not establish those results. ([Archive], Once/chart, Job error/streaming settings, Say transcript flags, Session Config/Hang Up; [C-Agent], **Error Handling**; [C-Say], **Exclude from Transcript**; [C-Hangup].)

### Questions requiring the owner/tenant

1. Is this SHA-identified `existing.zip` the intended current deliverable, and what exact Cognigy/Voice Gateway versions will import it? ([Archive], `index.json`; [Handover], §§1, 5; [C-Packages], **Restrictions**.)
2. Does the referenced Agent resolve, what global instructions/language/memory/voice settings does it add, and is the correct Knowledge Store actually assigned? ([Archive], Job reference/inherited settings; [C-Manage]; [C-Agent], **Parent Node**.)
3. Which first-follow-up wording/offer is approved where V4 and QA differ, including a Merchant who already said they use the portal? ([V4], ¶537, ¶588; [QA], E3; [Handover], §7.)
4. What is the actual Project-default provider/model, are legacy sampling/token fields supported, and what failure response is required? ([Archive], Job LLM/error config; [C-Agent], deprecation warning, **Advanced**, **Error Handling**.)
5. What date/offset arrives in `input.currentTime`, which time boundary is authoritative for Malaysia, and how should missing-year/impossible dates be clarified? ([C-Input], **currentTime Object**; [V4], ¶16, ¶314, ¶377; [Archive], initializer.)
6. What upstream handling really provides safety/other-brand/human transfer and unsupported-guidance boundaries, and is call recording actually enabled for the greeting's disclosure? ([V4], ¶¶18–31; [Archive], greeting and complete graph; [QA], E2:E3; [Handover], §12.)

## Sources

All local links below are preexisting originals in `reference/`; archive citations specify resource entries and DOCX/XLSX citations specify locations above. Product links are first-party current Cognigy documentation consulted for this report.

[Archive]: existing.zip
[Handover]: handover.md
[V4]: <Grab Merchants Voicebot Use Case 4.docx>
[NiCE]: <NiCE - Analysis of Documents from Grab.docx>
[QA]: <Grab Pilot Test Cases - 30 Sep 2026.xlsx>
[Food FAQ]: GrabMY_FAQ_GrabFood.docx
[Mart FAQ]: GrabMY_FAQ_GrabMart.docx
[C-Release]: https://docs.cognigy.com/release-notes/2026.20.md
[C-Persona]: https://docs.cognigy.com/ai/agents/develop/persona.md
[C-Manage]: https://docs.cognigy.com/ai/agents/develop/manage-ai-agents.md
[C-Agent]: https://docs.cognigy.com/ai/agents/develop/node-reference/ai/ai-agent.md
[C-Resolve]: https://docs.cognigy.com/ai/agents/develop/node-reference/ai/resolve-tool-action.md
[C-If]: https://docs.cognigy.com/ai/agents/develop/node-reference/logic/if.md
[C-Say]: https://docs.cognigy.com/ai/agents/develop/node-reference/basic/say.md
[C-Hangup]: https://docs.cognigy.com/ai/agents/develop/node-reference/voice/voice-gateway/hangup.md
[C-Context]: https://docs.cognigy.com/ai/agents/develop/ai-agent-memory/context.md
[C-Input]: https://docs.cognigy.com/ai/agents/develop/ai-agent-memory/input.md
[C-Add]: https://docs.cognigy.com/ai/agents/develop/node-reference/logic/add-to-context.md
[C-Tags]: https://docs.cognigy.com/ai/agents/develop/knowledge-ai/knowledge-source/knowledge-source-tags.md
[C-Packages]: https://docs.cognigy.com/ai/platform-features/packages.md
[C-Models]: https://docs.cognigy.com/ai/agents/develop/gen-ai-and-llms/model-support-by-feature.md
