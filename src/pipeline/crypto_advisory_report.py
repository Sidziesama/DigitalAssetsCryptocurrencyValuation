"""One editable advisory report and a self-contained printable HTML edition."""
from __future__ import annotations

import argparse
import html
import json
import math
import re
from pathlib import Path

from .crypto_cross_asset import PRIMARY
from .crypto_h8_verified_universe import read_csv

COLORS={'GLD':'#b88017','SPY':'#276a9e','IWM':'#7863a6',PRIMARY:'#18334e','BTC':'#d97922','ETH':'#477881'}


def text(x,y,value,size=14,color='#19334b',anchor='start'):
    return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(str(value))}</text>'


def canvas(title,subtitle,height):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{height}" viewBox="0 0 1080 {height}" role="img" aria-label="{html.escape(title)}">','<rect width="1080" height="100%" fill="white"/>',text(25,32,title,22),text(25,57,subtitle,12,'#566677')]


def correlation_figure(cross):
    parts=canvas('Crypto co-movement: equities stronger than gold','Weekly return correlations; 52 observations. Lines show marginal 95% block-bootstrap intervals.',340)
    x=lambda v:280+(v+1)*340
    for tick in [-1,-.5,0,.5,1]:
        parts += [f'<line x1="{x(tick)}" y1="85" x2="{x(tick)}" y2="265" stroke="#dfe5eb"/>',text(x(tick),290,f'{tick:.1f}',12,anchor='middle')]
    for i,r in enumerate(r for r in cross['correlations'] if r['series']==PRIMARY):
        y=115+i*60
        parts += [text(25,y+5,{'GLD':'Gold / GLD','SPY':'S&P 500 / SPY','IWM':'Russell 2000 / IWM'}[r['benchmark']],15),f'<line x1="{x(r["bootstrap_low"]):.2f}" y1="{y}" x2="{x(r["bootstrap_high"]):.2f}" y2="{y}" stroke="{COLORS[r["benchmark"]]}" stroke-width="4"/>',f'<circle cx="{x(r["pearson"]):.2f}" cy="{y}" r="7" fill="{COLORS[r["benchmark"]]}"/>',text(980,y+5,f'{r["pearson"]:.2f}',16)]
    parts += [text(620,323,'−1: opposite moves       0: little linear relationship       +1: move together',12,anchor='middle'),'</svg>']
    return '\n'.join(parts)+'\n'


