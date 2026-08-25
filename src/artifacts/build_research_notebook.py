from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_BREAK
from datetime import date

OUT = 'outputs/digital_asset_valuation_research_notebook.docx'
BLUE = '183A5A'; TEAL = '167D7F'; LIGHT = 'EAF1F5'; PALE = 'F4F7F9'; GOLD='B68A35'; INK='17242E'; MUTED='5D6B75'; WHITE='FFFFFF'; RED='9B2C2C'

doc = Document()
sec=doc.sections[0]
sec.page_width=Inches(8.5); sec.page_height=Inches(11)
sec.top_margin=Inches(.82); sec.bottom_margin=Inches(.78); sec.left_margin=Inches(.82); sec.right_margin=Inches(.82)
sec.header_distance=Inches(.35); sec.footer_distance=Inches(.35)

styles=doc.styles
normal=styles['Normal']; normal.font.name='Aptos'; normal.font.size=Pt(10.2); normal.font.color.rgb=RGBColor.from_string(INK)
normal.paragraph_format.space_after=Pt(5.5); normal.paragraph_format.line_spacing=1.12
for nm,size,color,before,after in [('Title',27,BLUE,0,8),('Subtitle',12,MUTED,0,10),('Heading 1',17,BLUE,16,7),('Heading 2',13.5,TEAL,12,5),('Heading 3',11.5,BLUE,9,3)]:
    s=styles[nm]; s.font.name='Aptos Display' if nm in ('Title','Heading 1') else 'Aptos'; s.font.size=Pt(size); s.font.color.rgb=RGBColor.from_string(color); s.font.bold=nm!='Subtitle'; s.paragraph_format.space_before=Pt(before); s.paragraph_format.space_after=Pt(after); s.paragraph_format.keep_with_next=True
styles['Caption'].font.name='Aptos'; styles['Caption'].font.size=Pt(8.5); styles['Caption'].font.color.rgb=RGBColor.from_string(MUTED)
for nm in ['List Bullet','List Number']:
    styles[nm].font.name='Aptos'; styles[nm].font.size=Pt(10); styles[nm].paragraph_format.left_indent=Inches(.28); styles[nm].paragraph_format.first_line_indent=Inches(-.16); styles[nm].paragraph_format.space_after=Pt(3)

def shade(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=tcPr.find(qn('w:shd'))
    if shd is None: shd=OxmlElement('w:shd'); tcPr.append(shd)
    shd.set(qn('w:fill'),fill)
def margins(cell,top=80,start=105,bottom=80,end=105):
    tc=cell._tc.get_or_add_tcPr(); tcMar=tc.first_child_found_in('w:tcMar')
    if tcMar is None: tcMar=OxmlElement('w:tcMar'); tc.append(tcMar)
    for tag,val in [('top',top),('start',start),('bottom',bottom),('end',end)]:
        node=tcMar.find(qn('w:'+tag))
        if node is None: node=OxmlElement('w:'+tag); tcMar.append(node)
        node.set(qn('w:w'),str(val)); node.set(qn('w:type'),'dxa')
def set_repeat(row):
    trPr=row._tr.get_or_add_trPr(); el=OxmlElement('w:tblHeader'); el.set(qn('w:val'),'true'); trPr.append(el)
def table(headers, rows, widths=None, font=8.2):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
    t.style='Table Grid'; set_repeat(t.rows[0])
    for j,h in enumerate(headers):
        c=t.rows[0].cells[j]; shade(c,BLUE); margins(c); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); r=p.add_run(h); r.bold=True; r.font.color.rgb=RGBColor(255,255,255); r.font.size=Pt(font)
    for i,row in enumerate(rows):
        cells=t.add_row().cells
        for j,v in enumerate(row):
            c=cells[j]; margins(c); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if i%2: shade(c,PALE)
            p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
            r=p.add_run(str(v)); r.font.size=Pt(font); r.font.color.rgb=RGBColor.from_string(INK)
    if widths:
        for row in t.rows:
            for j,w in enumerate(widths): row.cells[j].width=Inches(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    return t
def p(text='',bold=False,italic=False,style=None,align=None,color=None,size=None):
    q=doc.add_paragraph(style=style)
    if align is not None:q.alignment=align
    r=q.add_run(text); r.bold=bold; r.italic=italic
    if color:r.font.color.rgb=RGBColor.from_string(color)
    if size:r.font.size=Pt(size)
    return q
def bullets(items):
    for x in items:p(x,style='List Bullet')
def numbered(items):
    for x in items:p(x,style='List Number')
def callout(label,text,fill=LIGHT):
    t=doc.add_table(rows=1,cols=1); t.autofit=False; t.columns[0].width=Inches(6.7); c=t.cell(0,0); shade(c,fill); margins(c,130,170,130,170)
    q=c.paragraphs[0]; q.paragraph_format.space_after=Pt(0); r=q.add_run(label+'  '); r.bold=True; r.font.color.rgb=RGBColor.from_string(TEAL); q.add_run(text)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
def formula(text):
    q=doc.add_paragraph(); q.alignment=WD_ALIGN_PARAGRAPH.CENTER; q.paragraph_format.space_before=Pt(4); q.paragraph_format.space_after=Pt(7)
    r=q.add_run(text); r.font.name='Cambria Math'; r.font.size=Pt(10.5); r.italic=True; r.font.color.rgb=RGBColor.from_string(BLUE)
def source(text,url):
    q=doc.add_paragraph(style='Caption'); q.paragraph_format.space_before=Pt(2); q.paragraph_format.space_after=Pt(5)
    q.add_run('Source: ').bold=True; q.add_run(text+' — '+url)
def pagebreak(): doc.add_page_break()

# Running furniture
h=sec.header.paragraphs[0]; h.text='DIGITAL ASSET VALUATION  /  LIVING RESEARCH NOTEBOOK'; h.style=styles['Caption']
h.runs[0].font.color.rgb=RGBColor.from_string(TEAL); h.runs[0].bold=True
f=sec.footer.paragraphs[0]; f.alignment=WD_ALIGN_PARAGRAPH.RIGHT; f.add_run('Version 1.0  •  22 August 2026  •  Page ')
fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); f._p.append(fld)

