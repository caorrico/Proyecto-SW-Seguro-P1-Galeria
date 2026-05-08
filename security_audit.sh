#!/bin/bash

# SecureFrame Gallery - Automated Security Audit Script
# Aligned with Strategic Plan Section 5.3 (SAST/SCA)

VENV="./backend/.venv_wsl/bin"
REPORT="SECURITY_REPORT.md"

echo "# SecureFrame Gallery: Security Audit Report" > $REPORT
echo "Date: $(date)" >> $REPORT
echo "---" >> $REPORT

echo "## 1. SCA (Software Composition Analysis) - pip-audit" >> $REPORT
echo "Checking for known vulnerabilities (CVEs) in dependencies..." >> $REPORT
echo '```' >> $REPORT
$VENV/pip-audit >> $REPORT 2>&1
echo '```' >> $REPORT

echo "## 2. SAST (Static Analysis Security Testing) - Bandit" >> $REPORT
echo "Scanning Python code for common security issues..." >> $REPORT
echo '```' >> $REPORT
$VENV/bandit -r ./backend/app >> $REPORT 2>&1
echo '```' >> $REPORT

echo "## 3. SAST - Semgrep (FastAPI Rules)" >> $REPORT
echo "Scanning for FastAPI-specific security patterns..." >> $REPORT
echo '```' >> $REPORT
$VENV/semgrep scan --config auto ./backend/app >> $REPORT 2>&1
echo '```' >> $REPORT

echo "---" >> $REPORT
echo "Audit complete. Review $REPORT for findings."
