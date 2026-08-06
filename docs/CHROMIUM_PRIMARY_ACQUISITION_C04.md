# C04 Chromium primary scan or author-data acquisition

## Objective

C04 converts the C03 acquisition blocker into a ranked, reviewable external-acquisition packet for the 1969 simultaneous chromium heat-capacity and resistivity experiment.

Target article:

> M. B. Salamon, D. S. Simons, and P. R. Garnier, “Simultaneous measurement of the anomalous heat capacity and resistivity of chromium near TN,” *Solid State Communications* 7(15), 1035–1038 (1969), DOI `10.1016/0038-1098(69)90464-5`.

The article acknowledges Advanced Research Projects Agency Contract SD-131.

## Ranked acquisition routes

### 1. Direct author route

The official University of Illinois Professor Emeritus profile for Myron B. Salamon provides the contact `salamon@utdallas.edu`.

The prepared request asks for an author PDF or scan, point arrays, figure definitions, AC modulation metadata, sample and thermometer information, and retained uncertainty records.

### 2. University of Illinois Archives

The University Archives physically holds **Materials Sciences Annual Technical Reports, 1963–**, series **11/14/818**. The catalogue describes these as reports submitted to ARPA under SD-131.

The collection is not asserted to contain the article figures or raw data. The prepared request asks staff to inspect the 1968–69 and 1969–70 material for a project entry, preprint, technical-report number, apparatus description, data appendix, or relevant figures.

### 3. Illinois Materials Research Laboratory

The current MRL general-inquiry route is `mrl@illinois.edu`. The request asks for a legacy publication or technical-report copy, archival laboratory record, or referral to the appropriate custodian.

### 4. Library document delivery

The article metadata are frozen in `docs/requests/C04_LIBRARY_REQUEST_METADATA.md` for a home-institution or local-library interlibrary-loan request.

University of Illinois users can use the University’s ILLiad/DocExpress services. A non-affiliated individual should route the request through their own institution or public library.

### 5. Publisher access

The ScienceDirect landing page exposes the article metadata and abstract. Full article bytes have not been acquired through this route.

## Prepared request packet

```text
docs/requests/C04_AUTHOR_DATA_REQUEST.md
docs/requests/C04_ARCHIVE_SCAN_REQUEST.md
docs/requests/C04_LIBRARY_REQUEST_METADATA.md
```

These are drafts only. No message is marked as sent. User approval and personal review are required before external correspondence.

## Intake contract

Any received file must enter the later intake stage without modification. The intake record must include:

- source route;
- date received;
- rights or access note;
- original file type and name;
- SHA-256 hash of original bytes;
- page, figure and panel identity for scans;
- scan resolution, with 300 dpi as the minimum target;
- derivative hashes for cropped or converted images.

OCR output cannot be treated as numerical data. A secondary redrawing cannot be relabelled as the primary scan.

## Result

```text
verified acquisition routes     5
request drafts present          true
external requests sent          0
responses received              0
primary files acquired          0
primary scan acquired           false
author arrays acquired          false
intake certificate ready        false
digitization allowed            false
curvature allowed               false
```

Status:

```text
PASS_CHROMIUM_C04_ACQUISITION_PACKET_READY_EXTERNAL_RESPONSE_REQUIRED
```

The packet is operationally ready, but no external response is falsely counted as data.

## Corrected dependency order

The next scientific stage is now

```text
C05_CHROMIUM_NEEL_CUT_SQUARE_ADAPTER_AND_BETA_BURDEN
```

C05 freezes the theorem-guided observer, metric, target, beta and seam-curvature contract before any numerical file is consumed. Actual primary files will then enter

```text
C06_CHROMIUM_PRIMARY_FILE_INTAKE_RESPONSE_PACKET_AND_BETA_INTERVAL.
```

This preserves the acquisition route while ensuring that received data populate a predeclared proof object instead of defining the proof after inspection.
