---
title: "How a Genome Is Built From Scratch"
subtitle: "An interactive guide to sequencing, assembly, scaffolding, polishing, quality control, and annotation"
summary: "A visual, interactive introduction to the algorithms, technologies, and quality metrics used to turn sequencing reads into chromosome-scale genome assemblies."
authors:
  - admin
tags:
  - Genome Assembly
  - Genomics
  - Sequencing
  - Bioinformatics
categories:
  - Technical Notes
date: "2026-09-06"
lastmod: "2026-09-06"
featured: false
weight: 30
draft: false
toc: true
math: true
external_link: "/notes/genome-assembly-guide/"
---

{{% callout note %}}
This article is an [interactive guide](/notes/genome-assembly-guide/) with visual explanations, a k-mer explorer, an N50 calculator, and a short self-test.
{{% /callout %}}

## From reads to chromosomes

Genome assembly is the reconstruction of a long DNA sequence from millions of shorter, overlapping reads. This guide presents that process as a graph and optimization problem, using a shredded-document analogy to explain how assemblers recover the original sequence while handling repeats, sequencing errors, and the two haplotypes of a diploid genome.

The guide covers:

- sequencing technologies and their tradeoffs in read length, accuracy, and cost;
- k-mers, overlap graphs, and de Bruijn graphs;
- modern assemblers such as hifiasm, Flye, and Verkko;
- the progression from contigs to scaffolds and chromosome-scale assemblies;
- Hi-C scaffolding, polishing, and cross-species approaches;
- N50, BUSCO, QV, and Merqury as complementary quality measures; and
- genome annotation and liftover after assembly.

Use the interactive navigation to move through the full pipeline, experiment with the k-mer and N50 widgets, and test your understanding at the end.
