/**
 * Builds the Phase 1 expert panel survey as a Google Form.
 *
 * HOW TO RUN
 *  1. Go to script.google.com and choose New project.
 *  2. Delete the sample code, paste this whole file in, and save.
 *  3. Press Run and pick buildSurvey. Approve the permission prompt
 *     (it asks for Forms access because it is creating a form for you).
 *  4. The execution log prints the edit URL and the public link.
 *
 * Re-running creates a SECOND form. To edit instead, open the one you made.
 */

function buildSurvey() {
  var form = FormApp.create('Cryptoasset Economic Function — Expert Panel')
    .setDescription(
      'An academic research panel on how cryptoassets should be classified by economic function.\n\n' +
      'About 12 minutes. There are no right answers to most of this — we are trying to establish where informed practitioners actually draw the lines, because those lines change what a study concludes.\n\n' +
      'Responses inform a working paper on cryptoasset economic classification. We will send you the findings. Individual responses are reported only in aggregate.')
    .setCollectEmail(false)
    .setProgressBar(true)
    .setShowLinkToRespondToAgain(false);

  var scale5 = function (item, low, high) { return item.setBounds(1, 5).setLabels(low, high); };

  // ---------------------------------------------------------------- Section 0
  form.addSectionHeaderItem().setTitle('About you')
    .setHelpText('Four quick questions so we can weight answers by background.');

  form.addMultipleChoiceItem().setTitle('Which best describes your role?').setRequired(true)
    .setChoiceValues(['Asset or wealth management', 'Financial advisory', 'Research or analytics',
      'Protocol or foundation', 'Exchange, custody or market infrastructure', 'Academic', 'Other']);

  form.addMultipleChoiceItem().setTitle('Years working with digital assets professionally').setRequired(true)
    .setChoiceValues(['Under 2', '2 to 5', '5 to 8', 'Over 8']);

  scale5(form.addScaleItem().setTitle('How familiar are you with protocol-level mechanics such as fee burns, staking design and issuance schedules?')
    .setRequired(true), 'Not familiar', 'I read protocol docs regularly');

  form.addMultipleChoiceItem().setTitle('Do you make or advise on allocation decisions in digital assets?')
    .setRequired(true).setChoiceValues(['Yes', 'No']);

  // ---------------------------------------------------------------- Section 1
  form.addPageBreakItem().setTitle('How you frame a cryptoasset')
    .setHelpText('We are testing whether economic function is a useful organising axis at all.');

  var frames = ['Technical architecture (Layer 1, Layer 2, rollup)',
    'Sector label (DeFi, infrastructure, gaming, payments)',
    'Economic function (what the token is used for and what accrues to it)',
    'Market capitalisation tier', 'Regulatory or legal status'];
  form.addGridItem().setTitle('How useful is each frame for organising your thinking about a cryptoasset?')
    .setRequired(true).setRows(frames)
    .setColumns(['1 Not useful', '2', '3', '4', '5 Essential']);

  var functions = ['Monetary use — used as money, settlement or a store of value',
    'Fee requirement — you must spend it to use the network',
    'Staking — locked or at risk to secure something',
    'Burn — usage permanently destroys supply',
    'Hard cap — a terminal supply limit that is very hard to change',
    'Collateral — accepted as material collateral elsewhere',
    'Governance — holding it gives real control',
    'Revenue capture — protocol revenue mechanically reaches the token',
    'Service utility — required to buy an identifiable service',
    'Incentives — a programme subsidises usage or participation'];
  form.addGridItem().setTitle('How much SHOULD each economic function matter to what a token is worth?')
    .setHelpText('Your view, not what the market currently prices.')
    .setRequired(true).setRows(functions)
    .setColumns(['1 Irrelevant', '2', '3', '4', '5 Decisive']);

  form.addParagraphTextItem()
    .setTitle('Is anything missing from that list of ten, or is anything on it redundant?');

  form.addMultipleChoiceItem().setTitle('Should technical architecture be treated as part of a token’s economic profile, or kept separate as context?')
    .setChoiceValues(['Part of the economic profile', 'Kept separate as context', 'Depends']);

  // ---------------------------------------------------------------- Section 2
  form.addPageBreakItem().setTitle('Where the lines sit')
    .setHelpText('Six short scenarios. Assets are deliberately unnamed so you judge the mechanism rather than the brand. Pick the closest answer, then give us one line of reasoning.');

  var scenario = function (title, help, choices) {
    form.addMultipleChoiceItem().setTitle(title).setHelpText(help).setRequired(true).setChoiceValues(choices);
    form.addTextItem().setTitle('Why? One line.');
  };

  scenario('Does the token capture value from that revenue?',
    'A protocol earns real revenue from usage. The revenue accumulates in a treasury. Token holders vote on how it is spent. The evidenced spending funds ecosystem grants, infrastructure and developer salaries. There is no burn, no buyback and no distribution to holders.',
    ['Yes, this is value capture', 'No, this is a governance right only', 'Depends']);

  scenario('Does the token capture value from usage?',
    'Every transaction on a network permanently destroys a portion of the native token by protocol rule. Nobody receives the destroyed tokens. Supply falls.',
    ['Yes, this is value capture', 'No', 'Depends']);

  scenario('For a classification made today, is the mechanism active?',
    'A protocol funded buybacks of its own token for twelve months. Governance paused the programme three months ago. The mechanism still exists in the code and could be restarted by a vote.',
    ['Active', 'Not active', 'Partially active']);

  scenario('Is the native token required in order to transact?',
    'On a particular chain, a transaction paying zero fee is valid under the consensus rules. Block producers simply choose not to include such transactions, so in practice everyone pays a fee.',
    ['Yes, required in substance', 'No, required only by convention', 'Depends']);

  scenario('Is that value accruing to the token, or payment for a service?',
    'Stakers receive newly issued tokens for securing a network. The tokens are newly created rather than transferred from fee revenue.',
    ['Value accruing to the token', 'Payment for a service rendered', 'Depends']);

  scenario('Is that economically equivalent to destroying them?',
    'Fees collected by a network are moved into an account that nobody controls and from which nothing can ever be spent. Total supply is unchanged, but the tokens are permanently immobilised.',
    ['Equivalent to destruction', 'Not equivalent', 'Depends']);

  // ---------------------------------------------------------------- Section 3
  form.addPageBreakItem().setTitle('Where materiality begins')
    .setHelpText('This is the section your judgement matters most for. We have to set thresholds and they should not be ours alone.');

  form.addMultipleChoiceItem().setTitle('At what point would you say an asset is materially used as collateral?')
    .setRequired(true).setChoiceValues(['Any observable use', 'Above USD 100m outstanding',
      'Above 1% of its own market cap', 'Above 5% of its own market cap',
      'Both a dollar floor and a percentage floor']).showOtherOption(true);

  form.addCheckboxItem().setTitle('What evidence would convince you a cryptoasset is genuinely used as money rather than merely traded?')
    .setHelpText('Select all that would count.').setRequired(true)
    .setChoiceValues(['Merchant or payment acceptance at scale',
      'On-chain transfer value large relative to market cap',
      'Held as a reserve asset by institutions or treasuries',
      'Used as a unit of account for pricing',
      'Material remittance or cross-border corridor volume',
      'Sustained non-speculative transaction counts',
      'None of these are sufficient on their own']).showOtherOption(true);

  form.addMultipleChoiceItem().setTitle('How long must a mechanism be live before you would count it in a classification?')
    .setRequired(true).setChoiceValues(['No minimum, count it from activation', '30 days', '90 days', '180 days', 'A full year']);

  form.addMultipleChoiceItem().setTitle('Should these functions be recorded as yes or no, or on a scale?')
    .setRequired(true).setChoiceValues(['Binary yes or no',
      'Three levels: none, partial, material', 'A continuous intensity score',
      'It depends by function']);

  form.addMultipleChoiceItem().setTitle('If evidence for a function is unavailable or ambiguous, what should the classification record?')
    .setRequired(true).setChoiceValues(['Record it as absent',
      'Record it as unknown and exclude the asset from tests using it',
      'Record a best estimate with a confidence flag']).showOtherOption(true);

  // ---------------------------------------------------------------- Section 4
  form.addPageBreakItem().setTitle('What would actually be useful')
    .setHelpText('Three questions on the output, then you are done.');

  form.addMultipleChoiceItem().setTitle('Which would be most useful in your work?')
    .setRequired(true).setChoiceValues([
      'A model estimating fair value from a token’s functions',
      'A model estimating risk profile — market sensitivity, drawdown, volatility — from its functions',
      'The classification itself, applied by me',
      'A screening tool that flags mismatches between price and function',
      'None of these']);

  form.addParagraphTextItem()
    .setTitle('Suppose a classification told you an asset is monetary, collateral-eligible and supply-capped, with no revenue capture. What, if anything, would you do differently?');

  form.addCheckboxItem().setTitle('What would make you trust a classification produced by researchers rather than a data vendor?')
    .setChoiceValues(['Published rules', 'Primary sources cited for every decision',
      'A second independent reviewer and a published agreement statistic',
      'Open code that regenerates every number', 'Named authors and institution',
      'A track record of predictions', 'Nothing would, I would use a vendor']).showOtherOption(true);

  form.addParagraphTextItem()
    .setTitle('Anything you would want this research to answer that it currently does not?');

  // ---------------------------------------------------------------- Section 5
  var blind = form.addPageBreakItem().setTitle('Optional: blind classification exercise')
    .setHelpText('About 20 minutes, and only worth doing if you read protocol documentation regularly.\n\n' +
      'Score each cell using only the rule text and your own knowledge. Please do not look up our answers. ' +
      'If you do not know, choose Unknown — a guess is worse than a gap here, because we are measuring agreement.');

  form.addMultipleChoiceItem().setTitle('Would you like to do the optional blind scoring exercise?')
    .setRequired(true).setChoiceValues(['Yes, continue', 'No, submit now']);

  var cells = [
    ['Litecoin', 'FEE REQUIREMENT: the token is protocol-required to pay ordinary transaction fees. Relay policy and optional discounts do not qualify.'],
    ['Dogecoin', 'BURN: a live rules-based mechanism irreversibly destroys tokens.'],
    ['Hedera (HBAR)', 'BURN: a live rules-based mechanism irreversibly destroys tokens.'],
    ['Chainlink (LINK)', 'REVENUE CAPTURE: a live mechanical route sends protocol revenue to the token or holders through distribution, buyback, burn or an enforceable claim. Governance over ecosystem spending alone does not qualify.'],
    ['Optimism (OP)', 'REVENUE CAPTURE: as above.'],
    ['Stellar (XLM)', 'BURN: as above.'],
    ['Cardano (ADA)', 'REVENUE CAPTURE: as above.'],
    ['Solana (SOL)', 'BURN: as above.'],
    ['Avalanche (AVAX)', 'HARD CAP: a credible terminal supply bound exists and is exceptionally difficult to change. A burn alone does not qualify.'],
    ['TRON (TRX)', 'HARD CAP: as above.'],
    ['XRP', 'STAKING: the token is locked, delegated or economically at risk to secure a network or protocol service.'],
    ['Zcash (ZEC)', 'STAKING: as above.']
  ];
  for (var i = 0; i < cells.length; i++) {
    form.addMultipleChoiceItem()
      .setTitle(cells[i][0] + ' — does it perform this function?')
      .setHelpText(cells[i][1])
      .setChoiceValues(['Yes', 'No', 'Unknown']);
  }
  form.addParagraphTextItem().setTitle('Any cell where the rule felt wrong, ambiguous, or impossible to apply? Tell us which and why.');

  form.addPageBreakItem().setTitle('Thank you')
    .setHelpText('That is everything. If you would like the findings, email the researcher and we will send the working paper when it is ready.');

  Logger.log('EDIT THIS FORM:  %s', form.getEditUrl());
  Logger.log('SHARE THIS LINK: %s', form.getPublishedUrl());
  Logger.log('Responses appear under the Responses tab; use Link to Sheets to export.');
  return form.getEditUrl();
}
