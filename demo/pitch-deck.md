# Digital Surveyor
### Automated Property Access Assessment for UK Removals

---

## The Problem

Every removals company has sent an 18-tonne truck to a road it can't fit down.

The result: emergency trans-shipping, long carries, angry customers, and
£4,000-8,000/year in wasted costs per depot. Dispatchers currently rely on
Google Street View (often outdated) or customer guesswork.

## The Solution

**Type a postcode → see instantly if your truck can reach the property.**

Digital Surveyor pulls real surveyed measurements from Ordnance Survey and
Environment Agency data, computes road width, approach gradient, and turning
space, and returns a Green/Amber/Red access rating for each vehicle class.

Not guesswork. Not Street View. Geometry.

## How It Works

1. **Postcode in** → geocode to exact coordinates
2. **OS MasterMap** → surveyed road edge geometry → compute actual road width
3. **LiDAR elevation** → 1m resolution terrain → compute approach gradient
4. **Scoring engine** → Green/Amber/Red for Luton van, 7.5t box truck, 18t pantechnicon

## Demo

| Postcode | Scenario | Result |
|----------|----------|--------|
| BN3 3EL  | Wide suburban avenue | All GREEN |
| BN2 1TJ  | Narrow Brighton terrace | 18t RED — shuttle required |
| BN1 5FG  | Steep hill approach | Gradient AMBER |
| BN1 8YJ  | Narrow + steep + dead end | All RED — Luton van only |

## Integration Opportunity

i-mve CRM already captures enquiry postcodes. Adding Digital Surveyor at the
quote stage means:

- **Right vehicle dispatched first time** → no surprises on moving day
- **Accurate quotes** → shuttle costs priced in upfront
- **Fewer failed access attempts** → happier customers, fewer complaints
- **Surveyor time saved** → human surveyors focus only on marginal cases

## Technology

- Data: OS MasterMap (government survey-grade), EA LiDAR (1m resolution)
- Stack: Python/FastAPI backend, React frontend, PostGIS database
- Deployed: Docker containers, ready for cloud deployment
- API-first: integrates with any CRM via REST API
