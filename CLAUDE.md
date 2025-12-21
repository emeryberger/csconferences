# CSConferences Update Log

## Update: December 2025

### Sources Used

The following sources were used to update conference acceptance statistics:

#### AI/ML Conferences
- **Conference Acceptance Rate GitHub**: https://github.com/lixin4ever/Conference-Acceptance-Rate
  - AAAI, NeurIPS, ICML, ICLR, CVPR, IJCAI data
- **Paper Copilot Statistics**: https://papercopilot.com/statistics/
  - NeurIPS, ICML detailed statistics
- **OpenAccept**: https://openaccept.org/c/ai/ijcai/
  - IJCAI acceptance rates

#### Robotics Conferences
- **AIST Robotics Acceptance Rate History**: https://staff.aist.go.jp/k.koide/acceptance-rate.html
  - ICRA and IROS 2023-2024 data

#### Graphics Conferences
- **Paper Copilot SIGGRAPH Statistics**: https://papercopilot.com/statistics/siggraph-statistics/
  - SIGGRAPH 2023-2024 (journal + dual track combined)

#### Security Conferences
- **Computer Security Conference Acceptance Rate GitHub**: https://github.com/puzhuoliu/Computer-Security-Conference-Acceptance-Rate
  - Oakland S&P, CCS, USENIX Security, NDSS data

#### Theory Conferences
- **STOC 2025 Accepted Papers**: https://acm-stoc.org/stoc2025/accepted-papers.html
- **Lance Fortnow's announcement**: https://x.com/fortnow/status/1888001873027739782

#### Systems Conferences
- **ETH Zurich Systems Group News**: https://systems.ethz.ch/news-and-events/news/2025/07/four-papers-accepted-at-sosp-2025-in-seoul-south-korea.html
  - SOSP 2025 data

#### Economics Conferences
- **Springer LNCS Proceedings**: https://link.springer.com/conference/wine
  - WINE proceedings with acceptance statistics in preface
- **ACM DL Proceedings**: https://dl.acm.org/
  - EC proceedings (front matter PDFs contain statistics)

### Entries Added/Updated

| Conference | Year | Accepted | Submitted | Source |
|------------|------|----------|-----------|--------|
| IJCAI | 2024 | 791 | 5651 | OpenAccept |
| IJCAI | 2025 | 1042 | 5404 | GitHub lixin4ever |
| ICML | 2025 | 3260 | 12107 | Paper Copilot |
| NeurIPS | 2025 | 5290 | 21575 | GitHub lixin4ever |
| CVPR | 2025 | 2872 | 13008 | GitHub lixin4ever |
| SIGGRAPH | 2023 | 212 | 611 | Paper Copilot |
| SIGGRAPH | 2024 | 252 | 844 | Paper Copilot |
| ICRA | 2023 | 1345 | 3125 | AIST |
| ICRA | 2024 | 1765 | 3937 | AIST |
| IROS | 2023 | 1196 | 2760 | AIST |
| IROS | 2024 | 1587 | 3344 | AIST |
| Oakland | 2025 | 256 | 1739 | GitHub puzhuoliu |
| CCS | 2025 | 316 | 2278 | GitHub puzhuoliu |
| UsenixSec | 2025 | 407 | 2385 | GitHub puzhuoliu |
| STOC | 2025 | 219 | 735 | STOC website |
| SOSP | 2025 | 65 | 368 | ETH Zurich |
| WINE | 2024 | 34 | 248 | Springer LNCS 15534 |
| EC | 2023 | 163 | - | DBLP |
| EC | 2024 | 205 | - | DBLP |

### Notable Trends and Surprising Increases

Several conferences showed significant year-over-year increases in submissions:

1. **ICLR**: 7,304 (2024) to 11,672 (2025) - **60% increase** in submissions
2. **NeurIPS**: 15,671 (2024) to 21,575 (2025) - **38% increase** in submissions
3. **ICML**: 9,473 (2024) to 12,107 (2025) - **28% increase** in submissions
4. **IJCAI**: 4,566 (2023) to 5,651 (2024) - **24% increase** in submissions
5. **SOSP**: 245 (2024) to 368 (2025) - **50% increase** in submissions
6. **Oakland S&P**: 1,449 (2024) to 1,739 (2025) - **20% increase** in submissions

