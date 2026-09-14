LifeOS Local Agent — migration complete 2026-09-09
====================================================
- Local Converso workflow: id=1 "LifeOS Voice Agent (Local)", published v2 (definition = copy of cloud wf 10786)
- CORRECTED 2026-09-11: published v5 (09-10 07:24) switched mode BYOK -> DOGRAH. Current: mode=dograh, api_key=mps_sk_yAlk...BLZWtJ, voice=dg_voice_b431dce61697bc3ba98d (Kiara, Dograh default voice), LLM = Dograh default (routed via services.dograh.com/api/v1/llm). NO glm-5.3-flash / Deepgram / ElevenLabs config is active anymore. The BYOK pipeline (glm-5.3-flash @ ollama.com/v1 + ElevenLabs Roger + Deepgram nova-3) lives only in archived v4.
- Embed token: emb_mxy89WFE8Dgj2CBRUEFm... (full: migration/local_embed_token.txt), resolves via https://converso.work/api/v1/public/embed/config/<token>
- Tools: 10 http_api tools inserted into local DB with EXACT cloud tool_uuids (org 1, user 1); created_at/updated_at must be non-NULL (fixed via UPDATE now())
- Dashboard: /var/www/lifeos/index.html (synced to /root/lifeos-prototype/index.html) — teal "L" button calls startLocalVoice() → injects dograh-widget.js with local token + apiEndpoint=converso.work; cloud green button untouched
- Verified end-to-end (text-chat): glm-5.3-flash tool calls → read_table/get_summary hit https://lifeos.converso.work/api/voice/* → seeded data returned (5 bills ₹23,206, 2 health profiles)
- Costs: LLM → Ollama Cloud plan; STT → Deepgram free credits; TTS → ElevenLabs free 10k chars/mo; platform = local (no Dograh credits for the LOCAL agent; cloud agent 10786 continues on Dograh billing)
- Known: running converso-api-1 build predates /text-chat/sessions/{id}/end route (404) — test sessions 3/4 remain "running"; harmless
- Restart caution: after DB restore/wipe, tools table must be re-seeded (see /tmp/tools_insert.sql pattern; JSON at /tmp/tools_rows.json)