def line_figure(title,subtitle,series,ylabel,percent=False,start_label='August 2025',end_label='August 2026'):
    parts=canvas(title,subtitle,490); all_values=[v for values in series.values() for v in values if v is not None]
    low,high=min(all_values),max(all_values); padding=(high-low)*.08 or .1; low-=padding;high+=padding
    left,top,width,height=85,95,850,310
    for i in range(5):
        value=low+(high-low)*i/4;y=top+height-height*i/4
        parts += [f'<line x1="{left}" y1="{y}" x2="{left+width}" y2="{y}" stroke="#e1e7ed"/>',text(left-10,y+4,f'{value:.2f}' if percent else f'{value:.0f}',12,anchor='end')]
    for i,(name,values) in enumerate(series.items()):
        points=' '.join(f'{left+width*j/max(len(values)-1,1):.2f},{top+height-height*(value-low)/(high-low):.2f}' for j,value in enumerate(values) if value is not None)
        color=COLORS.get(name,'#526c86')
        parts += [f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5"/>',f'<rect x="{25+i*205}" y="445" width="15" height="4" fill="{color}"/>',text(45+i*205,451,name if name!=PRIMARY else 'Crypto basket',12)]
    parts += [text(85,426,start_label,12),text(935,426,end_label,12,anchor='end'),text(85,81,ylabel,12,'#566677'),'</svg>']
    return '\n'.join(parts)+'\n'


def heatmap(cross):
    labels=[PRIMARY,'BTC','ETH','Crypto ex BTC and ETH']+[r['series'] for r in cross['correlations'] if r['series'].startswith('Group: ') and r['benchmark']=='GLD']
    parts=canvas('Economic groups show similar equity co-movement','Weekly Pearson correlations. Groups overlap; these are descriptive comparisons.',135+38*len(labels))
    for j,b in enumerate(['GLD','SPY','IWM']): parts.append(text(480+j*180,88,b,14,anchor='middle'))
    for i,label in enumerate(labels):
        y=105+i*38;parts.append(text(25,y+23,label.replace('Group: ','').replace('_',' '),13))
        for j,b in enumerate(['GLD','SPY','IWM']):
            r=next(r for r in cross['correlations'] if r['series']==label and r['benchmark']==b);v=r['pearson']
            alpha=abs(v) if v is not None else 0
            color=f'rgb({int(245-150*alpha)},{int(247-95*alpha)},{int(250-45*alpha)})' if v is not None and v>=0 else f'rgb(250,{int(247-130*alpha)},{int(245-130*alpha)})'
            parts += [f'<rect x="{400+j*180}" y="{y}" width="160" height="32" fill="{color}"/>',text(480+j*180,y+22,f'{v:.2f}' if v is not None else 'Unavailable',14,anchor='middle')]
    return '\n'.join(parts+['</svg>'])+'\n'


def figures(cross,weekly,rolling):
    growth={name:[100.0] for name in [PRIMARY,'GLD','SPY','IWM']}
    for r in weekly:
        if all(name in r and r[name]!='' for name in growth):
            for name in growth: growth[name].append(growth[name][-1]*(1+float(r[name])))
    rolling_values={b:[float(r['correlation']) if r['correlation']!='' else None for r in rolling if r['benchmark']==b] for b in ['GLD','SPY','IWM']}
    return {
        'crypto-cross-asset-correlations.svg':correlation_figure(cross),
        'crypto-cross-asset-growth.svg':line_figure('What happened to a hypothetical $100?','Matched weekly endpoints; ETF adjusted returns and a fixed crypto basket. Trading costs excluded.',growth,'Wealth index ($100 at first endpoint)',start_label=weekly[0]['previous_date'],end_label=weekly[-1]['date']),
        'crypto-cross-asset-rolling.svg':line_figure('Market relationships change over time','Trailing 60 common U.S. sessions; crypto includes intervening weekend returns.',rolling_values,'Pearson correlation',True,start_label=rolling[0]['date'],end_label=rolling[-1]['date']),
        'crypto-cross-asset-groups.svg':heatmap(cross),
    }


def render(cross,valuation,findings,architecture,profiles,dashboard,manifest):
    primary=[r for r in cross['correlations'] if r['series']==PRIMARY]
    models={r['model_id']:r for r in valuation['models']}
    gain=1-models['identity_groups']['loao_rmse_log_cap']/models['identity_breadth']['loao_rmse_log_cap']
    worsening=models['fundamentals_capture']['loao_rmse_log_cap']/models['fundamentals_activity']['loao_rmse_log_cap']-1
    down=next(r for r in cross['stress_regimes'] if r['series']==PRIMARY and r['regime']=='SPY_negative_week')
    lines=['# Digital assets: economic function, valuation and market risk','','Independent research discussion draft | 19 October 2026','','Prepared for an advisory audience, including the planned Goldman Sachs advisory discussion. This document is independent research and carries no firm endorsement. Historical evidence ends in August 2026; it is not an October market update.','','## One-page briefing','','### What we built','','A verified economic-function matrix for 23 cryptoassets, five hypothesis studies, six exploratory relative-valuation models, and a matched-return benchmark comparison. These layers answer different questions: what a token does, what may support its value, and how its market risk relates to traditional assets.','','### Three messages for the meeting','','| What we measured | What the evidence says | Advisory use |','|---|---|---|',f'| Economic design | 230 sourced decisions; same-architecture pairs share {architecture["mean_same_architecture_similarity"]:.1%} of functions versus {architecture["mean_cross_architecture_similarity"]:.1%} across architectures | Select economic peers and metrics using the token’s actual functions |',f'| Relative value | Eight groups reduce held-out error by {gain:.1%} versus a raw function count; adding capture to the fundamentals model worsens error by {worsening:.1%} | Use models to structure questions; investigate large residuals and wide uncertainty bands |',f'| Portfolio context | Weekly co-movement is strongest with SPY in this sample; crypto loses in {down["share_negative"]:.0%} of SPY-negative weeks | Assess crypto as a risky allocation; low average correlation alone does not establish protection |','','### What can be presented with confidence','','The classification instrument is auditable and useful for economic due diligence. The numerical findings are reproducible exploratory estimates. Precision, generalizability and independent validation are different standards: these data do not establish universal valuation multiples, safe-haven status or trading signals.','','## 1. Research scope and classification','','The ten functions are monetary use, gas, staking, burn, scarcity, collateral, governance, protocol capture, utility and incentives. Architecture records operational context. Assets can have several economic functions; governance over a treasury does not itself establish value reaching the token or holder.','','Each decision follows a written rule, dated primary evidence and a recorded adjudication. All 230 cells have evidence, but only ten have an independent blind review. Full-matrix inter-rater reliability has not been established. The industry survey remains a route to external rule validation.','','## 2. What the hypotheses currently show','','| Question | Result | Interpretation for advisory discussion |','|---|---|---|',f'| H1: does usage relate to value? | One-year transaction coefficient {findings["H1"]["one_year_transaction_count_coefficient"]:.3f}; exact p={findings["H1"]["one_year_transaction_count_exact_p"]:.3f}; sign changes without XLM | Suggestive, sensitive to asset composition |',f'| H2: does capture strengthen the fee–value relationship? | Broad interaction p={findings["H2"]["pooled_market_cap_exact_p"]:.3f}; strict capture p=0.478 | The definition changes the conclusion; fees are not automatically holder income |',f'| H3: do supply events move prices in the predicted direction? | {findings["H3"]["supply_events_matching_predicted_sign"]}/{findings["H3"]["supply_events_estimated"]} events match; asset-level p={findings["H3"]["supply_event_asset_sign_flip_p"]:.2f} | No support for a standalone unlock/burn rule; only three independent assets |','| H4: does staking affect liquid float and risk? | ETH archival active-stake data missing | Not yet estimated |','| H8: do groups improve on counting functions? | Best single-group error improvement about 2.8%; separate later validation is frozen | Discovery-sample association; RV1 below is a different model extension |','','Earlier function–risk tests yielded no result surviving the declared 10% false-discovery correction. Null and unstable results remain part of the research record.','','## 3. Relative valuation: useful comparison, limited precision','','RV1 estimates historical geometric mean capitalization with each target asset held out of training and scaling. Ridge regression uses a fixed penalty of 10; no penalty or predictor is selected from these new outcomes. The historical outcomes had already been examined in earlier work, so RV1 remains exploratory.','','| Model | Asset count | Held-out log-cap error | What it tests |','|---|---:|---:|---|']
    meanings={'identity_mean':'Same-sample mean benchmark','identity_breadth':'Count of ten functions','identity_groups':'Eight economic groups jointly','fundamentals_mean':'Smaller-sample mean benchmark','fundamentals_activity':'Fees, volume and chain/application scope','fundamentals_capture':'Adds static verified capture'}
    for r in valuation['models']: lines.append(f'| {r["model_id"]} | {r["assets"]} | {r["loao_rmse_log_cap"]:.3f} | {meanings[r["model_id"]]} |')
    lines+=['','Errors are comparable only within identical samples. The identity model substantially underpredicts BTC: observed/model capitalization is about 168x. This is an example of missing economic information and model inadequacy, not proof that BTC is overpriced. Empirical error bands are descriptive and have no calibrated coverage guarantee.','','Peer valuation uses shared functions, matched fee scope, a target excluded from its peer set, and at least three eligible peers. Holder-revenue multiples require verified capture. Provider-defined holder revenue is not automatically a legal cash-flow entitlement. Asset estimates and all contributions are preserved in the RV1 CSV.','','## 4. Crypto versus gold and U.S. equities','','### What is being compared','','GLD represents gold, SPY represents the S&P 500, and IWM represents Russell 2000. Vendor-adjusted ETF returns reflect the instruments rather than exact spot-gold or index total returns. Crypto is a retrospective fixed basket of 21 eligible assets, rebalanced equally each calendar day before costs. HYPE has no source history and TON has only 310 of 363 required calendar closes, below the fixed 90% rule. These exclusions follow coverage, not observed correlations.','','The primary study has 52 matched weekly returns, from endpoints 22 August 2025 through 21 August 2026. Crypto compounds through weekends between the same ETF endpoints. U.S. holidays are not filled with artificial zero returns. Crypto UTC and ETF New York closing times differ; shifted-close checks quantify sensitivity.','','### Main correlations','','A correlation near +1 means returns tend to move together; near zero means little linear co-movement. It does not describe whether an asset is cheap, whether both assets made money, or whether losses are protected.','','| Benchmark proxy | Weekly Pearson | Rank correlation | 95% block-bootstrap interval | Weeks |','|---|---:|---:|---|---:|']
    for r in primary: lines.append(f'| {r["benchmark"]} | {r["pearson"]:.2f} | {r["spearman"]:.2f} | {r["bootstrap_low"]:.2f} to {r["bootstrap_high"]:.2f} | {r["pairs"]} |')
    lines+=['','Intervals use 2,000 paired circular moving-block draws in four-week blocks. They are marginal intervals for three declared correlations, not simultaneous familywise intervals or confirmatory significance tests. The gold and small-cap intervals include zero. The one-year sample cannot establish stable multi-cycle relationships.','','![Correlation estimates and uncertainty](../figures/crypto-cross-asset-correlations.svg)','','### Returns and risk on the same endpoints','','| Series | Period return | Annualized weekly volatility | Worst drawdown observed at weekly endpoints |','|---|---:|---:|---:|']
    for r in cross['performance']: lines.append(f'| {r["series"]} | {r["total_return"]:.1%} | {r["annualized_volatility"]:.1%} | {r["sampled_max_drawdown"]:.1%} |')
    lines+=['','Drawdowns sampled weekly can miss deeper intraday or daily losses. Volatility uses weekly standard deviation times √52. No borrowing, staking income, transaction costs or investor taxes are included for crypto; adjusted ETF prices use the vendor’s treatment of distributions. USDT-versus-USD basis risk remains.','','![Growth of a hypothetical $100](../figures/crypto-cross-asset-growth.svg)','','### Does the conclusion survive other measurements?','','| Measurement | Gold / GLD | S&P 500 / SPY | Russell 2000 / IWM |','|---|---:|---:|---:|']
    for scenario in ['daily','weekly_first_half','weekly_second_half','weekly_crypto_shift_minus1','weekly_crypto_shift_plus1']:
        subset=[r for r in cross['robustness'] if r['series']==PRIMARY and r['scenario']==scenario]
        values={r['benchmark']:f'{r["pearson"]:.2f}' if r['pearson'] is not None else 'Unavailable' for r in subset}
        lines.append('| '+scenario.replace('_',' ')+' | '+' | '.join(values[b] for b in ['GLD','SPY','IWM'])+' |')
    lines+=['','The gold relationship changes sign across chronological halves. Russell 2000 co-movement is sensitive to the timing choice. SPY remains positive in all listed measurements, but its magnitude changes. A single correlation matrix would conceal this instability. The rolling series below is descriptive and contains overlapping windows.','','![Rolling correlations](../figures/crypto-cross-asset-rolling.svg)','','### What happens when equities fall?','','| Regime | Series | Weeks | Mean weekly return | Share of weeks with losses |','|---|---|---:|---:|---:|']
    for r in cross['stress_regimes']:
        if r['series'] in [PRIMARY,'GLD','SPY','IWM']: lines.append(f'| {r["regime"].replace("_"," ")} | {r["series"]} | {r["weeks"]} | {r["mean_weekly_return"]:.1%} | {r["share_negative"]:.0%} |')
    lines+=['','Crypto lost money in two-thirds of the 21 SPY-negative weeks. In the 11 worst-quintile SPY weeks, its average return was also negative. Eleven observations are too few for the declared regime-correlation threshold; those correlations are withheld. These are conditional descriptions, with no proof of safe-haven behavior or a causal stress mechanism.','','### Do economic groups behave alike?','','![Economic-group correlation map](../figures/crypto-cross-asset-groups.svg)','','Groups overlap; the same token can appear in several baskets. These results describe the current classification applied retrospectively. Differences cannot establish a causal effect of staking, governance or capture.','','## 5. Technical market context','','Technical measures describe past trend and price variation. They enter the report as market context; they do not set the economic classifications or valuation model choices. The following table reuses the archived dashboard inputs and is dated at the actual observed close.','','| Asset | Last observed close date | Prior 30-day return | Prior 90-day return | 30-day volatility, annualized |','|---|---|---:|---:|---:|']
    for p in dashboard['asset_results']:
        t=p['technical_market_state']; vals=[]
        for key in ['return_30d','return_90d','realized_volatility_30d_annualized']:
            v=t[key]['value']; vals.append(f'{v:.1%}' if v is not None else 'Unavailable')
        lines.append(f'| {p["symbol"]} | {t["as_of_date"] or "Unavailable"} | '+' | '.join(vals)+' |')
    lines+=['','These existing dashboard momentum labels use counts of daily observations; gaps can change their calendar meaning. The new cross-asset analysis independently requires every intervening calendar return and does not use these indicators as predictors.','','## 6. Advisory application and open work','','Use the work in this order: identify the token’s economic functions; select comparable assets and relevant fundamentals; inspect the model’s error and precision; then assess traditional-asset co-movement, stress behavior and market risk. Final portfolio judgment requires client-specific objectives and exposure constraints beyond this research.','','| Finding | Decision supported | What must happen before a stronger claim |','|---|---|---|','| Economic groups improve some held-out comparisons | Organize peer selection by function | External rule feedback and later samples |','| Fees alone do not establish holder value | Trace the actual capture mechanism | Better time-varying capture and distribution measurement |','| BTC is poorly explained by the function model | Treat residuals as due-diligence questions | Monetary adoption, network and liquidity fundamentals |','| Correlations change with sample and clock | Use ranges and stress context | Longer history and synchronized intraday closes |','| H4 remains blocked | Keep staking-liquidity conclusions open | Archive-capable ETH consensus data |','','Immediate follow-up is methodological review of the draft, external survey feedback, a longer benchmark history with a separately frozen window, and independent verification of critical market prices. Do not retune the current results to improve the presentation.','','## Appendix A. Economic classification and peer context','','| Asset | Architecture | Verified economic roles | Closest economic comparables |','|---|---|---|']
    for p in profiles['profiles']: lines.append(f'| {p["symbol"]} | {p["architecture_context"]} | {"; ".join(p["economic_identity"])} | {", ".join(r["symbol"] for r in p["closest_economic_comparables"])} |')
    lines+=['','## Appendix B. Reproducibility and limitations','','CA1 was specified and committed before its estimates. Benchmark payloads are archived unchanged with SHA-256 checksums and retrieval timestamps. The normalized data rebuild without credentials. Weekly return tables, all asset/group correlations, sensitivity results and rolling series are retained in `data/processed/03_risk/`. RV1 estimates and coefficients’ contributions are in `data/processed/02_valuation/`.','','Sources are public and auditable, but critical market figures have not yet been verified against an independent second vendor. Current-universe selection creates survivorship bias. Equal weighting emphasizes smaller assets and daily rebalancing is hypothetical. Historical USDT prices are approximate USD measures. Contemporary function codes are not historical point-in-time signals. Correlation coefficients do not identify causal exposures, formal multi-factor loadings or diversification during every stress event. Single-coder classifications, overlapping groups, small cross-sections, a single market year and data-provider definitions constrain inference.','','### Source and instrument references','','GLD follows gold bullion less expenses; SPY seeks S&P 500 price and yield exposure; IWM seeks Russell 2000 exposure. ETF adjusted closes are obtained from the archived vendor responses, not from the issuer product pages.']
    for b in manifest['instruments']: lines += ['',f'- [{b["symbol"]} official instrument description]({b["official_instrument_source"]}). Snapshot retrieved {b["retrieved_at_utc"]}; SHA-256 `{b["sha256"]}`.']
    lines+=['','### Rebuild commands','','```bash','python -m src.pipeline.cross_asset_market_data --repo . --offline','python -m src.pipeline.crypto_cross_asset --repo .','python -m src.pipeline.crypto_advisory_report --repo .','```','']
    group_values=[r['pearson'] for r in cross['correlations'] if r['series'].startswith('Group: ') and r['benchmark']=='SPY' and r['pearson'] is not None]
    position=lines.index('### Do economic groups behave alike?')
    lines[position+1:position+1]=['',f'Group-basket SPY correlations cluster between {min(group_values):.2f} and {max(group_values):.2f}. Economic roles distinguish valuation channels, while this sample shows broadly shared equity co-movement. The observed differences are not evidence of distinct risk factors.']
    position=next(i for i,line in enumerate(lines) if line.startswith('Intervals use 2,000'))
    lines[position]+=' Bootstrap interpretation assumes the chosen period represents sufficiently stable dependence; regime changes weaken that approximation.'
    return '\n'.join(lines)


def html_edition(markdown,charts):
    """Render the controlled report source; embed every generated SVG for sharing."""
    parts=[]; table=False; code=False
    for line in markdown.splitlines():
        if line.startswith('```'):
            code=not code;parts.append('<pre>' if code else '</pre>'); continue
        if code: parts.append(html.escape(line)+'\n');continue
        if line.startswith('|'):
            if re.match(r'^\|[\s:|\-]+\|$',line): continue
            if not table: parts.append('<div class="table-wrap"><table>');table=True;tag='th'
            else: tag='td'
            cells=line.strip('|').split('|');parts.append('<tr>'+''.join(f'<{tag}>{html.escape(c.strip())}</{tag}>' for c in cells)+'</tr>');continue
        if table: parts.append('</table></div>');table=False
        image=re.match(r'!\[(.*?)\]\(../figures/(.*?)\)',line)
        if image:
            parts.append('<figure>'+charts[image.group(2)]+f'<figcaption>{html.escape(image.group(1))}</figcaption></figure>');continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'));parts.append(f'<h{level}>{html.escape(line[level:].strip())}</h{level}>');continue
        if line:
            escaped=html.escape(line)
            escaped=re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)',r'<a href="\2">\1</a>',escaped)
            parts.append('<p>'+escaped+'</p>')
    if table:parts.append('</table></div>')
    style='body{font:16px/1.6 Arial,sans-serif;color:#19334b;background:#f0f3f6;margin:0}main{max-width:1120px;background:white;margin:32px auto;padding:52px}h1{font-size:34px;line-height:1.2}h2{border-top:2px solid #ced8e2;padding-top:24px;margin-top:48px}h3{font-size:19px}p{max-width:100ch}table{border-collapse:collapse;width:100%;font-size:13px;margin:16px 0}th{text-align:left;background:#19334b;color:white}th,td{padding:10px;border-bottom:1px solid #dbe2e9;vertical-align:top}tr:nth-child(even){background:#f4f6f8}.table-wrap{overflow:auto}figure{margin:32px 0;break-inside:avoid}svg{width:100%;height:auto}figcaption{font-size:12px;color:#536779}pre{padding:18px;background:#f3f5f7;white-space:pre-wrap}a{color:#276a9e}@media print{body{background:white}main{margin:0;padding:0;max-width:none}h2{break-before:page}thead{display:table-header-group}tr{break-inside:avoid}a{color:inherit}table{font-size:10px}p{font-size:12px}}'
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Digital assets — independent advisory research</title><style>'+style+'</style></head><body><main>'+''.join(parts)+'</main></body></html>\n'


def run(repo:Path):
    def load(path):return json.loads((repo/path).read_text())
    cross=load('data/processed/03_risk/crypto_cross_asset.json')
    charts=figures(cross,read_csv(repo/'data/processed/03_risk/crypto_cross_asset_weekly.csv'),read_csv(repo/'data/processed/03_risk/crypto_cross_asset_rolling.csv'))
    for name,svg in charts.items():(repo/'research/figures'/name).write_text(svg)
    markdown=render(cross,load('data/processed/02_valuation/crypto_relative_valuation.json'),load('data/processed/02_valuation/crypto_findings_summary.json')['findings'],load('data/processed/02_valuation/crypto_architecture_similarity.json'),load('data/processed/02_valuation/crypto_advisory_profiles.json'),load('data/processed/02_valuation/crypto_market_valuation_dashboard.json'),load('data/processed/00_foundation/cross_asset_benchmarks_manifest.json'))
    report=repo/'research/findings/crypto-advisory-report.md';report.write_text(markdown)
    (repo/'research/findings/crypto-advisory-report.html').write_text(html_edition(markdown,charts))
    return {'status':'crypto_advisory_report_complete','report':str(report.relative_to(repo)),'figures':list(charts)}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
