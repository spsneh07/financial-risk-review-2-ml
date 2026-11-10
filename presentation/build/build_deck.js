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

// =============================================================== 1. Title
pres.addSection({ title: "Introduction" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
s.addText("Financial Market Risk Profiling and Regime Detection", { placeholder: "title" });
s.addText("Clustering, Gaussian Mixture Models, Hidden Markov Models and Linear Dynamical Systems",
  { placeholder: "body" });
text(s, [
  { text: "Machine Learning · Project Review 2", options: { bold: true, breakLine: true, color: C.background1 } },
  { text: "Made by Srushti More [298], Agadh Khanolkar [299], Sneh Prasad [311] · 12 October 2026", options: { color: "CADCFC" } },
], 0.8, 5.4, 8.6, 0.8, { fontSize: 16 });
text(s, [{ text: "Unit III  Clustering & mixture models", options: { breakLine: true } },
  { text: "Unit IV  HMM, Sum-Product & LDS" }], 9.6, 5.4, 3.2, 0.8,
  { fontSize: 14, color: "CADCFC", align: "right" });
s.addNotes("Good morning. Our project has two parts that map to Units III and IV. Part A groups 12 NSE stocks into risk profiles with K-means, Gaussian mixtures and hierarchical clustering, and studies how the choice of distance changes the groups. Part B finds hidden market regimes in the NIFTY 50 with a Hidden Markov Model, runs exact Sum-Product inference that we coded ourselves, and compares it with a continuous Linear Dynamical System. Everything runs from one notebook on a laptop, and every number on these slides comes from that run.");

// =============================================================== 2. Problem & objectives
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
s.addText("Problem statement and objectives", { placeholder: "title" });
text(s, "Risk is not one number, and markets do not behave the same way all the time. We ask two questions:",
  0.6, 1.3, 12.1, 0.45, { fontSize: 16, color: C.text2 });
const objCards = [
  ["A", "Which stocks share a risk profile?", C.accent1, [
    "7 risk features per stock: return, volatility, skew, kurtosis, VaR, CVaR, drawdown",
    "Compare K-means, GMM and hierarchical clustering",
    "Test Manhattan, Cosine and Mahalanobis distances, with PCA",
    "Measure how stable the clusters are with ARI"]],
  ["B", "Which market regime are we in?", C.accent2, [
    "3-state Gaussian HMM fitted to NIFTY 50 daily returns",
    "Exact Sum-Product (forward-backward) posteriors, coded in NumPy",
    "Viterbi decoding as a separate max-product algorithm",
    "Compare with continuous LDS / Kalman models on held-out data"]],
];
objCards.forEach(([letter, head, col, items], i) => {
  const x = 0.6 + i * 6.2;
  card(s, x, 1.95, 5.9, 3.0, { name: `objective-${letter}` });
  s.addText(letter, { x: x + 0.3, y: 2.2, w: 0.6, h: 0.6, shape: pres.shapes.OVAL, fill: { color: col },
    color: C.background1, bold: true, fontSize: 20, align: "center", valign: "middle", isTextBox: true });
  text(s, head, x + 1.1, 2.25, 4.6, 0.55, { fontSize: 18, bold: true, fontFace: THEME.headFontFace });
  text(s, bullets(items), x + 0.35, 2.95, 5.3, 1.95, { fontSize: 14.5, paraSpaceAfter: 6 });
});
stat(s, 0.6, 5.45, 3.0, "12 stocks", "9 sectors, NSE, Oct 2021 to Sep 2026", C.accent1);
stat(s, 3.8, 5.45, 3.0, `${(B.train_days + B.test_days).toLocaleString("en-US")} days`, "NIFTY 50 returns, 2015 to Sep 2026", C.accent1);
stat(s, 7.0, 5.45, 2.6, "31 tests", "pytest: all pass", C.accent3);
stat(s, 9.8, 5.45, 3.0, "~1 min", "whole notebook, Restart & Run All, CPU", C.accent2);
s.addNotes("The problem: a single number like volatility hides the shape of risk, and a single model of the market ignores that markets switch between calm and stressed periods. Part A builds a 7-feature risk profile for each stock and clusters them. Part B infers hidden regimes over time. The numbers at the bottom are real: 12 stocks across 9 sectors, about 2,900 index days, 31 automated tests that all pass, and a full run of about half a minute.");

// =============================================================== 3. Architecture
pres.addSection({ title: "Method" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
s.addText("System architecture and workflow", { placeholder: "title" });
function box(x, y, w, h, head, body, fill, ink) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.1, fill: { color: fill },
    line: { color: fill, width: 0.5 }, objectName: `box-${head}` });
  text(s, [{ text: head, options: { bold: true, fontSize: 14, breakLine: true, color: ink } },
    { text: body, options: { fontSize: 11.5, color: ink } }], x + 0.12, y + 0.12, w - 0.24, h - 0.24,
    { paraSpaceAfter: 3 });
}
function arrow(x1, y1, x2, y2) {
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001,
    h: Math.abs(y2 - y1) || 0.001, flipV: y2 < y1, line: { color: "7A8794", width: 1.5, endArrowType: "triangle" } });
}
box(0.6, 1.55, 2.05, 4.75, "Data layer",
  "1. Cached CSV\n2. yfinance\n3. eod2 NSE dataset (GitHub)\n4. Synthetic fallback, always labelled\n\nAlign trading dates, forward-fill gaps of 3 days or less, log returns",
  HEX.dk1, HEX.lt1);