# Cover
p('NYU Tandon School of Engineering',bold=True,color=TEAL,size=11)
p('Financial Engineering • Master’s Research Project',color=MUTED,size=10)
p('\nDigital Asset Valuation',style='Title')
p('Economic Taxonomy, Measurement Codebook, and Empirical Research Design',style='Subtitle')
p('Living Research Notebook',bold=True,color=GOLD,size=14)
p('\nA reproducible framework for distinguishing money-like stablecoins, network-native cryptoassets, protocol tokens, governance instruments, and digital claims—and for testing how design, usage, liquidity, and risk map into observed value.',size=11)
callout('Research premise', '“Stablecoin” describes a target outcome; “cryptocurrency” describes a technical form. Valuation begins with economic function, enforceable rights, and the channels through which demand or cash flow can accrue to the token.')
table(['Document control','Current entry'],[
('Version','1.0 — baseline consolidation and Phase 2 design'),('Status','Working notebook; classifications are research codes, not legal conclusions'),('As-of date','22 August 2026'),('Primary unit of analysis','Asset × date; stablecoin × venue × timestamp where available'),('Reproducibility standard','Rules, source date, evidence URL, coder, confidence, and revision history retained')],[1.7,5.0],8.8)
p('How to maintain this notebook',style='Heading 2')
bullets(['Freeze each empirical extract with a retrieval timestamp and raw-file checksum.', 'Treat protocol upgrades, issuer terms, and legal rights as time-varying—not permanent asset attributes.', 'Record classification disagreements and adjudication; never overwrite a prior code without a dated change log.', 'Pre-register primary outcomes, sample, exclusions, and model variants before estimating headline results.'])
pagebreak()

p('Notebook map',style='Heading 1')
table(['Part','Purpose'],[(1,'Objective, scope, and research principles'),(2,'Phase 1 economic taxonomy and classification architecture'),(3,'Stablecoin and cryptoasset design categories'),(4,'Value-accrual and rights/claims codebooks'),(5,'Quantitative variables, empirical targets, and H1–H8'),(6,'Data schemas: asset_master, economic_design, stablecoin_design'),(7,'Reserve-quality and depeg-risk frameworks'),(8,'Phase 2 data engineering and empirical analysis'),(9,'Governance, validation, and limitations'),('Appendices','Example classifications, data dictionary, and sources')],[.7,6.0],9)
p('Version history',style='Heading 2')
table(['Version','Date','Scope','Next decision'],[('1.0','2026-08-22','Consolidated Phase 1; formalized codebook and Phase 2 plan','Freeze sample and source licenses')],[.8,1.1,3.2,1.6],8.5)

p('1. Objective, scope, and research principles',style='Heading 1')
p('Project objective',style='Heading 2')
p('Build a defensible economic taxonomy of stablecoins and cryptocurrencies that determines which variables should be tested empirically, then estimate whether economic design, usage, liquidity, supply, security, and legal/contractual rights explain peg robustness, adoption, valuation, returns, or risk.')
callout('Core contribution','The project links economic theory → explicit classification rules → versioned panel data → falsifiable hypotheses. It does not assume that labels such as L1, DeFi, or stablecoin are sufficient valuation categories.')
p('Scope and exclusions',style='Heading 2')
bullets(['In scope: fiat-referenced and other stable-value tokens; native L1/L2 assets; DeFi, oracle, governance, utility, incentive, and tokenized-claim instruments.', 'Asset classifications may overlap. A token can be monetary, gas, staking, collateral, and protocol-linked at the same time.', 'Legal-security status is recorded as jurisdiction- and transaction-specific metadata; this notebook does not provide legal advice.', 'NFTs and tokenized securities may enter comparison samples, but are not the initial core panel unless data quality supports them.'])
p('Research principles',style='Heading 2')
numbered(['Function over marketing label.','Rights and claims separated from use cases.','Mechanism activation separated from mere technical possibility.','Point-in-time coding for designs that change.','Observable thresholds where possible; documented expert judgment where necessary.','Survivorship-bias control: failed and delisted assets remain eligible.','Primary-source evidence for design fields; independent data for market outcomes.'])

p('2. Phase 1 economic taxonomy',style='Heading 1')
p('Classification architecture',style='Heading 2')
formula('Asset → {Economic function, Value accrual, Monetary/supply model, Architecture, Rights & claims, Primary risks}')
table(['Dimension','Question','Representative fields'],[
('Economic function','What service does holding or using the token provide?','money; settlement; compute; security; intermediation; governance; access; claim'),
('Value accrual','Why could incremental activity create token demand or reduce net supply?','VA_* indicators; directness; strength; activation date'),
('Supply model','How are units issued, burned, unlocked, or capped?','cap; issuance; burn; inflation; unlocks; circulating/fully diluted supply'),
('Architecture','Where and how does it operate?','L1/L2/app; consensus; bridges; native vs issued; upgrade control'),
('Rights & claims','What is legally or programmatically enforceable?','redemption; collateral; cash flow; governance; equity; debt; none'),
('Primary risks','What breaks value or convertibility?','market; liquidity; credit; counterparty; smart contract; governance; regulatory')],[1.2,2.4,3.1],8.2)
p('Primary economic functions',style='Heading 2')
table(['Function','Description','Examples / analogues'],[
('Money / settlement','Transfer, unit of account within a system, liquidity bridge, or store of value','BTC, USDC, USDT / currency or monetary asset'),
('Network infrastructure','Pays for blockspace/computation and/or secures consensus','ETH, SOL, AVAX / infrastructure plus commodity'),
('Financial intermediation','Coordinates lending, trading, liquidity, or risk transfer','AAVE, UNI, CRV / financial service'),
('Governance','Controls protocol parameters, treasury, upgrades, or delegates','UNI, ARB, SKY / voting or control right'),
('Utility / access','Required to consume an identifiable service','LINK, FIL / service credit or commodity'),
('Investment / claim','Represents contractual financial or economic rights','tokenized debt/equity, redeemable stablecoins / security or deposit-like claim')],[1.3,3.0,2.4],8.2)

