# YONISO-MANASIKARA v3.0.0

> **โยนิโสมนสิการ** — recursive root questioning discipline.
> Applied on every fix, plan, review, or architectural decision in Claude Code.

> หลักการตั้งคำถามย้อนกลับ — discipline สำหรับ Claude Code agent ทุกครั้งที่แก้บั๊ก เขียนแผน หรือ review โค้ด

---

## 📜 Origin / ที่มา

YONISO was born from **R-CORE-007** in the CLAUDE.md of LMA (Local Multi-Agent OS). Agents kept patching surface-level symptoms without asking *why the bug existed in the first place.*

YONISO เกิดจาก agent ชอบแก้บั๊กแบบ surface-level โดยไม่ถามว่า *ทำไมบั๊กถึงเกิดตั้งแต่แรก*

**Timeline:**

| Date / วันที่ | Event / เหตุการณ์ |
|---------------|---------------------|
| 02 Jun 2026 | ADR-022 APPROVED (Triad 2-of-3: benz Strategic YES + Quality concur) — 9arm enforcement activated |
| 02 Jun 2026 | First yoniso commit — closed root-causes from scheduler audit (`bb56e82`) |
| 02 Jun 2026 | Yoniso test suite + 7 agent manifests (`5062e84`) |
| 03 Jun 2026 | 11 code-review-max findings with real YONISO 2-layer RCA (`4e197f1`) |
| 05 Jun 2026 | **v3.0.0** — signal-based auto-classification + 4-point layer quality heuristics + feedback loop (`8a302cc`) |

**DNA:** YONISO is the only **LMA-native** skill among the 5 in the 9ARM bundle. The other 4 (debug-mantra, post-mortem, scrutinize, management-talk) were ported from existing Claude Code skills. YONISO was purpose-built for enforcing recursive root questioning.

YONISO เป็น skill เดียวใน 5 ตัวของ 9ARM bundle ที่เป็น **LMA-native** — ไม่ได้ port มาจาก Claude Code skills เหมือนอีก 4 ตัว สร้างขึ้นมาเพื่อบังคับใช้ recursive root questioning โดยเฉพาะ

---

## 🧠 Three-Phase Discipline / หลักการ 3 เฟส

### Phase 1 — PRE-FIX ASSESS

Classify severity from **observable signals** — not the agent's opinion.
วัดความรุนแรงจาก **สัญญาณจริง** ไม่ใช่ความคิดเห็นของ agent

| Signal / สัญญาณ | Severity / ความรุนแรง | Min Layers / ชั้นต่ำสุด |
|------------------|------------------------|--------------------------|
| Crash, data-loss, auth-bypass, SQLi, RCE | **CRITICAL** | 4 |
| Wrong output, API break, race condition, >50% perf regression | **HIGH** | 3 |
| Edge-case, missing validation | **MEDIUM** | 2 |
| Typo, formatting, rename | **LOW** | 1 |

**Auto-classify always wins over self-report.** If an agent claims "severity = LOW" but signals show CRITICAL → the gate rejects with a discrepancy flag. The agent must justify why signals don't apply.

**Auto-classify ชนะ self-report เสมอ** — ถ้า agent บอก "ไม่รุนแรง" แต่สัญญาณบอก CRITICAL → gate ปฏิเสธ

### Phase 2 — DURING FIX

Chain the "why" layers. Each layer must pass **4 quality heuristics:**
ไล่ why-chain ตามชั้นที่กำหนด แต่ละชั้นต้องผ่าน **4 กฎคุณภาพ:**

1. **Specific** — names a concrete identifier (function, file:line, variable, config key). Not "there was a sync issue."
   ระบุชื่อฟังก์ชัน/ไฟล์/บรรทัด (ไม่ใช่ "มันพังเพราะ sync issue")
2. **Causal** — uses causal language ("because", "which caused", "allowing", "without"). Not correlation.
   ใช้คำเชื่อมสาเหตุ (เพราะว่า, ซึ่งทำให้, เปิดทางให้)
3. **Novel** — introduces new information, not a restatement of the layer above.
   ไม่ใช่แค่พูดซ้ำชั้นก่อนหน้าด้วยคำอื่น
