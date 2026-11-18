# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-11-17

### Added
- **Data Quality Dashboard**: A new default view that provides deep insights into the health, freshness, and composition of the dataset.
- New quality analysis report for `unlinked_documents`, identifying documents that are not connected to any meeting.
- New quality analysis report for `meetings_without_documents`.
- CI workflow now publishes a data quality summary on every harvest run.