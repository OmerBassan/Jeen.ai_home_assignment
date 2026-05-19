# Provider Decisions — Dana Voice Agent (El Al Outbound)

## Context & Decision Framework

Dana operates in one of the harshest environments a voice agent can face: a busy international airport terminal. The three criteria that drive every decision below:

1. **Hebrew accuracy** — Hebrew is a morphologically complex language underrepresented in most training datasets. Every model choice below is first evaluated on whether it can handle conversational Israeli Hebrew reliably — in clean conditions and under noise. A misrecognition at any layer cascades: wrong transcript → wrong LLM interpretation → wrong function call → bad data on the ground crew dashboard.

2. **Noise tolerance** — Ben Gurion Terminal 3 has constant PA announcements, jet noise, crowds, and reverb. An STT model that struggles under noise doesn't just perform worse — it actively harms the passenger experience by forcing retries in a time-critical situation.

3. **Reliability under pressure** — Dana's job ends with a function call that writes status to the ground crew dashboard. One wrong status (`resolved` instead of `escalated`, for example) means ground crew acts on bad data. This is not a chatbot — it's an operational system.

Every tradeoff below is evaluated against these three constraints first, with cost and latency as secondary factors.

---

## STT — Speech-to-Text

### Candidates Evaluated

| Parameter | **Deepgram Nova-3** | Whisper v3 |
|---|---|---|
| Hebrew accuracy (clean audio) | Very good | Excellent |
| Hebrew accuracy (noisy audio) | Good | Excellent |
| Noise resilience | Good | Excellent |
| Latency | ~100ms (streaming) | ~300ms (batch) |
| Streaming support | Yes | No |
| Price (per hour) | ~$0.059 | ~$0.006 |
| Open source / hosted | Hosted only | Both |

### Deep Dive

**Hebrew accuracy** is the primary criterion, and it is where this decision starts. Both models clear the production bar for conversational airport Hebrew — but differently. Whisper v3's 680,000-hour multilingual training includes strong Hebrew representation and gives it a measurable edge in worst-case noisy conditions. Deepgram Nova-3 has invested heavily in Hebrew since Nova-2 and performs at a very good level for telephony-grade audio. For the structured, telephony-filtered input this pipeline receives, both produce transcripts accurate enough to drive reliable downstream decisions. Hebrew accuracy is satisfied by both models; the question becomes which performs better within those constraints.

**When Hebrew accuracy is satisfied, latency becomes the tiebreaker for UX.** Deepgram's streaming architecture processes audio while the passenger is still speaking, delivering a first transcript in ~100ms. Whisper requires the full audio clip before batch processing begins — adding ~300ms per turn. In a time-critical call where a passenger needs to start moving, that latency compounds across every exchange and is perceptible. The passenger experience is meaningfully better with a faster-responding agent, and that is why Deepgram is the primary choice.

**Noise resilience**: Deepgram's streaming model is tuned for real-world telephony noise. Whisper's accuracy advantage under extreme unstructured noise (open crowds, reverb) is precisely why it is the fallback — if Deepgram degrades in the worst airport conditions, Whisper's batch pass over the full audio recovers it.

**Price**: Both cost approximately $0.001 per average call. Not a factor.

### Decision: Deepgram Nova-3
**Fallback: Whisper v3** — if Deepgram has an outage or quality degrades under extreme noise, Whisper's superior Hebrew accuracy in batch mode makes it the right emergency fallback.

---

## LLM — Language Model

### Candidates Evaluated

| Parameter | GPT-4.1 | GPT-4o |
|---|---|---|
| Hebrew quality | Excellent | Excellent |
| Function calling accuracy | Excellent, improved | Excellent, proven |
| Latency (TTFT) | ~300-400ms | ~400-500ms |
| Instruction following | Excellent | Excellent |
| Price (input/1M tokens) | $2.00 | $2.50 |
| Price (output/1M tokens) | $8.00 | $10.00 |
| Production maturity | High | Very high |

### Deep Dive

**Hebrew language understanding** is the primary filter. The gap between models surfaces in edge cases — slang, mid-sentence code-switching (passengers routinely mix Hebrew and English), and inferring intent from short emotional phrases like "אני בדרך, רגע" vs. "אני לא בא". Both GPT-4.1 and GPT-4o handle informal Israeli Hebrew at a high level, including colloquial and time-pressured speech. This is the baseline both models must clear, and both do.

**Function calling** is the decisive differentiator within that baseline. Dana must call `update_dashboard`, `end_phone_call`, or `transfer_to_human` reliably at the right moment, with the right arguments, based on complex conversational context. GPT-4.1 (released April 2025) improves specifically on instruction following and structured output reliability over GPT-4o — making it the stronger choice for an agent whose correctness is operationally critical. One wrong status written to the dashboard has real consequences; that risk profile favors the model with the stronger function calling track record.

**GPT-4.1 vs GPT-4o**: GPT-4.1 is both cheaper ($2.00 vs $2.50 input, $8.00 vs $10.00 output) and faster (~300-400ms vs ~400-500ms TTFT), with stronger instruction following. There is no reason to prefer GPT-4o over GPT-4.1 — it is the clear upgrade. GPT-4o is the fallback precisely because it is the previous battle-tested flagship with proven production reliability, not a step down in capability.

### Decision: GPT-4.1

