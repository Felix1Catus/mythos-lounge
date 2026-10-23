# P03 INSTRUMENT_SELFTEST — kills U2 (instrument-trust)

**TRIGGER:** Before consuming any instrument output; before handing any instrument to the user.

**RULE:** No instrument is handed to the user and no instrument output is consumed until it
passes a logged known-answer self-test (capture hook fetches known URL → "hook active=ok";
parser round-trips a known sample; browser driver screenshots proof). Instrument output
contradicting client ground truth is WRONG until exonerated. Third fix on the same
instrument in one session → stop, rebuild the self-test from scratch, don't patch again.
Machine form: `python3 ~/targets/_shared/probelib.py` self-test must PASS (3 arms).