p('3. Stablecoin and cryptoasset categories',style='Heading 1')
p('Stablecoin structural classes',style='Heading 2')
table(['Code','Class','Stabilization mechanism','Illustrative assets','Dominant risks'],[
('S1','Fiat/reserve-backed','Issuer holds off-chain reserves and offers primary-market issuance/redemption','USDC, USDT, PYUSD, FDUSD, RLUSD','reserve credit/liquidity, custody, issuer, legal claim, redemption friction'),
('S2','Crypto-overcollateralized','On-chain collateral above liabilities; liquidation and peg facilities','USDS, GHO','collateral gap, oracle, liquidation, governance, smart contract'),
('S3','Synthetic / hedged','Long backing plus offsetting derivatives or other hedge','USDe','basis/funding, exchange/custodian, hedge slippage, liquidity'),
('S4','Algorithmic / reflexive','Endogenous mint/burn or seigniorage mechanism without exogenous full reserve','historical UST-style systems','death spiral, endogenous collateral, confidence/run'),
('S5','Asset/commodity-referenced','Redeemable or economically linked to non-fiat reference asset','PAXG','custody, assay/title, redemption, tracking error')],[.45,1.15,2.25,1.15,1.75],7.6)
source('International policy work emphasizes reserve quality, liquidity, segregation, legal claims, and timely redemption','https://www.bis.org/cpmi/publ/d220.pdf')
p('Stablecoin example map (initial universe; verify at each observation date)',style='Heading 2')
table(['Asset','Class','Backing / mechanism','Primary redemption','Holder yield','Key measurement note'],[
('USDC','S1','cash, short Treasuries, overnight Treasury repo/MMF structures','eligible account holders; 1:1 issuer process','No at token level','separate reserve income from holder return'),
('USDT','S1','reported reserve portfolio','verified primary customers; terms/minimum/fees apply','No at token level','code access, minimum, fee, timing separately'),
('PYUSD','S1','fiat deposits, Treasuries, cash equivalents','issuer/intermediary process','No at token level','issuer and distribution channels differ'),
('USDS','S2','diversified protocol collateral and peg facilities','protocol conversion routes','No; savings wrapper separate','do not assign wrapper yield to base token'),
('GHO','S2','Aave collateral architecture','protocol mechanisms','structure-dependent','facilitator and liquidation design are time-varying'),
('USDe','S3','crypto/stable backing plus derivatives hedges','approved primary process','No; sUSDe separate','funding, basis, counterparty, custody exposures'),
('UST (historical)','S4','reflexive conversion with LUNA','protocol conversion before failure','historical incentives','retain as failure case')],[.55,.45,1.75,1.45,.8,1.7],7.0)
source('Circle current reserve composition and issuance/redemption disclosure','https://www.circle.com/transparency')
p('Non-stable cryptoasset classes and value drivers',style='Heading 2')
table(['Class','Illustrative assets','Primary function','Candidate value-accrual channels'],[
('Monetary / PoW L1','BTC','censorship-resistant settlement and store of value','monetary demand; credible scarcity; security/settlement'),
('Smart-contract L1','ETH, SOL, AVAX, ADA, SUI, TON, TRX','blockspace, compute, settlement, security','gas; stake; burn; collateral; ecosystem demand'),
('L2 / scaling governance','ARB, OP','governance and ecosystem coordination','governance; incentive; possible protocol linkage'),
('DeFi protocol','UNI, AAVE, CRV, SKY','exchange, lending, liquidity, monetary governance','governance; protocol cash-flow linkage; utility; incentives'),
('Oracle / service infrastructure','LINK','data/service procurement and security','utility; staking; protocol/service demand'),
('Liquid-staking governance','LDO','governance of staking middleware','governance; protocol economics, if activated'),
('Ecosystem / exchange-linked','BNB','gas, staking, exchange/ecosystem utility','gas; stake; burns; utility; incentive')],[1.2,1.2,2.1,2.3],7.7)
source('Ethereum base fees are burned under EIP-1559','https://eips.ethereum.org/EIPS/eip-1559')
source('Bitcoin Core validates the protocol’s 21 million limit','https://bitcoin.org/en/bitcoin-core/features/validation')

p('4. Formal value-accrual codebook',style='Heading 1')
callout('Coding convention','Each VA variable is binary for the primary specification and accompanied by VA_*_strength ∈ {0,1,2}, evidence_url, evidence_date, activation_start, activation_end, coder, and confidence. “1” means the criterion is met during the coded period—not that price must rise.')
table(['Code','Set to 1 when…','Exclusions / evidence test'],[
('VA_MONETARY','The asset is materially used or explicitly held as medium of exchange, settlement asset, reserve/store of value, or unit of account; satisfy ≥2: meaningful transfer/settlement volume, broad venue/wallet acceptance, material long-horizon holdings, or credible monetary policy narrative supported by behavior.','Marketing alone fails. Stablecoins qualify if transactional/settlement use is observable; governance tokens do not qualify merely because transferable.'),
('VA_GAS','The native token is required by protocol rules to pay transaction, execution, storage, or blockspace fees for ordinary network use.','Optional fee discounts or payment via conversion wrappers do not qualify unless the token is protocol-required at settlement.'),
('VA_STAKE','Token must be locked/delegated or placed at slashable/economic risk to validate, secure, or provide protocol services, with active rewards/penalties.','Passive yield, liquidity mining, or non-security lockups excluded.'),
('VA_BURN','A live, rules-based mechanism irreversibly destroys tokens, and burn is linked to usage, revenue, or scheduled protocol action.','Discretionary buyback announcements without completed burns are strength 0; one-off burns are coded with dates.'),
('VA_SCARCITY','Supply has a credible hard cap or deterministic terminal bound that cannot be changed without exceptional consensus/governance; annualized dilution must also be reported.','A nominal max supply with routine governance override, large undisclosed unlocks, or rebasing does not earn strength 2.'),
('VA_COLLATERAL','Asset is accepted as collateral in economically material lending, derivatives, stablecoin, or security systems. Primary rule: collateral TVL ≥1% of circulating market cap or ≥$100m for ≥90 days; sensitivity uses 0.5%/$50m.','Wallet holdings, LP pairing, or staking alone excluded; wrapped representations consolidated to underlying.'),
('VA_GOV','Holding/delegating the token gives live, exercisable voting, proposal, veto, or treasury-control power.','Informal signaling only is strength 0; measure participation and concentration separately.'),
('VA_PROTOCOL','A live mechanism routes protocol revenue/economic surplus to holders through distribution, buyback/burn, fee discount funded by revenue, or treasury rights with an enforceable governance path.','Expected future fee switch or vague “ecosystem value” excluded from binary code; record as PROTOCOL_OPTION=1.'),
('VA_UTILITY','Token is technically or contractually required to consume a non-generic service beyond simple transfer—e.g., oracle payment, storage, identity, access, or resource purchase.','General tradability, governance alone, or speculative holding excluded.'),
('VA_INCENTIVE','Protocol systematically issues/distributes the token to subsidize desired behavior such as liquidity, usage, development, or participation.','Consensus staking issuance belongs in VA_STAKE unless a separable subsidy program exists; record gross incentives and net retention.')
],[1.0,3.45,2.25],7.35)
p('Strength scale and adjudication',style='Heading 2')
table(['Strength','Interpretation','Minimum evidence'],[('0','Absent, inactive, purely optional, or de minimis','primary source reviewed; criterion not met'),('1','Active but indirect, restricted, recently activated, or economically modest','primary source + at least one quantitative indicator'),('2','Active, direct, persistent, and economically material','primary source + ≥90 days of material observed use or contractual directness')],[.7,3.2,2.8],8.3)
bullets(['Two independent coders classify the initial sample; report Cohen’s κ by code.', 'Disagreements are adjudicated using the written rule, not token reputation.', 'Recode at protocol-upgrade, fee-switch, redemption-term, or material governance-change dates.', 'Primary regressions use preregistered binary rules; strength and alternate thresholds are robustness checks.'])