text(s, "PART A · Unit III · 12 stocks", 3.0, 1.3, 8, 0.3, { fontSize: 12, bold: true, color: C.accent1 });
text(s, "PART B · Unit IV · NIFTY 50", 3.0, 3.95, 8, 0.3, { fontSize: 12, bold: true, color: C.accent2 });
const xs = [3.0, 5.1, 7.2, 9.3], bw = 1.85;
const laneA = [["Risk features", "7 per stock, z-scored"], ["PCA", "3 PCs = 93% of variance"],
  ["Clustering", "K-means · GMM · Ward\n+ precomputed distances"], ["Evaluation", "Silhouette · DB · CH\nARI stability"]];
const laneB = [["Returns (%)", "Chronological split\ntrain ≤ 2023 < test"], ["Gaussian HMM", "Baum-Welch EM\n10 restarts"],
  ["Inference", "Sum-Product (ours)\nViterbi (ours)"], ["LDS / Kalman", "Trend + log-vol\npredictive test"]];
laneA.forEach(([h, b], i) => box(xs[i], 1.65, bw, 1.95, h, b, "D6E4F5", HEX.dk1));
laneB.forEach(([h, b], i) => box(xs[i], 4.3, bw, 1.95, h, b, "FBE1D6", HEX.dk1));
for (let i = 0; i < 3; i++) { arrow(xs[i] + bw, 2.62, xs[i + 1], 2.62); arrow(xs[i] + bw, 5.27, xs[i + 1], 5.27); }
arrow(2.65, 2.62, 3.0, 2.62); arrow(2.65, 5.27, 3.0, 5.27);
box(11.5, 1.55, 1.25, 4.75, "Outputs", "20 figures\n\nCSV tables\n\nresults .json\n\nslides", HEX.accent3, HEX.lt1);
arrow(xs[3] + bw, 2.62, 11.5, 2.62); arrow(xs[3] + bw, 5.27, 11.5, 5.27);
text(s, [{ text: "Run everything:  ", options: { bold: true } },
  { text: "Financial_Risk_Regime_Project.ipynb", options: { fontFace: "Courier New" } },
  { text: "  →  Restart & Run All (about 1 minute; ends with \"All checks passed\")", options: {} }], 0.6, 6.5, 12.1, 0.4, { fontSize: 13, color: C.text2 });
s.addNotes("This is the whole pipeline. The data layer tries a local cache first, then yfinance, then a public NSE end-of-day dataset on GitHub, and only then synthetic data, which is labelled synthetic on every chart. Prices are aligned to one trading calendar. Short gaps are forward-filled and never back-filled, so no future prices leak into the past. Part A turns each stock into 7 risk features, standardises them, applies PCA and clusters them. Part B splits index returns by date, fits the HMM on the training years only, runs our own inference code and compares it with Kalman models. Running the notebook top to bottom produces all figures and tables.");

// =============================================================== 4. Data & features
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
s.addText("Dataset, preprocessing and risk features", { placeholder: "title" });
tag(s, "PART A", C.accent1);
const rows = [
  ["Source", "NSE end-of-day closes (eod2 dataset), split and bonus adjusted"],
  ["Universe", "RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, HINDUNILVR, ITC, SUNPHARMA, MARUTI, TATASTEEL, BHARTIARTL, LT"],
  ["Window", `${A.window[0]} to ${A.window[1]}  ·  ${A.n_days.toLocaleString("en-US")} daily log returns`],
  ["Cleaning", "Common calendar; forward-fill gaps of 3 days or less; no back-fill"],
  ["Scaling", "StandardScaler (z-score) before any distance-based method"],
];
s.addTable(rows.map(([k, v]) => [{ text: k, options: { bold: true, color: C.text1 } }, { text: v }]),
  { x: 0.6, y: 1.35, w: 6.1, colW: [1.25, 4.85], fontSize: 12, color: C.text1, valign: "middle",
    border: { type: "solid", pt: 0.75, color: "D5DCE4" }, fill: { color: HEX.lt1 }, rowH: 0.5, margin: 0.06 });
