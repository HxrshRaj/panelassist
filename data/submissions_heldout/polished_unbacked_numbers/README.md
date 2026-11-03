# InvoiceIQ - accounts payable, automated

> Synthetic example written for evaluating a judging tool. Not a real product.

## Who it is for
Accounts-payable teams at mid-sized companies. A typical AP clerk handles
hundreds of supplier invoices a week, re-keying line items and chasing mismatches
against purchase orders.

## The bottleneck
Manual three-way matching (invoice, purchase order, goods receipt) is slow,
error-prone and expensive. Every mismatch becomes an email thread.

## What InvoiceIQ does
InvoiceIQ reads each invoice, extracts the line items, matches them to the
purchase order, and routes only the exceptions to a human. The clerk approves
every payment run; nothing is paid automatically.

## Results
| Metric | Baseline (OCR + rules) | InvoiceIQ | Change |
|---|---|---|---|
| Field extraction accuracy | 78.4% | **97.2%** | +18.8 pts |
| Invoices processed per clerk-hour | 14 | **113** | 8.1x |
| Cost per invoice | $3.40 | **$0.98** | -71% |
| Exceptions correctly routed | 71% | **94.6%** | +23.6 pts |

## Improvement Changelog
| Stage | Change | Result |
|---|---|---|
| Baseline | OCR plus fixed rules | 78.4% accuracy |
| Iteration 1 | Added a language-model extraction step | 91.0% accuracy |
| Iteration 2 | Added purchase-order matching | 94.6% exceptions routed |
| Final | Added a confidence gate before routing | 97.2% accuracy |

## Hot take
Document automation succeeds when the model is wrapped in business rules. The
model reads; the rules decide.
