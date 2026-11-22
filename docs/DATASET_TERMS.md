# WebLINX source data, license, and redistribution boundaries

This repository contains original analysis code and derived numeric/categorical results for the paper *What Must a Web-Agent Log Remember? Candidate Omission, Evidence Collision, and Selective Retention*.

## Source and attribution

- Dataset creator: Xing Han Lù, Zdeněk Kasner, and Siva Reddy.
- Source: [McGill-NLP/WebLINX-full](https://huggingface.co/datasets/McGill-NLP/WebLINX-full).
- Frozen raw-data revision: `36ef9f79b43df50e25b7f3b68e5c9f6ccf4160e8`.
- Selected official DMR data: `candidates/test_iid.jsonl`; raw demonstration replays and screenshots are downloaded at the same revision.
- Cite: Lù, Kasner, and Reddy, *WebLINX: Real-World Website Navigation with Multi-Turn Dialogue*, 2024, [arXiv:2402.05930](https://arxiv.org/abs/2402.05930). Consult the publisher's dataset card for its preferred current citation.

## License and publisher terms

The dataset publisher identifies the WebLINX data license as **Creative Commons Attribution–NonCommercial–ShareAlike 4.0 International (CC BY-NC-SA 4.0)**. The publisher also states additional conditions, which include:

1. Dataset use must comply with applicable law and the rights of other parties.
2. WebLINX may incorporate third-party source material subject to additional conditions; users must respect those conditions.
3. Research use, including reliance on fair-use provisions where applicable, remains subject to the law of the user's jurisdiction, with responsibility resting on the user.
4. Redistributed derivatives must carry the publisher's dataset terms of use.

Read the publisher's **[complete License and Terms of Use](https://huggingface.co/datasets/McGill-NLP/WebLINX-full#license-and-terms-of-use)** before using or redistributing the data or material derived from it, and consult the [CC BY-NC-SA 4.0 license text](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode).

These terms and links are included here for source attribution and downstream notice. In any conflict, use the publisher's own current terms and applicable law.

## Boundary of this public artifact

- The repository's [MIT LICENSE](../LICENSE) licenses the researchers' original program source. It does **not** grant permissions over WebLINX or third-party webpage material.
- Published `results/` files are numeric or categorical research measurements, public demonstration/turn identifiers, and source provenance/checksums. Review any onward redistribution against the publisher's requirements, especially if combining these records with original WebLINX content.
- Original HTML pages, candidate text, screenshots, literal element XPath/UID values, browsing dialogues, and browser Trace/session archives are acquired only for local computations. This repository deliberately avoids republishing those raw materials.
- Scripts fetch source inputs at pinned publisher revisions. Each downstream user obtains those inputs under the publisher's applicable terms.
- Neither the MIT code license nor a future Zenodo deposit changes third-party data rights. Publication and archive reviews should inspect any added files before distribution.

Last source-terms review: 2026-11-22.