card(s, 0.6, 4.35, 6.1, 2.2, { name: "feature-card" });
text(s, [
  { text: "Features per stock (daily log returns rₜ)", options: { bold: true, fontSize: 14, breakLine: true } },
  { text: "Mean return  ·  Volatility σ  ·  Skewness  ·  Excess kurtosis", options: { breakLine: true } },
  { text: "VaR₉₅ = −q₀.₀₅(r)       CVaR₉₅ = −E[ r | r ≤ q₀.₀₅ ]", options: { fontFace: "Cambria", breakLine: true } },
  { text: "Max drawdown = maxₜ (1 − Wₜ / maxₛ≤ₜ Wₛ),  Wₜ = exp(Σ r)", options: { fontFace: "Cambria", breakLine: true } },
  { text: "VaR, CVaR and volatility are highly correlated (ρ ≈ 0.95). This is why Mahalanobis distance and PCA matter.",
    options: { color: C.text2, fontSize: 12.5 } },
], 0.85, 4.5, 5.7, 2.25, { fontSize: 13.5, paraSpaceAfter: 5 });
img(s, "A2_risk_feature_heatmap.png", 7.0, 1.35, { w: 5.75, alt: "Standardised risk feature heatmap" });
text(s, "Red = above average, blue = below average. INFY, TCS and TATASTEEL have the deepest drawdowns, and ITC and LT the most negative skew.",
  7.0, 5.1, 5.75, 0.9, { fontSize: 12, color: C.text2 });
s.addNotes("We use real NSE data adjusted for splits and bonuses. The window is about five years, roughly 1,235 trading days. Each stock becomes seven features. VaR and CVaR are historical estimates at 95%, reported as positive losses. Max drawdown is the worst peak-to-trough fall. Features are z-scored because otherwise volatility, measured in percent, would be swamped by kurtosis, which is a large unitless number. The heatmap already shows the structure the clusters will find. One caveat: the data is adjusted for splits but not for dividends.");

// =============================================================== 5. Clustering algorithms
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
s.addText("Clustering: K-means, GMM and hierarchical", { placeholder: "title" });
tag(s, "PART A", C.accent1);
const algs = [
  ["K-means", "min Σₖ Σᵢ∈Cₖ ‖xᵢ − μₖ‖²", "Hard assignments; k-means++, 20 inits. Defined only for squared Euclidean distance."],
  ["Gaussian mixture (EM)", "p(x) = Σₖ πₖ 𝒩(x | μₖ, Σₖ)", "Soft assignments. Spherical covariance with a variance floor of 0.1, since n = 12 is too small for full Σ."],
  ["Agglomerative", "Ward: merge with min Δ SSE", "Ward, average and complete linkage compared. Ward needs Euclidean distance."],
];
algs.forEach(([h, eq, d], i) => {
  const y = 1.35 + i * 1.62;
  card(s, 0.6, y, 4.9, 1.45, { name: `alg-${i}` });
  text(s, [{ text: h, options: { bold: true, fontSize: 15, breakLine: true } },
    { text: eq, options: { fontFace: "Cambria", fontSize: 14, color: C.accent1, breakLine: true } },
    { text: d, options: { fontSize: 11.5, color: C.text2 } }], 0.8, y + 0.1, 4.55, 1.3, { paraSpaceAfter: 2 });
});
img(s, "A3_elbow_silhouette_bic.png", 5.75, 1.4, { w: 7.0, alt: "Elbow, silhouette and BIC curves" });
const ksel = A.gmm_best;
text(s, [
  { text: "Choosing k", options: { bold: true, fontSize: 15, breakLine: true } },
  ...bullets([
    `GMM BIC is lowest at k = ${ksel.k} (BIC 244.6, ${ksel.covariance} covariance)`,
    `K-means silhouette favours k = ${A.k_best_silhouette_kmeans} (0.361), so the criteria do not fully agree`,
    `K = ${A.K_used} kept for the main comparison, based on BIC, to support the risk-profile interpretation`,
    "Without the variance floor, BIC kept falling as k grew because components shrank onto 2 to 3 points (overfitting)",
  ], { fontSize: 13 }),
], 5.75, 3.75, 7.0, 3.0, { paraSpaceAfter: 5 });
s.addNotes("Three algorithms with three different objectives. K-means minimises within-cluster squared Euclidean distance, which is why we never call anything Manhattan K-means. A GMM is a probabilistic version fitted by EM. With only 12 assets a full covariance per component cannot be estimated, so we use spherical covariances with a variance floor. Ward linkage merges the pair of clusters that least increases the sum of squares, so it only makes sense with Euclidean distance. To choose k: GMM BIC is lowest at 3, but K-means silhouette favours 2, which just isolates two outliers, so the criteria do not fully agree. We kept K equals 3 for the main comparison, based on BIC, because it supports the risk-profile interpretation, and we say so openly.");

