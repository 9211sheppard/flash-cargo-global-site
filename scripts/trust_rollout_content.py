"""Reviewed route definitions and blank process templates, not customer evidence."""

FBX_ROOT = 'https://www.freightos.com/enterprise/terminal/'
FBX_UPDATE = 'https://www.freightos.com/freight-resources/red-sea-container-traffic-set-for-full-return-in-q1-october-20-2026-update/'
PROCESS_LINE = 'Every order runs the same way: a written quote, staged payments, and the agreed checks before shipment.'
BANK_CHANGE_POLICY = 'We never change bank or payment details by email. Any change is confirmed through the request form before you pay.'
FBX_CONTEXT = 'Market context only. This index reading is not used to price, settle or compare your order.'
ANTI_PHISHING = 'We only email from @flashcargoglobal.com and never request payment by gift card, crypto or a personal account.'
PAYMENT_RULES = [
    ('A written quote comes first', 'Nothing is paid before a written, itemized quote. The quote identifies the product, quantity, currency, delivery scope, inclusions, exclusions and the agreed payment stages.'),
    ('Supplier payment is staged', 'Supplier payment is staged: a deposit, then the balance only after sample approval and any agreed pre-shipment inspection. The approved sample, agreed checks and acceptance decision belong in the order record.'),
    ('Pay a business, not a person', 'Payments go only to a business account or a recognized processor’s invoice, never a personal account. The business payee and payment instructions must match the written order agreement.'),
    ('Verify any change before paying', BANK_CHANGE_POLICY),
    ('No surprise fee requests', 'No surprise “release”, “customs” or “insurance” fees outside the written quote. Any proposed change must be itemized and agreed in writing before payment.'),
    ('Agree the remedy before payment', 'If goods fail inspection, the refund or replacement terms are written plainly. The order agreement identifies the remedy, responsibilities, applicable costs and timing before payment; no unspecified automatic refund, escrow or insurance protection is implied.'),
]

RETIRED_PREFIXES = {'/planning/':'/sourcing/', '/services/':'/delivery/', '/resources/':'/sourcing/'}
RETIRED_EXACT = {'/trust-center/':'/about/','/verify-flash-cargo-global/':'/about/','/official-flash-cargo-global/':'/about/','/resources/air-vs-ocean-freight-decision-guide/':'/delivery/','/resources/cross-border-trucking-preparation-guide/':'/delivery/','/resources/warehouse-staging-freight-guide/':'/delivery/','/resources/white-glove-freight-planning-guide/':'/delivery/'}

LANES = [
    {
        'slug': 'china-to-us-west-coast-sourcing-guide',
        'lane_id': 'china-us-west-coast',
        'title': 'China to the US West Coast: Sourcing Checks',
        'destination': 'the US West Coast',
        'port': 'Los Angeles',
        'index_lane': 'FBX01',
        'destination_region': 'north-america-west-coast',
        'fbx': 'FBX01',
        'index_label': 'China/East Asia to North America West Coast',
        'fbx_url': FBX_ROOT + 'fbx-01-china-to-north-america-west-coast/',
        'regional_fact': 'Freightos FBX01 measures 40ft container prices from China/East Asia to North America West Coast. It is a regional index, not a quote to a specific destination door.',
        'buyer_checks': [
            'Name the actual arrival port and final receiving address. A US West Coast brief is not interchangeable with a Canadian destination.',
            'Confirm who arranges the port handoff, onward transport, receiving appointment and unloading. Compare the same agreed scope across supplier quotes.',
            'Ask whether samples and production cartons need different delivery arrangements. Record the approved packing and carton marks before release.',
        ],
    },
    {
        'slug': 'china-to-us-east-coast-sourcing-guide',
        'lane_id': 'china-us-east-coast',
        'title': 'China to the US East Coast: Sourcing Checks',
        'destination': 'the US East Coast',
        'port': 'NY/NJ',
        'index_lane': 'FBX03',
        'destination_region': 'north-america-east-coast',
        'fbx': 'FBX03',
        'index_label': 'China/East Asia to North America East Coast',
        'fbx_url': FBX_ROOT + 'fbx-03-china-to-north-america-east-coast/',
        'regional_fact': 'Freightos FBX03 covers China/East Asia to North America East Coast in 40ft units, rather than one destination door.',
        'buyer_checks': [
            'Confirm the named East Coast port and receiving location instead of treating the whole coast as one delivery point.',
            'Keep the supplier production milestone separate from inspection release and the final receiving appointment. Each needs its own confirmation.',
            'Compare port-to-port and delivered quotes only after separating origin handling, destination handling, clearance coordination and onward delivery.',
        ],
    },
    {
        'slug': 'china-to-north-europe-sourcing-guide',
        'lane_id': 'china-north-europe',
        'title': 'China to North Europe: Supplier Order Checks',
        'destination': 'North Europe',
        'port': 'Rotterdam',
        'index_lane': 'FBX11',
        'destination_region': 'north-europe',
        'fbx': 'FBX11',
        'index_label': 'China/East Asia to North Europe',
        'fbx_url': FBX_ROOT + 'fbx-11-china-to-northern-europe/',
        'regional_fact': 'Freightos FBX11 covers China/East Asia to Northern Europe in 40ft units; its port list includes Rotterdam and other North European gateways.',
        'buyer_checks': [
            'Specify the importing country, arrival gateway and final receiving location. A regional ocean index does not establish the cost or requirements at the final destination.',
            'Keep product specifications, material descriptions, intended use and supplier documentation together for the responsible importer and qualified advisers to review.',
            'Record whether the buyer is comparing a European delivery option, a supplier sample movement or a later North American order. Do not apply one movement’s quote to another.',
        ],
    },
    {
        'slug': 'china-to-mediterranean-sourcing-guide',
        'lane_id': 'china-mediterranean',
        'title': 'China to the Mediterranean: Supplier Checks',
        'destination': 'the Mediterranean',
        'port': 'Genoa',
        'index_lane': 'FBX13',
        'destination_region': 'mediterranean',
        'fbx': 'FBX13',
        'index_label': 'China/East Asia to the Mediterranean',
        'fbx_url': FBX_ROOT + 'fbx-13-china-to-mediterranean/',
        'regional_fact': 'Freightos FBX13 covers China/East Asia to the Mediterranean in 40ft units, across multiple gateways and jurisdictions.',
        'buyer_checks': [
            'Name the destination country and port. A regional index does not make different national import procedures or inland delivery costs interchangeable.',
            'Agree product descriptions, packaging, sample references and quality-check responsibilities before the supplier prepares the order for dispatch.',
            'Separate a port-to-port comparison from the buyer’s delivered requirement. Ask for the destination charges, importer responsibilities and final receiving scope in writing.',
        ],
    },
]