4. **Actionable** — identifies something that can be changed.
   บอกสิ่งที่เปลี่ยนแปลงได้จริง

| Layer / ชั้น | Question / คำถาม | Must identify / ต้องระบุ |
|--------------|-------------------|---------------------------|
| **L1: Proximate** | What specifically broke? / อะไรพัง? | Function, line, condition that failed / ฟังก์ชัน, บรรทัด, condition ที่ fail |
| **L2: Systemic** | Why was that breakage possible? / ทำไมถึงพังได้? | Missing guard/contract/test/validation / guard/contract/test/validation ที่หายไป |
| **L3: Process** | Why did the process allow this? / ทำไม process ถึงปล่อยผ่าน? | CI gap, missing lint rule, missing test category / CI gap, missing lint rule, missing test |
| **L4: Meta** | Why does the system permit this class? / ทำไมระบบถึงมีช่องโหว่แบบนี้? | Architectural pattern, missing abstraction layer / architectural pattern, missing abstraction |

### Phase 3 — POST-FIX FEEDBACK

After the fix lands: compare predicted vs actual severity. Record any discrepancy in the knowledge base. The next bug of this pattern must use the corrected classification.

หลังแก้ → เทียบ predicted vs actual severity → บันทึก discrepancy ลง knowledge base

---

## 📊 Layer Escalation Matrix / ตารางเพิ่มชั้น

| ID | Signal / สัญญาณ | Min Layers / ชั้นต่ำสุด |
|----|------------------|--------------------------|
| E1 | severity = HIGH | 3 |
| E2 | severity = CRITICAL | 4 |
| E3 | known_pattern in knowledge base | 3 |
| E4 | recurrence_count ≥ 1 (same bug returned) | 4 |
| E5 | security_bug = true (from code surface scan) | 4 |
| E6 | data_loss_risk = true (from operation patterns) | 4 |
| E7 | >3 effective files (logic/API/schema only) | 3 |
| E8 | cross_subsystem = true | 3 |

Multiple triggers → highest layer wins (not additive).
Multiple triggers → เลือกชั้นสูงสุด (ไม่ใช่บวกกัน)

---

## 🔧 v2 → v3: 6 Structural Gaps Closed / 6 จุดอ่อนที่ปิดแล้ว

| # | Gap / จุดอ่อน | v2 | v3 |
|---|---------------|----|----|
| 1 | **Self-report trust** | Agent declares its own severity | Signal-based auto-classification |
| 2 | **Layer quality** | Why-chain not validated | 4-point quality heuristic per layer |
| 3 | **Signal weakness** | Counted `files_touched` (incl. format/rename) | Change-type classification (logic/API/schema only) |
| 4 | **Length proxy** | Depth measured by output length | Qualitative shallow-output criteria |
| 5 | **Timing** | Reactive-only | 3-phase proactive discipline |
| 6 | **No feedback** | No post-fix verification loop | Post-fix discrepancy audit |

---

## 📦 Installation / การติดตั้ง

```bash
npx @anthropic-ai/claude-code skills add punglink145/Yoniso
```

Or manually copy `SKILL.md` to `~/.claude/skills/yoniso/SKILL.md`.
หรือ copy `SKILL.md` ใส่ `~/.claude/skills/yoniso/SKILL.md` ด้วยตัวเอง

---

## 🎮 Usage / วิธีใช้

Type `/yoniso` in any Claude Code session — the skill auto-invokes.
ใน Claude Code session — `/yoniso` จะ invoke skill อัตโนมัติ

The skill also fires **proactively** when the agent attempts to:
หรือ skill จะทำงานเองแบบ proactive เมื่อ agent จะ:

- Fix a bug / แก้บั๊ก (fix)
- Write a plan / เขียนแผน (plan)
- Review code / review โค้ด (review)
- Make an architectural decision / ตัดสินใจ architectural

---

## 📁 Files / ไฟล์ใน repo

| File / ไฟล์ | Purpose / หน้าที่ |
|-------------|-------------------|
| `SKILL.md` | Claude Code skill definition — recital + 3-phase decision tree + enforcement rules |
| `README.md` | This file / ไฟล์นี้ |

---

## ⚖️ License

MIT