// =============================================================== 6. Distances & PCA
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
s.addText("Distance metrics and PCA", { placeholder: "title" });
tag(s, "PART A", C.accent1);
const mah = A.mahalanobis_notes;
const mets = [
  ["Manhattan", "d = Σⱼ |xⱼ − yⱼ|", "True metric, less sensitive to one extreme feature. Scale dependent, so we z-score first."],
  ["Cosine", "d = 1 − x·y / (‖x‖‖y‖)", "Compares the shape of the risk profile, not its size. Not a metric. Near-zero vectors are flagged (none here)."],
  ["Mahalanobis", "d² = (x−y)ᵀ S⁻¹ (x−y)", `Removes feature correlation. Raw S condition number ${Math.round(mah.cond_raw_cov)}; Ledoit-Wolf shrinkage (λ = ${f2(mah.shrinkage)}) brings it to ${f2(mah.cond_shrunk_cov)}; pseudo-inverse.`],
];
mets.forEach(([h, eq, d], i) => {
  const x = 0.6 + i * 4.1;
  card(s, x, 1.3, 3.9, 1.85, { name: `metric-${h}` });
  text(s, [{ text: h, options: { bold: true, fontSize: 15, breakLine: true } },
    { text: eq, options: { fontFace: "Cambria", fontSize: 14, color: C.accent1, breakLine: true } },
    { text: d, options: { fontSize: 11.5, color: C.text2 } }], x + 0.2, 1.4, 3.5, 1.7, { paraSpaceAfter: 2 });
});
img(s, "A7_distance_metric_comparison.png", 0.6, 3.35, { w: 8.9, alt: "Distance metric comparison" });
card(s, 9.75, 3.35, 3.0, 3.45, { name: "pca-card", fill: "FBE1D6", line: "FBE1D6" });
text(s, [
  { text: "Fair comparison", options: { bold: true, fontSize: 14, breakLine: true } },
  { text: "Every metric uses the same average-linkage clustering on a precomputed D, never Ward. Silhouette is computed in each metric's own D; DB and CH only in Euclidean space.", options: { fontSize: 12, breakLine: true } },
  { text: "PCA", options: { bold: true, fontSize: 14, breakLine: true } },
  { text: `PC1 ${pct(A.pca_explained[0])} (tail risk), PC2 ${pct(A.pca_explained[1])}, PC3 ${pct(A.pca_explained[2])}. 3 PCs keep 93%.`, options: { fontSize: 12 } },
], 9.95, 3.5, 2.65, 3.2, { paraSpaceAfter: 4 });
s.addNotes("For a fair metric comparison we hold the algorithm fixed: agglomerative average linkage on a precomputed distance matrix. Euclidean and Manhattan give the same partition here. Cosine finds the most separated groups in its own geometry, with silhouette 0.47, because it groups stocks by the shape of their risk profile rather than how extreme it is. Mahalanobis gives the lowest silhouette, but it stops the three nearly duplicate tail-risk features from counting three times. Its covariance was badly conditioned, so we used Ledoit-Wolf shrinkage plus a pseudo-inverse. On PCA: the first component is essentially tail risk, and three components keep 93% of the variance.");

// =============================================================== 7. Part A results
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Part A results: risk profiles and stability", { placeholder: "title" });
tag(s, "PART A", C.accent1);
img(s, "A5_pca_clusters.png", 0.6, 1.25, { w: 12.1, alt: "PCA scatter coloured by cluster" });
const sc = A.algorithm_scores;
const prof = [
  ["Cluster (Ward, K=3)", "Members", "Ann. vol", "CVaR₉₅", "Max DD"],
  ["0 · Low risk", "RELIANCE, HDFCBANK, ICICIBANK, HINDUNILVR, SUNPHARMA, MARUTI, BHARTIARTL", "21.3%", "3.0%", "26.8%"],
  ["1 · Tail risk", "ITC, LT  (skew −0.62, kurtosis 6.5)", "22.6%", "3.3%", "40.0%"],
  ["2 · High risk", "TCS, INFY, TATASTEEL", "26.4%", "4.0%", "49.3%"],
];
const cols = [HEX.accent4, HEX.accent2, HEX.accent3];
s.addTable(prof.map((r, i) => r.map((c, j) => ({ text: c, options: i === 0 ? { bold: true, color: C.background1, fill: { color: HEX.dk1 } }
  : (j === 0 ? { bold: true, color: C.background1, fill: { color: cols[i - 1] } } : {}) }))),
  { x: 0.6, y: 4.95, w: 7.6, colW: [1.55, 3.65, 0.8, 0.8, 0.8], fontSize: 11, color: C.text1, valign: "middle",
    border: { type: "solid", pt: 0.75, color: "D5DCE4" }, rowH: 0.42, margin: 0.05 });
