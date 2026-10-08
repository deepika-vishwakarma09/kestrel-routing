# AI usage log

## Tools
- **Claude** (claude.ai chat): my main helper from start to end.
- **No model API is used in the product.** The routing model is a small program that runs on the CPU. I did not use Groq or any other model API in this task, so the service needs no key.

## What I used Claude for
Claude was my main helper. I used it to go through the brief and the policy with me, to explore the data, to plan how to test the model, to write the code (cleaning, the model, the time-based tests, predictions, the rupee sums, the service and its screen), and to draft the memo and the write-ups. Some of the findings came out of working through the data with it: that the bot's labels are right only 77% of the time, that the last part of a two-part message tends to decide where a request ends up, and that most of the model's mistakes are vague messages. Claude also read 100 of the model's mistakes and gave each one a type.

## What I did myself
- Set up the repo, the virtual env and the folders, and ran every command.
- Compared each of my outputs with the numbers Claude gave me. When something did not match (my first run still used the old files), I replaced the files and ran it again.
- Read 500 of the 934 mistakes in `eval/errors.csv` myself. They are the ones the model was least sure about, so almost all of them (481 of 500) are messages that do not say what the problem is. This matched the types Claude had given in its own review.
- Decided to keep the model local, with no API, because the brief says it must start without a paid key and Farhan does not want a bill that grows with requests.
- Read the results and the memo, and decided what to send.

## Where it helped
- Seeing early that the target should be where a request ended up (`final_team`), not the bot's label. A model that copies the bot passes the 90% bar and is no better than the bot.
- Reading the mistakes and finding the "last part decides" pattern. It raised accuracy from 83.8% to 85.5%, with the same gain in all three tests.
- Checking which columns the model needed. Dropping three of them lost nothing.
- Quick code and tests for the service, including what happens when the model file is missing.

## Where it wasted time or was wrong
- The first expected-score file said 1 request in 10 ends up where the model was very sure was wrong. That was wrong (it was 1 in 63), and the file now works the number out from the data.
- One line in the same file ("expect about 78%") was typed by hand and went out of date when the model changed. It is now calculated too.
- The first model (83.8%) and its expected score (83.9%) had to be thrown away and redone after the last-part feature.
- I lost some time because some of my outputs were from the old files before I had replaced them.

## What I threw away
- Training on the bot's labels. It matched the bot 96.6% of the time but was right only 78.7% of the time.
- Character-based text features. They did not help and store more customer text.
- The channel, product and warranty columns. They added nothing, and the product column names a different product from the message in 17.5% of requests.
- The first model (83.8%) and the first expected score (83.9%).

## Cost
- No model API calls, so Rs 0 for the product.
- Claude: free plan
