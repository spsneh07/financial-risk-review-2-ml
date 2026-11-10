// Builds presentation/project_review_2.pptx from the figures/tables produced by main.py.
// Run from the project root:  node presentation/build/build_deck.js
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..", "..");
const FIG = (f) => path.join(ROOT, "outputs", "figures", f);
const R = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "results", "results.json")));
const A = R.part_a, B = R.part_b;
const SIZES = JSON.parse(fs.readFileSync(process.argv[2] || path.join(__dirname, "imgsizes.json")));
const SKILL_THEME = process.argv[3];

const THEME = {
  name: "Market Regimes",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B1F33", lt1: "FFFFFF", dk2: "3D4F63", lt2: "EEF3F8",
    accent1: "1E5AA8", accent2: "EB6834", accent3: "1BAF7A", accent4: "2A78D6",
    accent5: "EDA100", accent6: "E34948", hlink: "1E5AA8", folHlink: "6250D6",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Financial Market Risk Profiling and Regime Detection";
pres.author = "Srushti More, Agadh Khanolkar, Sneh Prasad";
// Hex values (mirroring THEME) so the deck renders identically even if the theme is not re-applied.
const C = { text1: HEX.dk1, text2: HEX.dk2, background1: HEX.lt1, background2: HEX.lt2,
  accent1: HEX.accent1, accent2: HEX.accent2, accent3: HEX.accent3, accent4: HEX.accent4,
  accent5: HEX.accent5, accent6: HEX.accent6 };
const W = 13.333;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.9,
      fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left" },
      text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.05, w: 11.7, h: 0.8,
      fontSize: 20, color: "CADCFC", valign: "top", align: "left" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  margin: [0.5, 0.6, 0.5, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.3, w: 10.6, h: 0.85,
      fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 },
      text: "" } },
    { text: { text: "ML Project Review 2  ·  Financial Risk Profiling & Regime Detection",
      options: { x: 0.6, y: 7.05, w: 8, h: 0.3, fontSize: 10, color: "7A8794", margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.05, w: 0.5, h: 0.3, fontSize: 10, color: "7A8794", align: "right" },
});

// ------------------------------------------------------------------ helpers
function img(slide, file, x, y, opts = {}) {
  const [pw, ph] = SIZES[file];
  let w = opts.w, h = opts.h;
  if (w && !h) h = (w * ph) / pw;
  if (h && !w) w = (h * pw) / ph;
  if (opts.maxH && h > opts.maxH) { h = opts.maxH; w = (h * pw) / ph; }
  if (opts.alignRight) x = x - w;
  slide.addImage({ path: FIG(file), x, y, w, h, altText: opts.alt || file, objectName: file });
  return { w, h };
}
function tag(slide, text, color) {
  slide.addText(text, { x: 11.35, y: 0.48, w: 1.4, h: 0.45, shape: pres.shapes.ROUNDED_RECTANGLE,
    rectRadius: 0.22, fill: { color }, color: C.background1, fontSize: 12, bold: true, align: "center",
    valign: "middle", isTextBox: true, objectName: "part-tag" });
}
function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08,
    fill: { color: opts.fill || HEX.lt2 }, line: { color: opts.line || HEX.lt2, width: 0.75 },
    objectName: opts.name || "card" });
}
function text(slide, runs, x, y, w, h, o = {}) {
  slide.addText(runs, Object.assign({ x, y, w, h, isTextBox: true, margin: 0, valign: "top",
    fontSize: 14, color: C.text1, paraSpaceAfter: 4 }, o));
}
function bullets(items, o = {}, trail = false) {
  return items.map((t, i) => {
    const base = Object.assign({ bullet: { indent: 14 }, breakLine: trail || i < items.length - 1 }, o);
    if (typeof t === "string") return { text: t, options: base };
    return { text: t.text, options: Object.assign(base, t.options || {}) };
  });
}
function stat(slide, x, y, w, big, label, color) {
  text(slide, [{ text: big, options: { fontSize: 34, bold: true, color: color || C.accent1,
    fontFace: THEME.headFontFace, breakLine: true } },
    { text: label, options: { fontSize: 12, color: C.text2 } }], x, y, w, 1.1);
}
const f2 = (v) => Number(v).toFixed(2);
const f3 = (v) => Number(v).toFixed(3);
const pct = (v) => (100 * v).toFixed(0) + "%";