p('5. Rights and claims taxonomy',style='Heading 1')
table(['Code','Definition','Measurement fields / caution'],[
('CLAIM_REDEMPTION','Legally or contractually recognized right to exchange token with issuer/protocol for reference asset or reserve value.','eligible holder, par/NAV, settlement asset, minimum, fee, SLA, jurisdiction, suspension rights'),
('CLAIM_COLLATERAL','Identifiable claim against a collateral pool, including liquidation waterfall or pro-rata reserve interest.','priority, segregation, bankruptcy remoteness, overcollateralization, oracle/liquidation rules'),
('CLAIM_CASHFLOW','Right or live mechanism to receive protocol/issuer cash flows or equivalent distributions.','source, seniority, discretion, tokenholder eligibility, activation date'),
('CLAIM_GOVERNANCE','Formal control over proposals, parameters, treasury, upgrades, or delegates.','scope, quorum, delegation, admin override, voter concentration'),
('CLAIM_EQUITY','Legal ownership interest in an entity.','jurisdiction, issuer, share class, transfer restriction'),
('CLAIM_DEBT','Contractual principal/interest claim.','maturity, coupon, seniority, obligor, collateral'),
('CLAIM_NONE','No claim against issuer, reserves, cash flow, entity, or governance.','protocol-native ownership is not automatically a claim')],[1.2,3.0,2.7],7.7)
callout('Important separation','Economic exposure is not the same as a legal claim. A token may benefit from network demand without any claim on an issuer; a redeemable stablecoin may have a claim but no reserve yield; a governance token may control a treasury without an automatic cash-flow entitlement.')

p('6. Quantitative variables and empirical targets',style='Heading 1')
p('Stablecoin structural and calculated variables',style='Heading 2')
table(['Family','Variables'],[
('Design','peg_asset; backing_type; collateralization_ratio; centralized_issuer; direct_redemption; redemption_minimum; redemption_fee; settlement_time; suspension_rights; reserve_transparency; report_frequency; holder_yield; yield_source; multi_chain'),
('Peg','price; signed_deviation; absolute_peg_error; realized_peg_volatility; max_depeg; band_breach; duration; recovery_time; downside semivariance'),
('Liquidity','spot volume; bid–ask spread; depth ±10/50 bps; venue count; DEX liquidity; slippage; primary issuance/redemption flow'),
('Adoption','circulating supply; market share; transfer volume; active addresses; chain coverage; protocol/exchange integrations; velocity'),
('Risk','reserve-quality score; redemption-friction score; concentration; custodian/bank exposure; smart-contract incidents; oracle/bridge exposure')],[1.0,5.9],8.2)
formula('dᵢₜ = Pᵢₜ / Pegᵢₜ − 1     ;     APEᵢₜ = |dᵢₜ|     ;     Breachᵢₜ(b)=1{|dᵢₜ|>b}')
formula('TimeOutsideᵢ(b) = (1/Nᵢ) Σₜ 1{|dᵢₜ|>b},  b ∈ {10,25,50,100,500 bps}')
p('Cryptocurrency factor families',style='Heading 2')
table(['Factor','Candidate variables','Key construction issue'],[
('Network N','active/new addresses; transactions; adjusted transfer value; growth','filter bots, change addresses, sybil activity, internal transfers'),
('Economic E','fees; protocol revenue; holder revenue; TVL; DEX volume; stablecoin supply','avoid double counting; distinguish fees from revenue and tokenholder revenue'),
('Supply S','circulating supply; issuance; burn; net issuance; unlock rate; float/FDV','point-in-time supply definitions and vendor differences'),
('Security Q','hash rate; stake; staking ratio; validator count/concentration; slashing','cross-chain comparability and delegated stake concentration'),
('Liquidity L','volume; turnover; spread; depth; venue count; price impact','wash trading, offshore venue coverage, survivorship'),
('Adoption A','developers; commits; repos; apps; integrations; chain users','deduplicate forks and bots; developer identity continuity'),
('Macro M','BTC/market return; rates; VIX; dollar; equity factors; funding/liquidations','common shocks and endogenous risk appetite')],[1.0,3.6,2.3],7.7)
source('DeFiLlama distinguishes fees, protocol revenue, holder revenue, TVL, incentives, and chain activity','https://defillama.com/data-definitions')
p('Empirical targets',style='Heading 2')
table(['Universe','Primary dependent variables','Core question'],[
('Stablecoins','peg deviation; breach probability; depeg duration/recovery; market share; supply growth; settlement volume','Which design features improve robustness and adoption, especially in stress?'),
('Non-stable crypto','log market cap; returns/forward returns; realized volatility; valuation multiples; crash/drawdown risk','Which fundamentals matter, and only when the token captures activity?')],[1.2,3.1,2.6],8.2)
formula('log(MCapᵢₜ)=αᵢ+γₜ+β₁log(Usersᵢₜ)+β₂log(Feesᵢₜ)+β₃Liquidityᵢₜ+β₄SupplyGrowthᵢₜ+β₅Stakingᵢₜ+εᵢₜ')

