# campus_mbti - Design Spec

> Human-readable design narrative. Machine-readable execution contract: `spec_lock.md`.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | campus_mbti |
| **Canvas Format** | PPT 16:9 (1280x720) |
| **Page Count** | 14 |
| **Design Style** | Memphis Pop (General Versatile mode) |
| **Target Audience** | Classroom students and professors (ML course) |
| **Use Case** | In-class presentation for machine learning course project |
| **Created Date** | 2026-06-08 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280 x 720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top/bottom 50px |
| **Content Area** | 1160 x 620 |

---

## III. Visual Theme

### Theme Style

- **Style**: Memphis Pop
- **Theme**: Light theme
- **Tone**: Playful, bold, energetic, young, design-forward

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#FFFAFB` | Main page background (soft pink-white) |
| **Secondary bg** | `#FFF0F3` | Card backgrounds, section backgrounds |
| **Primary** | `#FF6B8A` | Coral pink - titles, key decorations, icons |
| **Accent** | `#FFD93D` | Bright yellow - geometric shapes, highlights |
| **Secondary accent** | `#00D2D3` | Tiffany blue - charts, cards, secondary emphasis |
| **Tertiary accent** | `#A29BFE` | Electric purple - decorative elements |
| **Body text** | `#2D3436` | Main body text (dark charcoal) |
| **Secondary text** | `#636E72` | Captions, annotations |
| **Border/divider** | `#FDCB6E` | Card borders, Memphis pattern elements |
| **Success** | `#55EFC4` | Mint green - positive indicators |
| **Warning** | `#FF6B8A` | Coral pink - caution markers |

### Memphis Pattern Colors (decorative only)

| Role | HEX | Pattern |
| ---- | --- | ------- |
| **Polka dots** | `#2D3436` | Black dots on light backgrounds |
| **Stripes** | `#FFD93D` | Yellow stripes |
| **Squiggles** | `#00D2D3` | Blue wavy lines |
| **Triangles** | `#A29BFE` | Purple geometric fills |

### Gradient Scheme

```xml
<linearGradient id="memphisGrad" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#FF6B8A"/>
  <stop offset="50%" stop-color="#FFD93D"/>
  <stop offset="100%" stop-color="#00D2D3"/>
</linearGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: Geometric sans-serif for titles + clean sans-serif for body, Memphis-informed with bold display weights

### Font Stack

| Role | Stack |
|------|-------|
| Title | "Arial Black", "Microsoft YaHei", sans-serif |
| Body | "Microsoft YaHei", "PingFang SC", sans-serif |
| Emphasis | "Arial Black", "Microsoft YaHei", sans-serif |
| Code | Consolas, "Courier New", monospace |

### Size Ramp (baseline body: 18px)

| Role | Size (px) |
|------|-----------|
| cover_title | 64 |
| title | 36 |
| subtitle | 24 |
| body | 18 |
| annotation | 14 |
| hero_number | 56 |
| chart_label | 12 |

---

## V. Layout Strategy

### Page Rhythm

| Page | Tag | Rationale |
|------|-----|-----------|
| P01 | anchor | Cover with Memphis geometric decorations |
| P02 | anchor | Table of contents with bold color blocks |
| P03 | breathing | Chapter transition - intro section |
| P04 | dense | Background + data collection details |
| P05 | dense | Problem statement + motivation |
| P06 | breathing | Chapter transition - tech approach |
| P07 | dense | Three-phase technical roadmap |
| P08 | breathing | Chapter transition - results |
| P09 | dense | Four cluster groups with cards |
| P10 | dense | MBTI prediction results table |
| P11 | dense | Recommendation system architecture |
| P12 | dense | Visualization showcase grid |
| P13 | breathing | Limitations + future work |
| P14 | anchor | Closing slide with Memphis decoration |

### Page Layouts

- P01: free (Memphis cover)
- P02: free (Memphis TOC)
- P03: free
- P14: free

All pages are free design (no template inheritance) to achieve authentic Memphis Pop style.

---

## VI. Icon Strategy

- **Library**: Tabler Icons (outline style)
- **Style**: Geometric line icons at 2px stroke width
- **Color**: `#FF6B8A` primary, `#2D3436` secondary
- **Sourcing**: Inline SVG paths embedded directly

