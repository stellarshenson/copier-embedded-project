# notebooks

Data-science exploration that supports the firmware: a model of the analogue front end, a parser of
the serial log, a sweep of calibration values.

- `telemetry-exploration.ipynb` - the starter notebook; replace its question with the project's first
  one and keep the conclusion in the last cell
- One notebook per question, with a markdown conclusion that states the finding
- Keep the model in a `.py` file beside the notebook, so tests and tools can import it
- Cache large intermediate arrays under `notebooks/cache/` (gitignored), and export results once
- Execute the notebook with `jupyter nbconvert --to notebook --execute --inplace` before committing
  conclusions