// ======================= SHORT VERSION (7 slides, < 5 minutes) =======================
const big = { fontSize: 18 };

// 1. Title
pres.addSection({ title: "Short deck" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Short deck" });
s.addText("Financial Market Risk Profiling and Regime Detection", { placeholder: "title" });
s.addText("Clustering · GMM · Hidden Markov Models · Linear Dynamical Systems", { placeholder: "body" });
text(s, [
  { text: "Machine Learning · Project Review 2", options: { bold: true, breakLine: true, color: C.background1 } },
  { text: "Made by Srushti More [298], Agadh Khanolkar [299], Sneh Prasad [311]", options: { color: "CADCFC" } },
], 0.8, 5.4, 11, 0.8, { fontSize: 16 });
s.addNotes("Our project answers two questions: which stocks share a similar risk profile, and which hidden regime the market is in.");

// 2. Problem + pipeline
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Short deck" });
s.addText("Two questions, one pipeline", { placeholder: "title" });
[["A", "Which stocks share a risk profile?", "12 NSE stocks · K-means, GMM, Hierarchical", C.accent1],
 ["B", "Which market regime are we in?", "NIFTY 50 · HMM vs Kalman LDS", C.accent2]].forEach(([l, q, d, col], i) => {
  const x = 0.6 + i * 6.2;
  card(s, x, 1.45, 5.9, 1.7);
  s.addText(l, { x: x + 0.3, y: 1.75, w: 0.7, h: 0.7, shape: pres.shapes.OVAL, fill: { color: col },
    color: C.background1, bold: true, fontSize: 24, align: "center", valign: "middle", isTextBox: true });
  text(s, [{ text: q, options: { bold: true, fontSize: 20, breakLine: true, fontFace: THEME.headFontFace } },
    { text: d, options: { fontSize: 16, color: C.text2 } }], x + 1.25, 1.75, 4.5, 1.2);
});
const steps = [["Real NSE data", "2015 to Sep 2026"], ["Risk features", "7 per stock"], ["Models", "Cluster · HMM · LDS"],
  ["Evaluate", "Silhouette · ARI · test score"], ["Outputs", "20 plots · 31 tests"]];
steps.forEach(([h, d], i) => {
  const x = 0.6 + i * 2.48;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.6, w: 2.15, h: 2.0, rectRadius: 0.1,
    fill: { color: i === 4 ? HEX.accent3 : HEX.dk1 }, line: { color: i === 4 ? HEX.accent3 : HEX.dk1 } });
  text(s, [{ text: h, options: { bold: true, fontSize: 18, breakLine: true, color: C.background1 } },
    { text: d, options: { fontSize: 14, color: "CADCFC" } }], x + 0.15, 4.0, 1.85, 1.4, { align: "center" });
  if (i < 4) s.addShape(pres.shapes.LINE, { x: x + 2.15, y: 4.6, w: 0.33, h: 0.001,
    line: { color: "7A8794", width: 2, endArrowType: "triangle" } });
});
text(s, "One notebook:  Restart & Run All   (about 1 minute on a laptop)", 0.6, 6.05, 12, 0.5, { fontSize: 16, color: C.text2 });
s.addNotes("Part A groups 12 NSE stocks by risk. Part B finds hidden regimes in the NIFTY 50. One notebook loads real data, computes the features, runs every model and produces all plots in about a minute.");