p('7. Hypotheses H1–H8',style='Heading 1')
table(['ID','Hypothesis','Primary test / expected sign'],[
('H1','Network effects: greater economically valid usage is associated with higher market capitalization.','Panel FE; compare log-linear with quadratic/Metcalfe forms; βusers > 0.'),
('H2','Economic activity: fees/revenue predict value more strongly when VA_PROTOCOL or VA_BURN is active.','Fees × capture interaction > 0; compare gas tokens and governance-only tokens.'),
('H3','Supply: higher net issuance/unlocks predict lower forward returns, conditional on demand and market regime.','Local projections / panel return regressions; βnet issuance < 0.'),
('H4','Staking: higher staking ratio reduces liquid float but may widen spreads and has ambiguous return/volatility effects.','Estimate price, volatility, spread, and depth jointly; no forced one-sided sign.'),
('H5','Stablecoin reserves: higher liquid, low-credit-risk, short-duration reserve quality lowers depeg probability/severity.','Hazard/logit and panel APE; βreserve quality < 0.'),
('H6','Redemption: greater eligibility, fee, minimum, time, or suspension friction increases secondary-market deviations in stress.','Friction × stress > 0 in APE/breach models.'),
('H7','Stablecoin network effects: liquidity, integrations, and usage predict market share persistence and inflows.','Dynamic panel / share-change model; positive adoption coefficients.'),
('H8','Multi-function assets command a valuation premium only when functions are active and material.','Weighted VA breadth × quality; compare raw count; βbreadth > 0 after controls.')
],[.45,3.7,2.75],7.5)
p('Pre-specified falsification logic',style='Heading 2')
bullets(['Reject mechanism stories that rely on contemporaneous correlation alone; test lags, events, and placebo dates.', 'For H2 and H8, inactive or merely promised mechanisms form explicit negative controls.', 'For H5–H6, include failed stablecoins and test both normal and stress periods.', 'Report economic magnitudes, confidence intervals, within-R², out-of-sample performance, and multiple-testing adjusted q-values.'])

p('8. Reproducible data schemas',style='Heading 1')
p('General database conventions',style='Heading 2')
bullets(['Primary keys are stable internal IDs, never ticker symbols alone.', 'All time-varying design tables use valid_from and valid_to; open intervals use null valid_to.', 'All numeric fields carry units, frequency, source_id, retrieved_at_utc, and transformation version in lineage tables.', 'Unknown is null—not zero. Boolean 0 means reviewed and criterion not met.', 'Raw, staged, and analytical layers are immutable/versioned; transformations run from code and configuration.'])
p('asset_master',style='Heading 2')
table(['Field','Type','Definition'],[
('asset_id','string PK','stable internal identifier'),('symbol','string','point-in-time ticker; aliases in child table'),('asset_name','string','canonical name'),('asset_family','enum','stablecoin, L1, L2, DeFi, oracle, utility, claim, other'),('economic_function_primary','enum','principal economic service'),('economic_function_secondary','array/bridge','additional functions'),('layer','enum','L1, L2, app, off-chain claim, multi'),('native_chain_id','string FK','origin chain/network'),('contract_address','string nullable','checksummed address; chain-qualified'),('consensus','enum nullable','PoW, PoS family, other, NA'),('issuer_type','enum','none, corporate, foundation, DAO, protocol, SPV'),('launch_date','date','first economically live date'),('inactive_date','date nullable','failure/delisting/sunset date'),('status','enum','active, inactive, failed, migrated'),('source_id','string FK','authoritative evidence record')],[1.8,1.1,4.0],7.8)
p('economic_design (effective-dated)',style='Heading 2')
table(['Field group','Fields'],[
('Keys/time','asset_id; design_version; valid_from; valid_to'),('Value accrual binary','va_monetary; va_gas; va_stake; va_burn; va_scarcity; va_collateral; va_gov; va_protocol; va_utility; va_incentive'),('Strength','corresponding va_*_strength 0/1/2; va_breadth_count; va_breadth_weighted'),('Claims','claim_redemption; claim_collateral; claim_cashflow; claim_governance; claim_equity; claim_debt; claim_none'),('Supply','supply_model; max_supply; cap_credibility; issuance_rule; burn_rule; unlock_rule'),('Control','upgrade_authority; admin_key; governance_activation; concentration metric'),('Evidence','evidence_url; evidence_date; coder; reviewer; confidence; rationale; created_at')],[1.55,5.35],8.0)
p('stablecoin_design (effective-dated)',style='Heading 2')
table(['Field group','Fields'],[
('Keys/time','asset_id; design_version; valid_from; valid_to'),('Reference','peg_asset; peg_value; peg_currency; target_type'),('Backing','backing_class S1–S5; reserve_type; reserve_asset_breakdown; collateralization_target; hedge_type'),('Issuer/control','issuer; issuer_jurisdiction; centralized_issuer; protocol_governance'),('Redemption','direct_redemption; eligibility; KYC; min_amount; fee_fixed; fee_bps; settlement_target; hours; suspension/gating; in_kind_right'),('Yield','holder_yield; wrapper_required; yield_source; yield_variable'),('Transparency','attestation/audit; provider; frequency; lag_days; asset granularity; liability coverage'),('Risk scores','reserve_quality_score; redemption_friction_score; transparency_score; backing_concentration; counterparty_concentration'),('Evidence','terms_url; reserve_report_url; evidence_date; coder; reviewer; confidence')],[1.55,5.35],7.7)
p('Required companion tables',style='Heading 2')
table(['Table','Purpose'],[('source_registry','URL/provider, license, frequency, access method, retrieved_at, checksum'),('asset_alias','symbol/name/contract migrations by date'),('market_observation','price, market cap, volume, venue, quote, timestamp, vendor'),('network_observation','on-chain usage/security/supply metrics'),('stablecoin_reserve_snapshot','reported reserve weights and attributes by report date'),('event_registry','depegs, hacks, freezes, bank/custodian events, upgrades, governance actions'),('classification_log','old/new code, reason, evidence, coder, adjudicator, timestamp')],[1.8,5.1],8.2)