TEMPLATES = [
    ('itemized-quote-template', 'Sample template: itemized quote layout', [
        ('Order reference and revision', 'Record the agreed product brief and the version being quoted.'),
        ('Product and quantity', 'Identify the specification, quantity and unit.'),
        ('Currency', 'State USD or CAD as agreed; do not mix currencies in a total.'),
        ('Product amount', 'Enter the supplier-confirmed amount and its scope.'),
        ('Samples and checks', 'Record agreed sample, testing and inspection charges separately.'),
        ('Packing and origin handling', 'Identify the agreed packing and collection scope.'),
        ('Ocean, air or road transport', 'Identify the named route and the quoted transport component.'),
        ('Destination and delivery', 'State the clearance, handling, unloading and delivery inclusions.'),
        ('Duty, tax and insurance', 'Identify confirmed amounts, exclusions and the responsible party.'),
        ('Validity and changes', 'Record quote validity and how a change must be approved.'),
        ('Payment and remedy terms', 'Leave for the actual written order agreement; this template does not set policy.'),
    ]),
    ('supplier-shortlist-template', 'Sample template: supplier shortlist format', [
        ('Supplier identity', 'Record the business identity and the evidence reviewed; no example company is supplied.'),
        ('Production scope', 'Distinguish the manufacturer, trading activity and disclosed subcontracting.'),
        ('Specification match', 'Record the material, dimensions, finish and permitted variation.'),
        ('Minimum and capacity', 'Record the supplier-confirmed quantity unit and current availability.'),
        ('Sample evidence', 'Record the sample version, photographs and review outcome.'),
        ('Document scope', 'Identify issuer, covered product or facility, validity and verification gaps.'),
        ('Quote comparison', 'Compare the same quantity, currency, packing and delivery scope.'),
        ('Open questions', 'Record unresolved points and the person or business responsible for clarification.'),
        ('Buyer decision', 'Record the approval, rejection or further review needed.'),
    ]),
    ('inspection-checklist-template', 'Sample template: pre-shipment inspection checklist', [
        ('Approved reference', 'Identify the approved specification, sample and order revision.'),
        ('Inspection booking', 'Identify the independent inspector, date, access and agreed scope.'),
        ('Quantity and identification', 'Record the agreed counting method, product references and carton marks.'),
        ('Appearance and dimensions', 'Record checks and tolerances agreed for the actual product.'),
        ('Function and testing', 'List the tests within scope; specialist testing must be agreed separately.'),
        ('Packing', 'Record packaging, protection, labels and any agreed handling requirements.'),
        ('Evidence', 'Record photographs, findings and document references without unrelated personal data.'),
        ('Exceptions and corrective work', 'Record the issue, responsible party and required follow-up.'),
        ('Release decision', 'Record the responsible approval. A checklist is not a certificate or universal compliance guarantee.'),
    ]),
]

CAPABILITY_COPY = [
    'We curate supplier options, compare the brief against supporting information, and coordinate the agreed samples, checks and delivery scope.',
    'Third-party pre-shipment inspection can be booked on request. Scope, fees, access and acceptance criteria are agreed before the check. No inspection firm is represented here as a partner.',
    'No customs brokerage licence is claimed. Where a licensed or otherwise authorized customs service is required, that responsibility must be agreed with the appropriate provider.',
    'We do not guarantee delivery dates or rates. The written quote identifies its validity and the proposed scope; production, carrier availability and clearance can affect the plan.',
]
