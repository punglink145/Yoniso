# YONISO-MANASIKARA v3.0.0

> โยนิโสมนสิการ — หลักการตั้งคำถามย้อนกลับแบบ recursive root questioning
> Discipline สำหรับ Claude Code agent ทุกครั้งที่แก้บั๊ก เขียนแผน หรือ review โค้ด

---

## 📜 ที่มา

YONISO เกิดจาก **R-CORE-007** ใน CLAUDE.md ของ LMA (Local Multi-Agent OS) — agent ชอบแก้บั๊กแบบ surface-level โดยไม่ถามว่า *ทำไมบั๊กถึงเกิดตั้งแต่แรก*

**Timeline:**

| วันที่ | เหตุการณ์ |
|--------|-----------|
| 02 มิ.ย. 2026 | ADR-022 APPROVED (Triad 2-of-3 vote: benz Strategic YES + Quality concur) — 9arm enforcement เปิดตัว |
| 02 มิ.ย. 2026 | Yoniso commit แรก — ปิด root-cause จาก scheduler audit (`bb56e82`) |
| 02 มิ.ย. 2026 | Yoniso test suite + 7 agent manifests (`5062e84`) |
| 03 มิ.ย. 2026 | 11 code-review-max findings + YONISO 2-layer RCA ใช้งานจริง (`4e197f1`) |
| 05 มิ.ย. 2026 | **v3.0.0** — signal-based auto-classification + 4-point layer quality heuristics + feedback loop (`8a302cc`) |

**DNA:** YONISO เป็น skill เดียวใน 5 ตัวของ 9ARM bundle ที่เป็น **LMA-native** — ไม่ได้ port มาจาก Claude Code skills เหมือนอีก 4 ตัว (debug-mantra, post-mortem, scrutinize, management-talk)

---

## 🧠 หลักการ 3 เฟส

### Phase 1 — PRE-FIX ASSESS
วัดความรุนแรงจาก **สัญญาณจริง** ไม่ใช่ความคิดเห็นของ agent

| Signal | Severity | Min Layers |
|--------|----------|------------|
| Crash, data-loss, auth-bypass, SQLi, RCE | **CRITICAL** | 4 |
| Wrong output, API break, race condition, >50% perf regression | **HIGH** | 3 |
| Edge-case, missing validation | **MEDIUM** | 2 |
| Typo, formatting, rename | **LOW** | 1 |

**Auto-classify ชนะ self-report เสมอ** — ถ้า agent บอก "ไม่รุนแรง" แต่สัญญาณบอก CRITICAL → gate ปฏิเสธ

### Phase 2 — DURING FIX
ไล่ why-chain ตามชั้นที่กำหนด แต่ละชั้นต้องผ่าน **4 กฎคุณภาพ:**

1. **Specific** — ระบุชื่อฟังก์ชัน/ไฟล์/บรรทัด (ไม่ใช่ "มันพังเพราะ sync issue")
2. **Causal** — ใช้คำเชื่อมสาเหตุ (เพราะว่า, ซึ่งทำให้, เปิดทางให้)
3. **Novel** — ไม่ใช่แค่พูดซ้ำชั้นก่อนหน้าด้วยคำอื่น
4. **Actionable** — บอกสิ่งที่เปลี่ยนแปลงได้จริง

| Layer | คำถาม | ต้องระบุ |
|-------|--------|----------|
| **L1: Proximate** | อะไรพัง? | ฟังก์ชัน, บรรทัด, condition ที่ fail |
| **L2: Systemic** | ทำไมถึงพังได้? | guard/contract/test/validation ที่หายไป |
| **L3: Process** | ทำไม process ถึงปล่อยผ่าน? | CI gap, missing lint rule, missing test |
| **L4: Meta** | ทำไมระบบถึงมีช่องโหว่แบบนี้? | architectural pattern, missing abstraction |

### Phase 3 — POST-FIX FEEDBACK
หลังแก้ → เทียบ predicted vs actual severity → บันทึก discrepancy ลง knowledge base

---

## 📊 Layer Escalation Matrix

| ID | Signal | Min Layers |
|----|--------|------------|
| E1 | severity = HIGH | 3 |
| E2 | severity = CRITICAL | 4 |
| E3 | known_pattern in KB | 3 |
| E4 | recurrence_count ≥ 1 | 4 |
| E5 | security_bug = true | 4 |
| E6 | data_loss_risk = true | 4 |
| E7 | >3 effective files (logic/API/schema) | 3 |
| E8 | cross_subsystem = true | 3 |

Multiple triggers → highest layer wins (ไม่ใช่บวกกัน)

---

## 🔧 v2 → v3: 6 Structural Gaps ปิดแล้ว

| Gap | v2 | v3 |
|-----|----|----|
| 1. Self-report trust | Agent บอกความรุนแรงเอง | Signal-based auto-classification |
| 2. Layer quality | ไม่ validate คุณภาพ why-chain | 4-point quality heuristic ต่อชั้น |
| 3. Signal weakness | นับแค่ `files_touched` (รวม format/rename) | Change-type classification (นับเฉพาะ logic/API/schema) |
| 4. Length proxy | วัดความลึกจากความยาว | Qualitative shallow-output criteria |
| 5. Timing | Reactive-only | 3-phase proactive discipline |
| 6. No feedback | ไม่มี loop ตรวจสอบ | Post-fix discrepancy audit |

---

## 📦 การติดตั้ง

```bash
npx @anthropic-ai/claude-code skills add punglink145/yoniso
```

หรือ copy `SKILL.md` ใส่ `~/.claude/skills/yoniso/SKILL.md` ด้วยตัวเอง

---

## 🎮 วิธีใช้

ใน Claude Code session — `/yoniso` จะ invoke skill อัตโนมัติ

หรือ skill จะทำงานเองแบบ proactive เมื่อ agent จะ:
- แก้บั๊ก (fix)
- เขียนแผน (plan)
- review โค้ด (review)
- ตัดสินใจ architectural

---

## 📁 ไฟล์ใน repo

| ไฟล์ | หน้าที่ |
|------|--------|
| `SKILL.md` | Claude Code skill definition — recital + decision tree + enforcement rules |
| `README.md` | ไฟล์นี้ |

---

## ⚖️ License

MIT