**Fallback: GPT-4o** — the previous proven flagship. Same function calling reliability, battle-tested in production for over a year. If GPT-4.1 is unavailable or unsupported, GPT-4o is the safest net — not GPT-4.1-mini, which is too junior for edge case function calling to be a first fallback.

---

## TTS — Text-to-Speech

### Candidates Evaluated — Provider

| Parameter | ElevenLabs | Azure TTS (he-IL) |
|---|---|---|
| Hebrew voice quality | Excellent | Good |
| Prosody & naturalness | Best in class | Natural, slightly robotic |
| Emotional range | High | Moderate |
| Latency (first chunk) | ~250ms (v3) | ~100-200ms |
| Streaming support | Yes | Yes |
| Price (per 1M chars) | ~$11 | ~$4 |
| Native Hebrew voices | Yes (multilingual) | Yes (he-IL-AvriNeural, he-IL-HilaNeural) |

### Candidates Evaluated — ElevenLabs Model

| Model | Hebrew Stability | First-chunk Latency | Best For |
|---|---|---|---|
| **v3** | Excellent | ~250ms | Real-time voice agents — best stability/latency balance |
| Multilingual v2 | Good | ~400ms+ | Studio, pre-recorded content |

### Deep Dive

**Hebrew voice quality** is the primary criterion, and it is where ElevenLabs separates itself. A voice that sounds unnatural in Hebrew immediately signals "robot" to a native speaker — wrong stress patterns, flat intonation, mispronounced common words. That signal undermines Dana's warm, urgent persona at the worst possible moment. ElevenLabs produces the most natural Hebrew prosody available: stress patterns, intonation, and pacing match natural Israeli speech in a way that is audible within the first sentence.

**Azure TTS** with `he-IL-HilaNeural` is the comparison point and a genuine alternative — natural enough for production, backed by reliable infrastructure, and significantly cheaper. It lacks ElevenLabs' warmth and emotional nuance but produces Hebrew that does not sound robotic.

**Prosody and emotional range** matter specifically because of Dana's tone requirement: calm, warm, and urgent simultaneously. A flat voice does the opposite — it increases passenger anxiety at an already stressful moment. ElevenLabs handles this register consistently; Azure approximates it.

**ElevenLabs model selection**: v3 vs Multilingual v2 was the real choice. Multilingual v2 is technically capable, but in practice it produces inconsistent Hebrew output — occasional mispronunciations, stress-pattern drift across sentences, and less reliable emotional tone. v3, released in 2025, is meaningfully more stable in Hebrew: the prosody holds across the full call rather than degrading mid-conversation. Multilingual v2's ~400ms+ first-chunk latency also makes it unsuitable for real-time phone conversation, but stability was the primary reason it was ruled out — a faster but unreliable voice would still undermine Dana's persona.

**Price**: For short calls (~300 words avg), the absolute cost difference between ElevenLabs and Azure is ~$0.001 per call — negligible at current volumes.

### Decision: ElevenLabs v3 (primary) / Azure TTS he-IL-HilaNeural (fallback)
ElevenLabs v3 for the best available Hebrew prosody and emotional range at real-time latency. Azure `he-IL-HilaNeural` as provider fallback if ElevenLabs is unavailable.

---

## Pipeline vs. Realtime Architecture

### What Was Considered

GPT-4o Realtime API and Gemini Native Audio were evaluated. Both eliminate the STT → LLM → TTS pipeline in favor of a single end-to-end audio model. The theoretical advantages are significant: lower total latency, no transcription errors propagating to the LLM, more natural turn-taking.

### Why Pipeline Wins — For Now

**Hebrew under noise**: Realtime audio models are trained on broad multilingual data but have not been specifically optimized for Hebrew accuracy in noisy environments the way Whisper v3 has. There is no published benchmark for Hebrew ASR quality in realtime models under airport-level noise.

**Function calling maturity**: Realtime models handle function calling differently — it is embedded in the audio stream rather than structured JSON. The reliability and predictability of function calls in production edge cases has not been sufficiently documented for a use case where wrong output has direct operational consequences.

**Observability**: With a pipeline, each step (transcript, LLM response, TTS) can be logged and audited separately. This is critical for debugging why a specific call went wrong. Realtime models produce a single opaque audio-in / audio-out interaction that is harder to inspect.

### When to Switch

Realtime models are the right long-term direction. The switch becomes justified when:
- Hebrew accuracy benchmarks for realtime models under noise are published and competitive with Whisper v3
- Function calling in realtime models reaches the same reliability as GPT-4o structured outputs
- Vapi (or equivalent) provides native realtime model support with the same webhook/dashboard integration

---

## Final Decision Summary

| Layer | Decision | Fallback | Key Reason |
|---|---|---|---|
| STT | **Deepgram Nova-3** | Whisper v3 | Production-ready Hebrew accuracy for telephony; ~100ms streaming latency breaks the tie |
| LLM | **GPT-4.1** | GPT-4o | Excellent Hebrew + strongest function calling reliability; cheaper and faster than GPT-4o |
| TTS | **ElevenLabs v3** | Azure TTS he-IL-HilaNeural | Best Hebrew prosody and emotional range available; audibly natural from the first sentence |
| Architecture | **Pipeline** | — | Reliability, observability, proven Hebrew STT |