const seeds = Object.fromEntries(A.stability_seeds.map((r) => [r.method, r.mean_ARI]));
const boot = Object.fromEntries(A.stability_bootstrap.map((r) => [r.method, r.mean_ARI]));
text(s, [
  { text: "Stability (ARI ignores label numbering)", options: { bold: true, fontSize: 14, breakLine: true } },
  ...bullets([
    `Seeds: K-means ARI ${f2(seeds["K-means (random init, n_init=1)"])} with one random start vs ${f2(seeds["K-means (k-means++, n_init=20)"])} with k-means++ (20 starts); Ward is deterministic`,
    `Block bootstrap (100×): ARI only ${f2(boot["GMM"])} to ${f2(boot["Avg-link Mahalanobis"])}; Mahalanobis is the most stable`,
    `Silhouette: Ward ${f2(sc.silhouette["Hierarchical (Ward)"])} · K-means ${f2(sc.silhouette["K-means"])} · GMM ${f2(sc.silhouette["GMM (spherical)"])}`,
  ], { fontSize: 12 }),
], 8.45, 4.95, 4.3, 1.95, { paraSpaceAfter: 4 });
s.addNotes("Ward has the best silhouette, so it is our main partition. Three groups appear. A low-risk core of seven names. A tail-risk pair, ITC and LT: their volatility is average, but returns are negatively skewed and fat-tailed, with a 40% drawdown. And a high-risk group: the two IT majors plus Tata Steel, with the largest CVaR and drawdowns near 50%. On stability, the honest finding is that with 12 assets, resampling the trading days changes the clusters a lot: bootstrap ARI is only about 0.26 to 0.50. Mahalanobis is the most stable. K-means with a single random start is unstable, and k-means++ with 20 starts fixes most of that. Note that the PCA plot is for visualisation only; it does not prove the clusters are good.");

// =============================================================== 8. HMM
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Hidden Markov Model: transitions and emissions", { placeholder: "title" });
tag(s, "PART B", C.accent2);
card(s, 0.6, 1.3, 4.4, 4.75, { name: "hmm-def" });
const ms = B.model_selection;
text(s, [
  { text: "Model", options: { bold: true, fontSize: 15, breakLine: true } },
  { text: "zₜ ∈ {1,2,3},  p(z₁) = π", options: { fontFace: "Cambria", breakLine: true } },
  { text: "p(zₜ = j | zₜ₋₁ = i) = Aᵢⱼ", options: { fontFace: "Cambria", breakLine: true } },
  { text: "yₜ | zₜ = k  ~  𝒩(μₖ, σₖ²)", options: { fontFace: "Cambria", breakLine: true } },
  { text: `Fitted by Baum-Welch on ${B.train_days} training days (2015 to 2023), best of 10 random restarts`, options: { fontSize: 12, color: C.text2, breakLine: true } },
  { text: "Naming rule (state ids are arbitrary)", options: { bold: true, fontSize: 15, breakLine: true } },
  ...bullets(["Largest σ → High-Volatility", "Of the other two: higher μ → Bull, lower μ → Bear"], { fontSize: 13 }, true),
  { text: `BIC: 1 state ${Math.round(ms[0].bic)} · 2 states ${Math.round(ms[1].bic)} · 3 states ${Math.round(ms[2].bic)} · 4 states ${Math.round(ms[3].bic)} → BIC is lowest at 3 states`,
    options: { fontSize: 12, color: C.text2, breakLine: true } },
  { text: `4 states has slightly better test log-lik (${ms[3].test_loglik_per_day.toFixed(4)} vs ${ms[2].test_loglik_per_day.toFixed(4)}/day); we keep 3 for the Bull / Bear / High-Vol interpretation`,
    options: { fontSize: 12, color: C.text2 } },
], 0.85, 1.45, 4.0, 5.3, { fontSize: 14, paraSpaceAfter: 5 });
img(s, "B4_transition_emissions.png", 5.25, 1.35, { w: 7.5, alt: "Transition matrix and emission densities" });
const rs = Object.fromEntries(B.regime_stats.map((r) => [r.regime, r]));
const hvState = Object.keys(B.state_names).find((k) => B.state_names[k] === "High-Volatility");
text(s, [
  { text: "What the model learned", options: { bold: true, fontSize: 14, breakLine: true } },
  ...bullets([
    "Bull and Bear are very persistent (stay probability 0.988 and 0.981; expected runs of about 86 and 51 days)",
    `High-Volatility (σ ≈ 3.9%/day) is short (about 7 days) and always exits to Bear, never straight to Bull`,
    `"Bear" has a mean near 0 (−0.003%) and σ ≈ 1.05%: in practice a choppy, risk-off regime more than a crash`,
  ], { fontSize: 12.5 }),
], 5.25, 4.1, 7.5, 2.7, { paraSpaceAfter: 4 });
s.addNotes("The HMM has three hidden states, a transition matrix and one Gaussian per state for daily percent returns. We fit it on 2015 to 2023 only, with ten random restarts of EM, and keep the best likelihood. We never assume state 0 means Bull: names come from the learned parameters. The largest variance is High-Volatility, and of the other two the higher mean is Bull. BIC selects three states as the best balance of fit and complexity, although a four-state model scores slightly better on held-out likelihood; we keep three because they map onto Bull, Bear and High-Volatility, so the best number of states depends on the criterion. The transition matrix is easy to read: calm regimes persist for weeks or months, and the crisis state lasts about a week and always passes through Bear on the way back. The Bear label is a statistical interpretation: its mean is close to zero, so it is better described as choppy or risk-off.");