p('9. Stablecoin backing and redemption codebook',style='Heading 1')
p('Backing classification',style='Heading 2')
table(['Variable','Allowed values','Rule'],[
('backing_class','S1/S2/S3/S4/S5','classify economic stabilization mechanism, not branding'),('reserve_type','cash; bank deposit; T-bill; repo; MMF; bond; loan; CP/CD; crypto; stablecoin; commodity; derivative receivable; other','code market-value weights from latest eligible report'),('collateral_location','off-chain; on-chain; hybrid','where enforceable backing resides'),('collateralization_basis','par; market value; risk-adjusted; protocol oracle','denominator and valuation method must be stored'),('segregation','verified; asserted; absent; unknown','verified requires legal/audit evidence, not website language alone'),('bankruptcy_remoteness','verified; asserted; absent; unknown','jurisdiction-specific legal analysis; never infer from segregation'),('hedge_coverage','gross delta; net delta; basis; venue/custodian shares','for S3; record methodology and frequency')],[1.3,2.2,3.4],7.8)
p('Redemption classification',style='Heading 2')
table(['Code','Definition'],[
('R0 — none','No functioning redemption into reference asset; secondary-market exit only.'),('R1 — protocol/open','Any holder can use an on-chain mechanism, subject only to protocol fees/limits.'),('R2 — issuer/direct broad','Eligible verified customers can redeem directly; access is broadly available in stated jurisdictions.'),('R3 — issuer/direct restricted','Whitelisting, institutional status, geography, minimum size, banking access, or material onboarding restricts access.'),('R4 — intermediated','Most holders rely on exchanges, market makers, or authorized participants; no direct claim/process for ordinary holders.'),('R5 — discretionary/gated','Issuer/protocol retains or has exercised material suspension, delay, in-kind, quota, or gate rights.')],[1.35,5.55],8.1)
p('Redemption-friction score (0 best; 100 worst)',style='Heading 2')
table(['Component','Weight','Example scoring anchors'],[
('Access/eligibility','25','0 open; 10 standard KYC broad; 25 institutional/whitelist/geographic constraint'),('Minimum size','15','0 none/de minimis; 5 ≤$10k; 10 $10k–$100k; 15 >$100k'),('Explicit fee','15','0 none; scale by effective bps for standard ticket; cap 15'),('Settlement time/hours','15','0 near-real-time/24×7; 5 same day; 10 1–2 business days; 15 longer/unclear'),('Suspension/gating/in-kind rights','20','0 narrow/none; 10 conditional; 20 broad or exercised'),('Operational dependence','10','0 protocol/open; 5 single issuer rail; 10 multiple intermediaries/manual uncertainty')],[2.0,.65,4.25],7.8)
formula('RedemptionFriction = Σⱼ wⱼ sⱼ, normalized to [0,100]; retain every component for interpretation')

p('10. Reserve-quality scoring framework',style='Heading 1')
callout('Purpose','Create a transparent, reproducible explanatory variable—not a credit rating. Score the disclosed portfolio and institutional safeguards separately; use missing-data penalties and sensitivity ranges rather than false precision.')
p('A. Asset-level quality score',style='Heading 2')
table(['Dimension','Weight','High score','Low score'],[
('Liquidity under stress','25','cash/central-bank money, very short sovereign bills, reliable same-day monetization','illiquid credit, loans, thin crypto, long settlement'),('Credit quality','20','sovereign/central-bank or high-quality secured exposure','unrated/high-yield, affiliated or opaque exposure'),('Duration / market risk','15','very short duration and low price volatility','long duration, material convexity/basis/FX risk'),('Valuation certainty','10','observable prices, daily mark, simple instruments','model-valued, stale, complex, disputed'),('Currency/peg match','10','same currency and no unhedged basis','material FX or reference-asset mismatch'),('Concentration/diversification','10','diversified custodians/banks/issuers within safe asset set','single weak counterparty or correlated concentration'),('Encumbrance/availability','10','unencumbered and immediately available','pledged, rehypothecated, operationally unavailable')],[1.8,.55,2.4,2.0],7.5)
formula('AssetQualityₜ = Σₖ wₖ qₖₜ ;  PortfolioQualityₜ = Σₐ ReserveWeightₐₜ × AssetQualityₐₜ')
p('B. Institutional safeguards adjustment',style='Heading 2')
table(['Adjustment','Range','Rule'],[('Coverage','−20 to +5','market value / token liabilities; haircut stressed assets'),('Segregation & bankruptcy remoteness','−15 to +5','verified legal protection scores highest; unknown is not verified'),('Transparency & assurance','−10 to +5','frequency, lag, granularity, independent assurance, liabilities included'),('Custody/operational resilience','−10 to +5','custodian quality, access, concentration, settlement continuity')],[2.2,.8,3.9],8.0)
formula('ReserveQuality = clamp(PortfolioQuality + SafeguardsAdjustment, 0, 100)')
p('Scoring implementation rules',style='Heading 2')
bullets(['Use the reserve report available to the market at time t—not a later restatement—to avoid look-ahead bias.', 'Map every reserve line item to a scoring bucket; disclose unmapped weight.', 'For “other” or undisclosed assets, use a conservative base score and report optimistic/pessimistic bounds.', 'Stress haircuts should draw from HQLA/liquidity principles but remain a research specification, not regulatory equivalence.', 'Report both composite and components; test whether liquidity, transparency, or legal safeguards drive results.'])
source('BIS/CPMI guidance highlights duration, credit quality, liquidity, concentration, segregation, and timely redemption','https://www.bis.org/cpmi/publ/d220.pdf')
source('BIS research models interactions among information, reserve quality, volatility, and run risk','https://www.bis.org/publ/work1164.htm')

p('11. Depeg-risk measurement framework',style='Heading 1')
p('Price construction hierarchy',style='Heading 2')
numbered(['Normalize each venue quote to the peg currency; convert non-USD quotes with synchronized FX/reference rates.', 'Remove stale, zero-volume, and mechanically bad observations using preregistered filters.', 'Prefer volume-capped, liquidity-weighted venue median; cap any venue’s weight to limit manipulation.', 'Construct CEX and DEX series separately, then a composite; preserve source-level prices.', 'Use intraday data for event metrics and daily VWAP/median for long panels; do not mix frequencies silently.'])
p('Outcome definitions',style='Heading 2')
table(['Metric','Definition','Use'],[
('Signed deviation dₜ','Pₜ/Pegₜ − 1','direction; discount vs premium'),('Absolute peg error','|dₜ|','continuous stability loss'),('Band breach','1{|dₜ| > b}, b=10/25/50/100/500 bps','comparable event threshold'),('Depeg onset','first of k consecutive observations outside b after clean window','reduces microstructure false positives'),('Duration','time until m consecutive observations back inside recovery band','survival/recovery analysis'),('Maximum adverse excursion','largest discount during episode','severity'),('Area under depeg','Σ |dₜ|Δt during episode','joint severity and duration'),('Downside semivariance','E[min(dₜ,0)²]','focus on loss of par'),('Liquidity stress','spread, depth, price impact, volume imbalance','distinguish price signal from market impairment')],[1.55,2.75,2.6],7.8)
p('Baseline event rule',style='Heading 2')
callout('Primary definition','A 50-bps depeg begins after three consecutive 5-minute composite observations outside ±50 bps, following at least one hour inside ±25 bps. Recovery requires twelve consecutive 5-minute observations inside ±25 bps. Daily panels use closing/median breach and episode carry-forward. Thresholds are robustness variants.')
p('Depeg-risk models',style='Heading 2')
formula('Pr(Breachᵢₜ=1)=logit⁻¹(αᵢ+γₜ+β₁ReserveQualityᵢ,ₜ₋₁+β₂Frictionᵢ,ₜ₋₁+β₃Liquidityᵢ,ₜ₋₁+β₄Stressₜ+β₅Friction×Stress)')
formula('hᵢ(τ|X)=h₀(τ)exp(Xβ)  for onset or recovery hazards; cluster by asset and episode')
bullets(['Use two-way fixed effects where variation permits; correlated random effects or between estimators for slow-moving designs.', 'For major shocks (SVB/USDC, Terra, custody/exchange failures), use event studies with clearly defined information times.', 'Competing-risk labels distinguish issuer/reserve, collateral, protocol/oracle, venue liquidity, regulatory, and market-wide events.', 'Validate composite prices against issuer mint/redeem data where available and triangulate vendors.'])

