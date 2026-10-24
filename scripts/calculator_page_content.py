"""A quote-input tool and a clearly attributed official calculation example."""

CALCULATOR = {
    'audience': 'buyer', 'path': '/landed-cost-calculator/', 'title': 'Landed Cost Calculator',
    'h1': 'Know the cost before you buy.', 'kicker': 'Buyer planning',
    'description': 'Add confirmed product, inspection, delivery, duty and tax amounts in USD or CAD. Unknown costs stay quote required; no tariff or exchange rate is guessed.',
    'quick_answer': 'A landed-cost comparison adds the confirmed product and order costs in one currency, then divides by the usable quantity where a unit figure is needed. This worksheet uses your quoted amounts, not assumed tariff or tax rates. Unknown costs remain quote required, and the result is a planning total rather than a customs assessment.',
    'cta': 'Start a sourcing request', 'cta_url': '/contact/#buyer-request', 'sources': ['cbsa', 'cbp'],
    'sections': [
        ('Start with confirmed amounts', [
            'The purpose of a landed-cost comparison is to make the buying decision clearer before an order is approved. Begin with the actual product version, quantity and quoted price. Then identify the costs required to make that order available at the agreed receiving point. A useful total distinguishes what is confirmed, what is excluded and what still needs a quote. It should not make uncertainty disappear simply because a spreadsheet cell is empty.',
            'Keep the source and date of each figure with the purchase file. A supplier quotation, an inspection proposal and a delivery quote may have different validity periods and conditions. If the quantity, packing, destination or service changes, review the affected amounts. A total based on an earlier specification is not automatically suitable for a revised order.'
        ]),
        ('Use one currency and one cost boundary', [
            'Choose USD or CAD for the comparison and convert any foreign-currency amount using the appropriate documented basis before including it. This worksheet does not retrieve an exchange rate or decide which rate is legally required for a customs declaration. Keep a record of the original currency, conversion source and date outside the worksheet so that another person can understand how the amount was obtained.',
            'Also agree what the result is intended to cover. A cash requirement to receive an order is different from a management cost after a potentially recoverable tax is considered. Keep the purchase-approval total, a customs valuation calculation and an accounting treatment distinct. The same invoice can support more than one calculation, but those calculations do not necessarily have the same inputs or purpose.'
        ]),
        ('Product, samples and inspection', [
            'The product amount should match the approved specification and quantity unit. Check whether packaging, branding, tooling or setup is included before comparing two supplier offers. A lower unit price can be misleading when the offer excludes a necessary component or applies only to a different order size. Record what the supplier has actually agreed to provide.',
            'Samples and quality checks can be grouped separately where they are part of the proposed order cost. Include only the agreed sample production, sample delivery, inspection and testing charges within the chosen scope. Do not assume that a pre-shipment inspection includes every specialist test, or that sample approval automatically removes the need for an inspection. Unconfirmed charges remain quote required.'
        ]),
        ('Avoid counting delivery twice', [
            'A delivery quotation may combine collection, consolidation, transport, destination handling, clearance and final delivery, or it may show those elements separately. Read the scope before allocating the amounts. If a combined price already includes a service, do not add that service again under another heading. Keep an itemized record of the allocation so that the total can be reconciled to the quote.',
            'The worksheet separates origin and packing, transport, insurance, clearance and final delivery to encourage that review. Those headings do not imply that each amount will be charged separately, or that a zero is normally correct. Where a cost is included elsewhere, a confirmed zero can make sense in that heading. A blank amount means the decision is incomplete, not that the service is free.'
        ]),
        ('Duty and tax are separate assessments', [
            'Use an assessed or reviewed amount for customs duties and other applicable measures rather than selecting a convenient percentage. The product, origin, destination, classification, valuation and available treatment need to be established first. A supplier’s overseas product code or a description such as sample does not complete that work. The worksheet adds the resulting amount; it does not classify goods or establish eligibility.',
            'Taxes likewise need a product- and jurisdiction-specific review. Do not apply an example percentage to every order, and do not treat every tax as automatically recoverable. The official sources below explain why the customs calculation must be established separately from a general purchasing total. Seek the responsible authority or a qualified adviser where the correct treatment is uncertain.'
        ]),
        ('A published official example, not a supplier quote', [
            'CBSA’s example uses goods valued at US$100 and an illustrative exchange rate of CAN$1.37 per US dollar, giving a value for duty of CAN$137.00. Its assumed 4% duty produces CAN$5.48. The example’s taxable value is CAN$142.48, and its 5% GST is CAN$7.12. The duty and GST total CAN$12.60.',
            'These are the figures in the official illustration, not current rates for your product, a current exchange-rate quote, a completed Cargo Global order or a complete delivered price. They demonstrate the stated calculation only. Product selection, freight, insurance, other services and any additional applicable measure still need their own evidence before an order-specific landed total can be approved.'
        ]),
        ('Check the quantity behind a unit result', [
            'The comparison quantity needs to represent the unit you actually plan to use or sell. Pieces, cartons, kilograms and tonnes are not interchangeable. An order priced per carton may contain a different number of usable pieces from another supplier’s carton. Keep the conversion and packing assumptions with the approved specification instead of letting the headline unit cost hide that difference.',
            'The worksheet divides the confirmed cost total by the quantity you enter. It does not estimate rejects, damage, yields, shelf life or sellable stock. If a business decision needs an allowance for those factors, establish and document them separately. Do not invent a standard loss percentage or imply that an inspection guarantees every unit will be accepted.'
        ]),
        ('Review the result before approval', [
            'Reconcile the component amounts with the supplier, inspection and delivery documents before using the total in a purchase decision. Check that the currency, product version, quantity, destination and quote validity agree. Look for missing costs as well as duplicated ones. A lower total with a major exclusion is not a better comparison than a complete and clearly stated offer.',
            'Keep the approved quotation and payment stages separate from this planning worksheet. A browser calculation does not reserve goods, book transport, authorize payment or create a customs declaration. Share the underlying product brief through a sourcing request if you want Cargo Global to help compare the options and coordinate the order’s next steps.'
        ]),
    ],
    'process_title': 'Build a traceable purchase comparison',
    'steps': [
        ('Define the order', 'Identify the product version, quantity unit, currency and receiving point.'),
        ('Confirm each component', 'Obtain dated amounts and check which services are included, excluded or still quote required.'),
        ('Review duty and tax', 'Keep the applicable official assessment and valuation basis with the purchase file.'),
        ('Reconcile before approval', 'Check the sum, unit basis, quote validity and written approval rather than treating a worksheet as an order.'),
    ],
    'facts': [
        ('Official example currency', 'The CBSA illustration converts US$100 to CAN$137.00 using its example rate of 1.37, not a live exchange rate.', 'cbsa'),
        ('Official example charges', 'In that example only, duty is CAN$5.48 and GST is CAN$7.12, totalling CAN$12.60.', 'cbsa'),
        ('Importer responsibility', 'A US broker can assist, but the importer remains responsible for import compliance.', 'cbp'),
    ],
    'faqs': [
        ('Is this a customs-duty calculator?', 'No. It adds confirmed component amounts in one selected currency. Classification, origin, valuation, preferential treatment, additional measures and tax obligations must be established separately before a duty or tax amount is used.'),
        ('What if I do not have a delivery quote?', 'Leave the uncertain amount unresolved and obtain a quote. Unknown costs must not be silently replaced with zero. A complete planning total requires each included component to be known or explicitly confirmed as included elsewhere.'),
        ('Can I mix USD and CAD amounts?', 'No. Establish one currency for the comparison and document any conversion before including an amount. The official customs valuation conversion and your commercial budgeting conversion may have different requirements; the worksheet does not choose either for you.'),
        ('Are the example duty and tax rates my rates?', 'No. The figures are an illustration published by CBSA. They are not a classification or tax assessment for your goods, and the example exchange rate is not presented as today’s rate.'),
        ('Does a delivered quote always include everything?', 'No. Read the actual inclusions and exclusions. Taxes, inspection, unloading, appointments or specialist handling may sit outside a quoted scope. Count a service once and do not assume it is included because a quote uses the phrase door to door.'),
        ('Should I subtract tax that may be recoverable?', 'That is a separate accounting and eligibility question. Distinguish the cash needed for the order from a management cost after any confirmed recovery. Do not assume a tax is recoverable without checking the relevant conditions.'),
        ('Are these inputs sent to Cargo Global?', 'The worksheet calculation runs in the browser and does not submit its component amounts. A separate sourcing request is sent only when you complete and submit that request form with the information you choose to provide.'),
        ('Does this authorize a purchase?', 'No. A calculation is a planning aid. The actual supplier option, specification, quote, payment stages, quality checks and delivery scope must be reviewed and approved in writing before an order proceeds.'),
    ],
}