// =============================================================== 9. Sum-product vs Viterbi
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Sum-Product versus Viterbi decoding", { placeholder: "title" });
tag(s, "PART B", C.accent2);
card(s, 0.6, 1.3, 2.95, 2.45, { name: "sp-card" });
text(s, [
  { text: "Sum-Product", options: { bold: true, fontSize: 15, color: C.accent1, breakLine: true } },
  { text: "αₜ(j) = bⱼ(yₜ) Σᵢ αₜ₋₁(i) Aᵢⱼ", options: { fontFace: "Cambria", fontSize: 12.5, breakLine: true } },
  { text: "βₜ(i) = Σⱼ Aᵢⱼ bⱼ(yₜ₊₁) βₜ₊₁(j)", options: { fontFace: "Cambria", fontSize: 12.5, breakLine: true } },
  { text: "γₜ(i) = αₜ(i) βₜ(i) / p(y₁:T)", options: { fontFace: "Cambria", fontSize: 12.5, breakLine: true } },
  { text: "Sums over all paths. Gives the marginal p(zₜ | all data) for each day.", options: { fontSize: 11.5, color: C.text2 } },
], 0.75, 1.4, 2.7, 2.85, { paraSpaceAfter: 4 });
card(s, 3.7, 1.3, 2.95, 2.45, { name: "viterbi-card" });
text(s, [
  { text: "Viterbi", options: { bold: true, fontSize: 15, color: C.accent2, breakLine: true } },
  { text: "δₜ(j) = bⱼ(yₜ) maxᵢ δₜ₋₁(i) Aᵢⱼ", options: { fontFace: "Cambria", fontSize: 12.5, breakLine: true } },
  { text: "ψₜ(j) = argmaxᵢ δₜ₋₁(i) Aᵢⱼ", options: { fontFace: "Cambria", fontSize: 12.5, breakLine: true } },
  { text: "then trace back the pointers", options: { fontSize: 12.5, breakLine: true } },
  { text: "Maximises over paths. Gives one jointly most likely sequence z*.", options: { fontSize: 11.5, color: C.text2 } },
], 3.85, 1.4, 2.7, 2.85, { paraSpaceAfter: 4 });
text(s, [
  { text: "Verified (log-space, NumPy)", options: { bold: true, fontSize: 14, breakLine: true } },
  ...bullets([
    `log p(y₁:T) identical to hmmlearn: ${B.loglik_ours.toFixed(3)}`,
    `max |γ − γ_hmmlearn| = ${B.max_gamma_diff_vs_hmmlearn.toExponential(1)}; every row sums to 1`,
    "Toy 2-state HMM: matches enumeration of all 8 paths (p(y) = 0.10248)",
    `Viterbi = hmmlearn on 100% of days; differs from argmax γ on ${(100 * (1 - B.viterbi_vs_posterior_argmax_agreement)).toFixed(1)}% of days`,
  ], { fontSize: 12 }),
], 0.6, 4.0, 6.05, 2.6, { paraSpaceAfter: 6 });
img(s, "B5_sumproduct_vs_viterbi_2020.png", 6.9, 1.3, { w: 5.85, alt: "Sum-product vs Viterbi in 2020" });
text(s, "2020 COVID crash. Filtered (orange) is real-time: it uses data up to day t only. Smoothed (blue) and the full-sequence Viterbi path are retrospective: they use the whole series.",
  6.9, 4.55, 5.85, 0.8, { fontSize: 12, color: C.text2 });
