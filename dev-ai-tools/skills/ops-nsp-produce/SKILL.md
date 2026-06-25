---
name: ops-nsp-produce
description: >
  Produce a message to an NSP (Nike Streaming Platform) Kafka topic.
  Guides the user through providing broker, topic, and credential
  configuration, preparing a JSON payload, and running the producer
  script. The "ops-" prefix denotes an operations skill (as opposed
  to "dev-" for development skills). Use when the user wants to
  publish, produce, or send a message to an NSP Kafka topic or stream.
---

# NSP Kafka Producer

Produces a message to an NSP Kafka topic using OAuth-authenticated
SASL_SSL. The user provides all connection details -- this skill does
not attempt to discover stream configuration automatically.

## Related skills

- **`github`** -- GitHub operations gateway

## Prerequisites

The producer script requires `confluent_kafka` and `requests`, which
in turn require `librdkafka`.

```bash
brew install librdkafka
pip install confluent-kafka requests
```

If `confluent_kafka` fails to import, check that `librdkafka` is
installed and `pip install` was run in the correct Python environment.

## Phase 1: Gather configuration

Use **AskQuestion** to collect the following from the user. Do not
attempt to discover these automatically.

### 1. Broker URL

The NSP broker endpoint, e.g.
`<uuid>.na.nrtd.platforms.nike.com:9500`.

Direct the user to find it in the NSP UI at
`https://streams.platforms.nike.com` under their stream's connection
details.

### 2. Topic name

The full NSP topic name. Direct the user to find it in the NSP UI
under their stream's topics.

### 3. Credentials

`CLIENT_ID` and `CLIENT_SECRET` must be set as environment variables.
Direct the user to retrieve these from Cerberus or wherever their
service stores its NSP credentials.

**Never accept credentials as CLI arguments.**

Verify they are set:

```bash
[ -n "$CLIENT_ID" ] && [ -n "$CLIENT_SECRET" ] && echo "Credentials set" || echo "ERROR: set CLIENT_ID and CLIENT_SECRET"
```

### 4. Token URL

Default: `https://nike.okta.com/oauth2/aus27z7p76as9Dz0H1t7/v1/token`

Ask the user to confirm or provide an override if their service uses
a different Okta org.

## Phase 2: Prepare the payload

Ask the user for the message payload. Options:

1. **JSON file** -- path to an existing `.json` file
2. **Inline JSON** -- write a JSON file from user-provided content
3. **Stdin** -- pipe from another command (use `--payload -`)

Before producing, validate the payload is valid JSON:

```bash
python3 -m json.tool <payload-file> > /dev/null
```

Show the user a summary (file path, byte size, first few lines) and
ask for confirmation before sending.

## Phase 3: Produce the message

Resolve `SKILL_DIR` as the directory containing this `SKILL.md` file.

Run the producer script:

```bash
python3 "${SKILL_DIR}/scripts/nsp-produce.py" \
  --broker "<broker-url>" \
  --topic "<topic-name>" \
  --payload "<path-to-json-file>"
```

Optional arguments:

- `--key "<message-key>"` -- sets the Kafka message key
- `--token-url "<url>"` -- overrides the default Okta token URL

The script will:

1. Validate all required parameters
2. Print a summary (broker, topic, payload size)
3. Authenticate via OAuth
4. Produce the message
5. Report delivery result (topic, partition, offset) or failure

## Phase 4: Verify (optional)

Suggest the user verify the message was consumed using whatever
observability tools are appropriate for their service (e.g. Splunk,
SignalFx, application logs).
