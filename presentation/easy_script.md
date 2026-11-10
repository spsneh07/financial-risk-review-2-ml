# Easy Presentation Script (simple words)
**Financial Market Risk Profiling and Regime Detection**
Srushti More [298] · Agadh Khanolkar [299] · Sneh Prasad [311]

**Deck:** project_review_2.pptx (12 slides). **Time:** about 5 to 6 minutes. Short sentences, easy to say out loud. Just read the words in the boxes.

| Member | Slides | Topic | Words | Time |
|---|---|---|---|---|
| Srushti | 1–5 | Problem, data, grouping methods | 249 | ≈ 2:00 |
| Agadh | 6–7 | Distances, PCA, the risk groups | 189 | ≈ 1:45 |
| Sneh | 8–12 | Market moods (HMM), algorithms, results | 227 | ≈ 1:45 |

> Tip: if you forget a line, look at the slide and say the main point in your own words. That is completely fine.

---

## MEMBER 1: SRUSHTI MORE (≈ 2:00)

### Slide 1: Title (≈ 10 s)
**Key point:** two parts.
> Good morning. We are Srushti, Agadh and Sneh. Our project has two parts. Part A groups stocks by how risky they are. Part B finds the hidden mood of the stock market.

### Slide 2: Problem (≈ 25 s)
**Point at:** the A and B boxes.
> Why does this matter? Two stocks can look equally risky, but fall very differently in a crash. So one number is not enough. The market also changes its mood: calm, choppy or crisis. So we ask two questions. Which stocks are similar in risk? And what mood is the market in?

### Slide 3: Our flow (≈ 20 s)
**Point at:** the boxes, left to right.
> This is our flow. Real stock data from the NSE goes in. The top row groups twelve stocks. The bottom row studies the NIFTY 50 index. Everything runs in one notebook.

### Slide 4: Data and risk numbers (≈ 35 s)
**Point at:** the table, then the coloured heatmap.
> We took twelve big NSE stocks from nine sectors, with five years of daily data. We use daily returns, which means the daily percentage change, not the price. A costly share is not always a risky share. For each stock we calculated seven risk numbers, like how much it swings, how much it loses on its worst days, and its biggest fall. Then we put all the numbers on the same scale.

### Slide 5: Three grouping methods (≈ 30 s)
**Point at:** the three boxes on the left.
> We used three grouping methods. K-means puts each stock in the nearest group. GMM gives each stock a probability for every group. Hierarchical clustering joins similar stocks step by step, like a family tree. One test suggested three groups and another suggested two. We chose three, because three groups explain risk better.

**Transition:**
> Now Agadh will explain how we measure which stocks are similar.

---

## MEMBER 2: AGADH KHANOLKAR (≈ 1:45)

### Slide 6: Distance and PCA (≈ 50 s)
**Point at:** the three boxes at the top, then the coloured grid.
> Thanks, Srushti. To group stocks, we must measure how different they are. Manhattan distance simply adds up the differences. Cosine distance compares the shape of the risk, not its size. Mahalanobis distance avoids double counting, because some of our risk numbers move together. We tested all three in the same fair way. The result: the distance we choose changes the groups. We also used PCA. It squeezes our seven numbers into three, and still keeps ninety-three percent of the information.

### Slide 7: The risk groups (≈ 55 s)
**Point at:** the right-hand plot, then the table.
> Here are our groups. These dots are only a picture; the grouping itself used all seven numbers. Hierarchical clustering gave the cleanest groups. Group one is low risk: seven stocks, like Reliance, HDFC Bank and Sun Pharma. Group two is tail risk: ITC and L and T. They usually behave normally, but sometimes fall suddenly. Group three is high risk: TCS, Infosys and Tata Steel. At their worst, they fell about half their value. We also checked if the groups stay the same when the data changes a little. With only twelve stocks, they are only fairly stable.

**Transition:**
> Now Sneh will move from single stocks to the whole market.

---

## MEMBER 3: SNEH PRASAD (≈ 1:45)

### Slide 8: Market moods (≈ 30 s)
**Point at:** the coloured table, then the three curves.
> Thanks, Agadh. We cannot see the market's mood directly. We only see the daily returns. A Hidden Markov Model guesses the hidden mood from those returns. Ours has three moods. Bull means steady small gains. Bear means almost no gain, a choppy period. High volatility means big swings, about four percent a day, and it lasts about a week. The model also learns how likely the market is to switch from one mood to another.

### Slide 9: Two algorithms (≈ 30 s)
**Point at:** the two boxes, then the 2020 chart.
> To find the mood on each day, we wrote two algorithms ourselves. Sum-Product gives the chance of each mood on every day. Viterbi gives the one most likely chain of moods. Both look at the full history, so this chart is a look back, not a live prediction. Our answers match the official Python library exactly.

### Slide 10: Kalman filter (≈ 15 s)
**Point at:** the top chart.
> We also built a Kalman filter model. Here the hidden state is a smooth number instead of three moods. So the HMM jumps between moods, while the Kalman model changes slowly.

### Slide 11: Results (≈ 20 s)
**Point at:** the bar chart.
> We tested the models on new data from 2024 to 2026, which they had never seen. The Hidden Markov Model predicted best. Our limits: we used only twelve stocks, and the mood names are our own interpretation.

### Slide 12: Conclusion (≈ 10 s)
**Key point:** three simple takeaways.
> In short: stocks fall into three risk groups, the distance method matters, and market moods predict better than smooth trends. Thank you. We can show the demo now.

---

## Simple meanings (if someone asks)
- **Daily return:** how much the price changed today, in percent.
- **Volatility:** how much a stock swings up and down.
- **Drawdown:** the biggest fall from a high point.
- **Clustering:** putting similar things into groups.
- **PCA:** shrinking many numbers into a few, keeping most of the information.
- **Hidden Markov Model:** a model that guesses a hidden state (the market mood) from what we can see (returns).
- **Sum-Product:** the chance of each mood on each day.
- **Viterbi:** the single most likely sequence of moods.
- **Kalman filter:** tracks a hidden value that changes smoothly over time.