// 3. Data & features
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Short deck" });
s.addText("Data and risk features", { placeholder: "title" });
tag(s, "PART A", C.accent1);
img(s, "A2_risk_feature_heatmap.png", 6.2, 1.3, { w: 6.55 });
stat(s, 0.6, 1.5, 5.3, "12 stocks · 9 sectors", "NSE daily closes, Oct 2021 to Sep 2026", C.accent1);
text(s, bullets(["Mean return, volatility", "Skewness, kurtosis", "VaR 95% and CVaR 95%", "Maximum drawdown"], big),
  0.6, 2.9, 5.3, 2.2, { paraSpaceAfter: 8 });
text(s, "All features z-scored before clustering", 0.6, 5.3, 5.3, 0.5, { fontSize: 15, color: C.text2 });
s.addNotes("Each stock is described by seven risk numbers, including tail-risk measures like VaR, CVaR and drawdown. We standardise them so no single feature dominates. In the heatmap, red means riskier than average.");

// 4. Part A results
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Short deck" });
s.addText("Part A: three risk profiles", { placeholder: "title" });
tag(s, "PART A", C.accent1);
img(s, "A5_pca_clusters.png", 0.6, 1.3, { w: 12.1 });
[["Low risk", "7 stocks: banks, FMCG, pharma, telecom, auto", HEX.accent4],
 ["Tail risk", "ITC, LT: negative skew, fat tails", HEX.accent2],
 ["High risk", "TCS, INFY, TATASTEEL: ~49% drawdown", HEX.accent3]].forEach(([h, d, col], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 5.05, 3.9, 1.15, { fill: col, line: col });
  text(s, [{ text: h, options: { bold: true, fontSize: 17, breakLine: true, color: C.background1 } },
    { text: d, options: { fontSize: 13, color: C.background1 } }], x + 0.2, 5.15, 3.5, 1.0);
});
text(s, "Distance metric matters: Manhattan, Cosine and Mahalanobis give different groups. Mahalanobis is the most stable (ARI).",
  0.6, 6.4, 12.1, 0.45, { fontSize: 14, color: C.text2 });
s.addNotes("We used K equals 3 based on GMM BIC. K-means silhouette favours 2, so the criteria do not fully agree, and we kept 3 for the risk-profile interpretation. Hierarchical Ward clustering gives the cleanest groups: a low-risk core, a tail-risk pair, ITC and LT, and a high-risk group, the IT majors plus Tata Steel. Changing the distance changes the groups, and Mahalanobis was the most stable under resampling.");

// 5. HMM regimes
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Short deck" });
s.addText("Part B: hidden market regimes", { placeholder: "title" });
tag(s, "PART B", C.accent2);
img(s, "B1_nifty_regimes_viterbi.png", 0.6, 1.3, { w: 8.4 });
[["Bull", "+0.12%/day · calm · ~86-day runs", HEX.accent3], ["Bear", "≈0%/day · choppy · ~51-day runs", HEX.accent2],
 ["High-Vol", "σ 3.9%/day · ~7 days · COVID 2020", HEX.accent4]].forEach(([h, d, col], i) => {
  const y = 1.4 + i * 1.25;
  s.addShape(pres.shapes.OVAL, { x: 9.3, y: y + 0.12, w: 0.4, h: 0.4, fill: { color: col }, line: { color: col } });
  text(s, [{ text: h, options: { bold: true, fontSize: 18, breakLine: true } },
    { text: d, options: { fontSize: 13, color: C.text2 } }], 9.9, y, 2.9, 1.1);
});
text(s, "Retrospective view: full-sequence Viterbi labels; parameters fitted on 2015–2023 only. BIC selects 3 states (4 states scores slightly better on test data).", 0.6, 5.0, 8.4, 0.9,
  { fontSize: 15, color: C.text2 });
s.addNotes("The HMM learns three regimes from daily returns alone. We name them from the learned parameters, not the state numbers. It finds the COVID crash as the high-volatility regime. Its parameters were fitted only up to 2023. This chart is a retrospective labelling from full-sequence Viterbi decoding, not a real-time prediction. BIC selects three states; a four-state model scores slightly better on held-out data, but three give the clearest interpretation.");