s.addNotes("This is the key distinction. Sum-Product, the forward-backward algorithm, sums over every possible state sequence and gives, for each day, the probability of each regime given all the data. Viterbi replaces the sum with a max and returns the single most probable whole path. They can disagree, and here they do on about 3.7% of days, because the best path is not the same as picking the best state each day. We wrote both in NumPy in log space with log-sum-exp, so 2,900 steps do not underflow. We checked them three ways: same likelihood as hmmlearn, same posteriors to 1e-12, and on a toy example against brute-force enumeration of all 8 paths. The 2020 plot shows the regime switching into High-Volatility in March and leaving in May. The smoothed curve and the Viterbi path are retrospective, since they use the whole series; only the filtered curve is what we would have known in real time.");

// =============================================================== 10. LDS
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Continuous LDS (Kalman filter) versus HMM", { placeholder: "title" });
tag(s, "PART B", C.accent2);
card(s, 0.6, 1.3, 4.6, 2.2, { name: "lds-eq" });
const lv = B.lds_vol;
text(s, [
  { text: "Linear-Gaussian state space", options: { bold: true, fontSize: 15, breakLine: true } },
  { text: "xₜ = F xₜ₋₁ + c + wₜ,   wₜ ~ 𝒩(0, Q)", options: { fontFace: "Cambria", fontSize: 13, breakLine: true } },
  { text: "yₜ = H xₜ + d + vₜ,   vₜ ~ 𝒩(0, R)", options: { fontFace: "Cambria", fontSize: 13, breakLine: true } },
  { text: "Kₜ = Pₜ|ₜ₋₁Hᵀ(HPₜ|ₜ₋₁Hᵀ + R)⁻¹", options: { fontFace: "Cambria", fontSize: 13, breakLine: true } },
  { text: "NumPy Kalman filter + RTS smoother; Q and R fitted by maximum likelihood on training data", options: { fontSize: 11.5, color: C.text2 } },
], 0.8, 1.4, 4.25, 2.6, { paraSpaceAfter: 4 });
text(s, [
  { text: "Two LDS models", options: { bold: true, fontSize: 14, breakLine: true } },
  ...bullets([
    "LDS-Trend: random-walk drift of returns. MLE gives Q → 0, so the drift is constant: daily returns have no predictable trend",
    `LDS-Vol: AR(1) log-variance on log r² (quasi-likelihood). φ = ${f3(lv.phi)}, half-life ≈ ${Math.round(lv.half_life_days)} days`,
  ], { fontSize: 12.5 }),
], 0.6, 3.75, 4.6, 2.9, { paraSpaceAfter: 8 });
img(s, "B6_hmm_vs_lds.png", 5.45, 1.3, { w: 7.3, alt: "HMM vs LDS latent estimates" });
text(s, `Volatility estimates both follow 21-day realised volatility (correlation: HMM ${f2(B.corr_realised_vol.hmm)}, LDS-Vol ${f2(B.corr_realised_vol.lds_vol)}). The HMM jumps; the LDS moves smoothly.`,
  5.45, 5.15, 7.3, 0.7, { fontSize: 12, color: C.text2 });
s.addNotes("The LDS has a continuous hidden state instead of a discrete one. We implemented the Kalman filter and the Rauch-Tung-Striebel smoother ourselves and fitted the noise variances by maximum likelihood. The first model treats expected return as a slowly drifting random walk. The data pushes the drift noise to zero, which is a genuine finding: there is no exploitable trend in daily index returns. The second treats log-volatility as a mean-reverting AR(1), observed through log squared returns, a standard linearisation. It gives a smooth volatility curve with a two-month half-life. The HMM curve jumps between three levels. Both track realised volatility with correlation around 0.8. The HMM and LDS are not equivalent models: one has discrete states, the other continuous ones.");

