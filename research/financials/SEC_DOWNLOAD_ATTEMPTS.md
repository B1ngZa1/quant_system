# SEC filing download attempts

On 2026-09-21, the 11 direct SEC Archives URLs in `source_index.csv` were requested with HTTPS and a descriptive User-Agent. Each request returned HTTP 403 from the local fetch environment, so no placeholder HTML was retained and all 11 rows remain `cataloged` rather than `downloaded`.

Affected source IDs:

- `FIN_SSNC_FY2025`
- `FIN_FDS_FY2025`
- `FIN_SPGI_FY2025`
- `FIN_MSCI_FY2025`
- `FIN_NDAQ_FY2025`
- `FIN_CBOE_FY2025`
- `FIN_TW_FY2025`
- `FIN_SCHW_FY2025`
- `FIN_IBKR_FY2025`
- `FIN_HOOD_FY2025`
- `FIN_FUTU_FY2025`

The official URLs are preserved in the index. Do not replace them with unverified mirrors. A future run can retry through a permitted browser or an approved SEC-compliant fetch environment.

Company IR/official exchange alternatives were checked separately. Ten verified PDFs are now stored locally and tracked in `official_alternates.csv`; this does not erase the SEC 403 evidence or change the original regulatory URLs. S&P Global, Charles Schwab and Taiwan Semiconductor have official links recorded but remain unavailable locally because the current environment returned a TLS failure or HTTP 403.
