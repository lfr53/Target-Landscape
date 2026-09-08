# CVID Compass

### Connecting the CVID community through shared patterns

Bringing together patients and families, clinicians, and researchers around shared clinical features, immune profiles and research.

[Explore the website](https://lfr53.github.io/CVID-Compass/) · [Features](#explore-the-network) · [Run locally](#run-locally)

<img src="assets/network-background.png" alt="Soft medical illustration connecting antibody and immune-cell motifs around shared patterns" width="760">

*Network illustration used on the homepage. This is an illustration, not a screenshot of the interface.*

## About

CVID Compass is a phenotype-first rare-disease discovery prototype connecting patients, families, clinicians and researchers through CVID education, shared clinical features, research and specialist expertise.

It helps people explore three related questions:

- **Patients and families:** Who is like me?
- **Clinicians:** Has this pattern been seen before, and who is already working on it?
- **Researchers:** Where are similar patient groups being studied, and who is working on the same question?

Its early value comes from organising existing public research, cohorts, specialist teams and patient organisations. Anonymous contributed cases are a planned addition, not an existing patient database.

## Explore the network

| Area | What you can explore |
| --- | --- |
| Understand CVID | Topic-led navigation through original educational articles, immune-molecule explainers, references and illustrations. |
| Patients and families | A single-page questionnaire and a profile-based view of related cases, research and communities. |
| Clinicians | Structured case filters, illustrative anonymous cases and shared clinical features. |
| Researchers | Phenotype-defined groups, case counts and available distributions. |
| Research | Curated projects, cohorts, registries, historical research and clinical trials. |
| Research teams | Researchers, laboratories and centres with public sources; keyword and country filters. |
| Community | Patient organisations including PID Care China, Immunodeficiency UK, IDF, IDFA and IPOPI. |

The team directory includes INTREPID, Australia's Centre for Personalised Immunology, Fudan and Chongqing teams, alongside groups at Freiburg, Mount Sinai, Garvan, Newcastle, CHOP, Rockefeller and KU Leuven. Coverage is curated and incomplete; listings include broader IEI expertise as well as CVID-related work.

English and Chinese are available across the homepage, original educational articles and several exploration views. Some form options, research records and results still require translation.

## Learning, one topic at a time

The learning hub starts with topics rather than a complete article list:

1. Start with CVID
2. Genetics and immune molecules
3. Treatment and family life
4. Understanding research

Readers open a topic and then an article, while retaining the site's shared navigation and language controls. The original bilingual manuscripts and article illustrations are preserved.

## Research with context

Research is organised into four sections:

- Currently recruiting
- Active research / recruitment unclear
- People like me have been studied
- Registries & ongoing cohorts

These are discovery categories, not confirmation of eligibility or participation. Historical studies remain useful for identifying phenotype groups and relevant expertise. Some cohort entries currently appear in more than one section.

Newer records link to institutional profiles, publications or official organisations. Seed statuses are not synchronised with registries and require periodic verification. A team listing does not imply a partnership, an available referral route or open recruitment.

## Prototype status and privacy

- The three anonymous cases are **synthetic demonstration records**, not contributed patients.
- Questionnaire answers remain in page memory and are not automatically uploaded. Refreshing or closing the page can clear them.
- There is no production backend, registration, case contribution, recovery-code service or patient messaging.
- Family-cluster and treatment-response information is absent from the demonstration dataset and is labelled as unavailable.
- Case filters require all selected features; related research may share only some features. This is transparent tag exploration, not a validated medical matching algorithm.
- Country filtering depends on available profile metadata; older entries have less complete information.

The platform does not diagnose disease, recommend treatment or determine trial eligibility. Similar features do not establish clinical equivalence. Medical questions should be discussed with a qualified clinician.

## Technology

Static HTML, CSS and JavaScript, with hash-based navigation. Editable source uses ES modules; the delivered page loads a generated classic-script bundle for local-file compatibility.

```text
index.html
src/
  main.js                 # Routes and original discovery data
  site-bundle.js          # Generated script loaded by the page
  final-homepage.js        # Homepage and role entry points
  patient-form.js          # Single-page patient form
  exploration.js          # Clinician and researcher views
  education-view.js       # Topic and article navigation
  network-directory.js    # Research and community records
  expanded-teams.js       # Additional teams and directory filters
  reference-visuals.js     # Icons and illustrated navigation
  *.css                   # Shared and page-specific styles
assets/                   # Homepage artwork
education/
  src/                    # Original bilingual education content
  assets/                 # Original article illustrations
  content/                # Supporting content
scripts/
  build-preview.cjs       # Rebuild the browser script
.github/workflows/
  pages.yml               # GitHub Pages deployment
```

The integrated learning hub is `#cvid`; articles use `#article-<slug>`. The preserved `education/index.html` is a legacy entry.

## Run locally

Open `index.html` with the complete folder structure intact. The generated bundle supports opening the delivered page directly from disk.

An HTTP server is also suitable. For example, with Python installed:

```sh
python -m http.server 8000
```

Then open `http://localhost:8000`.

After editing JavaScript source, rebuild the script loaded by the page:

```sh
node scripts/build-preview.cjs
```

Commit both the changed source files and the regenerated `src/site-bundle.js`. Hosting the prepared files requires no package installation.

## Deploy to GitHub Pages

Upload `index.html`, `src/`, `assets/`, `education/`, `scripts/` and this README to the repository root.

Update the existing Pages workflow with the supplied `.github/workflows/pages.yml`. Replace the existing deployment configuration rather than adding a second competing workflow. Its existing filename can be retained.

**The deployment must copy `education/`.** The original workflow omitted this directory, which contains the integrated learning hub's content and illustrations.

The supplied workflow deploys on pushes to `main`. Use GitHub Actions as the Pages deployment source, inspect the workflow result and then check the deployed website. Updating only `index.html` without `src/site-bundle.js` can leave the page unable to load.

## Verification and next steps

Checks have covered JavaScript syntax, shared-feature filtering, bilingual article routes, source preservation, directory links and startup across 26 route/language combinations using a DOM stub. These checks do not constitute a full browser, visual, accessibility or medical-content audit.

Remaining work includes completing translations and conditional fields, improving source metadata, validating responsive layouts and user journeys, and verifying research statuses. Anonymous contribution and secure case management remain future backend work.

## Content and attribution

Original educational manuscripts and illustrations are retained. Homepage artwork and design references were supplied by the project owner; development included AI assistance.

Third-party publications, names and artwork retain their respective rights. No institutional endorsement or blanket licence over third-party material is implied.