p('12. Phase 2 data-source plan',style='Heading 1')
table(['Data domain','Preferred source class','Frequency','Fields / use','Risks & controls'],[
('Prices, market cap, supply','CoinGecko or licensed institutional vendor; exchange APIs for intraday','5-min/daily','price, cap, volume, supply, venue quotes','vendor methodology; stale/false volume; triangulate and snapshot'),
('DeFi/protocol economics','DeFiLlama APIs/exports plus protocol dashboards','daily','TVL, fees, revenue, holder revenue, incentives, stablecoin supply','definition drift; store metric definition/version'),
('On-chain network','native nodes/indexers, Dune/Flipside/Token Terminal as available','daily/weekly','addresses, tx, fees, flows, staking, validators','sybil/bot/internal transfers; chain-specific cleaning'),
('Supply/unlocks','protocol contracts/docs, Tokenomist or equivalent','daily/event','issuance, burn, unlocks, circulating/FDV','revisions and vesting ambiguity'),
('Stablecoin reserves','issuer reports, attestations/audits, regulator filings','report date','asset weights, liabilities, custodians, assurance','publication lag; effective-date and known-at date both stored'),
('Redemption terms','issuer terms/APIs/help centers; protocol contracts/docs','event-sourced','eligibility, min, fee, timing, gates','terms change; archive snapshots'),
('Liquidity/order books','major CEX/DEX APIs or licensed vendor','minute/hour','spread, depth, price impact, slippage','coverage/license; wash trading'),
('Macro/market','FRED, Treasury, Cboe/market vendors','daily','rates, DXY, VIX, equities, credit, FX','calendar/time-zone alignment'),
('Development','GitHub API + curated repo map','weekly/monthly','developers, commits, releases','forks, bots, repo changes'),
('Events/legal','official notices, court/regulator records, protocol postmortems','event','event time/type/severity','timestamp ambiguity; two-source verification')
],[1.15,1.65,.65,1.7,1.65],6.8)
source('CoinGecko API documentation','https://docs.coingecko.com/')
source('DeFiLlama definitions','https://defillama.com/data-definitions')
p('Data acquisition sequence',style='Heading 2')
numbered(['Freeze the research universe and observation window; include active, failed, migrated, and delisted assets.', 'Complete point-in-time design coding and source registry before outcomes are modeled.', 'Pull raw data into dated immutable partitions; log request parameters, retrieval time, status, and checksum.', 'Normalize identifiers, timestamps (UTC), units, chain/contract mappings, and quote currency.', 'Run automated QA: uniqueness, continuity, missingness, stale prices, supply jumps, cross-source tolerances.', 'Build analysis-ready panels only through version-controlled transformations; publish a machine-readable data dictionary.', 'Create a frozen preregistration snapshot before headline estimation.'])
p('Recommended initial sample and windows',style='Heading 2')
bullets(['Stablecoins: top assets by historical market cap plus all economically relevant failures; monthly membership to reduce survivorship bias.', 'Cryptoassets: stratified panel across monetary L1, smart-contract L1, L2 governance, DeFi, oracle/service, and ecosystem tokens.', 'Daily panel for 2019–2026 where data permit; intraday stablecoin event panel for selected stress episodes.', 'Minimum-history rules should be outcomes-neutral and reported with excluded-asset diagnostics.'])

p('13. Phase 2 empirical-analysis plan',style='Heading 1')
table(['Workstream','Question','Primary design','Robustness'],[
('A. Taxonomy validation','Do codes cluster into coherent economic archetypes?','descriptive cross-tabs; PCA/MCA; inter-rater reliability','alternate thresholds; leave-one-code-out'),
('B. Stablecoin peg risk','Do reserves and redemption predict breaches and recovery?','panel logit/LPM; FE APE; Cox/AFT duration','bands/frequencies; CEX vs DEX; rare-event logit'),
('C. Stablecoin adoption','What predicts share/inflows?','dynamic panel; fractional response; flow regressions','lag structures; market stress; chain fixed effects'),
('D. Crypto valuation','Do users, fees, capture, supply, and liquidity explain market cap?','asset/time FE; correlated RE for slow design variables','Fama–MacBeth; alternative market cap/supply; winsorization'),
('E. Forward returns','Do issuance/unlocks and activity changes predict returns?','panel predictive regressions; local projections','Newey–West/two-way clusters; market/beta controls'),
('F. Mechanism events','What happens when burn, fee switch, staking, or redemption terms activate?','event study / difference-in-differences','pre-trends; matched controls; placebo dates'),
('G. Out-of-sample','Does economic design improve prediction?','rolling/expanding windows; nested models','time-series CV; no random shuffle; calibration')
],[1.0,1.65,2.25,2.0],7.2)
p('Identification and inference',style='Heading 2')
bullets(['Most results are associational unless a credible event or instrument supports causal interpretation.', 'Lag design and reserve variables by their public-availability date; never backfill information before disclosure.', 'Use asset and time fixed effects, chain/sector trends where justified, and two-way clustered or Driscoll–Kraay errors as appropriate.', 'Address endogeneity with event timing, pre-trends, instrumental variables only where defensible, and explicit sensitivity analysis.', 'Winsorization thresholds, transformations, and missing-data treatment are preregistered; report untrimmed results.', 'Control false discovery across hypothesis families and clearly label exploratory results.'])
p('Minimum viable analysis deliverables',style='Heading 2')
table(['Deliverable','Acceptance criterion'],[('Phase 1 frozen codebook','all assets coded with dated evidence; κ reported; disputes resolved'),('Stablecoin panel','price and design history with episode labels and QA report'),('Crypto panel','daily/monthly fundamentals with lineage and missingness map'),('Descriptive atlas','coverage, distributions, correlations, and failure cases'),('H1–H8 model pack','primary + preregistered robustness tables, diagnostics, effect sizes'),('Reproducibility bundle','environment lock, scripts, config, checksums, codebook, README')],[1.8,5.1],8.1)