// 6. Sum-product vs Viterbi + LDS
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Short deck" });
s.addText("Inference and HMM vs LDS", { placeholder: "title" });
tag(s, "PART B", C.accent2);
card(s, 0.6, 1.4, 5.4, 1.3);
text(s, [{ text: "Sum-Product (forward-backward)", options: { bold: true, fontSize: 17, color: C.accent1, breakLine: true } },
  { text: "Sums over paths → p(regime | data) each day", options: { fontSize: 14 } }], 0.8, 1.5, 5.0, 1.3);
card(s, 0.6, 2.95, 5.4, 1.3);
text(s, [{ text: "Viterbi", options: { bold: true, fontSize: 17, color: C.accent2, breakLine: true } },
  { text: "Maximises over paths → single best regime sequence", options: { fontSize: 14 } }], 0.8, 3.1, 5.0, 1.1);
card(s, 0.6, 4.5, 5.4, 1.3, { fill: "D9F2E7", line: "D9F2E7" });
text(s, [{ text: "Coded in NumPy, verified", options: { bold: true, fontSize: 17, breakLine: true } },
  { text: "Matches hmmlearn exactly; checked against brute force", options: { fontSize: 14 } }], 0.8, 4.65, 5.0, 1.1);
img(s, "B7_predictive_loglik.png", 6.3, 1.4, { w: 6.45 });
text(s, "On unseen 2024–26 data the discrete HMM predicts best. The continuous Kalman LDS gives smooth volatility but cannot capture regime jumps.",
  6.3, 4.4, 6.45, 1.2, { fontSize: 15, color: C.text2 });
s.addNotes("Sum-Product gives the probability of each regime on each day; Viterbi gives the single best path. Both are written in NumPy and match the library exactly. We compared the HMM with a continuous Kalman-filter LDS on unseen data. The HMM predicts best, because volatility regimes matter more than trend.");

// 7. Conclusion
s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Short deck" });
text(s, "Conclusion", 0.8, 0.6, 11.7, 0.9, { fontSize: 36, bold: true, color: C.background1, fontFace: THEME.headFontFace });
[["Built", HEX.accent3, ["3 clustering methods + 3 distances", "HMM with our own Sum-Product and Viterbi", "Kalman LDS comparison · 31 tests"]],
 ["Learned", HEX.accent5, ["Stocks form 3 risk tiers", "Distance choice changes clusters", "Regimes beat smooth trends"]],
 ["Next", HEX.accent2, ["More stocks (NIFTY 100)", "Multivariate HMM", "Regime-aware portfolio"]]].forEach(([h, col, items], i) => {
  const x = 0.8 + i * 4.0;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.8, w: 3.75, h: 3.9, rectRadius: 0.08,
    fill: { color: "16304D" }, line: { color: "16304D" } });
  s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 2.12, w: 0.36, h: 0.36, fill: { color: col }, line: { color: col } });
  text(s, h, x + 0.8, 2.05, 2.7, 0.5, { fontSize: 20, bold: true, color: C.background1 });
  text(s, bullets(items, { fontSize: 16, color: "E3EAF2" }), x + 0.3, 2.85, 3.2, 2.7, { paraSpaceAfter: 10 });
});
text(s, "Thank you · Live demo: the notebook", 0.8, 6.15, 11.7, 0.5, { fontSize: 16, color: "CADCFC" });
s.addNotes("To sum up: we built and tested everything on real data. Stocks fall into three risk tiers, the choice of distance matters, and discrete regimes forecast better than smooth trends. Thank you.");

(async () => {
  const out = path.join(ROOT, "presentation", process.env.OUT_NAME || "project_review_2_short.pptx");
  await pres.writeFile({ fileName: out });
  if (SKILL_THEME) { const { applyTheme } = require(SKILL_THEME); await applyTheme(out, THEME); }
  console.log("wrote", out);
})();
