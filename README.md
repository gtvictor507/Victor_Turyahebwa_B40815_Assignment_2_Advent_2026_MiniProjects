# Victor_Turyahebwa_B40815_Assignment_2_Advent_2026_MiniProjects

This repository contains the two mini-projects required for the MSDS OOP with Python assignment:

1. **Weather Forecast with Web APIs** - direct HTTP integration with Open-Meteo and MET Norway, robust retries, offline parsing tests, a table, and a labelled chart.
2. **Uganda Tax Engine** - an object-oriented, Decimal-only implementation of PAYE, payroll deductions, VAT, corporate income tax, and a scenario-comparison extension.

## Repository structure

```text
.
├── project1_weather.ipynb
├── project2_tax_engine.ipynb
├── README.md
├── requirements.txt
├── data/
│   ├── geocoding_empty.json
│   ├── geocoding_kampala.json
│   ├── met_norway_forecast.json
│   └── open_meteo_forecast.json
├── src/
│   ├── weather_api.py
│   └── tax_engine/
│       ├── errors.py
│       ├── models.py
│       ├── money.py
│       ├── payroll.py
│       ├── planner.py
│       └── taxes.py
└── tests/
    ├── test_tax_engine.py
    └── test_weather_parsing.py
```

## Setup and execution

Python 3.11 or later is recommended.

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install and test:

```bash
python -m pip install -r requirements.txt
pytest -q
jupyter lab
```

For a quick offline smoke check (also useful before installing pytest), run `python tests/run_offline_checks.py`.

Open each notebook and choose **Kernel > Restart Kernel and Run All Cells**. In `project1_weather.ipynb`, If the live services or network are unavailable, the notebook falls back to the saved fixtures so the parsing, table, chart, and report remain reproducible.

## Design summary

### Mini-Project 1

`src/weather_api.py` separates network I/O from parsing. The `urllib` and `requests` examples expose the same geocoding purpose while allowing a direct comparison. `request_json()` supplies timeouts, `raise_for_status()`, exponential backoff, a retry cap, and a clear final exception. Pure parsing functions accept saved JSON, which makes the tests deterministic and offline. Location ambiguity is visible: candidates are numbered and a configuration value selects one rather than silently assuming the first match.

The Open-Meteo daily response is converted to a DataFrame with dates, decoded WMO descriptions, and units in column names. The notebook plots minimum/maximum temperatures on one axis and precipitation on a second axis. MET Norway is used as a second source and its coordinates are rounded to four decimal places.

### Mini-Project 2

The tax package models stable domain concepts rather than building one long calculator. `Tax` is an abstract base class with `calculate(TaxContext) -> TaxResult`. PAYE, NSSF, LST, VAT, and corporate income tax implement that contract. Composition is used by `PayrollService`, which coordinates the calculators without inheriting their implementation. `Money` is an immutable UGX value object with explicit whole-shilling, half-up rounding and the required overloaded operators.

The PAYE schedule is versioned by an effective date. The implemented resident schedule is the URA schedule effective **1 July 2026**: nil through UGX 335,000; 20% of the excess through UGX 410,000; UGX 15,000 plus 25% of the excess through UGX 485,000; and UGX 33,750 plus 30% above that, with an additional 10% surcharge on income above UGX 10,000,000. The non-resident schedule is also implemented. Boundary tests cover every required edge, and Hypothesis checks non-negativity, monotonicity, and the rule that PAYE cannot exceed income.

The payroll order used for this assignment is: determine gross cash pay (salary plus allowances); calculate employee and employer NSSF on gross; apply the configured Local Service Tax deduction before PAYE, as instructed by the brief; calculate PAYE; then deduct employee NSSF, LST, and PAYE to determine net pay. Employer NSSF is reported as an employer cost and is not deducted from the employee's net pay.

## Findings

- Direct API integration is short to prototype but production reliability requires explicit timeouts, bounded retries, diagnostics, attribution, and a privacy decision about location data.
- A stable parsing layer is more testable than code that mixes HTTP, transformation, and display in one notebook cell.
- `Decimal` plus an explicit rounding policy prevents binary floating-point artefacts and makes every tax result auditable to a whole shilling.
- Inheritance is useful for the common `Tax` interface; composition is the better choice for payroll because PAYE, NSSF, and LST are separate calculations with different rules.
- A versioned schedule and boundary/property tests reduce the risk created by progressive tax bands, but legislation still has to be monitored and the schedule updated.

## Regulatory and API sources

- Uganda Revenue Authority, [PAYE rates](https://ura.go.ug/en/domestic-taxes/paye-rates/) - resident and non-resident monthly schedules.
- Uganda Revenue Authority, [Changes to PAYE return following the Income Tax (Amendment) Act, 2026](https://ura.go.ug/en/changes-to-paye-return-form-following-the-income-tax-amendment-act-2026/) - 1 July 2026 effective date.
- Uganda Revenue Authority, [A Guide to Taxation in Uganda, FY 2023/24](https://ura.go.ug/wp-content/uploads/2024/06/Taxation-handbook-FY2023-24.pdf) - VAT and corporate-tax background.
- NSSF Uganda, [Membership](https://www.nssfug.org/about-us/membership/) - employee 5%, employer 10%.
- Open-Meteo, [Weather Forecast API documentation](https://open-meteo.com/en/docs) and [Terms](https://open-meteo.com/en/terms).
- MET Norway, [Locationforecast 2.0](https://api.met.no/weatherapi/locationforecast/2.0/documentation), [Terms of Service](https://docs.api.met.no/doc/TermsOfService), and [Licensing and Data Policy](https://docs.api.met.no/doc/License).

## AI-use declaration

An AI coding assistant was used to help structure the repository, refine the reports, discussions and documentation.