// =============================================================== 11. Results & limitations
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Results, limitations and discussion", { placeholder: "title" });
img(s, "B1_nifty_regimes_viterbi.png", 0.6, 1.25, { w: 6.9, alt: "NIFTY regimes" });
img(s, "B7_predictive_loglik.png", 0.6, 3.95, { w: 6.9, alt: "Predictive log likelihood" });
card(s, 7.75, 1.25, 5.0, 2.45, { name: "findings" });
const pc = Object.fromEntries(B.predictive_comparison.map((r) => [r.model.split(" ")[0], r.test_loglik_per_day]));
text(s, [
  { text: "Findings (held-out test: Jan 2024 to Sep 2026)", options: { bold: true, fontSize: 14, breakLine: true } },
  ...bullets([
    `HMM-3 beats the i.i.d. baseline by ${f3(pc["HMM-3"] - pc["i.i.d."])} nats/day; LDS-Vol by ${f3(pc["LDS-Vol"] - pc["i.i.d."])}; LDS-Trend by about 0`,
    "Scoring: one-step predictive density p(yₜ | y₁:ₜ₋₁), same data and units for all models",
    `Test-period shares (retrospective Viterbi labels): ${Math.round(rs.Bull["share_test_%"])}% Bull, ${Math.round(rs.Bear["share_test_%"])}% Bear, under 1% High-Vol`,
  ], { fontSize: 12.5 }),
], 7.95, 1.35, 4.65, 2.3, { paraSpaceAfter: 4 });
card(s, 7.75, 3.9, 5.0, 2.9, { name: "limits", fill: "FBE1D6", line: "FBE1D6" });
text(s, [
  { text: "Limitations (stated openly)", options: { bold: true, fontSize: 14, breakLine: true } },
  ...bullets([
    "Only 12 assets, so cluster stability under resampling is modest (ARI about 0.3 to 0.5)",
    "Regime names are statistical; \"Bear\" has a mean near 0",
    "LDS-Vol density is a quasi-likelihood approximation (marked *)",
    "Prices adjusted for splits and bonuses, not dividends; yfinance was blocked in the build environment, so the NSE GitHub dataset was used",
    "HMM-4 fits the test data slightly better (−1.1726 vs −1.1744) but has a worse BIC",
  ], { fontSize: 12 }),
], 7.95, 4.0, 4.65, 2.75, { paraSpaceAfter: 3 });
s.addNotes("Top left: the Viterbi regimes over eleven years. High-Volatility marks the COVID crash, Bull covers the 2017 and 2023 to 2024 rallies, and Bear covers 2015 to 2016 and the late-2024 correction. The parameters were fitted only on data up to 2023, but the regime colours come from full-sequence Viterbi decoding, so they are a retrospective labelling, not real-time predictions. Bottom left is the fair comparison: each model gives a predictive density for tomorrow's return using only past data, scored on the test period. The HMM is clearly best, LDS-Vol helps because it captures volatility clustering, and LDS-Trend equals the baseline. The limitations on the right are stated openly, especially the small number of assets and that regime names are interpretations.");

// =============================================================== 12. Conclusion
pres.addSection({ title: "Conclusion" });
s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Conclusion" });
text(s, "Conclusion and future scope", 0.8, 0.5, 11.7, 0.9, { fontSize: 36, bold: true, color: C.background1, fontFace: THEME.headFontFace });
const concl = [
  ["Implemented and verified", HEX.accent3, [
    "K-means, GMM, Ward / average / complete linkage on real NSE data",
    "Manhattan, Cosine and Mahalanobis (shrinkage + pseudo-inverse); PCA; ARI stability",
    "3-state Gaussian HMM with our own Sum-Product and Viterbi, checked against hmmlearn and brute force",
    "Kalman filter, RTS smoother and two MLE-fitted LDS models, with a fair predictive comparison",
    "One self-contained notebook and 31 passing tests"]],
  ["Key takeaways", HEX.accent5, [
    "Three risk tiers: core, tail-risk (ITC, LT), high-risk (IT majors + steel)",
    "The choice of distance changes the clusters (ARI as low as 0.14)",
    "Discrete regimes forecast better than a continuous trend, because volatility clustering matters more than drift"]],
  ["Future scope (not built)", HEX.accent2, [
    "Larger universe (NIFTY 100 or 500) for more stable clusters",
    "Multivariate HMM emissions (returns + volatility + breadth)",
    "Student-t emissions; switching LDS; regime-aware portfolio backtest"]],
];
concl.forEach(([h, col, items], i) => {
  const x = 0.8 + i * 4.0;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.6, w: 3.75, h: 4.6, rectRadius: 0.08,
    fill: { color: "16304D" }, line: { color: "16304D", width: 0.5 }, objectName: `concl-${i}` });
  s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: 1.85, w: 0.32, h: 0.32, fill: { color: col }, line: { color: col } });
  text(s, h, x + 0.7, 1.8, 2.9, 0.45, { fontSize: 16, bold: true, color: C.background1 });
  text(s, bullets(items, { fontSize: 14, color: "E3EAF2" }), x + 0.25, 2.45, 3.3, 3.7, { paraSpaceAfter: 8 });
});
s.addNotes("To conclude: everything in the green column is implemented, run on real data and covered by tests. The yellow column holds the main lessons: risk profiles depend on the distance you choose, and for daily index returns, modelling volatility regimes matters far more than modelling drift. The orange column is future work that we have not built. Thank you, and we are happy to take questions or run the live demo.");

(async () => {
  const out = path.join(ROOT, "presentation", "project_review_2.pptx");
  await pres.writeFile({ fileName: out });
  if (SKILL_THEME) {
    const { applyTheme } = require(SKILL_THEME);
    await applyTheme(out, THEME);
  }
  console.log("wrote", out);
})();
