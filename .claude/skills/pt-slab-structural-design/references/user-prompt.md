# Recommended User Prompt for PT Slab Skill

Copy and adapt the prompt below when requesting a full PT slab drawing package.

---

```
Use the skill `pt-slab-structural-design`.

I am providing a draft floor structural layout for a post-tensioned (PT) slab. 
Please review it against Eurocode 2 (EN 1992-1-1) and prepare the complete standard drawing package following the established 10-sheet format.

### Project context
- Project code / name: [fill in]
- Floor level: [e.g. 8F / Level 8]
- Design basis file (if available): [path or paste key data]
- National Annex (if any): [e.g. UK NA / generic EC2 / Cambodia]

### Draft layout (provide one of the following)
- Attach drawing / PDF / image of the draft floor plan, **or**
- Describe / list:
  - Grid lines and overall dimensions
  - Column positions and sizes
  - Proposed slab thickness(es)
  - Drop panel locations and sizes
  - Beam sizes and locations (if any)
  - Openings / sleeves
  - Any special constraints (fire rating, exposure class, tendon system preference, etc.)

### Required deliverable
Produce the full standard package in this exact order:

1. Concrete Body Layout
2. Beam Reinforcement Details
3. Drop Panel Reinforcement Details 1
4. Drop Panel Reinforcement Details 2
5. Drop Panel Reinforcement Details 3
6. Slab / Ring Reinforcement Details
7. Tendon Layout Plan (with full Eurocode design notes)
8–10. Tendon Profile Details

Follow the company drawing standards, title-block format, layer conventions and Eurocode material defaults already defined in this repository.  
Flag any missing information as “TBC” and do not invent values.  
List all assumptions (concrete class, strand type, friction parameters, cover, exposure class, etc.) clearly.
```
