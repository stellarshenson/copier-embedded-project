# Circuit simulation

An LTspice-compatible netlist of the circuit around the MCU pin. The ATtiny84 PA0 output drives a
non-inverting op-amp with gain 2. The firmware itself is not co-simulated: the pin is a 0-5 V pulse
at 1 kHz, the shape the starter firmware produces, and the analog circuit is simulated around it.

- `circuit.cir` - the netlist. LTspice opens it with File > Open or runs it in batch with
  `ltspice -b circuit.cir`; ngspice runs it with `ngspice -b circuit.cir`.
- `run.py` - the non-interactive runner. It uses LTspice when it is on PATH, otherwise ngspice,
  prints one JSON line and fails when the gain is wrong.
- `test_circuit.py` - the pytest wrapper. It skips with the reason when neither simulator exists.

The input divider R1/R2 scales 5 V to 2.5 V; the feedback R3/R4 sets gain 2, so the output swings
0 V to 5 V. The measurement points are 0.25 ms (input high) and 0.75 ms (input low).

The component is opt-in. A project without it carries no `ltspice/` folder and no `ltspice` target.
