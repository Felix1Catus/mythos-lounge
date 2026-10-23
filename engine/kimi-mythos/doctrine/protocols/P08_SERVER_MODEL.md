# P08 SERVER_MODEL — kills U12 (checklist-trap)

**TRIGGER:** Per program, continuously; review before every session's first probe.

**RULE:** Maintain `STATE/TARGET_MODEL.md` (HOW_THE_TARGET_THINKS): the server's mental
model inferred from its own client + responses — trust boundaries, what's recomputed
server-side vs trusted from client, state machines, enum maps, error branches. Every
response either confirms or UPDATES the model. 0days live in the delta between model and
implementation: hunt (a) values the server trusts from the client without recomputation,
(b) two code paths validating the same input differently (parser/normalizer differentials),
(c) states reachable out of order (race/TOCTOU, step-skips), (d) business-model trust
(invitation/deposit/non-pay/enterprise flows), (e) branches your error ladder mapped but
never entered.
