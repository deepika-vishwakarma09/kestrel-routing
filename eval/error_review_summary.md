# Review of the model's mistakes

The model got 934 of the 6,502 requests in the time-based tests wrong (14.4%). I looked at them in three ways.

1. **A random sample of 100 mistakes was read and typed by Claude, the AI assistant I used.** Each was given a type. 98 are still wrong in the final model (the other 2 were fixed by a later change), so `error_review.csv` holds 98 rows. The sample was drawn from an earlier build of the model.
2. **I read the first 500 of the 934 mistakes myself** (the file `errors.csv`, sorted from least sure to most sure). These are the model's least-sure mistakes, so they are almost all vague messages (481 of 500). The types matched Claude's.
3. **I typed Claude's rule for "vague" into code and applied it to all 934.** The rule checks whether anything is left in the message once the product name, greetings, payment words and generic phrases such as "need help with" are removed. On the 98 messages Claude typed by hand it agreed every time (98 of 98).

## Results

| Kind of mistake | The 98 reviewed by Claude | All 934 (rule) | What it looks like |
|---|---|---|---|
| Vague: the message does not say what the problem is | 83 (85%) | 787 (84%) | "not happy with [product]", "help [product]", "service request for [product]" |
| Clear message, but where it ended up contradicts it (looks like label noise) | 7 (7%) | 74 (8%, together with the next row's kind) | an invoice query that ended in Installations; "stopped working after 7 months" that ended in Billing |
| Clear message, two teams defensible | 2 (2%) | (in the row above) | a leaking product could be Repairs or Warranty Claims |
| Two-part message whose last part is generic | 6 (6%) | 73 (8%) | "shield plan renewal for [product], need help with my [product]" |

The rule cannot tell label noise from "two teams defensible", so the all-934 column counts them together.

## What this means

- About 84% of the mistakes are messages that name a product but not the problem, so no model reading the text can route them. That is about 12% of all requests.
- Only about 16% of the mistakes (about 2% of requests) look fixable or arguable. So routing from the text alone cannot get much above 88% to 89% against where requests really end up: 100% minus the 12% that are vague, plus a little for lucky guesses on those. The 90% asked for in the brief is out of reach on this data unless a person asks the customer.
- For those vague messages the right answer is a question to the customer, not a guess. That is why the service sends low-confidence requests to a person.
- The model is sometimes quite sure about a vague message. 113 of the 787 vague mistakes (14%) had confidence of 0.5 or more, so the 0.7 cut-off for automatic routing catches most but not all of them. Payment words are a little more common among these (15% against 3% for the unsure ones), which fits policy section 3: a customer saying they paid does not make it a billing request.

## One data issue found while reading

In 17.5% of requests (1,744 of 9,984 that name one product) the product named in the message is different from the `product_family` column. I did not trust that column; the model does not use it. Dropping it, `channel` and `warranty_status` changed accuracy by less than 0.1 points.

## Limits of this review

Claude's types were assigned by one reader, and a second reader may split "vague" and "two teams defensible" differently. The rule for "vague" was built from the same 98 messages it was checked on, so its 98-of-98 agreement is not an independent test. The review covers mistakes only, so it says nothing about how often the model is right for the right reasons.
