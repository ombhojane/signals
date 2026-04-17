# Eval Report — 2026-04-12 02:25 UTC

## Headline metrics

- **Rug detection rate**: 0% (3 rugs evaluated)
- **Legit pass rate**: 90% (10 legits evaluated)
- **Kill-switch precision**: 0% (0/0 triggers on actual rugs)
- **Brier score (rugs)**: 0.563 — **Brier score (legits)**: 0.152
- **Avg latency**: 24.5s per case, total 319s

## Per-case results

| Case | Label | Action | Conf | Risk | KS | signal.overall | rug | mkt | social | hint | t(s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `usdc_sol` | legit | **HOLD** | 62 | MEDIUM | — | 0.78 | 0.95 | 0.90 | 0.25 | STRONG_BUY | 24.5 |
| `usdt_sol` | legit | **HOLD** | 48 | MEDIUM | — | 0.37 | 0.90 | 0.05 | 0.50 | SELL | 29.0 |
| `bonk` | legit | **HOLD** | 60 | MEDIUM | — | 0.61 | 0.93 | 0.44 | 0.50 | BUY | 25.8 |
| `wif` | legit | **HOLD** | 53 | MEDIUM | — | 0.61 | 0.99 | 0.44 | 0.50 | BUY | 23.0 |
| `jup` | legit | **HOLD** | 58 | MEDIUM | — | 0.75 | 0.93 | 0.70 | 0.50 | BUY | 26.8 |
| `jto` | legit | **BUY** | 60 | MEDIUM | — | 0.55 | 0.66 | 0.44 | 0.65 | HOLD | 28.6 |
| `pyth` | legit | **BUY** | 75 | LOW | — | 0.61 | 0.93 | 0.40 | 0.62 | BUY | 18.6 |
| `ray` | legit | **HOLD** | 60 | HIGH | — | 0.58 | 0.44 | 0.70 | 0.50 | HOLD | 26.0 |
| `msol` | legit | **STRONG_SELL** | 57 | HIGH | — | 0.38 | 0.00 | 0.60 | 0.50 | STRONG_SELL | 30.9 |
| `popcat` | legit | **HOLD** | 70 | MEDIUM | — | 0.51 | 0.75 | 0.30 | 0.66 | HOLD | 23.7 |
| `hawk_tuah` | pump_and_dump | **HOLD** | 53 | MEDIUM | — | 0.30 | 0.60 | 0.10 | 0.50 | SELL | 21.9 |
| `melania` | pump_and_dump | **HOLD** | 57 | MEDIUM | — | 0.46 | 0.84 | 0.20 | 0.50 | HOLD | 23.8 |
| `honeypot_example` | rug | **HOLD** | 17 | MEDIUM | — | 0.79 | 0.79 | 0.50 | 0.50 | HOLD | 16.5 |

## Action distribution by label

- **legit** (10): {'HOLD': 7, 'BUY': 2, 'STRONG_SELL': 1}
- **pump_and_dump** (2): {'HOLD': 2}
- **rug** (1): {'HOLD': 1}

## Average confidence by label

- **legit**: 60.3
- **pump_and_dump**: 55.0
- **rug**: 17.0

## Errors

None.