---

## VII. Visualization Strategy

Charts are hand-drawn in SVG with Memphis styling:
- Bold geometric data representations
- Rounded bar charts with colorful fills
- Circular/radial progress indicators
- No standard chart templates; all custom Memphis-style

---

## VIII. Image Resource List

All images are user-supplied project output PNGs.

| ID | Filename | Type | Acquire Via | Status |
|----|----------|------|-------------|--------|
| img_01 | output_radar.png | Chart | user | Ready |
| img_02 | output_heatmap.png | Chart | user | Ready |
| img_03 | output_pca.png | Chart | user | Ready |
| img_04 | output_elbow_silhouette.png | Chart | user | Ready |
| img_05 | output_feature_importance.png | Chart | user | Ready |
| img_06 | output_confusion_matrices.png | Chart | user | Ready |

---

## IX. Content Outline

### Part 1: Opening

#### P01 - Cover
- **Layout**: Full Memphis geometric background + centered title
- **Title**: Campus Companion Recommendation System
- **Subtitle**: Based on MBTI Traits and Micro-Consumption Features
- **Info**: ML Course Project 2026

#### P02 - Table of Contents
- **Layout**: Four color blocks in 2x2 grid
- **Items**: 01 Project Overview / 02 Data and Methods / 03 Core Results / 04 Future Directions

### Part 2: Project Overview

#### P03 - Chapter Transition: Project Overview
- **Layout**: Large number + geometric shapes
- **Title**: 01 PROJECT OVERVIEW

#### P04 - Background and Motivation
- **Core message**: Consumption + personality are the two core dimensions of campus social matching
- **Content**: Problem statement, target users, project objectives

#### P05 - Data Collection
- **Core message**: 62 valid survey responses covering 5 modules
- **Content**: Survey design (5 modules x 19 questions), data statistics

### Part 3: Technical Approach

#### P06 - Chapter Transition: Technical Approach
- **Layout**: Large number + geometric shapes
- **Title**: 02 TECHNICAL APPROACH

#### P07 - Three-Phase Pipeline
- **Core message**: Unsupervised clustering -> Supervised classification -> Recommendation system
- **Content**: Phase 1: K-Means clustering, Phase 2: Random Forest MBTI prediction, Phase 3: Flask web app

### Part 4: Core Results

#### P08 - Chapter Transition: Core Results
- **Layout**: Large number + geometric shapes
- **Title**: 03 CORE RESULTS

#### P09 - Clustering Results (K=4)
- **Core message**: Four distinct campus consumer groups identified
- **Content**: Group cards (Digital-heavy, Frugal, Social, Self-improvement)
- **Visualization**: img_01 radar chart

#### P10 - MBTI Prediction Results
- **Core message**: Consumption patterns predict MBTI with up to 61.3% accuracy
- **Content**: Four-dimension accuracy table, key findings
- **Visualization**: img_05 feature importance

#### P11 - Recommendation System Architecture
- **Core message**: End-to-end pipeline from input to TOP-5 matches
- **Content**: Architecture flow diagram

#### P12 - Visualization Showcase
- **Core message**: Comprehensive visual analytics
- **Content**: Grid of project visualizations
- **Visualization**: img_02, img_03, img_04, img_06

### Part 5: Future Directions

#### P13 - Limitations and Future Work
- **Core message**: Small sample size is the main bottleneck; deep learning is the next step
- **Content**: Four limitations, four future directions

#### P14 - Closing
- **Layout**: Memphis geometric background + centered thank you
- **Title**: THANK YOU
- **Subtitle**: Questions and Discussion

---

## X. Speaker Notes Requirements

One speaker note file per page, saved to `notes/`.

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:
1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. Raw Unicode for typographic characters; XML reserved chars escaped
8. `clipPath` conditionally allowed only on `<image>` elements

### PPT Compatibility Rules:
- `<g opacity="...">` FORBIDDEN
- Image transparency uses overlay mask layer
- Inline styles only
