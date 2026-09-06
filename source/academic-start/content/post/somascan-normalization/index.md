---
title: "SomaScan Normalization: Steps, Equations, and Rationale"
subtitle: "Steps, equations, and the reasoning behind each stage of the standard pre-processing pipeline"
summary: "A technical note on the five-stage SomaScan preprocessing pipeline, including its normalization equations and rationale."
authors:
  - admin
tags:
  - SomaScan
  - Proteomics
  - Normalization
  - Bioinformatics
categories:
  - Technical Notes
date: "2026-07-14"
lastmod: "2026-07-14"
featured: false
weight: 10
draft: false
toc: true
math: true
external_link: "/notes/somascan-normalization/"
---

> This document follows, notation-for-notation, the pipeline and equations described in Candia, J. *"SomaScan Bioinformatics: Normalization, Quality Control, and Assessment of Pre-Analytical Variation."* bioRxiv 2024.02.09.579724 (2024) — the only source used here that publishes the actual mathematical steps and accompanying R implementation, rather than a narrative description.

---

## Table of Contents

1. [Overview of the pipeline](#overview-of-the-pipeline)
2. [Why normalize at all?](#why-normalize-at-all)
3. [Step 1 — Hybridization control normalization](#step-1--hybridization-control-normalization-hyb)
4. [Step 2 — Median signal normalization on calibrators](#step-2--median-signal-normalization-on-calibrators-hybmsncal)
5. [Step 3 — Plate-scale normalization](#step-3--plate-scale-normalization-hybmsncalps)
6. [Step 4 — Inter-plate calibration](#step-4--inter-plate-calibration-hybmsncalpscal)
7. [Step 3 vs. Step 4 — what's actually different](#step-3-vs-step-4--whats-actually-different-and-why-both-are-needed)
8. [Step 5 — Median signal normalization on all sample types](#step-5--median-signal-normalization-on-all-sample-types-hybmsncalpscalmsnall)
9. [The one idea behind all five steps](#the-one-idea-behind-all-five-steps)
10. [SomaLogic's ANML (context)](#somalogics-anml-context--not-part-of-this-papers-own-pipeline)
11. [Validation vs. SomaLogic's pipeline](#validation-does-the-internal-reference-pipeline-match-somalogics-own-output)
12. [Applied scenarios](#applied-scenarios-normalization-in-practice)
13. [References](#references)

---

## Overview of the pipeline

Candia (2024) formalizes SomaScan normalization as a five-step sequence, each producing a named, versioned RFU matrix. The paper's own naming convention (used internally in the accompanying R code) chains each step's abbreviation onto the last, which is a useful way to keep track of exactly what has and hasn't been corrected at any given point *(Candia 2024, Table 2)*.

```
Raw (raw)
  → 1. Hybridization (hyb)
    → 2. Median, calibrators only (hyb.msnCal)
      → 3. Plate-scale (hyb.msnCal.ps)
        → 4. Calibration (hyb.msnCal.ps.cal)
          → 5. Median, all sample types (hyb.msnCal.ps.cal.msnAll)
```

| Step | Name | Abbreviation | Scale factor granularity |
|---|---|---|---|
| 0 | Raw | `raw` | none |
| 1 | Hybridization control normalization | `hyb` | well-specific |
| 2 | Median signal normalization on calibrators | `hyb.msnCal` | calibrator- and dilution-specific |
| 3 | Plate-scale normalization | `hyb.msnCal.ps` | plate-specific (one number per plate) |
| 4 | Inter-plate calibration | `hyb.msnCal.ps.cal` | plate- **and** SOMAmer-specific |
| 5 | Median signal normalization on all sample types | `hyb.msnCal.ps.cal.msnAll` | well-specific (grouped by sample type) |

*(Candia 2024, Table 2)*. The last column is the key thing to track through this document: each step generates scale factors at a different level of granularity, and later steps generally operate on finer subdivisions of the data than earlier ones — which is exactly the relationship between Steps 3 and 4 discussed below.

---

## Why normalize at all?

SomaScan is a highly multiplexed, aptamer-based assay that simultaneously measures thousands of human proteins spanning femto- to micro-molar concentrations, using SOMAmer (Slow Offrate Modified Aptamer) reagents selected via the SELEX process for high affinity, slow off-rate, and high specificity to their protein targets *(Candia 2024, "The SomaScan assay")*. Samples are organized in 96-well plates alongside buffer, calibrator, and QC wells provided by SomaLogic from pooled healthy donor controls *(Candia 2024)*.

> **Core reasoning**
> Raw data, as obtained after aggregation from the slide-based hybridization microarrays, exhibits intra-plate nuisance variance due to differences in loading volume, leaks, washing conditions, and similar sources, which is then compounded with batch effects across plates *(Candia 2024, "Data Normalization Procedures")*. The five-step sequence exists specifically to account for this intra- and inter-plate variability across buffer, calibrator, QC, and experimental samples, while preserving genuine biological differences *(Candia 2024)*.

---

## Step 1 — Hybridization Control Normalization (hyb)

Hybridization control normalization is designed to adjust for nuisance variance on the basis of individual wells. Each well contains n<sub>HCE</sub> = 12 Hybridization Control Elution (HCE) SOMAmers at different concentrations spanning more than three orders of magnitude *(Candia 2024, Step 1)*.

**Reasoning — why this step is first**
This is the finest-grained correction in the pipeline, operating at the level of a single well before any comparison across samples or plates is made. Because HCE probes are added at a fixed, known concentration with no biological content, any well-to-well variation in their signal must be purely technical, giving a clean per-well correction factor.

**Equations**

Scale factor for the *i*-th well (Eq. 1):

```
SF_i = median_α ( RFU^HCE,ref_α / RFU^HCE,obs_iα )      for α = 1,...,n_HCE
```

Internal (plate-specific) reference (Eq. 2):

```
RFU^HCE,ref_α ≡ median_i { RFU^HCE,obs_iα }              for i = 1,...,n_s
```

- `α` — indexes the n<sub>HCE</sub> = 12 HCE SOMAmers (Greek subscripts denote SOMAmers throughout this paper's notation)
- `i` — indexes wells (Latin subscripts denote wells/samples)
- `n_s` — number of wells on the plate (96)
- `RFU^HCE,ref_α` — reference RFU for HCE SOMAmer α, taken here as the median across all wells on the plate (an internal reference), rather than an external fixed value

Once SF<sub>i</sub> is determined for well *i*, every SOMAmer's RFU in that well is multiplied by the same scale factor *(Candia 2024, Step 1)*.

*Source: Candia 2024, bioRxiv 2024.02.09.579724, Eqs. 1–2*

---

## Step 2 — Median Signal Normalization on Calibrators (hyb.msnCal)

Median signal normalization is an intra-plate procedure performed within wells of the same sample class (buffer, QC, calibrator, or experimental) and within SOMAmers of the same dilution group. It is intended to remove sample-to-sample differences in total RFU brightness arising from differences in overall protein concentration, pipetting variation, reagent concentration variation, assay timing, and similar sources within a group of otherwise comparable samples *(Candia 2024, Step 2)*.

**Reasoning — why restrict this step to calibrators only, at this stage**
Performing median signal normalization on experimental samples *before* inter-plate calibration risks enhancing plate-to-plate differences, as discussed in the author's earlier work *(Candia 2024, citing Candia et al. 2017)*. So at this point in the pipeline, the step is deliberately restricted to calibrator wells only — experimental samples get their own median normalization later, in Step 5, after plate-level effects have been removed.

**Equations**

Ratio for sample *i*, SOMAmer α (Eq. 3):

```
r^gd_iα = RFU_iα / median_j { RFU_jα }                   for j = 1,...,n^g_s
```

Scale factor for sample *i* (Eq. 4):

```
SF^gd_i = 1 / median_α { r^gd_iα }                        for α = 1,...,n^d_SOMAmer
```

- `g` — sample type grouping (here, calibrator)
- `d` — SOMAmer dilution grouping
- `n^g_s` — number of samples of type g
- `n^d_SOMAmer` — number of SOMAmers in dilution group d

To median-normalize sample *i*, all its SOMAmer RFUs within the same dilution group are multiplied by SF<sup>gd</sup><sub>i</sub> *(Candia 2024, Step 2)*.

*Source: Candia 2024, Eqs. 3–4*

---

## Step 3 — Plate-Scale Normalization (hyb.msnCal.ps)

Plate-scale normalization aims to control for variance in total signal intensity from plate to plate. No protein spikes are added to the calibrator for this purpose — the procedure relies solely on the endogenous levels of each protein within the set of calibrator replicates already present on the plate *(Candia 2024, Step 3)*.

**Reasoning — why the whole plate is corrected by one number**
At this stage, the goal is specifically to correct the overall brightness level of an entire plate — a single multiplicative drift affecting the whole run (for example, from reagent lot or day-to-day instrument variation). Collapsing many per-SOMAmer estimates down to one plate-wide median scale factor is what makes this a genuinely plate-level (rather than SOMAmer-level) correction.

**Equations**

SOMAmer-and-plate-specific ratio, for SOMAmer α on plate *p* (Eq. 5):

```
SF^p_α = RFU^Cal,ref_α / median_i { RFU^Cal,obs_iα }^p    for i = 1,...,n_Cal
```

Internal interplate reference (Eq. 6):

```
RFU^Cal,ref_α ≡ median_{p,i} { RFU^Cal,obs_iα }           for p = 1,...,n_p; i = 1,...,n_Cal
```

Plate-scale factor — collapsed across all SOMAmers (Eq. 7):

```
SF^p = median_α { SF^p_α }                                for α = 1,...,n_SOMAmer
```

- `n_Cal` — number of calibrator replicates per plate
- `n_p` — total number of plates in the study
- `RFU^Cal,ref_α` — the interplate reference for SOMAmer α, i.e. the median across *all* calibrators on *all* plates
- `SF^p` — the single number applied to every SOMAmer, in every well, on plate p

For all wells on plate *p* and all SOMAmers, RFUs are multiplied by this single plate-scale factor SF<sup>p</sup> *(Candia 2024, Step 3)*.

*Source: Candia 2024, Eqs. 5–7*

---

## Step 4 — Inter-Plate Calibration (hyb.msnCal.ps.cal)

The paper states this step directly:

> "Following plate-scale normalization, we recalculate SOMAmer- and plate-specific scale factors via Eqs. (5)-(6). Separately for each SOMAmer and plate, all wells on the plate are corrected by the recalculated SF<sup>p</sup><sub>α</sub>." *(Candia 2024, Step 4)*

**Equations**

Recalculated SOMAmer-and-plate-specific ratio (re-applying Eq. 5, on already plate-scaled data):

```
SF^p_α = RFU^Cal,ref_α / median_i { RFU^Cal,obs_iα }^p    for i = 1,...,n_Cal
```

Recalculated internal reference (re-applying Eq. 6, on already plate-scaled data):

```
RFU^Cal,ref_α ≡ median_{p,i} { RFU^Cal,obs_iα }
```

Applied correction — **note this is NOT collapsed by median across SOMAmers**:

```
RFU_iα^(4) = RFU_iα^(3) × SF^p_α        (applied per SOMAmer α, per plate p)
```

*Source: Candia 2024, "Inter-plate calibration" section, re-using Eqs. 5–6*

---

## Step 3 vs. Step 4 — What's Actually Different, and Why Both Are Needed

Steps 3 and 4 use the **identical** ratio equation (Eq. 5) and the identical reference definition (Eq. 6). The entire difference between them is **what happens after that ratio is computed**, and **what data it's computed on**.

| | Step 3 (Plate-scale) | Step 4 (Calibration) |
|---|---|---|
| **Input data** | Data after Steps 1–2 only (hyb.msnCal) | Data *after* plate-scaling has already been applied (hyb.msnCal.ps) |
| **SF<sup>p</sup><sub>α</sub> computed?** | Yes — per SOMAmer, per plate (Eq. 5) | Yes — *recalculated* per SOMAmer, per plate, on the new plate-scaled values |
| **Final collapsing step** | Collapsed: `SF^p = median_α(SF^p_α)` — one number per plate (Eq. 7) | **Not collapsed.** Every SOMAmer keeps its own scale factor per plate |
| **What gets corrected** | Overall plate brightness — a single multiplicative shift applied uniformly to every SOMAmer on the plate | Each SOMAmer's individual residual plate-to-plate drift, independent of every other SOMAmer |
| **Granularity** | Plate-specific | Plate- *and* SOMAmer-specific |

> **Why Step 4 is still needed after Step 3**
>
> Step 3's median-across-SOMAmers collapse (Eq. 7) is a deliberate simplification: it assumes that once you strip out the single dominant, plate-wide brightness shift, everything else is noise around zero — i.e., that all SOMAmers on a plate drifted by the same overall multiplicative amount. That assumption is good enough to fix the biggest source of inter-plate variance, but it is not exact. Individual SOMAmer reagents can still carry their own residual, SOMAmer-specific plate-to-plate drift after the shared drift has been removed — for instance, from reagent-lot-specific binding efficiency differences that don't affect every SOMAmer equally.
>
> Step 4 targets exactly this leftover, individual variation. Because it reuses Eqs. 5–6 on the plate-scaled data *without* collapsing to a single median value, it recovers a distinct scale factor for every SOMAmer on every plate, correcting the SOMAmer-specific residual that survived the coarser, plate-wide Step 3 correction.
>
> **In short: Step 3 removes the shared (plate-level) component of inter-plate variance; Step 4 removes what's left over at the level of each individual SOMAmer.** Running Step 4 without Step 3 first would conflate these two different sources of drift; running Step 3 alone would leave SOMAmer-specific drift uncorrected.

*Source: Candia 2024, "Inter-plate calibration" section — "Following plate-scale normalization, we recalculate SOMAmer- and plate-specific scale factors..."*

---

## Step 5 — Median Signal Normalization on All Sample Types (hyb.msnCal.ps.cal.msnAll)

At this stage, after correcting plate-to-plate variability to the fullest extent possible, median signal normalization (the same procedure as Step 2, Eqs. 3–4) is performed separately on each sample type — QC, experimental samples, buffer, and calibrator — rather than being restricted to calibrators only. This yields the final, fully normalized dataset *(Candia 2024, Step 5)*.

**Reasoning — why experimental samples wait until now**
This mirrors the logic given for restricting Step 2 to calibrators: applying median normalization to experimental samples earlier, before plate-level effects (Steps 3–4) were removed, risked amplifying plate-to-plate differences rather than correcting for genuine sample-to-sample brightness variation. Once the plate has been fully calibrated, it's safe to apply the same median-normalization logic to every sample type.

*Source: Candia 2024, Step 5, reusing Eqs. 3–4*

---

## The One Idea Behind All Five Steps

Every step in this pipeline is doing the same basic thing: **matching something to a standard.** What changes from step to step is which unit gets matched, and which reference is used as the standard to match it against.

| Step | What gets matched | The standard it's matched to |
|---|---|---|
| **1. Hybridization** | Each *well* | That well's own hybridization control signal |
| **2. Median signal (calibrators)** | Each *calibrator sample* | The median signal of all calibrators on the plate |
| **3. Plate-scale** | Each *plate*, as a whole | The median calibrator level across all plates — one shared correction applied to everything on the plate |
| **4. Calibration** | Each *SOMAmer*, individually | That same SOMAmer's own median level across all plates — a separate correction for every SOMAmer |
| **5. Median signal (all samples)** | Each *sample*, of any type | The median signal across all samples of that same type |

So the pipeline isn't five different ideas — it's one idea, "match to a standard," repeated at five different levels of granularity: well, calibrator sample, plate, SOMAmer, and finally every sample. Each step simply picks a different unit to correct and a different reference to correct it against.

---

## SomaLogic's ANML (Context — Not Part of This Paper's Own Pipeline)

It's worth being precise about scope here: Candia (2024)'s five-step pipeline above is an **independent, internal-reference-only reconstruction** of SomaScan normalization, built specifically so that users aren't dependent on SomaLogic's proprietary external references. SomaLogic's own delivered `adat` files instead follow a related but not identical sequence that uses external references and adds an additional adaptive normalization by maximum likelihood (ANML) step, delivered in files with a suffix such as `hybNorm.medNormInt.plateScale.calibrate.anmlQC.qcCheck.anmlSMP` *(Candia 2024, "Summary and Conclusions")*.

> **Why this distinction matters**
> SomaLogic's pipeline has historically operated as a largely undocumented process, described to users only at a narrative level, and has changed over time — switching from internal to external references, reordering median normalization, and splitting inter-plate calibration into the plate-scale-then-calibration structure described above — without shared version control, which makes it hard to compare studies run years apart or on different assay versions *(Candia 2024, "Summary and Conclusions")*.

---

## Validation: Does the Internal-Reference Pipeline Match SomaLogic's Own Output?

Using nearly 1,800 experimental samples from the Baltimore Longitudinal Study on Aging (BLSA), the author compared, for each of the 7,289 human protein SOMAmers in the 7K plasma assay, the Spearman correlation between SomaLogic's own fully normalized external-reference output and the fully normalized internal-reference pipeline described above *(Candia 2024, "Summary and Conclusions")*. The distribution of per-SOMAmer correlations across all 7,289 SOMAmers had a median of r = 0.996, indicating the two approaches are highly concordant despite using entirely different reference schemes *(Candia 2024, Fig. 6)*.

Because this is a Spearman correlation, which is invariant to any monotonic transformation of the data (including a log transform), this concordance holds regardless of what scale the RFU values are subsequently analyzed on *(Candia 2024, "Summary and Conclusions")*.

*Source: Candia 2024, Fig. 6 and accompanying text*

---

## Applied Scenarios: Normalization in Practice

*This section collects real-world normalization scenarios and the reasoning behind how to handle them, as a practical companion to the formal steps above.*

### Scenario 1 — Combining Batches with Unbalanced Groups and a Partially Shared Bridging Control

**The situation**

A common scenario arises when a study combines two separately-run SomaScan batches: one batch containing the disease/case group of interest but few or no healthy controls, and a second, independently run batch (possibly from a different lab) contributing the bulk of the healthy control samples. Both batches share a common bridging control material run on every plate, intended to allow cross-batch comparison. In practice, this bridging material may not always be composed of the exact same aliquots in both batches — sometimes it is literally the same physical aliquots reused across batches, and sometimes it is a similarly-prepared but distinct pool. This distinction matters enormously for what can and cannot be concluded from it.

**Why this is a hard case**

> **The core problem**
> When the case group exists almost entirely in one batch and the control group exists almost entirely in the other, the biological contrast of interest (case vs. control) becomes confounded with the technical contrast (batch A vs. batch B). No normalization procedure, standard or custom, can fully separate a real disease effect from a batch effect when there is no data point that varies in group while holding batch constant, or vice versa. This is a design-level limitation that downstream statistics cannot fully resolve — it can only be characterized and partially mitigated.

A visual PCA check across batch and sample type is a useful first diagnostic here: if the shared bridging control clusters distinctly by batch rather than overlapping, that is direct evidence of residual, uncorrected batch structure. If the case group also shows very high internal spread compared to a tight control cluster, that asymmetry is worth noting but is not by itself diagnostic of batch effect, since it could equally reflect genuine biological heterogeneity in disease.

**What the bridging control can and cannot tell you**

| | Same physical aliquots reused across batches | Similarly-prepared but distinct pools |
|---|---|---|
| **What a measured difference means** | Purely technical batch effect — no compositional confound | Conflates true batch effect with pool composition differences; cannot be cleanly separated |
| **Usable as a correction anchor?** | Yes, with appropriate caution for small replicate counts | Weak at best; better used only as a rough diagnostic bound on batch effect, not a correction target |

**Strategy when the bridging control is the same material across batches**

If a small number of truly paired bridging replicates exist (the same aliquots measured once in each batch), they provide a clean, if statistically thin, estimate of the per-analyte batch shift. A workable strategy:

1. Estimate, per analyte, the batch shift using only the paired bridging replicates — not the full sample set — specifically to avoid the group/batch confound described above contaminating the batch estimate.
2. Because the number of paired replicates is typically very small (e.g., 3 per batch), treat the raw per-analyte shift estimates as unstable, and apply empirical Bayes shrinkage across all analytes toward a common batch-level shift — the same underlying logic used by ComBat, a well-established batch-correction method originally developed for microarray data and since adapted to other omics, including proteomics. This borrows statistical strength across analytes to stabilize what would otherwise be very noisy single-analyte estimates.
3. Apply the resulting shrunk, per-analyte correction to every sample in the affected batch — not just the bridging control — under the explicit assumption that the batch shift measured in the bridging material transfers to the biological samples of interest.
4. Prefer a mean-only correction (shifting the average level per analyte) over also correcting variance/scale differences between batches, since a handful of paired replicates cannot support a reliable variance estimate.
5. Validate the correction by checking whether it reduces the paired bridging-control difference relative to its pre-correction value. If it does not, the correction lacks empirical support and should not be trusted for adjusting the biological samples.

> **Why standard ComBat isn't used directly here**
> Standard ComBat implementations estimate batch effect parameters from the full distribution of samples within each batch. When batch and biological group are highly confounded, as in this scenario, that default estimation would conflate the two — potentially removing genuine biological signal along with batch noise. Restricting the parameter estimation step to only the shared bridging replicates, while still applying the resulting correction to all samples, preserves the core empirical Bayes shrinkage logic of ComBat while avoiding this specific failure mode.

**What this strategy does not resolve**

> **Residual limitations to disclose**
> Even a well-executed bridging correction of this kind cannot fully validate that the batch shift observed in the bridging material is identical to the batch shift experienced by the actual case and control samples — there is no independent way to check this without additional shared material. Analytes near the assay's limit of detection are particularly vulnerable, since missing or censored values in the small bridging replicate set can make the batch shift estimate unreliable or impossible for those specific analytes. Any analysis using this approach should explicitly disclose that batch and biological group are structurally confounded by design, and that statistical correction mitigates but does not eliminate this limitation.

---

## References

1. Candia, J. *SomaScan Bioinformatics: Normalization, Quality Control, and Assessment of Pre-Analytical Variation.* bioRxiv 2024.02.09.579724 (2024). [biorxiv.org/content/10.1101/2024.02.09.579724v1](https://www.biorxiv.org/content/10.1101/2024.02.09.579724v1) — primary source for all equations, step definitions, and R code referenced throughout this document.

2. Candia, J. et al. *Assessment of variability in the somascan assay.* Scientific Reports 7, 14248 (2017). Cited within Candia 2024 as the earlier work establishing the risk of amplifying plate effects if median normalization on experimental samples precedes inter-plate calibration.

3. Candia, J., Daya, G., Tanaka, T., Ferrucci, L. & Walker, K. *Assessment of variability in the plasma 7k somascan proteomics assay.* Scientific Reports 12, 17147 (2022). Source of the BLSA technical-replicate framework used for the validation and PAV-SST assessments in Candia 2024.

4. Lopez-Silva, C. et al. *Comparison of aptamer-based and antibody-based assays for protein quantification in chronic kidney disease.* CJASN 17, 350–360 (2022). Cited within Candia 2024 regarding potential attenuation of clinical associations by SomaLogic's external-reference normalization.

5. Pietzner, M. et al. *Synergistic insights into human health from aptamer- and antibody-based proteomic profiling.* Nature Communications 12, 6822 (2021). Cited within Candia 2024 regarding correlation with Olink when normalization is or isn't applied.

6. Johnson, W.E., Li, C. & Rabinovic, A. *Adjusting batch effects in microarray expression data using empirical Bayes methods.* Biostatistics 8, 118–127 (2007). Original ComBat method, referenced in the applied scenarios section as the basis for empirical Bayes shrinkage in bridging-control batch correction.

---

*All equations, step orderings, and figure/equation numbers in the normalization-steps sections above are reproduced (in the paper's own notation) from Candia (2024), bioRxiv 2024.02.09.579724, which is distributed under a CC0 license as a US Government work.*
