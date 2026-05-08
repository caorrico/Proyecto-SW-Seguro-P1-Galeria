# SecureFrame Gallery: Security Audit Report
Date: Fri May  8 12:01:10 -05 2026
---
## 1. SCA (Software Composition Analysis) - pip-audit
Checking for known vulnerabilities (CVEs) in dependencies...
```
No known vulnerabilities found
```
## 2. SAST (Static Analysis Security Testing) - Bandit
Scanning Python code for common security issues...
```
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.12.3
Run started:2026-05-08 17:01:40.822641+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 1141
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
Files skipped (0):
```
## 3. SAST - Semgrep (FastAPI Rules)
Scanning for FastAPI-specific security patterns...
```
               
               
┌─────────────┐
│ Scan Status │
└─────────────┘
  Scanning 26 files tracked by git with 1059 Code rules:
                                                                                                                        
  Language      Rules   Files          Origin      Rules                                                                
 ─────────────────────────────        ───────────────────                                                               
  python          243      26          Community    1059                                                                
  <multilang>      47      26                                                                                           
                                                                                                                        
                
                
┌──────────────┐
│ Scan Summary │
└──────────────┘
✅ Scan completed successfully.
 • Findings: 0 (0 blocking)
 • Rules run: 290
 • Targets scanned: 26
 • Parsed lines: ~100.0%
 • Scan was limited to files tracked by git
 • For a detailed list of skipped files and lines, run semgrep with the --verbose flag
Ran 290 rules on 26 files: 0 findings.
(need more rules? `semgrep login` for additional free Semgrep Registry rules)

If Semgrep missed a finding, please send us feedback to let us know!
See https://semgrep.dev/docs/reporting-false-negatives/
```
---