p('14. Validation, governance, and limitations',style='Heading 1')
p('Quality gates',style='Heading 2')
table(['Gate','Test'],[('Classification','two-coder agreement; evidence completeness; point-in-time validity'),('Identity','chain-qualified contract; migrations and wrapped assets reconciled'),('Market data','cross-vendor price tolerance; stale/zero-volume filters; outlier review'),('Accounting','fees ≠ revenue ≠ tokenholder revenue; flows and stocks not mixed'),('Time','UTC normalization; disclosure-known date; no look-ahead'),('Models','residuals, influence, multicollinearity, serial/cross-sectional dependence, calibration'),('Reproduction','clean run from frozen raw snapshot; output hashes and environment captured')],[1.3,5.6],8.2)
p('Known limitations',style='Heading 2')
bullets(['Token design is endogenous to adoption and governance; simple regressions cannot establish causal value capture.', 'On-chain activity may be sybil-driven, automated, bridged, or internally generated.', 'Market cap uses circulating-supply estimates that differ across vendors and may overstate realizable value.', 'Reserve disclosures vary in frequency, granularity, assurance, and legal meaning.', 'Redemption access for eligible primary customers differs from economic exit liquidity for ordinary holders.', 'Composite scoring compresses heterogeneous risks; component results must accompany the headline score.', 'Regulation and legal claims are jurisdiction- and transaction-specific and can change rapidly.'])
p('Decision log for next notebook revision',style='Heading 2')
table(['Decision','Owner','Due before'],[('Finalize asset universe and historical membership rule','Researcher','first production extract'),('Select primary market/on-chain vendors and confirm licenses','Researcher + adviser','data acquisition'),('Approve reserve-score anchors and missing-data penalty','Researcher + adviser','stablecoin coding'),('Pre-register primary windows, bands, and model families','Researcher','headline estimation'),('Confirm repository/reproducibility requirements with NYU adviser','Researcher','submission packaging')],[2.9,1.5,2.5],8)

p('Appendix A. Illustrative value-accrual classifications',style='Heading 1')
p('These are baseline examples, not final point-in-time dataset entries. Each must be verified against dated primary evidence.',italic=True,color=MUTED)
table(['Asset','MON','GAS','STAKE','BURN','SCAR','COLL','GOV','PROT','UTIL','INC','Notes'],[
('BTC',1,0,0,0,1,1,0,0,0,0,'collateral subject to materiality threshold'),('ETH',1,1,1,1,0,1,0,1,1,0,'base fee burn; staking; protocol-native use'),('SOL',0,1,1,1,0,1,0,1,1,0,'verify burn rule and collateral materiality by date'),('UNI',0,0,0,0,0,0,1,0,0,1,'protocol option recorded separately if fee switch inactive'),('AAVE',0,0,0,0,0,0,1,1,1,1,'security/governance mechanisms are time-varying'),('LINK',0,0,1,0,0,0,0,1,1,1,'service utility and staking; verify activation scope'),('USDC',1,0,0,0,0,1,0,0,0,0,'redemption/collateral claims coded separately')
],[.65,.33,.33,.38,.38,.38,.38,.36,.38,.36,.36,1.9],6.5)
p('Appendix B. Variable naming and transformation rules',style='Heading 1')
table(['Rule','Standard'],[('Case','snake_case'),('Booleans','0/1; null = not known/not reviewed'),('Dates','ISO 8601; timestamps UTC'),('Currency','ISO code plus quote/reference asset'),('Amounts','raw native units and normalized USD field stored separately'),('Returns','log returns by default; simple returns for economic interpretation'),('Supply growth','log difference; annualization method explicit'),('Outliers','flag first; never silently delete'),('Revisions','append/version; do not overwrite raw or design history'),('Provenance','source_id + retrieved_at + checksum + transformation_version')],[1.7,5.2],8.2)
p('Appendix C. Selected authoritative and methodological sources',style='Heading 1')
refs=[
('BIS Working Paper 1164, Public information and stablecoin runs (2024; revised 2025)','https://www.bis.org/publ/work1164.htm'),
('BIS FSI Insights 57, Stablecoins: regulatory responses to their promise of stability (2024)','https://www.bis.org/fsi/publ/insights57.htm'),
('CPMI, Considerations for stablecoin arrangements in cross-border payments (2023)','https://www.bis.org/cpmi/publ/d220.pdf'),
('IMF, Understanding Stablecoins (2025)','https://www.imf.org/en/-/media/files/publications/dp/2025/english/usea.pdf'),
('IMF WP, From Par to Pressure: Liquidity, Redemptions, and Fire Sales with a Systemic Stablecoin (2026)','https://www.elibrary.imf.org/abstract/journals/001/2026/005/001.2026.issue-005-en.xml'),
('Circle, USDC transparency and reserve composition','https://www.circle.com/transparency'),
('Ethereum Improvement Proposal 1559','https://eips.ethereum.org/EIPS/eip-1559'),
('Ethereum.org, proof-of-stake documentation','https://ethereum.org/developers/docs/consensus-mechanisms/pos/'),
('Bitcoin Core validation','https://bitcoin.org/en/bitcoin-core/features/validation'),
('DeFiLlama data definitions','https://defillama.com/data-definitions'),
('CoinGecko API documentation','https://docs.coingecko.com/')]
for i,(a,u) in enumerate(refs,1): p(f'{i}. {a}. {u}',size=8.5)
p('Source-use rule',style='Heading 2')
p('Issuer and protocol sources establish design and stated rights; independent data and institutional research evaluate outcomes and risk. A source’s inclusion does not imply endorsement. All web facts and classifications must be rechecked at the observation date and before final submission.')

# footer font
for section in doc.sections:
    for para in section.footer.paragraphs:
        for run in para.runs: run.font.name='Aptos'; run.font.size=Pt(8); run.font.color.rgb=RGBColor.from_string(MUTED)

doc.core_properties.title='Digital Asset Valuation — Living Research Notebook'
doc.core_properties.subject='Economic taxonomy, measurement codebook, and empirical research design'
doc.core_properties.author='NYU Financial Engineering Research Project'
doc.core_properties.keywords='digital assets, stablecoins, cryptocurrency, valuation, taxonomy, empirical finance'
doc.save(OUT)
print(OUT)
