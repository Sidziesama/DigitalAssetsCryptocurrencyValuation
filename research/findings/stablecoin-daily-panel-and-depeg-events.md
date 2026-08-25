# Stablecoin Daily Panel and Depeg Events

- USD-target stablecoins: 15 (PAXG excluded because its target is gold, not USD).
- Asset-day observations: 23,384.
- Daily 50-bps breach observations: 3,670.
- Primary episodes: 533 using a 50-bps onset and 25-bps recovery band.
- Primary-model episodes excluding the USTC failure control: 465.
- Recovered episodes: 519; right-censored episodes: 14.
- Extreme-deviation episodes flagged for source review: 8.
- Panel median absolute peg error: 10.000 bps.

An episode starts on the first daily observation outside the onset band and remains open until the first observation inside the narrower recovery band. Calendar gaps censor an open episode rather than being silently bridged. Area under deviation sums absolute basis-point deviations over observed episode days. These daily definitions are intended for the long panel; the notebook's consecutive-observation intraday rule remains the primary specification for future five-minute event data.
