**To:** Ritu Deshpande, Head of D2C Operations
**From:** Deepika Vishwakarma
**Date:** 8 October 2026
**Subject:** Replacing the routing bot

## Recommendation

Yes, do not renew the bot. Replace it with the model I built, but with one change to the plan: a person should read the roughly 1 in 6 requests the model is unsure about. Do not set the bar as "matches the bot's labels at 90%". That bar is easy to reach and does not help you.

## Why

**1. The bot's labels are not the right answer.** They show the queue the bot chose when the request came in, not where it ended up. Only 77% of the bot's choices match the team that finally closed the request, so 23% were wrong. A model trained to copy the bot matched it 97% of the time, but sent only 79% of requests to the right team, barely better than the bot itself. I trained mine on where requests actually ended up.

**2. The new model gets 86% right, against the bot's 77%.** I tested it three times on the most recent months it had not seen, 6,502 requests in all. The result stayed between 85% and 86% each time, and the range is 85% to 87%.

**3. It knows when it is not sure.** On 84% of requests it is very confident and is right 98% of the time. The other 16% (about 114 requests a month) are mostly messages such as "not happy with water purifier", which do not say what the problem is. People and models both get these wrong about 4 times in 5, so someone should ask the customer.

**4. 90% is out of reach from the message alone.** About 12% of requests are that vague. On this data the best any model can do is about 88%. The way to get higher is to ask one question when the request is created: "what is the problem?"

## The rupees

A wrongly routed request costs Rs 698: 1.44 transfers at Rs 305 each, plus one extra customer contact at Rs 260. At about 726 requests a month:

| Option | Monthly cost | Saving a year vs the bot |
|---|---|---|
| Keep the bot (wrong routings + licence) | Rs 1,42,383 | none |
| Model routes everything | Rs 72,800 | Rs 8.3 lakh |
| Model routes when sure, a person reads the rest | Rs 37,669 | Rs 12.6 lakh |

The last row assumes a person reading an unsure request costs Rs 260; it pays off as long as it costs less than Rs 568. **For Farhan: the model costs Rs 0 per request.** It makes no paid calls, so there is no bill that grows with volume. I have not priced hosting; it is a small program that runs on an ordinary server.

## Headcount

Do not plan from the bot's queue sizes. Billing, Repairs and Consumables receive work that belongs elsewhere (only 60% to 65% of what the bot sends them ends there). Requests per month by where they actually end up: Repairs 169, Installations 106, Returns 103, Product Advice 93, Warranty 92, Billing 88, Consumables 71. Installations, Returns and Warranty are each about a quarter bigger than the bot suggests. You did not send staffing numbers, so this shows demand, not load per person.

## What to do next week

1. **Run the model alongside the bot for two weeks.** The bot still routes; the model only suggests. Compare transfers. Ask the bot vendor for a short extension if the renewal date falls inside this.
2. **Choose who reads the unsure requests** and give them one question to ask the customer.
3. **Ask Tanmay for staff numbers and handling time per team**, so headcount can be planned properly.
4. **Add "what is the problem?" to intake.** Also fix the product field: in 17% of requests it names a different product from the message.

## How sure am I

I expect about 85% on the requests you held back (84% to 87%). That assumes the team that closed each request is the right answer; about 1 request in 80 ends somewhere that looks wrong, and no model can fix that. The Rs 698 and Rs 260 are your policy figures, and I assumed the model's wrong routings cost the same as the bot's. The model uses only the words in the message, and keeps no customer text or personal details.