The ML/AI conferences continue to see explosive growth in submission volumes, with ICLR showing the most dramatic increase at 60% year-over-year.

### Notes

- SIGGRAPH data combines journal track and dual track submissions/acceptances
- Some conferences have multiple submission cycles (CCS, Oakland) - data may represent totals or primary cycle
- Robotics data from AIST is considered authoritative for ICRA/IROS
- For preferred sources, check ACM DL and IEEE DL conference front matter via DBLP
- WINE 2024 accepted 34 full papers + 32 one-page abstracts from 248 submissions
- EC 2023 and EC 2024: accepted paper counts from DBLP; submission counts not available
- ACM DL front matter PDFs are blocked by Cloudflare; use DBLP API as alternative

### Workarounds for Obtaining Front Matter

ACM DL and IEEE DL front matter PDFs are often blocked by Cloudflare (403 errors or "Just a moment..." pages). The following workarounds can help:

1. **Wayback Machine**: Use archived versions of ACM DL pages
   - URL pattern: `https://web.archive.org/web/2024/https://dl.acm.org/action/showFmPdf?doi=...`
   - Example: `curl -sL "https://web.archive.org/web/2024/https://dl.acm.org/action/showFmPdf?doi=10.1145%2F3580507" -o /tmp/ec2023.pdf`
   - Limitation: Not all pages are archived; recent conferences may not be available

2. **DBLP API for Paper Counts**: When front matter is unavailable, count accepted papers via DBLP
   - API endpoint: `https://dblp.org/search/publ/api?q=toc:db/conf/<venue>/<venue><year>.bht:&h=500&format=json`
   - Example: `curl -s "https://dblp.org/search/publ/api?q=toc:db/conf/sigecom/sigecom2024.bht:&h=500&format=json" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['result']['hits']['@total'])"`
   - Limitation: Only provides accepted paper counts, not submission counts

3. **Springer LNCS Proceedings**: For WINE, SODA, and other Springer-published conferences
   - Prefaces often contain submission/acceptance statistics
   - Access via: `https://link.springer.com/conference/<venue>`

4. **Conference Websites**: Check official conference sites and call-for-papers pages
   - Statistics sometimes appear in announcements or news sections
   - Archive.org may have older versions with statistics

5. **OpenResearch.org**: Historical acceptance rates for many conferences
   - URL: `https://www.openresearch.org/wiki/<CONFERENCE>`
   - Limitation: Data may lag behind by 1-3 years

### EC Conference Historical Data

From various sources (primarily ACM DL front matter), EC acceptance patterns show:
- EC 2018: 70 accepted / 269 submitted (26.0%)
- EC 2019: 106 accepted / 382 submitted (27.7%)
- EC 2020: 99 accepted / 491 submitted (20.2%)
- EC 2021: 130 accepted / 500 submitted (26.0%) - from ACM DL front matter
- EC 2022: 150 accepted / 549 submitted (27.3%) - from ACM DL front matter
- EC 2023: 163 accepted, submissions unknown ("record number" per preface)
- EC 2024: 205 accepted, submissions unknown

EC 2023 and EC 2024 submission counts require direct access to front matter or organizer confirmation.

### Pre-approved Sites for Web Fetching

The following domains are pre-approved for automatic access:
- `github.com` - Conference acceptance rate repositories
- `staff.aist.go.jp` - AIST robotics acceptance rate data
- `papercopilot.com` - Conference statistics
- `dl.acm.org` - ACM Digital Library proceedings (note: front matter PDFs blocked by Cloudflare)
- `aclweb.org` - ACL Anthology and wiki
- `link.springer.com` - Springer LNCS proceedings
- `openreview.net` - OpenReview conference submissions
- `dblp.org` - DBLP bibliography (use API for paper counts)
